import asyncio
import json
import threading

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from app.core.deps import require_permission, require_web_session
from app.core.security import decode_access_token
from app.db.session import get_db, get_session_factory
from app.models import User
from app.modules.containers.api import _sock_recv, _sock_send
from app.modules.scripts import (
    SCRIPT_CREATE,
    SCRIPT_DELETE,
    SCRIPT_OPERATE,
    SCRIPT_READ,
    SCRIPT_UPDATE,
)
from app.modules.scripts import runtime as script_runtime
from app.modules.scripts.runs import ScriptRunService
from app.modules.scripts.scheduler import ScriptScheduleService
from app.modules.scripts.schemas import (
    AvailableImagesResponse,
    RunSubmitResponse,
    ScriptEnvironmentInfo,
    ScriptFileContent,
    ScriptFileEntry,
    ScriptFileListResponse,
    ScriptFileWriteRequest,
    ScriptPathRequest,
    ScriptProjectItem,
    ScriptProjectListResponse,
    ScriptProjectPayload,
    ScriptRenameRequest,
    ScriptRunItem,
    ScriptRunListResponse,
    ScriptRunLog,
    ScriptSchedulePayload,
    ScriptScheduleItem,
)
from app.modules.scripts.services import ScriptProjectService, project_workspace_dir
from app.repositories.users import UserRepository
from app.schemas.common import MessageResponse, message_response
from app.services.permissions import has_permission

router = APIRouter(prefix="/api/scripts", tags=["scripts"])
WEB_ONLY = [Depends(require_web_session)]


@router.get("", response_model=ScriptProjectListResponse, dependencies=WEB_ONLY)
def list_scripts(
    keyword: str = "",
    language: str = "",
    network_mode: str = "",
    created_by: str = "",
    sort_order: str = "descend",
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=500),
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission(SCRIPT_READ)),
) -> ScriptProjectListResponse:
    return ScriptProjectService(db).list_projects(actor, keyword, language, network_mode, created_by, sort_order, page, page_size)


@router.post("", response_model=ScriptProjectItem, dependencies=WEB_ONLY)
def create_script(
    payload: ScriptProjectPayload,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission(SCRIPT_CREATE)),
) -> ScriptProjectItem:
    return ScriptProjectService(db).create(actor, payload)


@router.get("/images", response_model=AvailableImagesResponse, dependencies=WEB_ONLY)
def list_script_images(
    db: Session = Depends(get_db),
    _: User = Depends(require_permission(SCRIPT_READ)),
) -> AvailableImagesResponse:
    return script_runtime.list_available_images(db)


@router.get("/runs/{run_id}", response_model=ScriptRunItem, dependencies=WEB_ONLY)
def get_script_run(
    run_id: str,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission(SCRIPT_READ)),
) -> ScriptRunItem:
    return ScriptRunService(db).get_run(actor, run_id)


@router.get("/runs/{run_id}/log", response_model=ScriptRunLog, dependencies=WEB_ONLY)
def get_script_run_log(
    run_id: str,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission(SCRIPT_READ)),
) -> ScriptRunLog:
    return ScriptRunService(db).run_log(actor, run_id)


@router.post("/runs/{run_id}/cancel", response_model=ScriptRunItem, dependencies=WEB_ONLY)
def cancel_script_run(
    run_id: str,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission(SCRIPT_OPERATE)),
) -> ScriptRunItem:
    return ScriptRunService(db).cancel(actor, run_id)


@router.put("/schedules/{schedule_id}", response_model=ScriptScheduleItem, dependencies=WEB_ONLY)
def update_script_schedule(
    schedule_id: int,
    payload: ScriptSchedulePayload,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission(SCRIPT_OPERATE)),
) -> ScriptScheduleItem:
    return ScriptScheduleService(db).update(actor, schedule_id, payload)


@router.delete("/schedules/{schedule_id}", response_model=MessageResponse, dependencies=WEB_ONLY)
def delete_script_schedule(
    schedule_id: int,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission(SCRIPT_OPERATE)),
) -> MessageResponse:
    ScriptScheduleService(db).delete(actor, schedule_id)
    return message_response("script.scheduleDeleted", "Schedule deleted")


@router.get("/{project_id}", response_model=ScriptProjectItem, dependencies=WEB_ONLY)
def get_script(
    project_id: int,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission(SCRIPT_READ)),
) -> ScriptProjectItem:
    service = ScriptProjectService(db)
    return service.project_item(service.get_project(actor, project_id))


@router.put("/{project_id}", response_model=ScriptProjectItem, dependencies=WEB_ONLY)
def update_script(
    project_id: int,
    payload: ScriptProjectPayload,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission(SCRIPT_UPDATE)),
) -> ScriptProjectItem:
    return ScriptProjectService(db).update(actor, project_id, payload)


@router.delete("/{project_id}", response_model=MessageResponse, dependencies=WEB_ONLY)
def delete_script(
    project_id: int,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission(SCRIPT_DELETE)),
) -> MessageResponse:
    ScriptProjectService(db).delete(actor, project_id)
    return message_response("script.deleted", "Script project deleted")


