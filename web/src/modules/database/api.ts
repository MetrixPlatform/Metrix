import { del, download, post, put, queryString, request } from "../../api/client";
import type { PageResult, ServerMessage } from "../../api/types";

export type DatabaseType = "mysql" | "mariadb";
export type DataJobKind = "export" | "import";
export type DataJobStatus = "pending" | "running" | "success" | "failed";
export type DataFormat = "csv" | "xlsx" | "sqlite" | "sql";

export interface DatabaseConnection {
  id: number;
  conn_id: string;
  name: string;
  db_type: DatabaseType;
  host: string;
  port: number;
  username: string;
  default_database: string;
  is_shared: boolean;
  is_active: boolean;
  created_by: number | null;
  created_by_username: string;
  created_at: string;
  updated_at: string;
}

export interface DatabaseConnectionPayload {
  name: string;
  conn_id: string;
  db_type: DatabaseType;
  host: string;
  port: number;
  username: string;
  password: string;
  default_database: string;
  is_shared: boolean;
  is_active: boolean;
}

export interface DatabaseTestPayload {
  id?: number | null;
  db_type: DatabaseType;
  host: string;
  port: number;
  username: string;
  password: string;
  default_database: string;
}

export interface ConnectionFilters {
  keyword?: string;
  db_type?: DatabaseType | "";
  shared?: "shared" | "private" | "";
  is_active?: boolean | null;
  created_by?: "all" | "me" | "";
  sort_order?: "ascend" | "descend";
  page?: number;
  page_size?: number;
}

export interface SchemaItem {
  name: string;
}

export interface TableItem {
  name: string;
}

export interface ColumnItem {
  name: string;
  type: string;
  nullable: boolean;
  default: unknown;
  primary_key: boolean;
  autoincrement: boolean;
  comment: string;
}

export interface TableData {
  columns: ColumnItem[];
  primary_keys: string[];
  rows: Record<string, unknown>[];
  total: number;
  page: number;
  page_size: number;
}

export interface QueryPayload {
  sql: string;
  database?: string;
  page?: number;
  page_size?: number;
}

export interface QueryResult {
  statement_type: "read" | "write";
  columns: string[];
  rows: Record<string, unknown>[];
  total: number;
  page: number;
  page_size: number;
  affected_rows: number;
}

export interface RunScriptPayload {
  content?: string;
  script_id?: number | null;
  database?: string;
  stop_on_error?: boolean;
}

export interface RunScriptResult {
  results: Array<{
    index: number;
    sql: string;
    ok: boolean;
    message: string;
    affected_rows: number;
    columns: string[];
    rows: Record<string, unknown>[];
  }>;
  stopped: boolean;
}

export interface SqlScript {
  id: number;
  name: string;
  content: string;
  connection_id: number | null;
  connection_name: string;
  description: string;
  is_shared: boolean;
  created_by: number | null;
  created_by_username: string;
  created_at: string;
  updated_at: string;
}

export interface SqlScriptPayload {
  name: string;
  content: string;
  connection_id: number | null;
  description: string;
  is_shared: boolean;
}

export interface DataJob {
  id: number;
  job_id: string;
  kind: DataJobKind;
  connection_id: number;
  conn_id: string;
  connection_name: string;
  format: DataFormat;
  status: DataJobStatus;
  file_name: string;
  file_size: number;
  row_count: number;
  error_code: string;
  created_by: number | null;
  created_at: string;
  started_at: string | null;
  finished_at: string | null;
  expires_at: string | null;
  downloaded_at: string | null;
}

export interface JobSubmitResponse {
  job_id: string;
  status: string;
}

export function listDatabaseConnections(filters: ConnectionFilters = {}) {
  return request<PageResult<DatabaseConnection>>(`/databases${queryString(filters)}`);
}

export function createDatabaseConnection(payload: DatabaseConnectionPayload) {
  return post<DatabaseConnection>("/databases", payload);
}

export function updateDatabaseConnection(id: number, payload: DatabaseConnectionPayload) {
  return put<DatabaseConnection>(`/databases/${id}`, payload);
}

export function deleteDatabaseConnection(id: number) {
  return del<ServerMessage>(`/databases/${id}`);
}

export function testDatabaseConnection(payload: DatabaseTestPayload) {
  return post<ServerMessage>("/databases/test", payload);
}

export function listSchemas(connId: string) {
  return request<SchemaItem[]>(`/databases/${encodeURIComponent(connId)}/schemas`);
}

export function listTables(connId: string, database = "") {
  return request<TableItem[]>(`/databases/${encodeURIComponent(connId)}/tables${queryString({ database })}`);
}

export function listColumns(connId: string, database: string, table: string) {
  return request<ColumnItem[]>(`/databases/${encodeURIComponent(connId)}/columns${queryString({ database, table })}`);
}

