import json
from urllib.parse import quote

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.deps import require_any_permission, require_permission, require_web_session
from app.db.session import get_db
from app.models import User
from app.modules.database import (
    DATABASE_CREATE,
    DATABASE_DELETE,
    DATABASE_OPERATE,
    DATABASE_READ,
    DATABASE_UPDATE,
    SQL_SCRIPT_CREATE,
    SQL_SCRIPT_DELETE,
    SQL_SCRIPT_READ,
    SQL_SCRIPT_UPDATE,
)
from app.modules.database.jobs import DataJobService
from app.modules.database.schemas import (
    AlterTableRequest,
    CreateTableRequest,
    DataJobItem,
    DataJobListResponse,
    DatabaseConnectionItem,
    DatabaseConnectionListResponse,
    DatabaseConnectionPayload,
    DatabaseTestRequest,
    ExportRequest,
    ImportRequest,
    JobSubmitResponse,
    QueryRequest,
    QueryResponse,
    RenameTableRequest,
    RowCreateRequest,
    RowDeleteRequest,
    RowUpdateRequest,
    RunScriptRequest,
    RunScriptResponse,
    SchemaAlterRequest,
    SchemaCreateRequest,
    SchemaItem,
    SqlScriptItem,
    SqlScriptListResponse,
    SqlScriptPayload,
    TableDataResponse,
    TableItem,
)
from app.modules.database.services import DatabaseService, SqlScriptService
from app.schemas.common import MessageResponse, message_response

router = APIRouter(prefix="/api/databases")
scripts_router = APIRouter(prefix="/api/sql-scripts", tags=["sql-scripts"], dependencies=[Depends(require_web_session)])
jobs_router = APIRouter(prefix="/api/data-jobs", tags=["data-jobs"])
MANAGE_TAGS = ["databases"]
MANAGE_DEPENDENCIES = [Depends(require_web_session)]
DATA_TAGS = ["database-data"]


@router.get("", response_model=DatabaseConnectionListResponse, tags=MANAGE_TAGS, dependencies=MANAGE_DEPENDENCIES)
def list_databases(
    keyword: str = "",
    db_type: str = "",
    shared: str = "",
    is_active: bool | None = None,
    created_by: str = "",
    sort_order: str = "descend",
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=500),
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission(DATABASE_READ)),
) -> DatabaseConnectionListResponse:
    return DatabaseService(db).list_connections(actor, keyword, db_type, shared, is_active, created_by, sort_order, page, page_size)


@router.post("", response_model=DatabaseConnectionItem, tags=MANAGE_TAGS, dependencies=MANAGE_DEPENDENCIES)
def create_database(
    payload: DatabaseConnectionPayload,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission(DATABASE_CREATE)),
) -> DatabaseConnectionItem:
    return DatabaseService(db).create(actor, payload)


@router.post("/test", response_model=MessageResponse, tags=MANAGE_TAGS, dependencies=MANAGE_DEPENDENCIES)
def test_database(
    payload: DatabaseTestRequest,
    db: Session = Depends(get_db),
    actor: User = Depends(require_any_permission(DATABASE_CREATE, DATABASE_UPDATE)),
) -> MessageResponse:
    DatabaseService(db).test_connection(actor, payload)
    return message_response("database.connectionOk", "Database connection is healthy")


@router.put("/{connection_id}", response_model=DatabaseConnectionItem, tags=MANAGE_TAGS, dependencies=MANAGE_DEPENDENCIES)
def update_database(
    connection_id: int,
    payload: DatabaseConnectionPayload,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission(DATABASE_UPDATE)),
) -> DatabaseConnectionItem:
    return DatabaseService(db).update(actor, connection_id, payload)


@router.delete("/{connection_id}", response_model=MessageResponse, tags=MANAGE_TAGS, dependencies=MANAGE_DEPENDENCIES)
def delete_database(
    connection_id: int,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission(DATABASE_DELETE)),
) -> MessageResponse:
    DatabaseService(db).delete(actor, connection_id)
    return message_response("common.deleted", "Deleted")


@router.get("/{conn_id}/schemas", response_model=list[SchemaItem], tags=DATA_TAGS)
def list_schemas(
    conn_id: str,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission(DATABASE_READ)),
) -> list[SchemaItem]:
    return DatabaseService(db).schemas(actor, conn_id)


@router.get("/{conn_id}/tables", response_model=list[TableItem], tags=DATA_TAGS)
def list_tables(
    conn_id: str,
    database: str = "",
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission(DATABASE_READ)),
) -> list[TableItem]:
    return DatabaseService(db).tables(actor, conn_id, database)


