import { reactive } from "vue";

import { appKey } from "../config/app";
import { setI18nLocale } from "../i18n";
import { DEFAULT_LOCALE, isLocale, type Locale } from "../i18n/messages";
import { settingsStore } from "./settings";

const THEME_KEY = appKey("dark");
const LOCALE_KEY = appKey("locale");

export const appStore = reactive({
  dark: localStorage.getItem(THEME_KEY) === "1",
  locale: initialLocale(),
  toggleTheme() {
    appStore.dark = !appStore.dark;
    localStorage.setItem(THEME_KEY, appStore.dark ? "1" : "0");
    applyTheme(appStore.dark);
  },
  setLocale(locale: Locale) {
    appStore.locale = isLocale(locale) ? locale : DEFAULT_LOCALE;
    localStorage.setItem(LOCALE_KEY, appStore.locale);
    document.documentElement.lang = appStore.locale;
    setI18nLocale(appStore.locale);
  }
});

applyTheme(appStore.dark);
document.documentElement.lang = appStore.locale;
setI18nLocale(appStore.locale);

function applyTheme(dark: boolean) {
  document.documentElement.dataset.theme = dark ? "dark" : "light";
}

function initialLocale(): Locale {
  const saved = localStorage.getItem(LOCALE_KEY);
  if (isLocale(saved)) {
    return saved;
  }
  return settingsStore.defaultLocale();
}
