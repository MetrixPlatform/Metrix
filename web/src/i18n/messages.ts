import zhCN from "./locales/zh-CN.json";

export type Locale = string;
export type TranslateParam = string | number | boolean | null | undefined;
export type TranslateParams = Record<string, TranslateParam>;
export type MessageTree = { [key: string]: string | MessageTree };
export type LocaleMessages = MessageTree & { language: string };
export type I18nKey = string;

export const DEFAULT_LOCALE: Locale = "zh-CN";

const defaultModuleMessages = import.meta.glob<MessageTree>("../modules/*/i18n/zh-CN.json", { eager: true, import: "default" });
const messageModules = import.meta.glob<MessageTree>(["./locales/*.json", "!./locales/zh-CN.json"], { import: "default" });
const moduleMessageModules = import.meta.glob<MessageTree>(["../modules/*/i18n/*.json", "!../modules/*/i18n/zh-CN.json"], {
  import: "default"
});
const languageModules = import.meta.glob<string>(["./locales/*.json", "!./locales/zh-CN.json"], { import: "language" });

export const defaultMessages = mergeMessages(zhCN as MessageTree, ...Object.values(defaultModuleMessages));

const baseLocaleLoaders: Record<Locale, () => Promise<MessageTree>> = {
  ...moduleMap(messageModules),
  [DEFAULT_LOCALE]: () => Promise.resolve(zhCN as MessageTree)
};
const moduleLocaleLoaders = moduleLoaderMap(moduleMessageModules);
const localeLoaders = Object.fromEntries(
  Object.entries(baseLocaleLoaders).map(([locale, loadBase]) => [
    locale,
    async () => mergeMessages(await loadBase(), ...(await loadModuleMessages(locale)))
  ])
) as Record<Locale, () => Promise<LocaleMessages>>;
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

function moduleLocaleFromPath(path: string) {
  return path.replace(/^\.\.\/modules\/[^/]+\/i18n\//, "").replace(/\.json$/, "");
}

function moduleLoaderMap(modules: Record<string, () => Promise<MessageTree>>) {
  return Object.entries(modules).reduce<Record<Locale, Array<() => Promise<MessageTree>>>>((groups, [path, loader]) => {
    const locale = moduleLocaleFromPath(path);
    groups[locale] ||= [];
    groups[locale].push(loader);
    return groups;
  }, {});
}

async function loadModuleMessages(locale: Locale) {
  return Promise.all((moduleLocaleLoaders[locale] || []).map((loader) => loader()));
}

function mergeMessages(...sources: MessageTree[]): LocaleMessages {
  return sources.reduce<MessageTree>((merged, source) => mergeInto(merged, source), {}) as LocaleMessages;
}

function mergeInto(target: MessageTree, source: MessageTree): MessageTree {
  for (const [key, value] of Object.entries(source)) {
    if (key === "language" && Object.hasOwn(target, key)) continue;
    if (isRecord(value) && isRecord(target[key])) {
      mergeInto(target[key] as MessageTree, value);
    } else if (isRecord(value)) {
      target[key] = mergeInto({}, value);
    } else {
      target[key] = value;
    }
  }
  return target;
}
