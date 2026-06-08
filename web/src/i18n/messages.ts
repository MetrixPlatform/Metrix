import zhCN from "./locales/zh-CN.json";

export const locales = ["zh-CN", "en-US"] as const;

export type Locale = (typeof locales)[number];
export type TranslateParam = string | number | boolean | null | undefined;
export type TranslateParams = Record<string, TranslateParam>;
export type LocaleMessages = typeof zhCN;
export type I18nKey = string;

export const DEFAULT_LOCALE: Locale = "zh-CN";
export const defaultMessages = zhCN;

const localeLoaders = {
  "zh-CN": () => Promise.resolve(zhCN),
  "en-US": () => import("./locales/en-US.json").then((module) => module.default as LocaleMessages)
} satisfies Record<Locale, () => Promise<LocaleMessages>>;

export function isLocale(value: unknown): value is Locale {
  return typeof value === "string" && locales.includes(value as Locale);
}

export async function loadLocaleMessages(locale: Locale) {
  return localeLoaders[locale]();
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
