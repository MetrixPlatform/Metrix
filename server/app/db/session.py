from collections.abc import Generator
from pathlib import Path

from fastapi import HTTPException, status
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.install import is_installed, load_install_config
from app.db.init import sync_database

_engine: Engine | None = None
_session_factory: sessionmaker[Session] | None = None
_session_factory_engine: Engine | None = None
_engine_url = ""


def create_engine_for_url(database_url: str) -> Engine:
    if database_url.startswith("sqlite:///"):
        db_path = Path(database_url.removeprefix("sqlite:///"))
        db_path.parent.mkdir(parents=True, exist_ok=True)
    return create_engine(
        database_url,
        connect_args={"check_same_thread": False} if database_url.startswith("sqlite") else {},
        pool_pre_ping=not database_url.startswith("sqlite"),
    )


def get_engine() -> Engine:
    global _engine, _engine_url
    if not is_installed():
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="系统未初始化")
    database_url = load_install_config().database_url
    if _engine is None or _engine_url != database_url:
        _engine = create_engine_for_url(database_url)
        _engine_url = database_url
        sync_database(_engine)
    return _engine


def get_session_factory() -> sessionmaker[Session]:
    global _session_factory, _session_factory_engine
    engine = get_engine()
    if _session_factory is None or _session_factory_engine is not engine:
        _session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
        _session_factory_engine = engine
    return _session_factory


def reset_engine() -> None:
    global _engine, _session_factory, _session_factory_engine, _engine_url
    if _engine is not None:
        _engine.dispose()
    _engine = None
    _session_factory = None
    _session_factory_engine = None
    _engine_url = ""


def get_db() -> Generator[Session, None, None]:
    db = get_session_factory()()
    try:
        yield db
    finally:
        db.close()
