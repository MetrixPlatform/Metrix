import { reactive } from "vue";

const THEME_KEY = "metrix.dark";

export const appStore = reactive({
  dark: localStorage.getItem(THEME_KEY) === "1",
  toggleTheme() {
    this.dark = !this.dark;
    localStorage.setItem(THEME_KEY, this.dark ? "1" : "0");
  }
});
