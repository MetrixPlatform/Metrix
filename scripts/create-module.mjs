import { existsSync, mkdirSync, writeFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const rootDir = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const [rawName, zhTitleArg, enTitleArg] = process.argv.slice(2);

if (!rawName) {
  fail('Usage: node scripts/create-module.mjs <module-name> ["Chinese title"] ["English title"]');
}

const kebab = toKebab(rawName);
if (!/^[a-z][a-z0-9-]*$/.test(kebab)) {
  fail("Module name must start with a letter and contain only letters, numbers, dashes or underscores.");
}

const snake = kebab.replaceAll("-", "_");
const camel = toCamel(kebab);
const pascal = toPascal(kebab);
const constant = snake.toUpperCase();
const zhTitle = zhTitleArg || kebab;
const enTitle = enTitleArg || toTitle(kebab);

const targets = [
  ["web module", path.join(rootDir, "web", "src", "modules", kebab)],
  ["server module", path.join(rootDir, "server", "app", "modules", snake)]
];

for (const [label, dir] of targets) {
  if (existsSync(dir)) {
    fail(`${label} already exists: ${dir}`);
  }
}

write(path.join(rootDir, "web", "src", "modules", kebab, "index.ts"), webIndexTemplate());
write(path.join(rootDir, "web", "src", "modules", kebab, "api.ts"), webApiTemplate());
write(path.join(rootDir, "web", "src", "modules", kebab, "views", `${pascal}View.vue`), webViewTemplate());
write(path.join(rootDir, "web", "src", "modules", kebab, "i18n", "zh-CN.json"), jsonTemplate(zhLocale()));
write(path.join(rootDir, "web", "src", "modules", kebab, "i18n", "en-US.json"), jsonTemplate(enLocale()));
write(path.join(rootDir, "server", "app", "modules", snake, "__init__.py"), serverInitTemplate());
write(path.join(rootDir, "server", "app", "modules", snake, "api.py"), serverApiTemplate());

console.log(`Created module ${kebab}`);
console.log(`Web:    web/src/modules/${kebab}`);
console.log(`Server: server/app/modules/${snake}`);

function write(filePath, content) {
  mkdirSync(path.dirname(filePath), { recursive: true });
  writeFileSync(filePath, `${content.trimEnd()}\n`, "utf-8");
}

function webIndexTemplate() {
  return `import { Database20Regular } from "@vicons/fluent";

import { defineMenuGroup, defineModule, definePage, routePermission } from "../types";

export default defineModule({
  key: "${kebab}",
  version: "0.1.0",
  order: 100,
  dependencies: ["core"],
  menuGroups: [
    defineMenuGroup({ key: "${camel}Group", labelKey: "route.group.${camel}", icon: Database20Regular, order: 100 })
  ],
  pages: [
    definePage({
      key: "${camel}",
      path: "/${kebab}",
      titleKey: "route.${camel}",
      component: () => import("./views/${pascal}View.vue"),
      permission: routePermission("${snake}"),
      fallbackOrder: 100,
      menu: { group: "${camel}Group", icon: Database20Regular, order: 10 }
    })
  ]
});`;
}

function webApiTemplate() {
  return `import { request } from "../../api/client";
import type { ServerMessage } from "../../api/types";

export function ping${pascal}() {
  return request<ServerMessage>("/${kebab}/ping");
}`;
}

function webViewTemplate() {
  return `<template>
  <section class="work-card list-page-card">
    <div class="module-placeholder">
      <n-empty :description="t('${camel}.empty')">
        <template #extra>
          <n-button :loading="loading" text @click="loadStatus">{{ t("${camel}.refresh") }}</n-button>
        </template>
      </n-empty>
    </div>
  </section>
</template>

<script setup lang="ts">
import { onMounted, ref } from "vue";
import { NButton, NEmpty, useMessage } from "naive-ui";

import { t } from "../../../i18n";
import { messageText, showError } from "../../../utils/message";
import { ping${pascal} } from "../api";

const message = useMessage();
const loading = ref(false);

async function loadStatus() {
  loading.value = true;
  try {
    message.success(messageText(await ping${pascal}(), "${camel}.ready"));
  } catch (error) {
    showError(message, error);
  } finally {
    loading.value = false;
  }
}

onMounted(loadStatus);
</script>`;
}

function serverInitTemplate() {
  return `from app.core.module import AppModule, action_code, define_module, page_permission, resource_action, resource_permissions

${constant}_READ = action_code("${snake}", "read")

APP_MODULE = define_module(
    AppModule(
        key="${snake}",
        version="0.1.0",
        order=100,
        dependencies=("core",),
        router_paths=("app.modules.${snake}.api:router",),
        page_permissions=(
            page_permission("${snake}", "${snake}", 1000, ${constant}_READ),
        ),
        resource_permissions=(
            resource_permissions(
                "${snake}",
                "${camel}",
                1000,
                (
                    resource_action("read", 20),
                ),
            ),
        ),
    )
)`;
}

function serverApiTemplate() {
  return `from fastapi import APIRouter, Depends

from app.core.deps import require_permission
from app.models import User
from app.modules.${snake} import ${constant}_READ
from app.schemas.common import MessageResponse, message_response

router = APIRouter(prefix="/api/${kebab}", tags=["${kebab}"])


@router.get("/ping", response_model=MessageResponse)
def ping_${snake}(actor: User = Depends(require_permission(${constant}_READ))) -> MessageResponse:
    return message_response("${camel}.ready", "Module is ready", username=actor.username)`;
}

function zhLocale() {
  return {
    route: {
      [camel]: zhTitle,
      group: {
        [camel]: zhTitle
      }
    },
    permission: {
      group: {
        [camel]: zhTitle
      },
      [`route:${snake}`]: zhTitle,
      [`action:${snake}:read`]: `查询${zhTitle}`
    },
    [camel]: {
      empty: `${zhTitle}模块待开发`,
      refresh: "检查接口",
      ready: "模块已连接"
    }
  };
}

function enLocale() {
  return {
    route: {
      [camel]: enTitle,
      group: {
        [camel]: enTitle
      }
    },
    permission: {
      group: {
        [camel]: enTitle
      },
      [`route:${snake}`]: enTitle,
      [`action:${snake}:read`]: `Read ${enTitle}`
    },
    [camel]: {
      empty: `${enTitle} module is ready for development`,
      refresh: "Check API",
      ready: "Module is connected"
    }
  };
}

function jsonTemplate(data) {
  return JSON.stringify(data, null, 2);
}

function toKebab(value) {
  return value
    .trim()
    .replace(/([a-z0-9])([A-Z])/g, "$1-$2")
    .replace(/_/g, "-")
    .replace(/[^a-zA-Z0-9-]+/g, "-")
    .replace(/^-+|-+$/g, "")
    .replace(/-+/g, "-")
    .toLowerCase();
}

function toCamel(value) {
  return value.replace(/-([a-z0-9])/g, (_, char) => char.toUpperCase());
}

function toPascal(value) {
  const camelValue = toCamel(value);
  return camelValue.charAt(0).toUpperCase() + camelValue.slice(1);
}

function toTitle(value) {
  return value
    .split("-")
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

function fail(message) {
  console.error(message);
  process.exit(1);
}
