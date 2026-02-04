import { API_SERVER_URL, NEXT_PUBLIC_API_SERVER_URL } from "@/env";

/**
 * 실시간 시세 SSE 스트림 URL 생성
 *
 * @param identifier - 종목 식별자 (예: "KR:KOSPI:005930")
 * @returns SSE 엔드포인트 전체 URL
 */
export const getQuoteStreamUrl = (identifier: string): string => {
  const isServer = typeof window === "undefined";
  const baseUrl = isServer ? API_SERVER_URL : NEXT_PUBLIC_API_SERVER_URL || "";
  const normalizedIdentifier = normalizeIdentifier(identifier);
  return `${baseUrl}/api/v1/quotes/stream/${encodeURIComponent(normalizedIdentifier)}`;
};

const normalizeIdentifier = (identifier: string): string => {
  try {
    return decodeURIComponent(identifier);
  } catch {
    return identifier;
  }
};
