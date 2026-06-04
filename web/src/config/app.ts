const rawName = __APP_CONFIG__.appName?.trim();

export const APP_NAME = rawName || "App";
export const APP_SLUG = normalizeSlug(__APP_CONFIG__.appSlug) || normalizeSlug(APP_NAME) || "app";
export const DEFAULT_DATABASE_NAME = APP_SLUG;
export const DEFAULT_SQLITE_PATH = `runtime/${APP_SLUG}.db`;

export function appKey(name: string) {
  return `${APP_SLUG}.${name}`;
}

function normalizeSlug(value: string | undefined) {
  return value?.trim().toLowerCase().replace(/[^a-z0-9_]+/g, "_").replace(/^_+|_+$/g, "") || "";
}
