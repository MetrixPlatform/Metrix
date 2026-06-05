import { computed, watch } from "vue";
import { createI18n } from "vue-i18n";

import { appStore } from "../stores/app";
import { DEFAULT_LOCALE, hasMessageKey, isLocale, locales, messages, type I18nKey, type Locale, type TranslateParams } from "./messages";

export { DEFAULT_LOCALE, isLocale, locales };
export type { I18nKey, Locale, TranslateParams };

export const i18n = createI18n({
  legacy: false,
  locale: appStore.locale,
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
  return hasMessageKey(appStore.locale, key);
}

export function setI18nLocale(locale: Locale) {
  i18n.global.locale.value = locale;
}

watch(
  () => appStore.locale,
  (locale) => setI18nLocale(locale)
);

export function translateMessage(code: string, params: TranslateParams = {}, fallback = "") {
  if (code && hasI18nKey(code)) {
    return t(code, params);
  }
  return fallback || code || t("message.operationFailed");
}

export function formatDateTime(value: string | number | Date) {
  return new Date(value).toLocaleString(appStore.locale);
}

export function useI18n() {
  return {
    locale: computed(() => appStore.locale),
    t,
    formatDateTime
  };
}
