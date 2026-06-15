import { hasI18nKey, i18n, t, DEFAULT_LOCALE } from ".";
import type { TranslateParams } from "./messages";

export function openApiText(key: string, fallback = "", params: TranslateParams = {}) {
  const i18nKey = `openapi.${key}`;
  const literalValue = literalOpenApiText(key);
  if (literalValue) {
    return interpolate(literalValue, params);
  }
  return hasI18nKey(i18nKey) ? t(i18nKey, params) : fallback;
}

function literalOpenApiText(key: string) {
  return literalOpenApiTextFromMessages(i18n.global.getLocaleMessage(String(i18n.global.locale.value)), key)
    || literalOpenApiTextFromMessages(i18n.global.getLocaleMessage(DEFAULT_LOCALE), key);
}

function literalOpenApiTextFromMessages(messages: unknown, key: string) {
  const operationMatch = key.match(/^operation\.(.+)\.(summary|description)$/);
  if (operationMatch) {
    return openApiString(messages, ["operation", operationMatch[1], operationMatch[2]]);
  }
  const parameterMatch = key.match(/^parameter\.(.+)\.([^.]+)$/);
  if (parameterMatch) {
    return openApiString(messages, ["parameter", parameterMatch[1], parameterMatch[2]]);
  }
  return "";
}

function openApiString(messages: unknown, path: string[]) {
  let current = isRecord(messages) ? messages.openapi : undefined;
  for (const part of path) {
    if (!isRecord(current)) return "";
    current = current[part];
  }
  return typeof current === "string" ? current : "";
}

function interpolate(value: string, params: TranslateParams) {
  return Object.entries(params).reduce((text, [key, param]) => text.replaceAll(`{${key}}`, String(param ?? "")), value);
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return Boolean(value) && typeof value === "object" && !Array.isArray(value);
}
