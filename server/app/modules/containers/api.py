import asyncio
import json
import threading

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.deps import require_permission
from app.core.security import decode_access_token
from app.db.session import get_db, get_session_factory
from app.models import User
from app.modules.containers import CONTAINER_CREATE, CONTAINER_DELETE, CONTAINER_OPERATE, CONTAINER_READ, CONTAINER_UPDATE
from app.repositories.users import UserRepository
from app.services.permissions import has_permission
from app.modules.containers.schemas import (
    ContainerCreatePayload,
    ContainerEngineStatus,
    ContainerItem,
    ContainerJobListResponse,
    ContainerListResponse,
    ContainerLogClearResult,
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


@instances_router.post("/{container_id}/clear-logs", response_model=ContainerLogClearResult)
def clear_container_logs(
    container_id: str,
    restart: bool = False,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission(CONTAINER_OPERATE)),
) -> ContainerLogClearResult:
    return ContainerService(db).clear_logs(actor, container_id, restart)


@instances_router.websocket("/{container_id}/exec")
async def container_exec_terminal(websocket: WebSocket, container_id: str) -> None:
    await websocket.accept()
    db = get_session_factory()()
    raw = None
    stop = threading.Event()
    try:
        user = _ws_authenticate(db, websocket)
        if user is None:
            await websocket.close(code=4401)
            return
        if not has_permission(user, CONTAINER_OPERATE):
            await websocket.close(code=4403)
            return
        command = websocket.query_params.get("cmd") or "/bin/sh"
        exec_user = websocket.query_params.get("user") or ""
        cols = _ws_int(websocket.query_params.get("cols"), 80)
        rows = _ws_int(websocket.query_params.get("rows"), 24)
        try:
            exec_id, raw, api = ContainerService(db).open_exec(user, container_id, command, exec_user, cols, rows)
        except HTTPException as exc:
            await websocket.send_text(json.dumps({"type": "error", "code": _ws_error_code(exc)}))
            await websocket.close()
            return
        loop = asyncio.get_running_loop()

        def pump() -> None:
            try:
                while not stop.is_set():
                    data = _sock_recv(raw, 4096)
                    if not data:
                        break
                    asyncio.run_coroutine_threadsafe(websocket.send_bytes(data), loop)
            except Exception:
                pass
            finally:
                stop.set()
                asyncio.run_coroutine_threadsafe(_ws_close(websocket), loop)

        threading.Thread(target=pump, name="container-exec", daemon=True).start()
        while True:
            text = await websocket.receive_text()
            try:
                payload = json.loads(text)
            except ValueError:
                continue
            kind = payload.get("type")
            if kind == "input":
                _sock_send(raw, payload.get("data", "").encode("utf-8"))
            elif kind == "resize":
                try:
                    api.exec_resize(exec_id, height=_ws_int(payload.get("rows"), rows), width=_ws_int(payload.get("cols"), cols))
                except Exception:
                    pass
    except WebSocketDisconnect:
        pass
    except Exception:
        pass
    finally:
        stop.set()
        if raw is not None:
            try:
                raw.close()
            except Exception:
                pass
        db.close()


def _ws_authenticate(db: Session, websocket: WebSocket) -> User | None:
    token = websocket.query_params.get("token")
    if not token:
        return None
    subject = decode_access_token(token)
    if subject is None:
        return None
    user = UserRepository(db).get(int(subject))
    if not user or not user.is_active or user.approval_status != "approved":
        return None
    return user


async def _ws_close(websocket: WebSocket) -> None:
    try:
        await websocket.close()
    except Exception:
        pass


def _sock_recv(raw: object, size: int) -> bytes:
    # docker-py returns NpipeSocket (Windows), socket.socket (unix) or SocketIO (tcp);
    # normalize reads so the exec bridge works across all Docker transports.
    recv = getattr(raw, "recv", None)
    if callable(recv):
        return recv(size)
    return raw.read(size)  # type: ignore[attr-defined]


def _sock_send(raw: object, data: bytes) -> None:
    sendall = getattr(raw, "sendall", None)
    if callable(sendall):
        sendall(data)
        return
    send = getattr(raw, "send", None)
    if callable(send):
        send(data)
        return
    raw.write(data)  # type: ignore[attr-defined]
    flush = getattr(raw, "flush", None)
    if callable(flush):
        flush()


def _ws_int(value: object, fallback: int) -> int:
    try:
        return max(1, min(int(value), 1000))  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return fallback


def _ws_error_code(exc: HTTPException) -> str:
    detail = exc.detail
    if isinstance(detail, dict):
        return str(detail.get("code", "error.requestFailed"))
    return "error.requestFailed"


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
