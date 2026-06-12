import { computed, reactive } from "vue";
import { createI18n } from "vue-i18n";

import { LOCALE_STORAGE_KEY } from "../config/app";
import {
  DEFAULT_LOCALE,
  defaultMessages,
  hasMessagePath,
  isLocale,
  loadLocaleName,
  loadLocaleMessages,
  locales,
  type I18nKey,
  type Locale,
  type TranslateParams
} from "./messages";

export { DEFAULT_LOCALE, isLocale, locales };
export type { I18nKey, Locale, TranslateParams };

export const i18n = createI18n({
  legacy: false,
  locale: initialLocale(),
  fallbackLocale: DEFAULT_LOCALE,
  messages: {
    [DEFAULT_LOCALE]: defaultMessages
  } as Record<string, typeof defaultMessages>,
  missingWarn: false,
  fallbackWarn: false
});
const loadedLocales = new Set<Locale>([DEFAULT_LOCALE]);
const localeNames = reactive<Record<string, string>>({
  [DEFAULT_LOCALE]: defaultMessages.language || DEFAULT_LOCALE
});
let localeNamesPromise: Promise<void> | null = null;

export const localeOptions = computed(() => locales.map((value) => ({ label: localeNames[value] || value, value })));

export function ensureLocaleNames() {
  localeNamesPromise ??= Promise.all(
    locales.map(async (locale) => {
      localeNames[locale] = await loadLocaleName(locale);
    })
  ).then(() => undefined);
  return localeNamesPromise;
}

export function t(key: I18nKey | string, params: TranslateParams = {}) {
  return String(i18n.global.t(key, params));
}

export function hasI18nKey(key: string) {
  return hasMessagePath(i18n.global.getLocaleMessage(currentLocale()), key) || hasMessagePath(i18n.global.getLocaleMessage(DEFAULT_LOCALE), key);
}

export async function setupI18n(locale: Locale = initialLocale()) {
  await setI18nLocale(locale);
}

export async function setI18nLocale(locale: Locale) {
  const nextLocale = isLocale(locale) ? locale : DEFAULT_LOCALE;
  if (!loadedLocales.has(nextLocale)) {
    const messages = await loadLocaleMessages(nextLocale);
    i18n.global.setLocaleMessage(nextLocale, messages);
    localeNames[nextLocale] = messages.language || nextLocale;
    loadedLocales.add(nextLocale);
  }
  i18n.global.locale.value = nextLocale;
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

export function initialLocale(): Locale {
  const saved = localStorage.getItem(LOCALE_STORAGE_KEY);
  return isLocale(saved) ? saved : DEFAULT_LOCALE;
}

function currentLocale(): Locale {
  const locale = i18n.global.locale.value;
  return isLocale(locale) ? locale : DEFAULT_LOCALE;
}
