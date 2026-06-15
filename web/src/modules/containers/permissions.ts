import { actionPermission } from "../types";

export const CONTAINER_CREATE = actionPermission("container", "create");
export const CONTAINER_READ = actionPermission("container", "read");
export const CONTAINER_UPDATE = actionPermission("container", "update");
export const CONTAINER_DELETE = actionPermission("container", "delete");
export const CONTAINER_OPERATE = actionPermission("container", "operate");
export const CONTAINER_MANAGE_OTHERS = actionPermission("container", "manage_others");