@router.get("/{project_id}/environment", response_model=ScriptEnvironmentInfo, dependencies=WEB_ONLY)
def get_script_environment(
    project_id: int,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission(SCRIPT_READ)),
) -> ScriptEnvironmentInfo:
    project = ScriptProjectService(db).get_project(actor, project_id)
    return script_runtime.environment_info(db, project, project_workspace_dir(project))


@router.get("/{project_id}/files", response_model=ScriptFileListResponse, dependencies=WEB_ONLY)
def list_script_files(
    project_id: int,
    path: str = "/",
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission(SCRIPT_READ)),
) -> ScriptFileListResponse:
    return ScriptProjectService(db).list_files(actor, project_id, path)


@router.delete("/{project_id}/files", response_model=MessageResponse, dependencies=WEB_ONLY)
def delete_script_file(
    project_id: int,
    path: str,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission(SCRIPT_OPERATE)),
) -> MessageResponse:
    ScriptProjectService(db).delete_entry(actor, project_id, path)
    return message_response("script.entryDeleted", "Entry deleted")


@router.get("/{project_id}/file", response_model=ScriptFileContent, dependencies=WEB_ONLY)
def read_script_file(
    project_id: int,
    path: str = Query(...),
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission(SCRIPT_READ)),
) -> ScriptFileContent:
    return ScriptProjectService(db).read_file(actor, project_id, path)


@router.post("/{project_id}/file", response_model=ScriptFileEntry, dependencies=WEB_ONLY)
def write_script_file(
    project_id: int,
    payload: ScriptFileWriteRequest,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission(SCRIPT_OPERATE)),
) -> ScriptFileEntry:
    return ScriptProjectService(db).write_file(actor, project_id, payload.path, payload.content)


@router.post("/{project_id}/mkdir", response_model=ScriptFileEntry, dependencies=WEB_ONLY)
def mkdir_script(
    project_id: int,
    payload: ScriptPathRequest,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission(SCRIPT_OPERATE)),
) -> ScriptFileEntry:
    return ScriptProjectService(db).mkdir(actor, project_id, payload.path)


@router.post("/{project_id}/rename", response_model=ScriptFileEntry, dependencies=WEB_ONLY)
def rename_script_entry(
    project_id: int,
    payload: ScriptRenameRequest,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission(SCRIPT_OPERATE)),
) -> ScriptFileEntry:
    return ScriptProjectService(db).rename(actor, project_id, payload.path, payload.new_name)


@router.post("/{project_id}/upload", response_model=ScriptFileEntry, dependencies=WEB_ONLY)
def upload_script_file(
    project_id: int,
    file: UploadFile = File(...),
    path: str = "/",
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission(SCRIPT_OPERATE)),
) -> ScriptFileEntry:
    return ScriptProjectService(db).upload_file(actor, project_id, path, file.filename or "", file.file, file.size)


@router.post("/{project_id}/runs", response_model=RunSubmitResponse, dependencies=WEB_ONLY)
def submit_script_run(
    project_id: int,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission(SCRIPT_OPERATE)),
) -> RunSubmitResponse:
    return ScriptRunService(db).submit(actor, project_id)


@router.get("/{project_id}/runs", response_model=ScriptRunListResponse, dependencies=WEB_ONLY)
def list_script_runs(
    project_id: int,
    status: str = "",
    trigger: str = "",
    sort_order: str = "descend",
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=500),
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission(SCRIPT_READ)),
) -> ScriptRunListResponse:
    return ScriptRunService(db).list_runs(actor, project_id, status, trigger, sort_order, page, page_size)


@router.get("/{project_id}/schedules", response_model=list[ScriptScheduleItem], dependencies=WEB_ONLY)
def list_script_schedules(
    project_id: int,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission(SCRIPT_READ)),
) -> list[ScriptScheduleItem]:
    return ScriptScheduleService(db).list_schedules(actor, project_id)


@router.post("/{project_id}/schedules", response_model=ScriptScheduleItem, dependencies=WEB_ONLY)
def create_script_schedule(
    project_id: int,
    payload: ScriptSchedulePayload,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission(SCRIPT_OPERATE)),
) -> ScriptScheduleItem:
    return ScriptScheduleService(db).create(actor, project_id, payload)


@router.websocket("/{project_id}/terminal")
async def script_terminal(websocket: WebSocket, project_id: int) -> None:
    await websocket.accept()
    db = get_session_factory()()
    container = None
    raw = None
    stop = threading.Event()
    try:
        user = _ws_authenticate(db, websocket)
        if user is None:
            await websocket.close(code=4401)
            return
        if not has_permission(user, SCRIPT_OPERATE):
            await websocket.close(code=4403)
            return
        try:
            project = ScriptProjectService(db).get_project(user, project_id)
        except HTTPException as exc:
            await websocket.send_text(json.dumps({"type": "error", "code": _ws_error_code(exc)}))
            await websocket.close()
            return
        command = websocket.query_params.get("cmd") or ""
        cols = _ws_int(websocket.query_params.get("cols"), 80)
        rows = _ws_int(websocket.query_params.get("rows"), 24)
        workspace = project_workspace_dir(project)
        workspace.mkdir(parents=True, exist_ok=True)
        try:
            container, exec_id, raw, api = script_runtime.open_terminal(db, project, workspace, command, cols, rows)
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

        threading.Thread(target=pump, name="script-exec", daemon=True).start()
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
        if container is not None:
            try:
                container.remove(force=True)
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
