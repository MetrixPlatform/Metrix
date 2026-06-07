from sqlalchemy.orm import Session

AUTH_SOURCE_API = "api"
AUTH_SOURCE_WEB = "web"


def set_auth_context(db: Session, source: str, api_token_prefix: str = "") -> None:
    db.info["auth_source"] = source
    db.info["api_token_prefix"] = api_token_prefix


def auth_source(db: Session) -> str:
    return str(db.info.get("auth_source") or AUTH_SOURCE_WEB)


def auth_api_token_prefix(db: Session) -> str:
    return str(db.info.get("api_token_prefix") or "")
