from __future__ import annotations

import re
import secrets
from typing import Any

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.exceptions import bad_request, forbidden, not_found, service_unavailable
from app.core.security import decrypt_secret, encrypt_secret
from app.models import User
from app.modules.database import (
    DATABASE_MANAGE_OTHERS,
    DATABASE_OPERATE,
    DATABASE_READ,
    SQL_SCRIPT_MANAGE_OTHERS,
)
from app.modules.database.engines import (
    ExternalDatabase,
    classify_sql,
    placeholder_name,
    split_sql_statements,
    test_external_connection,
)
from app.modules.database.models import DatabaseConnection, SqlScript
from app.modules.database.repositories import DatabaseConnectionRepository, SqlScriptRepository
from app.modules.database.schemas import (
    AlterTableRequest,
    ColumnDefinition,
    CreateTableRequest,
    DatabaseConnectionItem,
    DatabaseConnectionListResponse,
    DatabaseConnectionPayload,
    DatabaseTestRequest,
    QueryRequest,
    QueryResponse,
    RenameTableRequest,
    RowCreateRequest,
    RowDeleteRequest,
    RowUpdateRequest,
    RunScriptRequest,
    RunScriptResponse,
    SchemaAlterRequest,
    SchemaCreateRequest,
    SchemaItem,
    ScriptStatementResult,
    SqlScriptItem,
    SqlScriptListResponse,
    SqlScriptPayload,
    TableDataResponse,
    TableItem,
    clean_identifier,
)
from app.services.audit import audit_changes, audit_detail, record_audit
from app.services.permissions import has_permission

GENERATED_ID_PREFIX = "db_"
TYPE_RE = re.compile(r"^[A-Za-z0-9_(),\s]+$")
SAFE_DEFAULT_RE = re.compile(r"^[A-Za-z0-9_\-:.@\s]*$")


