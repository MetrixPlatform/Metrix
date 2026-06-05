import type { ServerMessage } from "../api/types";
import { t, translateMessage, type I18nKey } from "../i18n";

interface MessageApi {
  error(content: string): unknown;
}

export function showError(message: MessageApi, error: unknown) {
  message.error(error instanceof Error ? error.message : t("message.operationFailed"));
}

export function messageText(payload: ServerMessage, fallbackKey?: I18nKey) {
  const fallback = fallbackKey ? t(fallbackKey) : payload.message || "";
  return translateMessage(payload.code, payload.params || {}, fallback);
}
