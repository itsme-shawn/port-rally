import { API_SERVER_URL } from "@/env";

const isServer = typeof window === "undefined";

export async function apiClient<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  // 1. URL 결정 로직
  // Client: "" (상대 경로 -> Next.js Proxy를 통해 백엔드로 전달)
  // Server: API_SERVER_URL (서버에서 백엔드로 직접 통신)
  const baseUrl = isServer ? API_SERVER_URL : "";

  // endpoint가 /로 시작하지 않으면 추가
  const normalizedEndpoint = endpoint.startsWith("/") ? endpoint : `/${endpoint}`;
  const url = `${baseUrl}${normalizedEndpoint}`;

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

  // Browser 환경에서만 credentials 포함 (Server fetch는 쿠키 자동 처리 안됨)
  if (!isServer) {
    config.credentials = "include";
  }

  // 로그 (선택 사항)
  // console.log(`[API] ${options.method || "GET"} ${url}`);

  try {
    const response = await fetch(url, config);

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      // console.error(`[API Error]`, errorData);
      throw new Error(
        errorData.message || `API Error: ${response.status} ${response.statusText}`
      );
    }

    if (response.status === 204) {
      return {} as T;
    }

    return response.json();
  } catch (error) {
    // console.error(`[API Failed] ${url}`, error);
    throw error;
  }
}