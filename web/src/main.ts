import { createApp } from "vue";

import App from "./App.vue";
import { i18n, setupI18n } from "./i18n";
import { router } from "./router";
import { appStore } from "./stores/app";
import "./styles/main.css";

void bootstrap();

async function bootstrap() {
  await setupI18n(appStore.locale);
  createApp(App).use(i18n).use(router).mount("#app");
}
