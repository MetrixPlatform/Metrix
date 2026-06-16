import { actionPermission } from "../types";

export const SCRIPT_CREATE = actionPermission("script", "create");
export const SCRIPT_UPDATE = actionPermission("script", "update");
export const SCRIPT_DELETE = actionPermission("script", "delete");
export const SCRIPT_OPERATE = actionPermission("script", "operate");
export const SCRIPT_MANAGE_OTHERS = actionPermission("script", "manage_others");
