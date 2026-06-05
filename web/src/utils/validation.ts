import type { FormInst, FormItemRule } from "naive-ui";

import { t } from "../i18n";

const textTrigger = ["input", "blur"];

export function requiredRule(label: string): FormItemRule {
  return {
    required: true,
    message: t("validation.required", { label }),
    trigger: textTrigger
  };
}

export function numberRequiredRule(label: string): FormItemRule {
  return {
    type: "number",
    required: true,
    message: t("validation.required", { label }),
    trigger: ["input", "blur", "change"]
  };
}

export function minLengthRule(label: string, min: number): FormItemRule {
  return {
    min,
    message: t("validation.minLength", { label, min }),
    trigger: textTrigger
  };
}

export function maxLengthRule(label: string, max: number): FormItemRule {
  return {
    max,
    message: t("validation.maxLength", { label, max }),
    trigger: textTrigger
  };
}

export function phoneRule(): FormItemRule {
  return {
    validator: (_rule, value: string) => /^1[3-9]\d{9}$/.test(value),
    message: t("validation.phone"),
    trigger: textTrigger
  };
}

export function emailRule(): FormItemRule {
  return {
    validator: (_rule, value: string) => /^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(value),
    message: t("validation.email"),
    trigger: textTrigger
  };
}

export async function validateForm(form: FormInst | null): Promise<boolean> {
  try {
    await form?.validate();
    return true;
  } catch {
    return false;
  }
}
