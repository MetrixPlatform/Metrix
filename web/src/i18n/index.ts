import { computed } from "vue";
import { createI18n } from "vue-i18n";

import { appKey } from "../config/app";
import { DEFAULT_LOCALE, hasMessageKey, isLocale, locales, messages, type I18nKey, type Locale, type TranslateParams } from "./messages";

export { DEFAULT_LOCALE, isLocale, locales };
export type { I18nKey, Locale, TranslateParams };

const LOCALE_KEY = appKey("locale");

export const i18n = createI18n({
  legacy: false,
  locale: initialLocale(),
  fallbackLocale: DEFAULT_LOCALE,
  messages,
  missingWarn: false,
  fallbackWarn: false
});

export const localeOptions = [
  { labelKey: "language.zhCN" as I18nKey, value: "zh-CN" as Locale },
  { labelKey: "language.enUS" as I18nKey, value: "en-US" as Locale }
];

export function t(key: I18nKey | string, params: TranslateParams = {}) {
  return String(i18n.global.t(key, params));
}

export function hasI18nKey(key: string) {
  return hasMessageKey(currentLocale(), key);
}

export function setI18nLocale(locale: Locale) {
  i18n.global.locale.value = locale;
}

export function translateMessage(code: string, params: TranslateParams = {}, fallback = "") {
  if (code && hasI18nKey(code)) {
    return t(code, params);
  }
  return fallback || code || t("message.operationFailed");
}

export function formatDateTime(value: string | number | Date) {
  return new Date(value).toLocaleString(currentLocale());
}

export function useI18n() {
  return {
    locale: computed(() => currentLocale()),
    t,
    formatDateTime
  };
}

function initialLocale(): Locale {
  const saved = localStorage.getItem(LOCALE_KEY);
  return isLocale(saved) ? saved : DEFAULT_LOCALE;
}

function currentLocale(): Locale {
  const locale = i18n.global.locale.value;
  return isLocale(locale) ? locale : DEFAULT_LOCALE;
}
