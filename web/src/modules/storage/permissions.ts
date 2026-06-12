import { actionPermission } from "../types";

export const STORAGE_CREATE = actionPermission("storage", "create");
export const STORAGE_UPDATE = actionPermission("storage", "update");
export const STORAGE_DELETE = actionPermission("storage", "delete");
export const STORAGE_OPERATE = actionPermission("storage", "operate");
export const STORAGE_MANAGE_OTHERS = actionPermission("storage", "manage_others");
