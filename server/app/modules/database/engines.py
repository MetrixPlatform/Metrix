from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any
from urllib.parse import quote_plus

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import Engine, URL
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.pool import NullPool

from app.core.exceptions import bad_request, service_unavailable
from app.modules.database.models import DatabaseConnection
from app.modules.database.schemas import ColumnItem, TableIndexItem, clean_identifier

READ_SQL_KEYWORDS = {"SELECT", "SHOW", "DESC", "DESCRIBE", "EXPLAIN", "WITH"}
PAGEABLE_READ_KEYWORDS = {"SELECT", "WITH"}
MAX_PAGE_SIZE = 1000
DEFAULT_TIMEOUT_SECONDS = 30
# Connecting to a dead server should fail fast, but reads/writes can be legitimately
# long-running (imports and report SQL doing CREATE TABLE ... AS SELECT over millions of
# rows). Capping read/write at 30s killed such statements ("Lost connection ... read
# operation timed out"), so query timeouts are kept generous while connect stays short.
DEFAULT_QUERY_TIMEOUT_SECONDS = 3600


@dataclass(frozen=True)
class Dialect:
    key: str
    url_prefix: str
    default_port: int
    quote_char: str = "`"


DIALECTS = {
    "mysql": Dialect("mysql", "mysql+pymysql", 3306),
    "mariadb": Dialect("mariadb", "mysql+pymysql", 3306),
    # SQLite is kept for deterministic tests and local verification; UI only exposes MySQL/MariaDB.
    "sqlite": Dialect("sqlite", "sqlite", 0, '"'),
}


