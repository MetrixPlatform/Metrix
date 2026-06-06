import type { DataTableFilterState } from "naive-ui";

export function singleFilterValue(filterState: DataTableFilterState, key: string) {
  const value = filterState[key];
  return Array.isArray(value) ? value[0] ?? null : value ?? null;
}
