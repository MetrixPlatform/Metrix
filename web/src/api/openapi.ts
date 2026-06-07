import { authStore } from "../stores/auth";
import { t } from "../i18n";

export interface OpenApiDocument {
  openapi: string;
  info: {
    title: string;
    version: string;
    description?: string;
  };
  tags?: Array<{ name: string; description?: string }>;
  paths: Record<string, Record<string, OpenApiOperation>>;
  components?: Record<string, unknown>;
}

export interface OpenApiOperation {
  tags?: string[];
  summary?: string;
  description?: string;
  operationId?: string;
  parameters?: OpenApiParameter[];
  requestBody?: {
    required?: boolean;
    content?: Record<string, unknown>;
  };
  responses?: Record<string, { description?: string; content?: Record<string, unknown> }>;
}

export interface OpenApiParameter {
  name: string;
  in: string;
  required?: boolean;
  description?: string;
  schema?: Record<string, unknown>;
}

export async function getOpenApiDocument() {
  const headers = new Headers();
  if (authStore.token) {
    headers.set("Authorization", `Bearer ${authStore.token}`);
  }
  const response = await fetch("/openapi.json", { headers });
  if (!response.ok) {
    throw new Error(t(response.status === 403 ? "error.forbidden" : "api.requestFailed"));
  }
  return (await response.json()) as OpenApiDocument;
}
