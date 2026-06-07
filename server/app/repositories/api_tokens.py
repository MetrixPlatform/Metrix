from sqlalchemy.orm import Session

from app.models import ApiToken


class ApiTokenRepository:
    def __init__(self, db: Session):
        self.db = db

    def get(self, token_id: int) -> ApiToken | None:
        return self.db.get(ApiToken, token_id)

    def get_for_user(self, token_id: int, user_id: int) -> ApiToken | None:
        return self.db.query(ApiToken).filter(ApiToken.id == token_id, ApiToken.user_id == user_id).first()

    def get_by_hash(self, token_hash: str) -> ApiToken | None:
        return self.db.query(ApiToken).filter(ApiToken.token_hash == token_hash).first()

    def list_for_user(self, user_id: int) -> list[ApiToken]:
        return self.db.query(ApiToken).filter(ApiToken.user_id == user_id).order_by(ApiToken.created_at.desc(), ApiToken.id.desc()).all()

    def create(self, token: ApiToken) -> ApiToken:
        self.db.add(token)
        self.db.flush()
        return token

    def delete(self, token: ApiToken) -> None:
        self.db.delete(token)
        self.db.flush()
