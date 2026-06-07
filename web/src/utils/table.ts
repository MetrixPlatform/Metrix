import type { DataTableColumns, DataTableFilterState } from "naive-ui";

const DEFAULT_RESIZABLE_MIN_WIDTH = 80;
const DEFAULT_NON_RESIZABLE_COLUMN_KEYS = new Set(["actions"]);

interface ResizableColumnOptions {
  minWidth?: number;
  nonResizableKeys?: string[];
}

interface TableColumnWithMeta<T> {
  key?: string | number;
  type?: string;
  children?: DataTableColumns<T>;
  minWidth?: string | number;
  resizable?: boolean;
}

export function singleFilterValue(filterState: DataTableFilterState, key: string) {
  const value = filterState[key];
  return Array.isArray(value) ? value[0] ?? null : value ?? null;
}

export function withResizableColumns<T>(
  columns: DataTableColumns<T>,
  options: ResizableColumnOptions = {}
): DataTableColumns<T> {
  const minWidth = options.minWidth ?? DEFAULT_RESIZABLE_MIN_WIDTH;
  const nonResizableKeys = new Set([...DEFAULT_NON_RESIZABLE_COLUMN_KEYS, ...(options.nonResizableKeys ?? [])]);

  return columns.map((column) => {
    const tableColumn = column as TableColumnWithMeta<T>;
    if (Array.isArray(tableColumn.children)) {
      return {
        ...column,
        children: withResizableColumns(tableColumn.children, options)
      };
    }
    if (tableColumn.type === "selection" || tableColumn.type === "expand") {
      return column;
    }
    if (tableColumn.key === undefined || nonResizableKeys.has(String(tableColumn.key))) {
      return column;
    }
    return {
      minWidth,
      ...column,
      resizable: true
    };
  }) as DataTableColumns<T>;
}

export function updateColumnWidth(
  widths: Record<string, number>,
  columnKey: unknown,
  widthKeyMap: Record<string, string>,
  width: number
) {
  const key = typeof columnKey === "string" || typeof columnKey === "number" ? String(columnKey) : "";
  const widthKey = widthKeyMap[key];
  if (widthKey && Object.hasOwn(widths, widthKey)) {
    widths[widthKey] = Math.round(width);
  }
}

export function sumColumnWidths(widths: Record<string, number>) {
  return Object.values(widths).reduce((total, width) => total + width, 0);
}
