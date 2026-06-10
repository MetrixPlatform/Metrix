from functools import cache
from importlib import import_module
from pkgutil import iter_modules
from typing import Any

from fastapi import APIRouter

import app.modules as modules_package
from app.core.module import AppModule, PagePermissionSpec, ResourcePermissionSpec


@cache
def get_app_modules() -> tuple[AppModule, ...]:
    discovered = []
    for module_info in iter_modules(modules_package.__path__, f"{modules_package.__name__}."):
        if module_info.name.rsplit(".", 1)[-1] == "registry":
            continue
        module = import_module(module_info.name)
        app_module = getattr(module, "APP_MODULE", None)
        if isinstance(app_module, AppModule):
            discovered.append(app_module)
    return tuple(sorted(discovered, key=lambda item: (item.order, item.key)))


def get_page_permission_specs() -> tuple[PagePermissionSpec, ...]:
    return tuple(spec for module in get_app_modules() for spec in module.page_permissions)


def get_resource_permission_specs() -> tuple[ResourcePermissionSpec, ...]:
    return tuple(spec for module in get_app_modules() for spec in module.resource_permissions)


def get_openapi_hidden_tags() -> set[str]:
    return {tag for module in get_app_modules() for tag in module.openapi_hidden_tags}


def get_openapi_hidden_path_prefixes() -> tuple[str, ...]:
    return tuple(prefix for module in get_app_modules() for prefix in module.openapi_hidden_path_prefixes)


def load_module_routers() -> tuple[APIRouter, ...]:
    return tuple(load_object(path) for module in get_app_modules() for path in module.router_paths)


def load_object(path: str) -> Any:
    module_name, object_name = path.split(":", 1)
    return getattr(import_module(module_name), object_name)
