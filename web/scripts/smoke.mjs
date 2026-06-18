import { existsSync, readdirSync, readFileSync, statSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const rootDir = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const projectDir = path.resolve(rootDir, "..");
const modulesDir = path.join(rootDir, "src", "modules");
const localeDir = path.join(rootDir, "src", "i18n", "locales");
const requiredLocales = localeFiles(localeDir);
const baseMessages = Object.fromEntries(requiredLocales.map((locale) => [locale, readJson(path.join(localeDir, `${locale}.json`))]));
const moduleNames = moduleDirs(modulesDir);
const appConfig = readOptionalJson(path.join(projectDir, "app.config.json"));
const moduleEntries = new Map();

assert(requiredLocales.length > 0, "No base locale files found");
assertSameJsonKeys(baseMessages, "i18n/locales");
assertModuleFilters(appConfig, moduleNames);

for (const moduleName of moduleNames) {
  const moduleDir = path.join(modulesDir, moduleName);
  const entryPath = path.join(moduleDir, "index.ts");
  assert(existsSync(entryPath), `Missing module entry: ${moduleName}/index.ts`);
  const moduleEntry = readFileSync(entryPath, "utf-8");
  const moduleSource = `${moduleEntry}\n${readModuleSource(moduleDir)}`;
  moduleEntries.set(moduleName, moduleEntry);
  assert(moduleEntry.includes("defineModule"), `Module entry must use defineModule: ${moduleName}/index.ts`);
  assertModuleEntry(moduleEntry, moduleName);

  const i18nDir = path.join(moduleDir, "i18n");
  const moduleMessages = {};
  if (!existsSync(i18nDir)) {
    assert(requiredTranslationKeys(moduleEntry).length === 0, `Missing i18n directory for module ${moduleName}`);
    continue;
  }
  for (const locale of requiredLocales) {
    const localePath = path.join(i18nDir, `${locale}.json`);
    assert(existsSync(localePath), `Missing ${locale} locale for module ${moduleName}`);
    moduleMessages[locale] = readJson(localePath);
  }
  assertSameJsonKeys(moduleMessages, moduleName);
  assertModuleTranslations(moduleSource, moduleMessages, moduleName);
}

assertModuleGraph(moduleEntries);

for (const locale of requiredLocales) {
  const data = baseMessages[locale];
  assert(typeof data.language === "string" && data.language.trim(), `Missing language name in ${locale}.json`);
}

console.log("Frontend smoke checks passed");

function assertModuleEntry(moduleEntry, moduleName) {
  const key = singleMatch(moduleEntry, /\bkey:\s*["']([^"']+)["']/);
  const version = singleMatch(moduleEntry, /\bversion:\s*["']([^"']+)["']/);
  assert(key === moduleName, `Module key must match directory name: ${moduleName}`);
  assert(/^[a-z][a-z0-9-]*$/.test(key), `Invalid module key: ${key}`);
  assert(version, `Missing module version: ${moduleName}/index.ts`);
  assert(/^\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?$/.test(version), `Invalid module version: ${moduleName}@${version}`);
}

function assertModuleGraph(entries) {
  const moduleKeys = new Set(entries.keys());
  const menuGroups = [];
  const pageKeys = [];
  const pagePaths = [];
  const pagePermissions = [];
  const pageMenuGroups = [];

  for (const [moduleName, entry] of entries) {
    const dependencies = arrayValues(entry, /\bdependencies:\s*\[([^\]]*)\]/);
    for (const dependency of dependencies) {
      assert(moduleKeys.has(dependency), `Missing frontend module dependency: ${moduleName}->${dependency}`);
    }
    menuGroups.push(...matches(entry, /defineMenuGroup\(\s*\{\s*key:\s*["']([^"']+)["']/g));
    pageKeys.push(...matches(entry, /definePage\(\s*\{\s*key:\s*["']([^"']+)["']/g));
    pagePaths.push(...matches(entry, /\bpath:\s*["']([^"']+)["']/g));
    pagePermissions.push(
      ...matches(entry, /\bpermission:\s*actionPermission\(\s*["']([^"']+)["']\s*,\s*["']([^"']+)["']\s*\)/g).map(
        ([resource, action]) => `action:${resource}:${action}`
      )
    );
    pageMenuGroups.push(...matches(entry, /\bmenu:\s*\{[^}]*\bgroup:\s*["']([^"']+)["']/gs));
  }

  assertUnique("menu group key", menuGroups);
  assertUnique("page key", pageKeys);
  assertUnique("page path", pagePaths);
  assertUnique("page permission", pagePermissions);
  const menuGroupSet = new Set(menuGroups);
  for (const group of pageMenuGroups) {
    assert(menuGroupSet.has(group), `Unknown page menu group: ${group}`);
  }
}

function moduleDirs(dir) {
  return readdirSync(dir).filter((name) => {
    const fullPath = path.join(dir, name);
    return statSync(fullPath).isDirectory();
  });
}

function localeFiles(dir) {
  return readdirSync(dir)
    .filter((name) => name.endsWith(".json"))
    .map((name) => name.replace(/\.json$/, ""))
    .sort();
}

function readJson(filePath) {
  try {
    return JSON.parse(readFileSync(filePath, "utf-8"));
  } catch (error) {
    throw new Error(`Invalid JSON: ${filePath}\n${error instanceof Error ? error.message : String(error)}`);
  }
}

function readOptionalJson(filePath) {
  return existsSync(filePath) ? readJson(filePath) : {};
}

function readModuleSource(dir) {
  return readdirSync(dir).flatMap((name) => {
    const fullPath = path.join(dir, name);
    if (statSync(fullPath).isDirectory()) {
      return readModuleSource(fullPath);
    }
    return /\.(ts|vue)$/.test(name) ? readFileSync(fullPath, "utf-8") : [];
  }).join("\n");
}

function assertModuleFilters(config, moduleNames) {
  const modules = new Set(moduleNames);
  const enabled = moduleFilter(config.enabledModules);
  const disabled = moduleFilter(config.disabledModules);
  assert(!disabled.has("core"), "Core app module cannot be disabled in app.config.json");
  for (const value of [...enabled, ...disabled]) {
    assert(modules.has(value), `Unknown app module in app.config.json: ${value}`);
  }
}

function moduleFilter(value) {
  const items = Array.isArray(value) ? value : typeof value === "string" ? value.split(",") : [];
  return new Set(items.map((item) => (typeof item === "string" ? item.trim() : "")).filter(Boolean));
}

function assertModuleTranslations(moduleEntry, moduleMessages, moduleName) {
  for (const key of requiredTranslationKeys(moduleEntry)) {
    for (const locale of requiredLocales) {
      const messages = merge(baseMessages[locale], moduleMessages[locale] || {});
      assert(hasPath(messages, key), `Missing i18n key "${key}" in ${locale} for module ${moduleName}`);
    }
  }
}

function requiredTranslationKeys(moduleEntry) {
  const keys = [
    ...matches(moduleEntry, /\btitleKey:\s*["']([^"']+)["']/g),
    ...matches(moduleEntry, /\blabelKey:\s*["']([^"']+)["']/g),
    ...matches(moduleEntry, /\bactionPermission\(\s*["']([^"']+)["']\s*,\s*["']([^"']+)["']\s*\)/g).map(
      ([resource, action]) => `permission.action:${resource}:${action}`
    )
  ];
  return [...new Set(keys)].sort();
}

function assertSameJsonKeys(messagesByLocale, moduleName) {
  const [firstLocale] = requiredLocales;
  const expected = flatKeys(messagesByLocale[firstLocale] || {});
  for (const locale of requiredLocales.slice(1)) {
    const actual = flatKeys(messagesByLocale[locale] || {});
    const missing = expected.filter((key) => !actual.includes(key));
    const extra = actual.filter((key) => !expected.includes(key));
    assert(missing.length === 0, `Missing keys in ${moduleName}/${locale}.json: ${missing.join(", ")}`);
    assert(extra.length === 0, `Extra keys in ${moduleName}/${locale}.json: ${extra.join(", ")}`);
  }
}

function matches(text, pattern) {
  return [...text.matchAll(pattern)].map((match) => (match.length > 2 ? match.slice(1) : match[1]));
}

function singleMatch(text, pattern) {
  return text.match(pattern)?.[1] || "";
}

function arrayValues(text, pattern) {
  const match = text.match(pattern);
  if (!match) {
    return [];
  }
  return matches(match[1], /["']([^"']+)["']/g);
}

function assertUnique(label, values) {
  const seen = new Set();
  const duplicates = new Set();
  for (const value of values) {
    if (seen.has(value)) {
      duplicates.add(value);
    }
    seen.add(value);
  }
  assert(duplicates.size === 0, `Duplicate ${label}: ${[...duplicates].sort().join(", ")}`);
}

function flatKeys(value, prefix = "") {
  if (!isPlainObject(value)) {
    return prefix ? [prefix] : [];
  }
  return Object.entries(value).flatMap(([key, child]) => flatKeys(child, prefix ? `${prefix}.${key}` : key)).sort();
}

function hasPath(value, key) {
  return key.split(".").every((part, index, parts) => {
    if (!isPlainObject(value) || !(part in value)) {
      return false;
    }
    value = value[part];
    return index < parts.length - 1 ? isPlainObject(value) : value !== undefined && value !== "";
  });
}

function merge(base, extra) {
  const output = { ...base };
  for (const [key, value] of Object.entries(extra || {})) {
    output[key] = isPlainObject(value) && isPlainObject(output[key]) ? merge(output[key], value) : value;
  }
  return output;
}

function isPlainObject(value) {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function assert(condition, message) {
  if (!condition) {
    throw new Error(message);
  }
}
