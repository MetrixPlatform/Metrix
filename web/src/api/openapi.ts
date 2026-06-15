import { request } from "./client";
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
  components?: {
    schemas?: Record<string, OpenApiSchema>;
    [key: string]: unknown;
  };
}

export interface OpenApiOperation {
  tags?: string[];
  summary?: string;
  description?: string;
  operationId?: string;
  parameters?: OpenApiParameter[];
  requestBody?: OpenApiRequestBody;
  responses?: Record<string, OpenApiResponse>;
}

export interface OpenApiParameter {
  name: string;
  in: string;
  required?: boolean;
  description?: string;
  schema?: OpenApiSchema;
  example?: unknown;
}

export interface OpenApiRequestBody {
  required?: boolean;
  description?: string;
  content?: Record<string, OpenApiMediaType>;
}

export interface OpenApiResponse {
  description?: string;
  content?: Record<string, OpenApiMediaType>;
}

export interface OpenApiMediaType {
  schema?: OpenApiSchema;
  example?: unknown;
  examples?: Record<string, { summary?: string; description?: string; value?: unknown }>;
}

export interface OpenApiSchema {
  $ref?: string;
  type?: string;
  format?: string;
  title?: string;
  description?: string;
  default?: unknown;
  example?: unknown;
  examples?: unknown[];
  enum?: unknown[];
  const?: unknown;
  nullable?: boolean;
  items?: OpenApiSchema;
  properties?: Record<string, OpenApiSchema>;
  required?: string[];
  allOf?: OpenApiSchema[];
  anyOf?: OpenApiSchema[];
  oneOf?: OpenApiSchema[];
  additionalProperties?: boolean | OpenApiSchema;
  [key: string]: unknown;
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

export async function getBaseUrls() {
  const result = await request<{ base_urls: string[] }>("/base-urls");
  return result.base_urls;
}
