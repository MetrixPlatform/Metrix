import { reactive } from "vue";

import { appKey, LOCALE_STORAGE_KEY } from "../config/app";
import { initialLocale, setI18nLocale } from "../i18n";
import { DEFAULT_LOCALE, isLocale, type Locale } from "../i18n/messages";

const THEME_KEY = appKey("dark");

export const appStore = reactive({
  dark: localStorage.getItem(THEME_KEY) === "1",
  locale: initialLocale(),
  toggleTheme() {
    appStore.dark = !appStore.dark;
    localStorage.setItem(THEME_KEY, appStore.dark ? "1" : "0");
    applyTheme(appStore.dark);
  },
  async setLocale(locale: Locale) {
    const nextLocale = isLocale(locale) ? locale : DEFAULT_LOCALE;
    await setI18nLocale(nextLocale);
    appStore.locale = nextLocale;
    localStorage.setItem(LOCALE_STORAGE_KEY, appStore.locale);
    document.documentElement.lang = appStore.locale;
  }
});

applyTheme(appStore.dark);
document.documentElement.lang = appStore.locale;

function applyTheme(dark: boolean) {
  document.documentElement.dataset.theme = dark ? "dark" : "light";
}
