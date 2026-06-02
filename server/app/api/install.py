from fastapi import APIRouter

from app.core.install import is_installed
from app.schemas.common import MessageResponse
from app.schemas.install import InstallRequest, InstallStatusResponse
from app.services.install import install_system, installed_database_type

router = APIRouter(prefix="/api/install", tags=["install"])


@router.get("/status", response_model=InstallStatusResponse)
def get_install_status() -> InstallStatusResponse:
    return InstallStatusResponse(installed=is_installed(), database_type=installed_database_type())


@router.post("", response_model=MessageResponse)
def install(payload: InstallRequest) -> MessageResponse:
    install_system(payload)
    return MessageResponse(message="系统初始化完成")
