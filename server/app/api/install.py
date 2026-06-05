from fastapi import APIRouter

from app.core.install import is_installed
from app.schemas.common import MessageResponse, message_response
from app.schemas.install import InstallDatabaseTestRequest, InstallRequest, InstallStatusResponse
from app.services.install import install_system, installed_database_type, test_database_connection

router = APIRouter(prefix="/api/install", tags=["install"])


@router.get("/status", response_model=InstallStatusResponse)
def get_install_status() -> InstallStatusResponse:
    return InstallStatusResponse(installed=is_installed(), database_type=installed_database_type())


@router.post("", response_model=MessageResponse)
def install(payload: InstallRequest) -> MessageResponse:
    install_system(payload)
    return message_response("install.finished", "Initialization completed")


@router.post("/test-database", response_model=MessageResponse)
def test_database(payload: InstallDatabaseTestRequest) -> MessageResponse:
    test_database_connection(payload)
    return message_response("install.connectionOk", "Database connection is healthy")
