import { API_SERVER_URL } from "@/env";
import { logger } from "@/lib/logger";

const isServer = typeof window === "undefined";

export async function apiClient<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const baseUrl = isServer ? API_SERVER_URL : "";
  const normalizedEndpoint = endpoint.startsWith("/") ? endpoint : `/${endpoint}`;
  const url = `${baseUrl}${normalizedEndpoint}`;
  const method = options.method || "GET";
  const context = isServer ? "ApiClient(S)" : "ApiClient(C)";
  const startTime = Date.now();

  const defaultHeaders: HeadersInit = {
    "Content-Type": "application/json",
  };

  const config: RequestInit = {
    ...options,
    headers: {
      ...defaultHeaders,
      ...options.headers,
    },
  };

  if (!isServer) {
    config.credentials = "include";
  }

  // 1. Request Logging
  let requestBody = undefined;
  if (options.body) {
      try {
          requestBody = JSON.parse(options.body as string);
      } catch {
          requestBody = options.body;
      }
  }
  logger.start(context, `${method} ${normalizedEndpoint}`, requestBody);

  try {
    const response = await fetch(url, config);

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      logger.fail(context, `${method} ${normalizedEndpoint}`, startTime, errorData);
      throw new Error(
        errorData.message || `API Error: ${response.status} ${response.statusText}`
      );
    }

    if (response.status === 204) {
      logger.end(context, `${method} ${normalizedEndpoint}`, startTime, "[No Content]");
      return {} as T;
    }

    const data = await response.json();
    
    // 2. Response Logging
    logger.end(context, `${method} ${normalizedEndpoint}`, startTime, data);
    
    return data;
  } catch (error) {
    logger.fail(context, `${method} ${normalizedEndpoint}`, startTime, error);
    throw error;
  }
}
