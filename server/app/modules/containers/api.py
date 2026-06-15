from fastapi import APIRouter, Depends, File, Query, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.deps import require_permission
from app.db.session import get_db
from app.models import User
from app.modules.containers import CONTAINER_CREATE, CONTAINER_DELETE, CONTAINER_OPERATE, CONTAINER_READ, CONTAINER_UPDATE
from app.modules.containers.schemas import (
    ContainerCreatePayload,
    ContainerEngineStatus,
    ContainerItem,
    ContainerJobListResponse,
    ContainerListResponse,
    ContainerLogsResponse,
    ImageItem,
    ImageListResponse,
    ImageVisibilityPayload,
    JobSubmitResponse,
)
from app.modules.containers.services import ContainerService
from app.schemas.common import MessageResponse, message_response

engine_router = APIRouter(prefix="/api/container-engine", tags=["container-engine"])
images_router = APIRouter(prefix="/api/container-images", tags=["container-images"])
instances_router = APIRouter(prefix="/api/container-instances", tags=["container-instances"])
jobs_router = APIRouter(prefix="/api/container-jobs", tags=["container-jobs"])


@engine_router.get("/status", response_model=ContainerEngineStatus)
def container_engine_status(
    db: Session = Depends(get_db),
    _: User = Depends(require_permission(CONTAINER_READ)),
) -> ContainerEngineStatus:
    return ContainerService(db).engine_status()


@images_router.get("", response_model=ImageListResponse)
def list_container_images(
    keyword: str = "",
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=500),
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission(CONTAINER_READ)),
) -> ImageListResponse:
    return ContainerService(db).list_images(actor, keyword, page, page_size)


@images_router.post("/import", response_model=JobSubmitResponse)
def import_container_image(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission(CONTAINER_CREATE)),
) -> JobSubmitResponse:
    return ContainerService(db).submit_import(actor, file)


@images_router.post("/{image_ref:path}/export", response_model=JobSubmitResponse)
def export_container_image(
    image_ref: str,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission(CONTAINER_READ)),
) -> JobSubmitResponse:
    return ContainerService(db).submit_export(actor, image_ref)


@images_router.put("/{image_ref:path}/visibility", response_model=ImageItem)
def update_container_image_visibility(
    image_ref: str,
    payload: ImageVisibilityPayload,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission(CONTAINER_UPDATE)),
):
    return ContainerService(db).set_image_public(actor, image_ref, payload.is_public)


@images_router.delete("/{image_ref:path}", response_model=MessageResponse)
def delete_container_image(
    image_ref: str,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission(CONTAINER_DELETE)),
) -> MessageResponse:
    ContainerService(db).delete_image(actor, image_ref)
    return message_response("container.imageDeleted", "Image deleted")


@instances_router.get("", response_model=ContainerListResponse)
def list_container_instances(
    keyword: str = "",
    status: str = "",
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=500),
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission(CONTAINER_READ)),
) -> ContainerListResponse:
    return ContainerService(db).list_containers(actor, keyword, status, page, page_size)


@instances_router.post("", response_model=ContainerItem)
def create_container_instance(
    payload: ContainerCreatePayload,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission(CONTAINER_CREATE)),
):
    return ContainerService(db).create_container(actor, payload)


@instances_router.post("/{container_id}/start", response_model=MessageResponse)
def start_container_instance(
    container_id: str,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission(CONTAINER_OPERATE)),
) -> MessageResponse:
    ContainerService(db).operate_container(actor, container_id, "start")
    return message_response("container.started", "Container started")


@instances_router.post("/{container_id}/stop", response_model=MessageResponse)
def stop_container_instance(
    container_id: str,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission(CONTAINER_OPERATE)),
) -> MessageResponse:
    ContainerService(db).operate_container(actor, container_id, "stop")
    return message_response("container.stopped", "Container stopped")


@instances_router.post("/{container_id}/restart", response_model=MessageResponse)
def restart_container_instance(
    container_id: str,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission(CONTAINER_OPERATE)),
) -> MessageResponse:
    ContainerService(db).operate_container(actor, container_id, "restart")
    return message_response("container.restarted", "Container restarted")


@instances_router.get("/{container_id}/logs", response_model=ContainerLogsResponse)
def get_container_logs(
    container_id: str,
    tail: int = Query(default=200, ge=1, le=5000),
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission(CONTAINER_READ)),
) -> ContainerLogsResponse:
    return ContainerLogsResponse(logs=ContainerService(db).logs(actor, container_id, tail))


@instances_router.delete("/{container_id}", response_model=MessageResponse)
def delete_container_instance(
    container_id: str,
    force: bool = False,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission(CONTAINER_DELETE)),
) -> MessageResponse:
    ContainerService(db).delete_container(actor, container_id, force)
    return message_response("container.deleted", "Container deleted")


@jobs_router.get("", response_model=ContainerJobListResponse)
def list_container_jobs(
    keyword: str = "",
    kind: str = "",
    status: str = "",
    sort_order: str = "descend",
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=500),
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission(CONTAINER_READ)),
) -> ContainerJobListResponse:
    return ContainerService(db).list_jobs(actor, keyword, kind, status, sort_order, page, page_size)


@jobs_router.get("/{job_id}/download")
def download_container_job(
    job_id: str,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission(CONTAINER_READ)),
) -> StreamingResponse:
    file_name, fileobj = ContainerService(db).download_job(actor, job_id)

    def stream():
        try:
            yield from fileobj
        finally:
            fileobj.close()

    return StreamingResponse(
        stream(),
        media_type="application/octet-stream",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{file_name}"},
    )