class DatabaseService:
    def __init__(self, db: Session):
        self.db = db
        self.connections = DatabaseConnectionRepository(db)
        self.scripts = SqlScriptRepository(db)

    def list_connections(
        self,
        actor: User,
        keyword: str = "",
        db_type: str = "",
        shared: str = "",
        is_active: bool | None = None,
        created_by: str = "",
        sort_order: str = "descend",
        page: int = 1,
        page_size: int = 20,
    ) -> DatabaseConnectionListResponse:
        visible_to = None if has_permission(actor, DATABASE_MANAGE_OTHERS) else actor.id
        is_shared = {"shared": True, "private": False}.get(shared)
        created_by_user_id = actor.id if created_by == "me" else None
        rows, total = self.connections.list(
            keyword,
            db_type,
            is_shared,
            is_active,
            created_by_user_id,
            visible_to,
            "ascend" if sort_order == "ascend" else "descend",
            page,
            page_size,
        )
        return DatabaseConnectionListResponse(items=self._connections_with_creators(rows), total=total, page=page, page_size=page_size)

    def create(self, actor: User, payload: DatabaseConnectionPayload) -> DatabaseConnectionItem:
        if not payload.password:
            raise bad_request("error.databasePasswordRequired", "Password is required")
        conn_id = payload.conn_id or self._generate_conn_id()
        if self.connections.get_by_conn_id(conn_id) is not None:
            raise bad_request("error.databaseIdTaken", "Connection ID already exists")
        connection = self.connections.create(
            DatabaseConnection(
                conn_id=conn_id,
                name=payload.name,
                db_type=payload.db_type,
                host=payload.host,
                port=payload.port,
                username=payload.username,
                password_encrypted=encrypt_secret(payload.password),
                default_database=payload.default_database,
                is_shared=payload.is_shared,
                is_active=payload.is_active,
                created_by=actor.id,
            )
        )
        record_audit(
            self.db,
            actor.id,
            "database.create",
            "database",
            connection.conn_id,
            connection.name,
            audit_detail(connection.name, meta=_connection_snapshot(connection)),
        )
        self.db.commit()
        return self._connection_with_creator(connection, actor.username)

    def update(self, actor: User, connection_id: int, payload: DatabaseConnectionPayload) -> DatabaseConnectionItem:
        connection = self._get(connection_id)
        self._ensure_can_manage(actor, connection)
        before = _connection_snapshot(connection)
        connection.name = payload.name
        connection.db_type = payload.db_type
        connection.host = payload.host
        connection.port = payload.port
        connection.username = payload.username
        connection.default_database = payload.default_database
        connection.is_shared = payload.is_shared
        connection.is_active = payload.is_active
        if payload.password:
            connection.password_encrypted = encrypt_secret(payload.password)
        record_audit(
            self.db,
            actor.id,
            "database.update",
            "database",
            connection.conn_id,
            connection.name,
            audit_detail(connection.name, audit_changes(before, _connection_snapshot(connection))),
        )
        self.db.commit()
        return self._connection_with_creator(connection, self._creator_username(connection))

    def delete(self, actor: User, connection_id: int) -> None:
        connection = self._get(connection_id)
        self._ensure_can_manage(actor, connection)
        record_audit(
            self.db,
            actor.id,
            "database.delete",
            "database",
            connection.conn_id,
            connection.name,
            audit_detail(connection.name, meta=_connection_snapshot(connection)),
        )
        self.connections.delete(connection)
        self.db.commit()

    def test_connection(self, actor: User, payload: DatabaseTestRequest) -> None:
        password = payload.password
        if not password and payload.id is not None:
            connection = self._get(payload.id)
            self._ensure_can_manage(actor, connection)
            password = self._password(connection)
        if not password:
            raise bad_request("error.databasePasswordRequired", "Password is required")
        test_external_connection(
            DatabaseConnection(
                conn_id="test",
                name="test",
                db_type=payload.db_type,
                host=payload.host,
                port=payload.port,
                username=payload.username,
                password_encrypted="",
                default_database=payload.default_database,
                is_shared=False,
                is_active=True,
                created_by=actor.id,
            ),
            password,
        )

    def schemas(self, actor: User, conn_id: str) -> list[SchemaItem]:
        connection = self._get_usable(actor, conn_id)
        with self._runtime(connection) as runtime:
            return [SchemaItem(name=name) for name in runtime.schemas()]

    def tables(self, actor: User, conn_id: str, database: str = "") -> list[TableItem]:
        connection = self._get_usable(actor, conn_id)
        database = self._database_name(connection, database)
        with self._runtime(connection, database) as runtime:
            return [TableItem(name=name) for name in runtime.tables(database)]

    def columns(self, actor: User, conn_id: str, database: str, table: str):
        connection = self._get_usable(actor, conn_id)
        database = self._database_name(connection, database)
        with self._runtime(connection, database) as runtime:
            return runtime.columns(table, database)

    def table_data(
        self,
        actor: User,
        conn_id: str,
        database: str,
        table: str,
        page: int,
        page_size: int,
        order_by: str = "",
        order_desc: bool = False,
        filter_value: str = "",
        include_total: bool = True,
    ) -> TableDataResponse:
        connection = self._get_usable(actor, conn_id)
        database = self._database_name(connection, database)
        table = clean_identifier(table, "table")
        with self._runtime(connection, database) as runtime:
            columns = runtime.columns(table, database)
            primary_keys = runtime.primary_keys(table, database)
            where_sql, params = _filter_clause(runtime, columns, filter_value)
            rows = runtime.table_rows(table, database, page, page_size, order_by, order_desc, where_sql, params)
            total_exact = include_total or len(rows) < page_size
            total = runtime.table_total(table, database, where_sql, params) if include_total else _estimated_total(page, page_size, len(rows))
        return TableDataResponse(
            columns=columns,
            primary_keys=primary_keys,
            rows=rows,
            total=total,
            total_exact=total_exact,
            page=page,
            page_size=page_size,
        )

    def query(self, actor: User, conn_id: str, payload: QueryRequest) -> QueryResponse:
        connection = self._get_usable(actor, conn_id)
        sql_type = classify_sql(payload.sql)
        self._ensure_sql_permission(actor, sql_type)
        database = self._database_name(connection, payload.database)
        try:
            with self._runtime(connection, database) as runtime:
                if sql_type == "read":
                    columns, rows, total, _ = runtime.execute_sql(payload.sql, payload.page, payload.page_size)
                    response = QueryResponse(
                        statement_type="read",
                        columns=columns,
                        rows=rows,
                        total=total,
                        page=payload.page,
                        page_size=payload.page_size,
                    )
                else:
                    affected = runtime.execute_write(payload.sql)
                    response = QueryResponse(statement_type="write", affected_rows=affected)
        except SQLAlchemyError as exc:
            raise bad_request("error.databaseSqlFailed", str(exc)) from exc
        record_audit(
            self.db,
            actor.id,
            "database.query",
            "database",
            connection.conn_id,
            connection.name,
            audit_detail(connection.name, meta={"type": sql_type}),
        )
        self.db.commit()
        return response

    def run_script(self, actor: User, conn_id: str, payload: RunScriptRequest) -> RunScriptResponse:
        connection = self._get_usable(actor, conn_id)
        if not has_permission(actor, DATABASE_OPERATE):
            raise forbidden()
        content = payload.content.strip()
        if not content and payload.script_id is not None:
            script = self._get_script_visible(actor, payload.script_id)
            content = script.content.strip()
        if not content:
            raise bad_request("error.sqlScriptContentRequired", "SQL script content is required")
        database = self._database_name(connection, payload.database)
        statements = split_sql_statements(content)
        results: list[ScriptStatementResult] = []
        stopped = False
        with self._runtime(connection, database) as runtime:
            for index, statement in enumerate(statements, start=1):
                try:
                    if classify_sql(statement) == "read":
                        columns, rows, _, _ = runtime.execute_sql(statement, 1, 200)
                        results.append(ScriptStatementResult(index=index, sql=statement, ok=True, columns=columns, rows=rows))
                    else:
                        affected = runtime.execute_write(statement)
                        results.append(ScriptStatementResult(index=index, sql=statement, ok=True, affected_rows=affected))
                except SQLAlchemyError as exc:
                    results.append(ScriptStatementResult(index=index, sql=statement, ok=False, message=str(exc)))
                    if payload.stop_on_error:
                        stopped = True
                        break
        record_audit(
            self.db,
            actor.id,
            "database.run_script",
            "database",
            connection.conn_id,
            connection.name,
            audit_detail(connection.name, meta={"count": len(results), "stopped": stopped}),
        )
        self.db.commit()
        return RunScriptResponse(results=results, stopped=stopped)

    def create_row(self, actor: User, conn_id: str, payload: RowCreateRequest) -> int:
        connection = self._get_usable(actor, conn_id)
        self._ensure_operate(actor)
        columns = [clean_identifier(column, "column") for column in payload.values]
        with self._runtime(connection, self._database_name(connection, payload.database)) as runtime:
            table = runtime.qualified_table(payload.table, payload.database)
            quoted = ", ".join(runtime.quote_identifier(column) for column in columns)
            placeholders = ", ".join(f":{placeholder_name(column)}" for column in columns)
            params = {placeholder_name(column): payload.values[column] for column in payload.values}
            return self._execute_audited(runtime, f"INSERT INTO {table} ({quoted}) VALUES ({placeholders})", params, actor, connection, "database.row_create")

    def update_row(self, actor: User, conn_id: str, payload: RowUpdateRequest) -> int:
        connection = self._get_usable(actor, conn_id)
        self._ensure_operate(actor)
        if not payload.keys:
            raise bad_request("error.databaseRowKeyRequired", "Row key is required")
        with self._runtime(connection, self._database_name(connection, payload.database)) as runtime:
            table = runtime.qualified_table(payload.table, payload.database)
            set_sql, set_params = _assignment_clause(runtime, payload.values, "set")
            where_sql, where_params = _where_keys(runtime, payload.keys)
            sql = f"UPDATE {table} SET {set_sql} WHERE {where_sql}"
            return self._execute_audited(runtime, sql, {**set_params, **where_params}, actor, connection, "database.row_update")

    def delete_row(self, actor: User, conn_id: str, payload: RowDeleteRequest) -> int:
        connection = self._get_usable(actor, conn_id)
        self._ensure_operate(actor)
        if not payload.keys:
            raise bad_request("error.databaseRowKeyRequired", "Row key is required")
        with self._runtime(connection, self._database_name(connection, payload.database)) as runtime:
            table = runtime.qualified_table(payload.table, payload.database)
            where_sql, params = _where_keys(runtime, payload.keys)
            return self._execute_audited(runtime, f"DELETE FROM {table} WHERE {where_sql}", params, actor, connection, "database.row_delete")

    def create_table(self, actor: User, conn_id: str, payload: CreateTableRequest) -> None:
        connection = self._get_usable(actor, conn_id)
        self._ensure_operate(actor)
        with self._runtime(connection, self._database_name(connection, payload.database)) as runtime:
            table_name = runtime.qualified_table(payload.name, payload.database)
            prefix = "CREATE TABLE IF NOT EXISTS" if payload.if_not_exists else "CREATE TABLE"
            columns_sql = ", ".join(_column_definition_sql(runtime, column) for column in payload.columns)
            runtime.execute_write(f"{prefix} {table_name} ({columns_sql})")
        self._audit_operate(actor, connection, "database.table_create", {"table": payload.name})

    def table_detail(self, actor: User, conn_id: str, database: str, table: str) -> dict[str, Any]:
        connection = self._get_usable(actor, conn_id)
        database = self._database_name(connection, database)
        with self._runtime(connection, database) as runtime:
            return {"columns": runtime.columns(table, database), "primary_keys": runtime.primary_keys(table, database)}

    def alter_table(self, actor: User, conn_id: str, table: str, payload: AlterTableRequest) -> None:
        connection = self._get_usable(actor, conn_id)
        self._ensure_operate(actor)
        table = clean_identifier(table, "table")
        with self._runtime(connection, self._database_name(connection, payload.database)) as runtime:
            table_name = runtime.qualified_table(table, payload.database)
            for item in payload.actions:
                if item.action == "add_column" and item.column:
                    runtime.execute_write(f"ALTER TABLE {table_name} ADD COLUMN {_column_definition_sql(runtime, item.column)}")
                elif item.action == "modify_column" and item.column:
                    keyword = "MODIFY COLUMN" if connection.db_type != "sqlite" else "ALTER COLUMN"
                    runtime.execute_write(f"ALTER TABLE {table_name} {keyword} {_column_definition_sql(runtime, item.column)}")
                elif item.action == "drop_column" and item.name:
                    runtime.execute_write(f"ALTER TABLE {table_name} DROP COLUMN {runtime.quote_identifier(item.name)}")
                else:
                    raise bad_request("error.databaseAlterInvalid", "Invalid alter table action")
        self._audit_operate(actor, connection, "database.table_alter", {"table": table})

    def rename_table(self, actor: User, conn_id: str, table: str, payload: RenameTableRequest) -> None:
        connection = self._get_usable(actor, conn_id)
        self._ensure_operate(actor)
        table = clean_identifier(table, "table")
        with self._runtime(connection, self._database_name(connection, payload.database)) as runtime:
            runtime.execute_write(f"RENAME TABLE {runtime.qualified_table(table, payload.database)} TO {runtime.qualified_table(payload.new_name, payload.database)}")
        self._audit_operate(actor, connection, "database.table_rename", {"table": table, "new_name": payload.new_name})

    def truncate_table(self, actor: User, conn_id: str, database: str, table: str) -> None:
        connection = self._get_usable(actor, conn_id)
        self._ensure_operate(actor)
        table = clean_identifier(table, "table")
        with self._runtime(connection, self._database_name(connection, database)) as runtime:
            runtime.execute_write(f"TRUNCATE TABLE {runtime.qualified_table(table, database)}")
        self._audit_operate(actor, connection, "database.table_truncate", {"table": table})

    def delete_table(self, actor: User, conn_id: str, database: str, table: str) -> None:
        connection = self._get_usable(actor, conn_id)
        self._ensure_operate(actor)
        table = clean_identifier(table, "table")
        with self._runtime(connection, self._database_name(connection, database)) as runtime:
            runtime.execute_write(f"DROP TABLE {runtime.qualified_table(table, database)}")
        self._audit_operate(actor, connection, "database.table_delete", {"table": table})

    def create_schema(self, actor: User, conn_id: str, payload: SchemaCreateRequest) -> None:
        connection = self._get_usable(actor, conn_id)
        self._ensure_operate(actor)
        with self._runtime(connection) as runtime:
            charset = _safe_option(payload.charset, "charset")
            collation = _safe_option(payload.collation, "collation")
            suffix = f" CHARACTER SET {charset}" if charset else ""
            suffix += f" COLLATE {collation}" if collation else ""
            runtime.execute_write(f"CREATE DATABASE {runtime.quote_identifier(payload.name)}{suffix}")
        self._audit_operate(actor, connection, "database.schema_create", {"schema": payload.name})

    def alter_schema(self, actor: User, conn_id: str, name: str, payload: SchemaAlterRequest) -> None:
        connection = self._get_usable(actor, conn_id)
        self._ensure_operate(actor)
        name = clean_identifier(name, "schema")
        with self._runtime(connection) as runtime:
            charset = _safe_option(payload.charset, "charset")
            collation = _safe_option(payload.collation, "collation")
            if not charset and not collation:
                raise bad_request("error.databaseSchemaAlterEmpty", "No schema option provided")
            suffix = f" CHARACTER SET {charset}" if charset else ""
            suffix += f" COLLATE {collation}" if collation else ""
            runtime.execute_write(f"ALTER DATABASE {runtime.quote_identifier(name)}{suffix}")
        self._audit_operate(actor, connection, "database.schema_alter", {"schema": name})

    def delete_schema(self, actor: User, conn_id: str, name: str) -> None:
        connection = self._get_usable(actor, conn_id)
        self._ensure_operate(actor)
        name = clean_identifier(name, "schema")
        with self._runtime(connection) as runtime:
            runtime.execute_write(f"DROP DATABASE {runtime.quote_identifier(name)}")
        self._audit_operate(actor, connection, "database.schema_delete", {"schema": name})

    def _get(self, connection_id: int) -> DatabaseConnection:
        connection = self.connections.get(connection_id)
        if connection is None:
            raise not_found()
        return connection

    def _get_usable(self, actor: User, conn_id: str) -> DatabaseConnection:
        connection = self.connections.get_by_conn_id(conn_id)
        if connection is None:
            raise not_found()
        if not connection.is_active:
            raise forbidden("error.databaseInactive", "Database connection is inactive")
        self._ensure_can_use(actor, connection)
        return connection

    def _ensure_can_use(self, actor: User, connection: DatabaseConnection) -> None:
        if connection.created_by == actor.id or connection.is_shared or has_permission(actor, DATABASE_MANAGE_OTHERS):
            return
        raise forbidden()

    def _ensure_can_manage(self, actor: User, connection: DatabaseConnection) -> None:
        if connection.created_by == actor.id or has_permission(actor, DATABASE_MANAGE_OTHERS):
            return
        raise forbidden()

    def _ensure_sql_permission(self, actor: User, sql_type: str) -> None:
        required = DATABASE_READ if sql_type == "read" else DATABASE_OPERATE
        if not has_permission(actor, required):
            raise forbidden()

    def _ensure_operate(self, actor: User) -> None:
        if not has_permission(actor, DATABASE_OPERATE):
            raise forbidden()

    def _runtime(self, connection: DatabaseConnection, database: str = "") -> ExternalDatabase:
        return ExternalDatabase(connection, self._password(connection), database)

    def _password(self, connection: DatabaseConnection) -> str:
        try:
            return decrypt_secret(connection.password_encrypted)
        except ValueError as exc:
            raise service_unavailable("error.databasePasswordInvalid", "Stored database password cannot be decrypted") from exc

    def _database_name(self, connection: DatabaseConnection, database: str = "") -> str:
        value = database.strip() or connection.default_database or ""
        return clean_identifier(value, "schema") if value else ""

    def _generate_conn_id(self) -> str:
        while True:
            conn_id = f"{GENERATED_ID_PREFIX}{secrets.token_urlsafe(8).replace('-', '').replace('_', '')[:12]}"
            if self.connections.get_by_conn_id(conn_id) is None:
                return conn_id

    def _connections_with_creators(self, rows: list[DatabaseConnection]) -> list[DatabaseConnectionItem]:
        names = self.connections.creator_usernames({row.created_by for row in rows if row.created_by is not None})
        return [self._connection_with_creator(row, names.get(row.created_by, "")) for row in rows]

    def _connection_with_creator(self, connection: DatabaseConnection, username: str = "") -> DatabaseConnectionItem:
        return DatabaseConnectionItem.model_validate(connection).model_copy(update={"created_by_username": username})

    def _creator_username(self, connection: DatabaseConnection) -> str:
        if connection.created_by is None:
            return ""
        return self.connections.creator_usernames({connection.created_by}).get(connection.created_by, "")

    def _get_script_visible(self, actor: User, script_id: int) -> SqlScript:
        script = self.scripts.get(script_id)
        if script is None:
            raise not_found()
        if script.created_by == actor.id or script.is_shared or has_permission(actor, SQL_SCRIPT_MANAGE_OTHERS):
            return script
        raise forbidden()

    def _execute_audited(
        self,
        runtime: ExternalDatabase,
        sql: str,
        params: dict[str, Any],
        actor: User,
        connection: DatabaseConnection,
        action: str,
    ) -> int:
        with runtime.engine.begin() as conn:
            result = conn.execute(text(sql), params)
            affected = result.rowcount if result.rowcount and result.rowcount > 0 else 0
        self._audit_operate(actor, connection, action, {"affected_rows": affected})
        return affected

    def _audit_operate(self, actor: User, connection: DatabaseConnection, action: str, meta: dict[str, Any]) -> None:
        record_audit(
            self.db,
            actor.id,
            action,
            "database",
            connection.conn_id,
            connection.name,
            audit_detail(connection.name, meta=meta),
        )
        self.db.commit()