export function getTableData(connId: string, database: string, table: string, page = 1, pageSize = 100, orderBy = "", filter = "") {
  return request<TableData>(
    `/databases/${encodeURIComponent(connId)}/table-data${queryString({ database, table, page, page_size: pageSize, order_by: orderBy, filter })}`
  );
}

export function queryDatabase(connId: string, payload: QueryPayload) {
  return post<QueryResult>(`/databases/${encodeURIComponent(connId)}/query`, payload);
}

export function runSqlScript(connId: string, payload: RunScriptPayload) {
  return post<RunScriptResult>(`/databases/${encodeURIComponent(connId)}/run-script`, payload);
}

export function createRow(connId: string, payload: { database?: string; table: string; values: Record<string, unknown> }) {
  return post<ServerMessage>(`/databases/${encodeURIComponent(connId)}/table-rows`, payload);
}

export function updateRow(connId: string, payload: { database?: string; table: string; keys: Record<string, unknown>; values: Record<string, unknown> }) {
  return put<ServerMessage>(`/databases/${encodeURIComponent(connId)}/table-rows`, payload);
}

export function deleteRow(connId: string, payload: { database?: string; table: string; keys: Record<string, unknown> }) {
  return request<ServerMessage>(`/databases/${encodeURIComponent(connId)}/table-rows`, { method: "DELETE", body: JSON.stringify(payload) });
}

export function createTable(connId: string, payload: { database?: string; name: string; columns: unknown[] }) {
  return post<ServerMessage>(`/databases/${encodeURIComponent(connId)}/tables`, payload);
}

export function renameTable(connId: string, table: string, payload: { database?: string; new_name: string }) {
  return post<ServerMessage>(`/databases/${encodeURIComponent(connId)}/tables/${encodeURIComponent(table)}/rename`, payload);
}

export function truncateTable(connId: string, database: string, table: string) {
  return post<ServerMessage>(`/databases/${encodeURIComponent(connId)}/tables/${encodeURIComponent(table)}/truncate${queryString({ database })}`);
}

export function dropTable(connId: string, database: string, table: string) {
  return del<ServerMessage>(`/databases/${encodeURIComponent(connId)}/tables/${encodeURIComponent(table)}${queryString({ database })}`);
}

export function createSchema(connId: string, payload: { name: string; charset?: string; collation?: string }) {
  return post<ServerMessage>(`/databases/${encodeURIComponent(connId)}/schemas`, payload);
}

export function dropSchema(connId: string, name: string) {
  return del<ServerMessage>(`/databases/${encodeURIComponent(connId)}/schemas/${encodeURIComponent(name)}`);
}

export function submitExport(connId: string, payload: { format: DataFormat; database?: string; tables?: string[]; sql?: string }) {
  return post<JobSubmitResponse>(`/databases/${encodeURIComponent(connId)}/export`, payload);
}

export function submitImport(connId: string, payload: { file: File; format: DataFormat; database?: string; target_table?: string; mode?: string; mapping?: Record<string, string>; create_table?: boolean }) {
  const body = new FormData();
  body.append("file", payload.file);
  body.append("format", payload.format);
  body.append("database", payload.database || "");
  body.append("target_table", payload.target_table || "");
  body.append("mode", payload.mode || "append");
  body.append("mapping", JSON.stringify(payload.mapping || {}));
  body.append("create_table", String(Boolean(payload.create_table)));
  return request<JobSubmitResponse>(`/databases/${encodeURIComponent(connId)}/import`, { method: "POST", body });
}

export function listSqlScripts(filters: { keyword?: string; connection_id?: number | null; shared?: string; created_by?: string; page?: number; page_size?: number } = {}) {
  return request<PageResult<SqlScript>>(`/sql-scripts${queryString(filters)}`);
}

export function createSqlScript(payload: SqlScriptPayload) {
  return post<SqlScript>("/sql-scripts", payload);
}

export function updateSqlScript(id: number, payload: SqlScriptPayload) {
  return put<SqlScript>(`/sql-scripts/${id}`, payload);
}

export function deleteSqlScript(id: number) {
  return del<ServerMessage>(`/sql-scripts/${id}`);
}

export function listDataJobs(filters: { kind?: string; status?: string; page?: number; page_size?: number } = {}) {
  return request<PageResult<DataJob>>(`/data-jobs${queryString(filters)}`);
}

export function getDataJob(jobId: string) {
  return request<DataJob>(`/data-jobs/${encodeURIComponent(jobId)}`);
}

export function downloadDataJob(jobId: string) {
  return download(`/data-jobs/${encodeURIComponent(jobId)}/download`);
}

export function deleteDataJob(jobId: string) {
  return del<ServerMessage>(`/data-jobs/${encodeURIComponent(jobId)}`);
}
