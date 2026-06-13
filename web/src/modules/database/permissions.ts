import { actionPermission } from "../types";

export const DATABASE_CREATE = actionPermission("database", "create");
export const DATABASE_READ = actionPermission("database", "read");
export const DATABASE_UPDATE = actionPermission("database", "update");
export const DATABASE_DELETE = actionPermission("database", "delete");
export const DATABASE_OPERATE = actionPermission("database", "operate");
export const DATABASE_MANAGE_OTHERS = actionPermission("database", "manage_others");

export const SQL_SCRIPT_CREATE = actionPermission("sql_script", "create");
export const SQL_SCRIPT_READ = actionPermission("sql_script", "read");
export const SQL_SCRIPT_UPDATE = actionPermission("sql_script", "update");
export const SQL_SCRIPT_DELETE = actionPermission("sql_script", "delete");