class SqlScriptService:
    def __init__(self, db: Session):
        self.db = db
        self.scripts = SqlScriptRepository(db)
        self.connections = DatabaseConnectionRepository(db)

    def list_scripts(
        self,
        actor: User,
        keyword: str = "",
        connection_id: int | None = None,
        database: str | None = None,
        shared: str = "",
        created_by: str = "",
        page: int = 1,
        page_size: int = 20,
    ) -> SqlScriptListResponse:
        visible_to = None if has_permission(actor, SQL_SCRIPT_MANAGE_OTHERS) else actor.id
        is_shared = {"shared": True, "private": False}.get(shared)
        created_by_user_id = actor.id if created_by == "me" else None
        rows, total = self.scripts.list(keyword, connection_id, database, is_shared, created_by_user_id, visible_to, page, page_size)
        return SqlScriptListResponse(items=[self._item(row) for row in rows], total=total, page=page, page_size=page_size)

    def create(self, actor: User, payload: SqlScriptPayload) -> SqlScriptItem:
        self._ensure_connection_visible(actor, payload.connection_id)
        script = self.scripts.create(
            SqlScript(
                name=payload.name,
                content=payload.content,
                connection_id=payload.connection_id,
                database=payload.database,
                description=payload.description,
                is_shared=payload.is_shared,
                created_by=actor.id,
            )
        )
        record_audit(self.db, actor.id, "sql_script.create", "sql_script", str(script.id), script.name, audit_detail(script.name))
        self.db.commit()
        return self._item(script)

    def update(self, actor: User, script_id: int, payload: SqlScriptPayload) -> SqlScriptItem:
        script = self._get(script_id)
        self._ensure_can_manage(actor, script)
        self._ensure_connection_visible(actor, payload.connection_id)
        before = _script_snapshot(script)
        script.name = payload.name
        script.content = payload.content
        script.connection_id = payload.connection_id
        script.database = payload.database
        script.description = payload.description
        script.is_shared = payload.is_shared
        record_audit(
            self.db,
            actor.id,
            "sql_script.update",
            "sql_script",
            str(script.id),
            script.name,
            audit_detail(script.name, audit_changes(before, _script_snapshot(script))),
        )
        self.db.commit()
        return self._item(script)

    def delete(self, actor: User, script_id: int) -> None:
        script = self._get(script_id)
        self._ensure_can_manage(actor, script)
        record_audit(self.db, actor.id, "sql_script.delete", "sql_script", str(script.id), script.name, audit_detail(script.name))
        self.scripts.delete(script)
        self.db.commit()

    def _get(self, script_id: int) -> SqlScript:
        script = self.scripts.get(script_id)
        if script is None:
            raise not_found()
        return script

    def _ensure_can_manage(self, actor: User, script: SqlScript) -> None:
        if script.created_by == actor.id or has_permission(actor, SQL_SCRIPT_MANAGE_OTHERS):
            return
        raise forbidden()

    def _ensure_connection_visible(self, actor: User, connection_id: int | None) -> None:
        if connection_id is None:
            return
        connection = self.connections.get(connection_id)
        if connection is None:
            raise not_found()
        if connection.created_by == actor.id or connection.is_shared or has_permission(actor, DATABASE_MANAGE_OTHERS):
            return
        raise forbidden()

    def _item(self, script: SqlScript) -> SqlScriptItem:
        connection = self.connections.get(script.connection_id) if script.connection_id else None
        creator_name = ""
        if script.created_by is not None:
            creator_name = self.scripts.creator_usernames({script.created_by}).get(script.created_by, "")
        return SqlScriptItem.model_validate(script).model_copy(
            update={
                "connection_name": connection.name if connection else "",
                "created_by_username": creator_name,
            }
        )