@router.get("/{conn_id}/columns", response_model=list, tags=DATA_TAGS)
def list_columns(
    conn_id: str,
    database: str = "",
    table: str = "",
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission(DATABASE_READ)),
) -> list:
    return DatabaseService(db).columns(actor, conn_id, database, table)


@router.get("/{conn_id}/table-data", response_model=TableDataResponse, tags=DATA_TAGS)
def table_data(
    conn_id: str,
    database: str = "",
    table: str = "",
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=100, ge=1, le=1000),
    order_by: str = "",
    filter: str = "",
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission(DATABASE_READ)),
) -> TableDataResponse:
    return DatabaseService(db).table_data(actor, conn_id, database, table, page, page_size, order_by, filter)


@router.post("/{conn_id}/query", response_model=QueryResponse, tags=DATA_TAGS)
def query_database(
    conn_id: str,
    payload: QueryRequest,
    db: Session = Depends(get_db),
    actor: User = Depends(require_any_permission(DATABASE_READ, DATABASE_OPERATE)),
) -> QueryResponse:
    return DatabaseService(db).query(actor, conn_id, payload)


@router.post("/{conn_id}/run-script", response_model=RunScriptResponse, tags=DATA_TAGS)
def run_script(
    conn_id: str,
    payload: RunScriptRequest,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission(DATABASE_OPERATE)),
) -> RunScriptResponse:
    return DatabaseService(db).run_script(actor, conn_id, payload)


@router.post("/{conn_id}/table-rows", response_model=MessageResponse, tags=DATA_TAGS)
def create_row(
    conn_id: str,
    payload: RowCreateRequest,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission(DATABASE_OPERATE)),
) -> MessageResponse:
    affected = DatabaseService(db).create_row(actor, conn_id, payload)
    return message_response("database.rowsAffected", "Rows affected", count=affected)


@router.put("/{conn_id}/table-rows", response_model=MessageResponse, tags=DATA_TAGS)
def update_row(
    conn_id: str,
    payload: RowUpdateRequest,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission(DATABASE_OPERATE)),
) -> MessageResponse:
    affected = DatabaseService(db).update_row(actor, conn_id, payload)
    return message_response("database.rowsAffected", "Rows affected", count=affected)


@router.delete("/{conn_id}/table-rows", response_model=MessageResponse, tags=DATA_TAGS)
def delete_row(
    conn_id: str,
    payload: RowDeleteRequest,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission(DATABASE_OPERATE)),
) -> MessageResponse:
    affected = DatabaseService(db).delete_row(actor, conn_id, payload)
    return message_response("database.rowsAffected", "Rows affected", count=affected)


@router.post("/{conn_id}/tables", response_model=MessageResponse, tags=DATA_TAGS)
def create_table(
    conn_id: str,
    payload: CreateTableRequest,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission(DATABASE_OPERATE)),
) -> MessageResponse:
    DatabaseService(db).create_table(actor, conn_id, payload)
    return message_response("common.saved", "Saved")


@router.get("/{conn_id}/tables/{table}", response_model=dict, tags=DATA_TAGS)
def table_detail(
    conn_id: str,
    table: str,
    database: str = "",
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission(DATABASE_READ)),
) -> dict:
    return DatabaseService(db).table_detail(actor, conn_id, database, table)


@router.post("/{conn_id}/tables/{table}/alter", response_model=MessageResponse, tags=DATA_TAGS)
def alter_table(
    conn_id: str,
    table: str,
    payload: AlterTableRequest,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission(DATABASE_OPERATE)),
) -> MessageResponse:
    DatabaseService(db).alter_table(actor, conn_id, table, payload)
    return message_response("common.saved", "Saved")


@router.post("/{conn_id}/tables/{table}/rename", response_model=MessageResponse, tags=DATA_TAGS)
def rename_table(
    conn_id: str,
    table: str,
    payload: RenameTableRequest,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission(DATABASE_OPERATE)),
) -> MessageResponse:
    DatabaseService(db).rename_table(actor, conn_id, table, payload)
    return message_response("common.saved", "Saved")


@router.post("/{conn_id}/tables/{table}/truncate", response_model=MessageResponse, tags=DATA_TAGS)
def truncate_table(
    conn_id: str,
    table: str,
    database: str = "",
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission(DATABASE_OPERATE)),
) -> MessageResponse:
    DatabaseService(db).truncate_table(actor, conn_id, database, table)
    return message_response("common.saved", "Saved")


@router.delete("/{conn_id}/tables/{table}", response_model=MessageResponse, tags=DATA_TAGS)
def delete_table(
    conn_id: str,
    table: str,
    database: str = "",
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission(DATABASE_OPERATE)),
) -> MessageResponse:
    DatabaseService(db).delete_table(actor, conn_id, database, table)
    return message_response("common.deleted", "Deleted")


