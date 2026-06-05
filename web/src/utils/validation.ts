import type { FormInst, FormItemRule } from "naive-ui";

const textTrigger = ["input", "blur"];

export function requiredRule(label: string): FormItemRule {
  return {
    required: true,
    message: `请输入${label}`,
    trigger: textTrigger
  };
}

export function numberRequiredRule(label: string): FormItemRule {
  return {
    type: "number",
    required: true,
    message: `请输入${label}`,
    trigger: ["input", "blur", "change"]
  };
}

export function minLengthRule(label: string, min: number): FormItemRule {
  return {
    min,
    message: `${label}至少 ${min} 个字符`,
    trigger: textTrigger
  };
}

export function maxLengthRule(label: string, max: number): FormItemRule {
  return {
    max,
    message: `${label}不能超过 ${max} 个字符`,
    trigger: textTrigger
  };
}

export function phoneRule(): FormItemRule {
  return {
    validator: (_rule, value: string) => /^1[3-9]\d{9}$/.test(value),
    message: "手机号码格式不正确",
    trigger: textTrigger
  };
}

export function emailRule(): FormItemRule {
  return {
    validator: (_rule, value: string) => /^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(value),
    message: "邮箱格式不正确",
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
