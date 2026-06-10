import type { AppModule } from "./types";

const moduleFiles = import.meta.glob<{ default: AppModule }>("./*/index.ts", { eager: true });

export const appModules = Object.entries(moduleFiles)
  .map(([path, file]) => normalizeModule(path, file.default))
  .sort((left, right) => (left.order || 0) - (right.order || 0) || left.key.localeCompare(right.key));

function normalizeModule(path: string, module: AppModule): AppModule {
  if (!module?.key) {
    throw new Error(`Invalid app module: ${path}`);
  }
  return module;
}