def _connection_snapshot(connection: DatabaseConnection) -> dict[str, object]:
    return {
        "conn_id": connection.conn_id,
        "name": connection.name,
        "db_type": connection.db_type,
        "host": connection.host,
        "port": connection.port,
        "username": connection.username,
        "default_database": connection.default_database,
        "is_shared": connection.is_shared,
        "is_active": connection.is_active,
    }


def _script_snapshot(script: SqlScript) -> dict[str, object]:
    return {
        "name": script.name,
        "connection_id": script.connection_id,
        "database": script.database,
        "description": script.description,
        "is_shared": script.is_shared,
    }


def _filter_clause(runtime: ExternalDatabase, columns, value: str) -> tuple[str, dict[str, Any]]:
    keyword = value.strip()
    if not keyword:
        return "", {}
    parts = []
    params: dict[str, Any] = {"filter": f"%{keyword}%"}
    for column in columns:
        parts.append(f"CAST({runtime.quote_identifier(column.name)} AS CHAR) LIKE :filter")
    return f" WHERE ({' OR '.join(parts)})" if parts else "", params


def _assignment_clause(runtime: ExternalDatabase, values: dict[str, Any], prefix: str) -> tuple[str, dict[str, Any]]:
    if not values:
        raise bad_request("error.databaseRowValuesRequired", "Row values are required")
    parts = []
    params = {}
    for name, value in values.items():
        clean = clean_identifier(name, "column")
        param = f"{prefix}_{placeholder_name(clean)}"
        parts.append(f"{runtime.quote_identifier(clean)} = :{param}")
        params[param] = value
    return ", ".join(parts), params


