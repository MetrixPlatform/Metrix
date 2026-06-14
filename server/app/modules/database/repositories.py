from __future__ import annotations

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models import User
from app.modules.database.models import DataJob, DatabaseConnection, SqlScript


class DatabaseConnectionRepository:
    def __init__(self, db: Session):
        self.db = db

    def get(self, connection_id: int) -> DatabaseConnection | None:
        return self.db.get(DatabaseConnection, connection_id)

    def get_by_conn_id(self, conn_id: str) -> DatabaseConnection | None:
        return self.db.query(DatabaseConnection).filter(DatabaseConnection.conn_id == conn_id).first()

    def list(
        self,
        keyword: str = "",
        db_type: str = "",
        is_shared: bool | None = None,
        is_active: bool | None = None,
        created_by_user_id: int | None = None,
        visible_to_user_id: int | None = None,
        created_at_order: str = "descend",
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[DatabaseConnection], int]:
        query = self.db.query(DatabaseConnection)
        if keyword:
            pattern = f"%{keyword}%"
            query = query.filter(
                or_(
                    DatabaseConnection.name.ilike(pattern),
                    DatabaseConnection.conn_id.ilike(pattern),
                    DatabaseConnection.host.ilike(pattern),
                    DatabaseConnection.default_database.ilike(pattern),
                )
            )
        if db_type:
            query = query.filter(DatabaseConnection.db_type == db_type)
        if is_shared is not None:
            query = query.filter(DatabaseConnection.is_shared == is_shared)
        if is_active is not None:
            query = query.filter(DatabaseConnection.is_active == is_active)
        if created_by_user_id is not None:
            query = query.filter(DatabaseConnection.created_by == created_by_user_id)
        if visible_to_user_id is not None:
            query = query.filter(
                or_(DatabaseConnection.created_by == visible_to_user_id, DatabaseConnection.is_shared.is_(True))
            )
        total = query.count()
        if created_at_order == "ascend":
            query = query.order_by(DatabaseConnection.created_at.asc(), DatabaseConnection.id.asc())
        else:
            query = query.order_by(DatabaseConnection.created_at.desc(), DatabaseConnection.id.desc())
        return query.offset((page - 1) * page_size).limit(page_size).all(), total

    def create(self, connection: DatabaseConnection) -> DatabaseConnection:
        self.db.add(connection)
        self.db.flush()
        return connection

    def delete(self, connection: DatabaseConnection) -> None:
        self.db.delete(connection)
        self.db.flush()

    def creator_usernames(self, user_ids: set[int]) -> dict[int, str]:
        if not user_ids:
            return {}
        rows = self.db.query(User.id, User.username).filter(User.id.in_(user_ids)).all()
        return {user_id: username for user_id, username in rows}


class SqlScriptRepository:
    def __init__(self, db: Session):
        self.db = db

    def get(self, script_id: int) -> SqlScript | None:
        return self.db.get(SqlScript, script_id)

    def list(
        self,
        keyword: str = "",
        connection_id: int | None = None,
        is_shared: bool | None = None,
        created_by_user_id: int | None = None,
        visible_to_user_id: int | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[SqlScript], int]:
        query = self.db.query(SqlScript)
        if keyword:
            pattern = f"%{keyword}%"
            query = query.filter(or_(SqlScript.name.ilike(pattern), SqlScript.description.ilike(pattern)))
        if connection_id is not None:
            query = query.filter(SqlScript.connection_id == connection_id)
        if is_shared is not None:
            query = query.filter(SqlScript.is_shared == is_shared)
        if created_by_user_id is not None:
            query = query.filter(SqlScript.created_by == created_by_user_id)
        if visible_to_user_id is not None:
            query = query.filter(or_(SqlScript.created_by == visible_to_user_id, SqlScript.is_shared.is_(True)))
        total = query.count()
        query = query.order_by(SqlScript.updated_at.desc(), SqlScript.id.desc())
        return query.offset((page - 1) * page_size).limit(page_size).all(), total

    def create(self, script: SqlScript) -> SqlScript:
        self.db.add(script)
        self.db.flush()
        return script

    def delete(self, script: SqlScript) -> None:
        self.db.delete(script)
        self.db.flush()

    def creator_usernames(self, user_ids: set[int]) -> dict[int, str]:
        if not user_ids:
            return {}
        rows = self.db.query(User.id, User.username).filter(User.id.in_(user_ids)).all()
        return {user_id: username for user_id, username in rows}


class DataJobRepository:
    def __init__(self, db: Session):
        self.db = db

    def get(self, job_id: str) -> DataJob | None:
        return self.db.query(DataJob).filter(DataJob.job_id == job_id).first()

    def list(
        self,
        kind: str = "",
        status: str = "",
        visible_to_user_id: int | None = None,
        created_at_order: str = "descend",
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[DataJob], int]:
        query = self.db.query(DataJob)
        if kind:
            query = query.filter(DataJob.kind == kind)
        if status:
            query = query.filter(DataJob.status == status)
        if visible_to_user_id is not None:
            query = query.filter(DataJob.created_by == visible_to_user_id)
        total = query.count()
        if created_at_order == "ascend":
            query = query.order_by(DataJob.created_at.asc(), DataJob.id.asc())
        else:
            query = query.order_by(DataJob.created_at.desc(), DataJob.id.desc())
        return query.offset((page - 1) * page_size).limit(page_size).all(), total

    def create(self, job: DataJob) -> DataJob:
        self.db.add(job)
        self.db.flush()
        return job

    def delete(self, job: DataJob) -> None:
        self.db.delete(job)
        self.db.flush()
