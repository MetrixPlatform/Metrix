import zhCN from "./locales/zh-CN.json";

export type Locale = string;
export type TranslateParam = string | number | boolean | null | undefined;
export type TranslateParams = Record<string, TranslateParam>;
export type LocaleMessages = typeof zhCN;
export type I18nKey = string;

export const DEFAULT_LOCALE: Locale = "zh-CN";
export const defaultMessages = zhCN;

const messageModules = import.meta.glob<LocaleMessages>(["./locales/*.json", "!./locales/zh-CN.json"], { import: "default" });
const languageModules = import.meta.glob<string>(["./locales/*.json", "!./locales/zh-CN.json"], { import: "language" });

const localeLoaders: Record<Locale, () => Promise<LocaleMessages>> = {
  ...moduleMap(messageModules),
  [DEFAULT_LOCALE]: () => Promise.resolve(zhCN)
};
const languageLoaders: Record<Locale, () => Promise<string>> = {
  ...moduleMap(languageModules),
  [DEFAULT_LOCALE]: () => Promise.resolve(zhCN.language)
};

export const locales = Object.keys(localeLoaders).sort((left, right) => {
  if (left === DEFAULT_LOCALE) return -1;
  if (right === DEFAULT_LOCALE) return 1;
  return left.localeCompare(right);
});

export function isLocale(value: unknown): value is Locale {
  return typeof value === "string" && locales.includes(value as Locale);
}

export async function loadLocaleMessages(locale: Locale) {
  return (localeLoaders[locale] || localeLoaders[DEFAULT_LOCALE])();
}

export async function loadLocaleName(locale: Locale) {
  return (await (languageLoaders[locale] || languageLoaders[DEFAULT_LOCALE])()) || locale;
}

export function hasMessagePath(messages: unknown, key: string) {
  if (!key) return false;
  return key.split(".").every((part) => {
    if (!isRecord(messages) || !Object.hasOwn(messages, part)) return false;
    messages = messages[part];
    return true;
  });
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return Boolean(value) && typeof value === "object" && !Array.isArray(value);
}

function moduleMap<T>(modules: Record<string, () => Promise<T>>) {
  return Object.fromEntries(Object.entries(modules).map(([path, loader]) => [localeFromPath(path), loader])) as Record<Locale, () => Promise<T>>;
}

function localeFromPath(path: string) {
  return path.replace(/^\.\/locales\//, "").replace(/\.json$/, "");
}
