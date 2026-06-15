from __future__ import annotations

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models import User
from app.modules.containers.models import ContainerImageRecord, ContainerJob


class ContainerImageRepository:
    def __init__(self, db: Session):
        self.db = db

    def list(
        self,
        image_ids: list[str],
        visible_to_user_id: int | None = None,
    ) -> list[ContainerImageRecord]:
        if not image_ids:
            return []
        query = self.db.query(ContainerImageRecord).filter(ContainerImageRecord.image_id.in_(image_ids))
        if visible_to_user_id is not None:
            query = query.filter(or_(ContainerImageRecord.created_by == visible_to_user_id, ContainerImageRecord.is_public.is_(True)))
        return query.all()

    def get_for_image(self, image_id: str, user_id: int | None = None) -> ContainerImageRecord | None:
        query = self.db.query(ContainerImageRecord).filter(ContainerImageRecord.image_id == image_id)
        if user_id is not None:
            query = query.filter(or_(ContainerImageRecord.created_by == user_id, ContainerImageRecord.is_public.is_(True)))
        return query.order_by(ContainerImageRecord.is_public.desc(), ContainerImageRecord.id.asc()).first()

    def get_owned(self, image_id: str, user_id: int) -> ContainerImageRecord | None:
        return (
            self.db.query(ContainerImageRecord)
            .filter(ContainerImageRecord.image_id == image_id, ContainerImageRecord.created_by == user_id)
            .first()
        )

    def upsert(self, image_id: str, repo_tags: str, created_by: int | None, source: str = "import") -> ContainerImageRecord:
        record = self.get_owned(image_id, created_by) if created_by is not None else None
        if record is None:
            record = ContainerImageRecord(image_id=image_id, repo_tags=repo_tags, created_by=created_by, source=source)
            self.db.add(record)
        else:
            record.repo_tags = repo_tags
            record.source = source
        self.db.flush()
        return record

    def delete_for_image(self, image_id: str, created_by: int | None = None) -> None:
        query = self.db.query(ContainerImageRecord).filter(ContainerImageRecord.image_id == image_id)
        if created_by is not None:
            query = query.filter(ContainerImageRecord.created_by == created_by)
        query.delete(synchronize_session=False)
        self.db.flush()

    def creator_usernames(self, user_ids: set[int]) -> dict[int, str]:
        if not user_ids:
            return {}
        rows = self.db.query(User.id, User.username).filter(User.id.in_(user_ids)).all()
        return {user_id: username for user_id, username in rows}


class ContainerJobRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, job: ContainerJob) -> ContainerJob:
        self.db.add(job)
        self.db.flush()
        return job

    def get(self, job_id: str) -> ContainerJob | None:
        return self.db.query(ContainerJob).filter(ContainerJob.job_id == job_id).first()

    def list(
        self,
        keyword: str = "",
        kind: str = "",
        status: str = "",
        visible_to_user_id: int | None = None,
        sort_order: str = "descend",
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[ContainerJob], int]:
        query = self.db.query(ContainerJob)
        if keyword:
            query = query.filter(or_(ContainerJob.image_ref.ilike(f"%{keyword}%"), ContainerJob.file_name.ilike(f"%{keyword}%")))
        if kind:
            query = query.filter(ContainerJob.kind == kind)
        if status:
            query = query.filter(ContainerJob.status == status)
        if visible_to_user_id is not None:
            query = query.filter(ContainerJob.created_by == visible_to_user_id)
        total = query.count()
        if sort_order == "ascend":
            query = query.order_by(ContainerJob.created_at.asc(), ContainerJob.id.asc())
        else:
            query = query.order_by(ContainerJob.created_at.desc(), ContainerJob.id.desc())
        return query.offset((page - 1) * page_size).limit(page_size).all(), total

    def creator_usernames(self, user_ids: set[int]) -> dict[int, str]:
        if not user_ids:
            return {}
        rows = self.db.query(User.id, User.username).filter(User.id.in_(user_ids)).all()
        return {user_id: username for user_id, username in rows}
