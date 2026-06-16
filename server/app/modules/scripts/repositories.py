from __future__ import annotations

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models import User
from app.modules.scripts.models import ScriptProject, ScriptRun, ScriptSchedule


class ScriptProjectRepository:
    def __init__(self, db: Session):
        self.db = db

    def get(self, project_id: int) -> ScriptProject | None:
        return self.db.get(ScriptProject, project_id)

    def get_by_slug(self, slug: str) -> ScriptProject | None:
        return self.db.query(ScriptProject).filter(ScriptProject.slug == slug).first()

    def list(
        self,
        keyword: str = "",
        language: str = "",
        network_mode: str = "",
        created_by_user_id: int | None = None,
        visible_to_user_id: int | None = None,
        created_at_order: str = "descend",
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[ScriptProject], int]:
        query = self.db.query(ScriptProject)
        if keyword:
            pattern = f"%{keyword}%"
            query = query.outerjoin(User, User.id == ScriptProject.created_by)
            query = query.filter(
                or_(
                    ScriptProject.name.ilike(pattern),
                    ScriptProject.slug.ilike(pattern),
                    ScriptProject.description.ilike(pattern),
                    User.username.ilike(pattern),
                    User.full_name.ilike(pattern),
                )
            )
        if language:
            query = query.filter(ScriptProject.language == language)
        if network_mode:
            query = query.filter(ScriptProject.network_mode == network_mode)
        if created_by_user_id is not None:
            query = query.filter(ScriptProject.created_by == created_by_user_id)
        if visible_to_user_id is not None:
            query = query.filter(ScriptProject.created_by == visible_to_user_id)
        total = query.count()
        if created_at_order == "ascend":
            query = query.order_by(ScriptProject.created_at.asc(), ScriptProject.id.asc())
        else:
            query = query.order_by(ScriptProject.created_at.desc(), ScriptProject.id.desc())
        return query.offset((page - 1) * page_size).limit(page_size).all(), total

    def create(self, project: ScriptProject) -> ScriptProject:
        self.db.add(project)
        self.db.flush()
        return project

    def delete(self, project: ScriptProject) -> None:
        self.db.delete(project)
        self.db.flush()

    def creator_usernames(self, user_ids: set[int]) -> dict[int, str]:
        if not user_ids:
            return {}
        rows = self.db.query(User.id, User.username).filter(User.id.in_(user_ids)).all()
        return {user_id: username for user_id, username in rows}


class ScriptRunRepository:
    def __init__(self, db: Session):
        self.db = db

    def get(self, run_id: str) -> ScriptRun | None:
        return self.db.query(ScriptRun).filter(ScriptRun.run_id == run_id).first()

    def create(self, run: ScriptRun) -> ScriptRun:
        self.db.add(run)
        self.db.flush()
        return run

    def delete(self, run: ScriptRun) -> None:
        self.db.delete(run)
        self.db.flush()

    def list(
        self,
        project_id: int,
        status: str = "",
        trigger: str = "",
        sort_order: str = "descend",
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[ScriptRun], int]:
        query = self.db.query(ScriptRun).filter(ScriptRun.project_id == project_id)
        if status:
            query = query.filter(ScriptRun.status == status)
        if trigger:
            query = query.filter(ScriptRun.trigger == trigger)
        total = query.count()
        if sort_order == "ascend":
            query = query.order_by(ScriptRun.created_at.asc(), ScriptRun.id.asc())
        else:
            query = query.order_by(ScriptRun.created_at.desc(), ScriptRun.id.desc())
        return query.offset((page - 1) * page_size).limit(page_size).all(), total

    def creator_usernames(self, user_ids: set[int]) -> dict[int, str]:
        if not user_ids:
            return {}
        rows = self.db.query(User.id, User.username).filter(User.id.in_(user_ids)).all()
        return {user_id: username for user_id, username in rows}


class ScriptScheduleRepository:
    def __init__(self, db: Session):
        self.db = db

    def get(self, schedule_id: int) -> ScriptSchedule | None:
        return self.db.get(ScriptSchedule, schedule_id)

    def create(self, schedule: ScriptSchedule) -> ScriptSchedule:
        self.db.add(schedule)
        self.db.flush()
        return schedule

    def delete(self, schedule: ScriptSchedule) -> None:
        self.db.delete(schedule)
        self.db.flush()

    def list_for_project(self, project_id: int) -> list[ScriptSchedule]:
        return (
            self.db.query(ScriptSchedule)
            .filter(ScriptSchedule.project_id == project_id)
            .order_by(ScriptSchedule.id.asc())
            .all()
        )

    def list_enabled(self) -> list[ScriptSchedule]:
        return self.db.query(ScriptSchedule).filter(ScriptSchedule.enabled.is_(True)).all()
