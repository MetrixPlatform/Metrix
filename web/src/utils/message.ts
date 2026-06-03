interface MessageApi {
  error(content: string): unknown;
}

export function showError(message: MessageApi, error: unknown) {
  message.error(error instanceof Error ? error.message : "操作失败");
}
