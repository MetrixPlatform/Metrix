from functools import cache
from importlib import import_module
import os
from pkgutil import iter_modules
import re
from typing import Any

from fastapi import APIRouter

import app.modules as modules_package
from app.core.module import (
    MODULE_LIFECYCLE_EVENTS,
    AppModule,
    MigrationStep,
    PagePermissionSpec,
    ResourcePermissionSpec,
    TableColumnSync,
)

MODULE_KEY_RE = re.compile(r"^[a-z][a-z0-9_]*$")
MODULE_VERSION_RE = re.compile(r"^\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?$")
MODULE_DEPENDENCY_RE = re.compile(r"^([a-z][a-z0-9_]*)(?:\s*(==|>=|<=|>|<)\s*([0-9]+(?:\.[0-9]+){0,2}))?$")


@cache
def get_discovered_app_modules() -> tuple[AppModule, ...]:
    discovered = []
    for module_info in iter_modules(modules_package.__path__, f"{modules_package.__name__}."):
        if module_info.name.rsplit(".", 1)[-1] == "registry":
            continue
        module = import_module(module_info.name)
        app_module = getattr(module, "APP_MODULE", None)
        if isinstance(app_module, AppModule):
            discovered.append(app_module)
    sorted_modules = tuple(sorted(discovered, key=lambda item: (item.order, item.key)))
    validate_discovered_app_modules(sorted_modules)
    return sorted_modules


@cache
def get_app_modules() -> tuple[AppModule, ...]:
    sorted_modules = tuple(_filter_modules(get_discovered_app_modules()))
    validate_app_modules(sorted_modules)
    return sorted_modules


def get_page_permission_specs() -> tuple[PagePermissionSpec, ...]:
    return tuple(spec for module in get_app_modules() for spec in module.page_permissions)


def get_resource_permission_specs() -> tuple[ResourcePermissionSpec, ...]:
    return tuple(spec for module in get_app_modules() for spec in module.resource_permissions)


def get_table_column_syncs() -> tuple[TableColumnSync, ...]:
    return tuple(sync for module in get_app_modules() for sync in module.table_syncs)


def get_migration_steps() -> tuple[tuple[AppModule, MigrationStep], ...]:
    return tuple((module, step) for module in get_app_modules() for step in module.migrations)


def get_openapi_hidden_tags() -> set[str]:
    return {tag for module in get_app_modules() for tag in module.openapi_hidden_tags}


def get_openapi_hidden_path_prefixes() -> tuple[str, ...]:
    return tuple(prefix for module in get_app_modules() for prefix in module.openapi_hidden_path_prefixes)


def load_module_routers() -> tuple[APIRouter, ...]:
    return tuple(load_object(path) for module in get_app_modules() for path in module.router_paths)


def load_module_models() -> None:
    for module in get_app_modules():
        for path in module.model_paths:
            import_module(path)


def load_object(path: str) -> Any:
    module_name, object_name = path.split(":", 1)
    return getattr(import_module(module_name), object_name)


def validate_discovered_app_modules(modules: tuple[AppModule, ...]) -> None:
    _ensure_unique("module key", (module.key for module in modules))
    for module in modules:
        if not MODULE_KEY_RE.fullmatch(module.key):
            raise RuntimeError(f"Invalid app module key: {module.key}")
        if not MODULE_VERSION_RE.fullmatch(module.version):
            raise RuntimeError(f"Invalid app module version: {module.key}@{module.version}")
        for hook in module.lifecycle_hooks:
            if hook.event not in MODULE_LIFECYCLE_EVENTS:
                raise RuntimeError(f"Invalid app module lifecycle event: {module.key}.{hook.event}")
            if not hook.key:
                raise RuntimeError(f"Invalid app module lifecycle hook key: {module.key}")
            if not hook.statements:
                raise RuntimeError(f"Empty app module lifecycle hook statements: {module.key}.{hook.key}")
    _ensure_unique(
        "lifecycle hook",
        (f"{module.key}:{hook.event}:{hook.key}" for module in modules for hook in module.lifecycle_hooks),
    )


