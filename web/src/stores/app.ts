import { reactive } from "vue";

const THEME_KEY = "metrix.dark";

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
