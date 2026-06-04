import { reactive } from "vue";

import { appKey } from "../config/app";

const THEME_KEY = appKey("dark");

export const appStore = reactive({
  dark: localStorage.getItem(THEME_KEY) === "1",
  toggleTheme() {
    appStore.dark = !appStore.dark;
    localStorage.setItem(THEME_KEY, appStore.dark ? "1" : "0");
    applyTheme(appStore.dark);
  }
});

applyTheme(appStore.dark);

function applyTheme(dark: boolean) {
  document.documentElement.dataset.theme = dark ? "dark" : "light";
}
