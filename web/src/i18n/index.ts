import { computed } from "vue";

import { appStore } from "../stores/app";
import { DEFAULT_LOCALE, isLocale, locales, translate, type I18nKey, type Locale, type TranslateParams } from "./messages";

export { DEFAULT_LOCALE, isLocale, locales, translate };
export type { I18nKey, Locale, TranslateParams };

export const localeOptions = [
  { labelKey: "language.zhCN" as I18nKey, value: "zh-CN" as Locale, shortLabel: "ZH" },
  { labelKey: "language.enUS" as I18nKey, value: "en-US" as Locale, shortLabel: "EN" }
];

export function t(key: I18nKey, params?: TranslateParams) {
  return translate(appStore.locale, key, params);
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
