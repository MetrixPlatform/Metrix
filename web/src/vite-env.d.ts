/// <reference types="vite/client" />

declare const __APP_CONFIG__: {
  appName?: string;
  appSlug?: string;
  enabledModules?: string[];
  disabledModules?: string[];
};

declare module "*.vue" {
  import type { DefineComponent } from "vue";

  const component: DefineComponent<object, object, unknown>;
  export default component;
}
