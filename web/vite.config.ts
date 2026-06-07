import vue from "@vitejs/plugin-vue";
import { defineConfig } from "vite";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const ROOT_DIR = path.dirname(fileURLToPath(import.meta.url));
const appConfig = loadAppConfig();

export default defineConfig({
  define: {
    __APP_CONFIG__: JSON.stringify(appConfig)
  },
  plugins: [
    vue(),
    {
      name: "app-config-html",
      transformIndexHtml(html) {
        return html.replaceAll("%APP_NAME%", escapeHtml(appConfig.appName));
      }
    }
  ],
  server: {
    proxy: {
      "/api/": "http://127.0.0.1:8000",
      "/openapi.json": "http://127.0.0.1:8000"
    }
  }
});

function loadAppConfig() {
  const configPath = path.resolve(ROOT_DIR, "../app.config.json");
  const fileConfig = readJson(configPath);
  const appName =
    cleanName(process.env.APP_NAME) ||
    cleanName(process.env.VITE_APP_NAME) ||
    cleanName(process.env.METRIX_APP_NAME) ||
    cleanName(fileConfig.appName) ||
    "App";
  return {
    appName,
    appSlug:
      cleanSlug(process.env.APP_SLUG) ||
      cleanSlug(process.env.VITE_APP_SLUG) ||
      cleanSlug(process.env.METRIX_APP_SLUG) ||
      cleanSlug(fileConfig.appSlug) ||
      slugify(appName)
  };
}

function readJson(filePath: string) {
  try {
    return JSON.parse(fs.readFileSync(filePath, "utf-8")) as { appName?: unknown; appSlug?: unknown };
  } catch {
    return {};
  }
}

function cleanName(value: unknown) {
  return typeof value === "string" ? value.trim() : "";
}

function cleanSlug(value: unknown) {
  return typeof value === "string" ? value.trim().toLowerCase().replace(/[^a-z0-9_]+/g, "_").replace(/^_+|_+$/g, "") : "";
}

function slugify(value: string) {
  return cleanSlug(value) || "app";
}

function escapeHtml(value: string) {
  return value.replace(/[&<>"']/g, (char) => {
    const entities: Record<string, string> = {
      "&": "&amp;",
      "<": "&lt;",
      ">": "&gt;",
      '"': "&quot;",
      "'": "&#39;"
    };
    return entities[char];
  });
}
