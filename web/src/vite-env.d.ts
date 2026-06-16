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

declare module "monaco-editor/esm/vs/basic-languages/sql/sql.js" {
  export const conf: unknown;
  export const language: {
    keywords: string[];
    operators: string[];
    builtinFunctions: string[];
    builtinVariables: string[];
  };
}

declare module "monaco-editor/esm/vs/basic-languages/*/*.js" {
  export const conf: unknown;
  export const language: {
    keywords?: string[];
    typeKeywords?: string[];
    operators?: string[];
    builtins?: string[];
    builtinFunctions?: string[];
    builtinVariables?: string[];
    tags?: string[];
    attributes?: string[];
  };
}