class ExternalDatabase:
    def __init__(self, connection: DatabaseConnection, password: str, database: str = ""):
        self.connection = connection
        self.password = password
        self.database = database.strip() or connection.default_database or ""
        self.dialect = dialect_for(connection.db_type)
        self.engine = create_external_engine(connection, password, self.database)

    def __enter__(self) -> ExternalDatabase:
        return self

    def __exit__(self, *_: object) -> None:
        self.dispose()

    def dispose(self) -> None:
        self.engine.dispose()

    def schemas(self) -> list[str]:
        inspector = inspect(self.engine)
        if self.connection.db_type == "sqlite":
            return ["main"]
        names = [
            name
            for name in inspector.get_schema_names()
            if name not in {"information_schema", "mysql", "performance_schema", "sys"}
        ]
        return sorted(names)

    def tables(self, database: str = "") -> list[str]:
        schema = _schema_arg(database or self.database, self.connection.db_type)
        inspector = inspect(self.engine)
        return sorted(inspector.get_table_names(schema=schema))

    def columns(self, table: str, database: str = "") -> list[ColumnItem]:
        schema = _schema_arg(database or self.database, self.connection.db_type)
        inspector = inspect(self.engine)
        primary_keys = set(inspector.get_pk_constraint(table, schema=schema).get("constrained_columns") or [])
        columns = []
        for column in inspector.get_columns(table, schema=schema):
            columns.append(
                ColumnItem(
                    name=column["name"],
                    type=str(column.get("type", "")),
                    nullable=bool(column.get("nullable", True)),
                    default=column.get("default"),
                    primary_key=column["name"] in primary_keys,
                    autoincrement=bool(column.get("autoincrement", False)),
                    comment=str(column.get("comment") or ""),
                )
            )
        return columns

    def primary_keys(self, table: str, database: str = "") -> list[str]:
        schema = _schema_arg(database or self.database, self.connection.db_type)
        return list(inspect(self.engine).get_pk_constraint(table, schema=schema).get("constrained_columns") or [])

    def indexes(self, table: str, database: str = "") -> list[TableIndexItem]:
        schema = _schema_arg(database or self.database, self.connection.db_type)
        indexes = []
        for item in inspect(self.engine).get_indexes(table, schema=schema):
            indexes.append(
                TableIndexItem(
                    name=str(item.get("name") or ""),
                    columns=[str(column) for column in item.get("column_names") or []],
                    unique=bool(item.get("unique", False)),
                )
            )
        return indexes

    def table_total(self, table: str, database: str = "", where_sql: str = "", params: dict[str, Any] | None = None) -> int:
        sql = f"SELECT COUNT(*) AS total FROM {self.qualified_table(table, database)}{where_sql}"
        with self.engine.connect() as conn:
            return int(conn.execute(text(sql), params or {}).scalar() or 0)

    def table_rows(
        self,
        table: str,
        database: str = "",
        page: int = 1,
        page_size: int = 100,
        order_by: str = "",
        order_desc: bool = False,
        where_sql: str = "",
        params: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        page_size = clamp_page_size(page_size)
        offset = max(page - 1, 0) * page_size
        order = ""
        if order_by:
            order = f" ORDER BY {self.quote_identifier(clean_identifier(order_by, 'order_by'))}{' DESC' if order_desc else ' ASC'}"
        sql = f"SELECT * FROM {self.qualified_table(table, database)}{where_sql}{order} LIMIT :limit OFFSET :offset"
        query_params = dict(params or {})
        query_params.update({"limit": page_size, "offset": offset})
        with self.engine.connect() as conn:
            return rows_to_dicts(conn.execute(text(sql), query_params).mappings().all())

    def execute_sql(self, sql: str, page: int = 1, page_size: int = 100) -> tuple[list[str], list[dict[str, Any]], int, int]:
        statement = sql.strip().rstrip(";")
        page_size = clamp_page_size(page_size)
        keyword = first_keyword(statement)
        with self.engine.connect() as conn:
            if keyword in PAGEABLE_READ_KEYWORDS:
                offset = max(page - 1, 0) * page_size
                result = conn.execute(text(f"{statement} LIMIT :limit OFFSET :offset"), {"limit": page_size, "offset": offset})
                total = _query_total(conn, statement)
            else:
                result = conn.execute(text(statement))
                total = -1
            rows = rows_to_dicts(result.mappings().all())
            return list(result.keys()), rows, total if total >= 0 else len(rows), result.rowcount if result.rowcount > 0 else 0

    def execute_write(self, sql: str) -> int:
        with self.engine.begin() as conn:
            result = conn.execute(text(sql))
            return result.rowcount if result.rowcount and result.rowcount > 0 else 0

    def execute_many(self, sql: str, rows: list[dict[str, Any]]) -> int:
        if not rows:
            return 0
        with self.engine.begin() as conn:
            result = conn.execute(text(sql), rows)
            return result.rowcount if result.rowcount and result.rowcount > 0 else len(rows)

    def execute_many_on(self, conn: Any, sql: str, rows: list[dict[str, Any]]) -> int:
        """executemany reusing a caller-held connection, so a multi-batch import opens one
        connection instead of reconnecting (NullPool) per batch."""
        if not rows:
            return 0
        result = conn.execute(text(sql), rows)
        return result.rowcount if result.rowcount and result.rowcount > 0 else len(rows)

    @contextmanager
    def session_connection(self):
        """Yield one AUTOCOMMIT connection reused for a whole script run so that
        session state (TEMPORARY tables, session variables) survives across
        statements. The default per-statement path opens a fresh connection each
        time and cannot keep such state because of NullPool."""
        conn = self.engine.connect().execution_options(isolation_level="AUTOCOMMIT")
        try:
            yield conn
        finally:
            conn.close()

    def execute_sql_on(self, conn: Any, sql: str, page: int = 1, page_size: int = 100) -> tuple[list[str], list[dict[str, Any]], int, int]:
        statement = sql.strip().rstrip(";")
        page_size = clamp_page_size(page_size)
        keyword = first_keyword(statement)
        if keyword in PAGEABLE_READ_KEYWORDS:
            offset = max(page - 1, 0) * page_size
            result = conn.execute(text(f"{statement} LIMIT :limit OFFSET :offset"), {"limit": page_size, "offset": offset})
            total = _query_total(conn, statement)
        else:
            result = conn.execute(text(statement))
            total = -1
        rows = rows_to_dicts(result.mappings().all())
        return list(result.keys()), rows, total if total >= 0 else len(rows), result.rowcount if result.rowcount > 0 else 0

    def execute_write_on(self, conn: Any, sql: str) -> int:
        result = conn.execute(text(sql))
        return result.rowcount if result.rowcount and result.rowcount > 0 else 0

    def supports_load_data(self) -> bool:
        """True when the server allows LOAD DATA LOCAL INFILE (MySQL/MariaDB with
        local_infile enabled). SQLite and a server with local_infile=OFF return False
        so the caller falls back to row-by-row inserts."""
        if self.connection.db_type not in {"mysql", "mariadb"}:
            return False
        try:
            with self.engine.connect() as conn:
                row = conn.execute(text("SHOW GLOBAL VARIABLES LIKE 'local_infile'")).first()
        except SQLAlchemyError:
            return False
        return bool(row) and str(row[1]).upper() in {"ON", "1"}

    def server_version(self) -> str:
        """Best-effort server version string (empty when unavailable)."""
        sql = "SELECT sqlite_version()" if self.connection.db_type == "sqlite" else "SELECT VERSION()"
        try:
            with self.engine.connect() as conn:
                row = conn.execute(text(sql)).first()
        except SQLAlchemyError:
            return ""
        return str(row[0]) if row and row[0] is not None else ""

    def load_data_local(self, file_path: str, table: str, columns: list[str], database: str = "") -> int:
        """Bulk-load a UTF-8 CSV (header row, comma separated, "-quoted, \\n lines) into an
        existing table via LOAD DATA LOCAL INFILE. Columns are listed explicitly so the CSV
        column order maps onto the (already prepared) target columns. Returns affected rows.
        Uses a raw DBAPI cursor because the local-infile handshake is driver-level."""
        quoted_cols = ", ".join(self.quote_identifier(column) for column in columns)
        local_path = file_path.replace("\\", "/").replace("'", "''")
        sql = (
            f"LOAD DATA LOCAL INFILE '{local_path}' INTO TABLE {self.qualified_table(table, database)} "
            "CHARACTER SET utf8mb4 "
            "FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '\"' ESCAPED BY '\\\\' "
            "LINES TERMINATED BY '\\n' IGNORE 1 LINES "
            f"({quoted_cols})"
        )
        raw = self.engine.raw_connection()
        try:
            cursor = raw.cursor()
            try:
                cursor.execute(sql)
                affected = cursor.rowcount
            finally:
                cursor.close()
            raw.commit()
            return int(affected) if affected and affected > 0 else 0
        finally:
            raw.close()

    def qualified_table(self, table: str, database: str = "") -> str:
        name = self.quote_identifier(clean_identifier(table, "table"))
        schema = (database or self.database).strip()
        if schema and self.connection.db_type != "sqlite":
            return f"{self.quote_identifier(clean_identifier(schema, 'schema'))}.{name}"
        return name

    def quote_identifier(self, value: str) -> str:
        quote_char = self.dialect.quote_char
        return quote_char + value.replace(quote_char, quote_char * 2) + quote_char


def dialect_for(db_type: str) -> Dialect:
    dialect = DIALECTS.get(db_type)
    if dialect is None:
        raise bad_request("error.databaseTypeUnsupported", "Unsupported database type")
    return dialect


def create_external_engine(connection: DatabaseConnection, password: str, database: str = "") -> Engine:
    dialect = dialect_for(connection.db_type)
    try:
        if connection.db_type == "sqlite":
            url = f"sqlite:///{connection.host}"
            return create_engine(url, poolclass=NullPool, connect_args={"check_same_thread": False})
        url = URL.create(
            dialect.url_prefix,
            username=connection.username,
            password=password,
            host=connection.host,
            port=connection.port or dialect.default_port,
            database=database or connection.default_database or None,
        )
        return create_engine(
            url,
            poolclass=NullPool,
            pool_pre_ping=True,
            connect_args={
                "connect_timeout": DEFAULT_TIMEOUT_SECONDS,
                "read_timeout": DEFAULT_QUERY_TIMEOUT_SECONDS,
                "write_timeout": DEFAULT_QUERY_TIMEOUT_SECONDS,
                # Allow LOAD DATA LOCAL INFILE so bulk CSV imports can stream the file to the
                # server instead of doing row-by-row INSERTs. Harmless for normal queries; only
                # takes effect when an import actually issues a LOAD DATA LOCAL statement.
                "local_infile": 1,
            },
        )
    except SQLAlchemyError as exc:
        raise service_unavailable("error.databaseConnectionFailed", "Database connection failed") from exc


def test_external_connection(connection: DatabaseConnection, password: str) -> None:
    try:
        with ExternalDatabase(connection, password) as runtime:
            with runtime.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            if connection.default_database:
                runtime.tables(connection.default_database)
    except SQLAlchemyError as exc:
        raise service_unavailable("error.databaseConnectionFailed", "Database connection failed") from exc


def classify_sql(sql: str) -> str:
    statements = split_sql_statements(sql)
    if len(statements) != 1:
        return "write"
    keyword = first_keyword(statements[0])
    return "read" if keyword in READ_SQL_KEYWORDS else "write"


def first_keyword(sql: str) -> str:
    stripped = sql.strip()
    while stripped.startswith("/*"):
        end = stripped.find("*/")
        if end < 0:
            break
        stripped = stripped[end + 2 :].strip()
    lines = [line.strip() for line in stripped.splitlines() if not line.strip().startswith("--")]
    stripped = " ".join(lines)
    return (stripped.split(None, 1)[0] if stripped else "").upper()


def split_sql_statements(sql: str) -> list[str]:
    statements: list[str] = []
    current: list[str] = []
    quote: str | None = None
    escape = False
    for char in sql:
        current.append(char)
        if escape:
            escape = False
            continue
        if char == "\\":
            escape = True
            continue
        if quote:
            if char == quote:
                quote = None
            continue
        if char in {"'", '"', "`"}:
            quote = char
            continue
        if char == ";":
            statement = "".join(current).strip().rstrip(";").strip()
            if statement:
                statements.append(statement)
            current = []
    tail = "".join(current).strip()
    if tail:
        statements.append(tail)
    return statements


def rows_to_dicts(rows: list[Any]) -> list[dict[str, Any]]:
    normalized = []
    for row in rows:
        data = dict(row)
        normalized.append({key: _jsonable(value) for key, value in data.items()})
    return normalized


def clamp_page_size(page_size: int) -> int:
    return min(max(page_size, 1), MAX_PAGE_SIZE)


def placeholder_name(name: str) -> str:
    return "p_" + quote_plus(name).replace("%", "_").replace("+", "_")


def _query_total(conn, sql: str) -> int:
    try:
        return int(conn.execute(text(f"SELECT COUNT(*) AS total FROM ({sql}) AS mtx_query")).scalar() or 0)
    except SQLAlchemyError:
        return -1


def _schema_arg(database: str, db_type: str) -> str | None:
    if db_type == "sqlite":
        return None
    return clean_identifier(database, "schema") if database else None


def _jsonable(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if hasattr(value, "isoformat"):
        return value.isoformat()
    if isinstance(value, bytes):
        return value.hex()
    return str(value)
