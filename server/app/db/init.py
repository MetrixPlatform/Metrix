import json

from sqlalchemy import inspect, text
from sqlalchemy.orm import Session, sessionmaker

from app.core.permissions import ADMIN_ROLE, DASHBOARD_READ, DEPRECATED_PERMISSION_CODES, PERMISSION_SEEDS, USER_ROLE
from app.core.security import hash_password
from app.db.base import Base
from app.models import Permission, Role, User
from app.modules.registry import get_app_modules, get_discovered_app_modules, get_migration_steps, get_table_column_syncs, load_module_models
from app.schemas.install import InstallRequest


def create_tables(engine) -> None:
    load_module_models()
    Base.metadata.create_all(bind=engine)


def seed_database(db: Session, payload: InstallRequest) -> None:
    _, admin_role = sync_seed_data(db)

    admin = db.query(User).filter(User.username == payload.admin_username).first()
    if admin is None:
        admin = User(
            username=payload.admin_username,
            full_name=payload.admin_full_name,
            phone=payload.admin_phone,
            email=payload.admin_email,
            company=payload.admin_company,
            department=payload.admin_department,
            password_hash=hash_password(payload.admin_password),
            approval_status="approved",
            is_active=True,
            is_builtin=True,
            roles=[admin_role],
        )
        db.add(admin)
    elif admin_role not in admin.roles:
        admin.roles.append(admin_role)

    db.commit()


def sync_database(engine) -> None:
    create_tables(engine)
    run_migrations(engine)
    sync_columns(engine)
    sync_module_states(engine)
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
    with session_factory() as db:
        sync_seed_data(db)
        db.commit()


def sync_seed_data(db: Session) -> tuple[dict[str, Permission], Role]:
    permissions_by_code = _sync_permission_seeds(db)
    admin_role = _ensure_role(db, ADMIN_ROLE, "role.admin.name", "role.admin.description", True)
    user_role = _ensure_role(db, USER_ROLE, "role.user.name", "role.user.description", True)
    admin_role.permissions = list(permissions_by_code.values())
    if not user_role.permissions:
        user_role.permissions = [permissions_by_code[DASHBOARD_READ]]
    return permissions_by_code, admin_role


def sync_columns(engine) -> None:
    inspector = inspect(engine)
    table_names = set(inspector.get_table_names())
    if not table_names:
        return
    with engine.begin() as conn:
        for sync in get_table_column_syncs():
            _sync_table_columns(conn, inspector, table_names, sync.table, sync.columns)


def sync_module_states(engine) -> None:
    discovered_modules = {module.key: module for module in get_discovered_app_modules()}
    enabled_modules = {module.key: module for module in get_app_modules()}
    with engine.begin() as conn:
        state_by_key = {
            row["key"]: row
            for row in conn.execute(text("SELECT `key`, version, status FROM module_states")).mappings()
        }
        for module in enabled_modules.values():
            state = state_by_key.get(module.key)
            if state is None:
                _run_recorded_lifecycle_hooks(conn, module, "install")
            elif state["version"] != module.version:
                _run_recorded_lifecycle_hooks(conn, module, "upgrade")
            _upsert_module_state(conn, module.key, module.version, "enabled", module.dependencies)

        for module in discovered_modules.values():
            if module.key in enabled_modules:
                continue
            state = state_by_key.get(module.key)
            if state is not None and state["status"] == "enabled":
                _run_recorded_lifecycle_hooks(conn, module, "disable")
            _upsert_module_state(conn, module.key, module.version, "disabled", module.dependencies)

        for key, state in state_by_key.items():
            if key not in discovered_modules and state["status"] != "missing":
                _upsert_module_state(conn, key, state["version"], "missing", ())


def run_migrations(engine) -> None:
    steps = get_migration_steps()
    if not steps:
        return
    with engine.begin() as conn:
        for module, step in steps:
            key = f"migration:{module.key}:{step.key}"
            if _has_migration_record(conn, key):
                continue
            for statement in step.statements:
                conn.execute(text(statement))
            _record_migration(
                conn,
                key,
                "migration",
                module.key,
                step.description or f"{module.key}@{module.version}:{step.key}",
            )


def run_module_uninstall(engine, module_key: str) -> None:
    modules = {module.key: module for module in get_discovered_app_modules()}
    module = modules.get(module_key)
    if module is None:
        raise RuntimeError(f"Unknown app module: {module_key}")
    with engine.begin() as conn:
        _run_recorded_lifecycle_hooks(conn, module, "uninstall")
        _upsert_module_state(conn, module.key, module.version, "uninstalled", module.dependencies)