def validate_app_modules(modules: tuple[AppModule, ...]) -> None:
    _ensure_unique("module key", (module.key for module in modules))
    modules_by_key = {module.key: module for module in modules}
    module_keys = set(modules_by_key)
    for module in modules:
        for dependency in module.dependencies:
            _dependency_key_and_constraint(dependency)
    missing_dependencies = sorted(
        f"{module.key}->{dependency}"
        for module in modules
        for dependency in module.dependencies
        if _dependency_key_and_constraint(dependency)[0] not in module_keys
    )
    if missing_dependencies:
        raise RuntimeError(f"Missing app module dependency: {', '.join(missing_dependencies)}")
    incompatible_dependencies = sorted(
        f"{module.key}->{dependency}"
        for module in modules
        for dependency in module.dependencies
        if not _dependency_is_satisfied(modules_by_key[_dependency_key_and_constraint(dependency)[0]].version, dependency)
    )
    if incompatible_dependencies:
        raise RuntimeError(f"Incompatible app module dependency: {', '.join(incompatible_dependencies)}")
    _ensure_unique("router path", (path for module in modules for path in module.router_paths))
    _ensure_unique("model path", (path for module in modules for path in module.model_paths))
    _ensure_unique("migration key", (f"{module.key}:{step.key}" for module in modules for step in module.migrations))
    _ensure_unique(
        "table column sync",
        (
            f"{sync.table}.{column}"
            for module in modules
            for sync in module.table_syncs
            for column in sync.columns
        ),
    )
    _ensure_unique("page permission code", (spec.code for module in modules for spec in module.page_permissions))
    _ensure_unique(
        "resource permission code",
        (
            spec.to_seed(action).code
            for module in modules
            for spec in module.resource_permissions
            for action in spec.actions
        ),
    )


def _filter_modules(modules: tuple[AppModule, ...]) -> tuple[AppModule, ...]:
    module_keys = {module.key for module in modules}
    enabled = _module_filter("METRIX_ENABLED_MODULES")
    disabled = _module_filter("METRIX_DISABLED_MODULES")
    _ensure_known_modules("enabled", enabled, module_keys)
    _ensure_known_modules("disabled", disabled, module_keys)
    if "core" in disabled:
        raise RuntimeError("Core app module cannot be disabled")
    return tuple(
        module
        for module in modules
        if (not enabled or module.key == "core" or module.key in enabled)
        and (module.key == "core" or module.key not in disabled)
    )


def _module_filter(name: str) -> set[str]:
    return {item.strip() for item in os.getenv(name, "").split(",") if item.strip()}


def _ensure_known_modules(label: str, values: set[str], module_keys: set[str]) -> None:
    unknown = values - module_keys
    if unknown:
        raise RuntimeError(f"Unknown {label} app module: {', '.join(sorted(unknown))}")


def _ensure_unique(label: str, values) -> None:
    seen = set()
    duplicates = set()
    for value in values:
        if value in seen:
            duplicates.add(value)
        seen.add(value)
    if duplicates:
        items = ", ".join(sorted(duplicates))
        raise RuntimeError(f"Duplicate app module {label}: {items}")


def _dependency_key_and_constraint(value: str) -> tuple[str, str, str]:
    match = MODULE_DEPENDENCY_RE.fullmatch(value.strip())
    if not match:
        raise RuntimeError(f"Invalid app module dependency: {value}")
    key, operator, version = match.groups()
    return key, operator or "", version or ""


def _dependency_is_satisfied(actual_version: str, dependency: str) -> bool:
    _, operator, required_version = _dependency_key_and_constraint(dependency)
    if not operator:
        return True
    actual = _version_tuple(actual_version)
    required = _version_tuple(required_version)
    if operator == "==":
        return actual == required
    if operator == ">=":
        return actual >= required
    if operator == "<=":
        return actual <= required
    if operator == ">":
        return actual > required
    if operator == "<":
        return actual < required
    return False


def _version_tuple(value: str) -> tuple[int, int, int]:
    core = value.split("-", 1)[0].split("+", 1)[0]
    parts = [int(part) for part in core.split(".")]
    return tuple((parts + [0, 0, 0])[:3])