@router.post("/{conn_id}/schemas", response_model=MessageResponse, tags=DATA_TAGS)
def create_schema(
    conn_id: str,
    payload: SchemaCreateRequest,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission(DATABASE_OPERATE)),
) -> MessageResponse:
    DatabaseService(db).create_schema(actor, conn_id, payload)
    return message_response("common.saved", "Saved")


@router.post("/{conn_id}/schemas/{name}/alter", response_model=MessageResponse, tags=DATA_TAGS)
def alter_schema(
    conn_id: str,
    name: str,
    payload: SchemaAlterRequest,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission(DATABASE_OPERATE)),
) -> MessageResponse:
    DatabaseService(db).alter_schema(actor, conn_id, name, payload)
    return message_response("common.saved", "Saved")


@router.delete("/{conn_id}/schemas/{name}", response_model=MessageResponse, tags=DATA_TAGS)
def delete_schema(
    conn_id: str,
    name: str,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission(DATABASE_OPERATE)),
) -> MessageResponse:
    DatabaseService(db).delete_schema(actor, conn_id, name)
    return message_response("common.deleted", "Deleted")


@router.post("/{conn_id}/export", response_model=JobSubmitResponse, tags=["data-jobs"])
def submit_export(
    conn_id: str,
    payload: ExportRequest,
    db: Session = Depends(get_db),
    actor: User = Depends(require_any_permission(DATABASE_READ, DATABASE_OPERATE)),
) -> JobSubmitResponse:
    return DataJobService(db).submit_export(actor, conn_id, payload)


@router.post("/{conn_id}/import", response_model=JobSubmitResponse, tags=["data-jobs"])
def submit_import(
    conn_id: str,
    file: UploadFile = File(...),
    format: str = Form(...),
    database: str = Form(""),
    target_table: str = Form(""),
    mode: str = Form("append"),
    mapping: str = Form("{}"),
    create_table: bool = Form(False),
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission(DATABASE_OPERATE)),
) -> JobSubmitResponse:
    payload = ImportRequest(
        format=format,
        database=database,
        target_table=target_table,
        mode=mode,
        mapping=json.loads(mapping or "{}"),
        create_table=create_table,
    )
    return DataJobService(db).submit_import(actor, conn_id, payload, file)


@scripts_router.get("", response_model=SqlScriptListResponse)
def list_sql_scripts(
    keyword: str = "",
    connection_id: int | None = None,
    shared: str = "",
    created_by: str = "",
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=500),
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission(SQL_SCRIPT_READ)),
) -> SqlScriptListResponse:
    return SqlScriptService(db).list_scripts(actor, keyword, connection_id, shared, created_by, page, page_size)


@scripts_router.post("", response_model=SqlScriptItem)
def create_sql_script(
    payload: SqlScriptPayload,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission(SQL_SCRIPT_CREATE)),
) -> SqlScriptItem:
    return SqlScriptService(db).create(actor, payload)


@scripts_router.put("/{script_id}", response_model=SqlScriptItem)
def update_sql_script(
    script_id: int,
    payload: SqlScriptPayload,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission(SQL_SCRIPT_UPDATE)),
) -> SqlScriptItem:
    return SqlScriptService(db).update(actor, script_id, payload)


@scripts_router.delete("/{script_id}", response_model=MessageResponse)
def delete_sql_script(
    script_id: int,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission(SQL_SCRIPT_DELETE)),
) -> MessageResponse:
    SqlScriptService(db).delete(actor, script_id)
    return message_response("common.deleted", "Deleted")


@jobs_router.get("", response_model=DataJobListResponse)
def list_data_jobs(
    kind: str = "",
    status: str = "",
    sort_order: str = "descend",
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=500),
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission(DATABASE_READ)),
) -> DataJobListResponse:
    return DataJobService(db).list_jobs(actor, kind, status, sort_order, page, page_size)


@jobs_router.get("/{job_id}", response_model=DataJobItem)
def get_data_job(
    job_id: str,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission(DATABASE_READ)),
) -> DataJobItem:
    return DataJobService(db).get_job(actor, job_id)


@jobs_router.get("/{job_id}/download")
def download_data_job(
    job_id: str,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission(DATABASE_READ)),
) -> StreamingResponse:
    file_name, stream = DataJobService(db).download(actor, job_id)
    encoded = quote(file_name)
    return StreamingResponse(
        stream,
        media_type="application/octet-stream",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{encoded}"},
    )


@jobs_router.delete("/{job_id}", response_model=MessageResponse)
def delete_data_job(
    job_id: str,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission(DATABASE_READ)),
) -> MessageResponse:
    DataJobService(db).delete(actor, job_id)
    return message_response("common.deleted", "Deleted")
