import re
from pathlib import Path
from urllib.parse import quote_plus

from sqlalchemy import text
from sqlalchemy.orm import Session, sessionmaker

from app.core.exceptions import bad_request
from app.core.install import default_sqlite_path, is_installed, load_install_config, write_install_config
from app.db.init import create_tables, seed_database
from app.db.session import create_engine_for_url, reset_engine
from app.schemas.install import InstallRequest

MYSQL_DATABASE_RE = re.compile(r"^[A-Za-z0-9_]+$")


def install_system(payload: InstallRequest) -> None:
    if is_installed():
        raise bad_request("系统已初始化")
    database_url = _database_url(payload)
    if payload.database_type == "mysql":
        _create_mysql_database(payload)

    engine = create_engine_for_url(database_url)
    try:
        create_tables(engine)
        session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
        with session_factory() as db:
            seed_database(db, payload)
    finally:
        engine.dispose()

    write_install_config(payload.database_type, database_url)
    reset_engine()


def installed_database_type() -> str | None:
    if not is_installed():
        return None
    return load_install_config().database_type


def _database_url(payload: InstallRequest) -> str:
    if payload.database_type == "sqlite":
        return _sqlite_url(payload.sqlite_path)
    if payload.mysql is None:
        raise bad_request("请填写 MySQL 连接信息")
    _guard_mysql_database(payload.mysql.database)
    password = quote_plus(payload.mysql.password)
    username = quote_plus(payload.mysql.username)
    return (
        f"mysql+pymysql://{username}:{password}@{payload.mysql.host}:{payload.mysql.port}/"
        f"{payload.mysql.database}?charset=utf8mb4"
    )


def _sqlite_url(sqlite_path: str) -> str:
    path = Path(sqlite_path.strip()) if sqlite_path.strip() else default_sqlite_path()
    if not path.is_absolute():
        path = Path.cwd() / path
    path.parent.mkdir(parents=True, exist_ok=True)
    return f"sqlite:///{path.as_posix()}"


def _create_mysql_database(payload: InstallRequest) -> None:
    if payload.mysql is None:
        raise bad_request("请填写 MySQL 连接信息")
    mysql = payload.mysql
    _guard_mysql_database(mysql.database)
    username = quote_plus(mysql.username)
    password = quote_plus(mysql.password)
    server_url = f"mysql+pymysql://{username}:{password}@{mysql.host}:{mysql.port}/?charset=utf8mb4"
    engine = create_engine_for_url(server_url)
    try:
        with engine.begin() as conn:
            conn.execute(text(f"CREATE DATABASE IF NOT EXISTS `{mysql.database}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"))
    finally:
        engine.dispose()


def _guard_mysql_database(database: str) -> None:
    if not MYSQL_DATABASE_RE.fullmatch(database):
        raise bad_request("MySQL 数据库名只能包含字母、数字和下划线")
