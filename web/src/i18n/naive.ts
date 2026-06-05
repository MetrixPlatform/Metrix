import { dateEnUS, dateZhCN, enUS, zhCN } from "naive-ui";

import type { Locale } from "./messages";

export const naiveLocales = {
  "zh-CN": { locale: zhCN, dateLocale: dateZhCN },
  "en-US": { locale: enUS, dateLocale: dateEnUS }
} satisfies Record<Locale, { locale: typeof zhCN; dateLocale: typeof dateZhCN }>;