def _run_recorded_lifecycle_hooks(conn, module, event: str) -> None:
    for hook in (item for item in module.lifecycle_hooks if item.event == event):
        key = f"hook:{module.key}:{event}:{module.version}:{hook.key}"
        if _has_migration_record(conn, key):
            continue
        for statement in hook.statements:
            conn.execute(text(statement))
        _record_migration(
            conn,
            key,
            "module_hook",
            module.key,
            hook.description or f"{module.key}@{module.version}:{event}:{hook.key}",
        )


def _upsert_module_state(conn, key: str, version: str, status: str, dependencies: tuple[str, ...]) -> None:
    payload = json.dumps(list(dependencies), ensure_ascii=False)
    existing = conn.execute(text("SELECT id FROM module_states WHERE `key` = :key"), {"key": key}).first()
    if existing:
        conn.execute(
            text(
                "UPDATE module_states SET version = :version, status = :status, dependencies = :dependencies, "
                "updated_at = CURRENT_TIMESTAMP WHERE `key` = :key"
            ),
            {"key": key, "version": version, "status": status, "dependencies": payload},
        )
        return
    conn.execute(
        text(
            "INSERT INTO module_states (`key`, version, status, dependencies, updated_at) "
            "VALUES (:key, :version, :status, :dependencies, CURRENT_TIMESTAMP)"
        ),
        {"key": key, "version": version, "status": status, "dependencies": payload},
    )


def _sync_table_columns(conn, inspector, table_names: set[str], table: str, column_sql: dict[str, str]) -> None:
    if table not in table_names:
        return
    existing_columns = {column["name"] for column in inspector.get_columns(table)}
    for name, statement in column_sql.items():
        if name not in existing_columns:
            conn.execute(text(statement))
            _record_migration(
                conn,
                f"column:{table}.{name}",
                "column",
                f"{table}.{name}",
                statement,
            )


def _record_migration(conn, key: str, kind: str, target: str, detail: str) -> None:
    if _has_migration_record(conn, key):
        return
    conn.execute(
        text(
            "INSERT INTO migration_records (`key`, kind, target, detail, applied_at) "
            "VALUES (:key, :kind, :target, :detail, CURRENT_TIMESTAMP)"
        ),
        {"key": key, "kind": kind, "target": target, "detail": detail},
    )


def _has_migration_record(conn, key: str) -> bool:
    return conn.execute(text("SELECT id FROM migration_records WHERE `key` = :key"), {"key": key}).first() is not None


def _sync_permission_seeds(db: Session) -> dict[str, Permission]:
    permissions_by_code = {}
    for seed in PERMISSION_SEEDS:
        permission = db.query(Permission).filter(Permission.code == seed.code).first()
        if permission is None:
            permission = Permission(
                code=seed.code,
                name=seed.name,
                type=seed.type,
                resource=seed.resource,
                group_name=seed.group_name,
                description=seed.description,
                sort_order=seed.sort_order,
            )
            db.add(permission)
        else:
            permission.name = seed.name
            permission.type = seed.type
            permission.resource = seed.resource
            permission.group_name = seed.group_name
            permission.description = seed.description
            permission.sort_order = seed.sort_order
        permissions_by_code[seed.code] = permission
    _delete_legacy_route_permissions(db)
    _delete_deprecated_permissions(db)
    db.flush()
    return permissions_by_code


def _ensure_role(db: Session, code: str, name: str, description: str, is_builtin: bool) -> Role:
    role = db.query(Role).filter(Role.code == code).first()
    if role is None:
        role = Role(code=code, name=name, description=description, is_builtin=is_builtin)
        db.add(role)
    else:
        role.name = name
        role.description = description
        role.is_builtin = is_builtin
    return role


def _delete_deprecated_permissions(db: Session) -> None:
    if not DEPRECATED_PERMISSION_CODES:
        return
    permissions = db.query(Permission).filter(Permission.code.in_(DEPRECATED_PERMISSION_CODES)).all()
    for permission in permissions:
        permission.roles.clear()
        db.delete(permission)


def _delete_legacy_route_permissions(db: Session) -> None:
    # route:* 页面权限已退役（页面/导航改由资源的查询权限充当网关），清理历史遗留行。
    permissions = db.query(Permission).filter(Permission.code.like("route:%")).all()
    for permission in permissions:
        permission.roles.clear()
        db.delete(permission)
