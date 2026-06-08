import { hasI18nKey, t } from ".";
import type { TranslateParams } from "./messages";

export function openApiText(key: string, fallback = "", params: TranslateParams = {}) {
  const i18nKey = `openapi.${key}`;
  return hasI18nKey(i18nKey) ? t(i18nKey, params) : fallback;
}
