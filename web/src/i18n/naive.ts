import { dateEnUS, dateZhCN, enUS, zhCN } from "naive-ui";

import type { Locale } from "./messages";

type NaiveLocale = typeof zhCN;

function withoutGenericPlaceholders(locale: NaiveLocale): NaiveLocale {
  return {
    ...locale,
    Cascader: { ...locale.Cascader, placeholder: "" },
    DatePicker: {
      ...locale.DatePicker,
      datePlaceholder: "",
      datetimePlaceholder: "",
      monthPlaceholder: "",
      yearPlaceholder: "",
      quarterPlaceholder: "",
      weekPlaceholder: "",
      startDatePlaceholder: "",
      endDatePlaceholder: "",
      startDatetimePlaceholder: "",
      endDatetimePlaceholder: "",
      startMonthPlaceholder: "",
      endMonthPlaceholder: ""
    },
    Input: { ...locale.Input, placeholder: "" },
    InputNumber: { ...locale.InputNumber, placeholder: "" },
    Select: { ...locale.Select, placeholder: "" },
    TimePicker: { ...locale.TimePicker, placeholder: "" }
  };
}

export const naiveLocales = {
  "zh-CN": { locale: withoutGenericPlaceholders(zhCN), dateLocale: dateZhCN },
  "en-US": { locale: withoutGenericPlaceholders(enUS), dateLocale: dateEnUS }
} satisfies Record<Locale, { locale: NaiveLocale; dateLocale: typeof dateZhCN }>;