def _where_keys(runtime: ExternalDatabase, keys: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    parts = []
    params = {}
    for name, value in keys.items():
        clean = clean_identifier(name, "column")
        param = f"key_{placeholder_name(clean)}"
        parts.append(f"{runtime.quote_identifier(clean)} = :{param}")
        params[param] = value
    return " AND ".join(parts), params


def _estimated_total(page: int, page_size: int, row_count: int) -> int:
    loaded_until = max(page - 1, 0) * page_size + row_count
    return loaded_until + (1 if row_count >= page_size else 0)


def _column_definition_sql(runtime: ExternalDatabase, column: ColumnDefinition) -> str:
    column_type = _safe_column_type(column.type)
    parts = [runtime.quote_identifier(column.name), column_type]
    if column.primary_key:
        parts.append("PRIMARY KEY")
    if column.autoincrement:
        parts.append("AUTO_INCREMENT")
    if not column.nullable:
        parts.append("NOT NULL")
    if column.default:
        parts.append(f"DEFAULT {_literal_default(column.default)}")
    return " ".join(parts)


def _safe_column_type(value: str) -> str:
    cleaned = value.strip().upper()
    if not cleaned or not TYPE_RE.fullmatch(cleaned):
        raise bad_request("error.databaseColumnTypeInvalid", "Invalid column type")
    return cleaned


def _literal_default(value: str) -> str:
    cleaned = value.strip()
    upper = cleaned.upper()
    if upper in {"CURRENT_TIMESTAMP", "CURRENT_DATE", "CURRENT_TIME", "NULL"}:
        return upper
    if not SAFE_DEFAULT_RE.fullmatch(cleaned):
        raise bad_request("error.databaseColumnDefaultInvalid", "Invalid column default")
    return "'" + cleaned.replace("'", "''") + "'"


def _safe_option(value: str, label: str) -> str:
    cleaned = value.strip()
    if not cleaned:
        return ""
    if not re.fullmatch(r"^[A-Za-z0-9_]+$", cleaned):
        raise bad_request("error.databaseOptionInvalid", f"Invalid {label}")
    return cleaned
