import type { AppModule } from "./types";

const moduleFiles = import.meta.glob<{ default: AppModule }>("./*/index.ts", { eager: true });
const enabledModules = new Set(__APP_CONFIG__.enabledModules || []);
const disabledModules = new Set(__APP_CONFIG__.disabledModules || []);

const discoveredModules = Object.entries(moduleFiles)
  .map(([path, file]) => normalizeModule(path, file.default))
  .sort((left, right) => (left.order || 0) - (right.order || 0) || left.key.localeCompare(right.key));

validateModuleFilters(discoveredModules);

export const appModules = discoveredModules.filter(isEnabledModule);

validateModules(appModules);

function normalizeModule(path: string, module: AppModule): AppModule {
  if (!module?.key) {
    throw new Error(`Invalid app module: ${path}`);
  }
  return module;
}

function isEnabledModule(module: AppModule) {
  if (module.key === "core") {
    return true;
  }
  if (disabledModules.has(module.key)) {
    return false;
  }
  return enabledModules.size === 0 || enabledModules.has(module.key);
}

function validateModuleFilters(modules: AppModule[]) {
  ensureKnownModules("enabled", enabledModules, modules);
  ensureKnownModules("disabled", disabledModules, modules);
  if (disabledModules.has("core")) {
    throw new Error("Core app module cannot be disabled");
  }
}

function validateModules(modules: AppModule[]) {
  ensureUnique("module key", modules.map((module) => module.key));
  const moduleKeys = new Set(modules.map((module) => module.key));
  const missingDependencies = modules.flatMap((module) =>
    (module.dependencies || [])
      .filter((dependency) => !moduleKeys.has(dependency))
      .map((dependency) => `${module.key}->${dependency}`)
  );
  if (missingDependencies.length > 0) {
    throw new Error(`Missing app module dependency: ${missingDependencies.sort().join(", ")}`);
  }
  ensureUnique("menu group key", modules.flatMap((module) => module.menuGroups?.map((group) => group.key) || []));
  ensureUnique("page key", modules.flatMap((module) => module.pages?.map((page) => page.key) || []));
  ensureUnique("page path", modules.flatMap((module) => module.pages?.map((page) => page.path) || []));
  ensureUnique(
    "page permission",
    modules.flatMap((module) => module.pages?.map((page) => page.permission).filter(isString) || [])
  );
}

function ensureKnownModules(label: string, values: Set<string>, modules: AppModule[]) {
  const moduleKeys = new Set(modules.map((module) => module.key));
  const unknown = [...values].filter((value) => !moduleKeys.has(value));
  if (unknown.length > 0) {
    throw new Error(`Unknown ${label} app module: ${unknown.sort().join(", ")}`);
  }
}

function ensureUnique(label: string, values: string[]) {
  const seen = new Set<string>();
  const duplicates = new Set<string>();
  for (const value of values) {
    if (seen.has(value)) {
      duplicates.add(value);
    }
    seen.add(value);
  }
  if (duplicates.size > 0) {
    throw new Error(`Duplicate app module ${label}: ${[...duplicates].sort().join(", ")}`);
  }
}

function isString(value: unknown): value is string {
  return typeof value === "string";
}
