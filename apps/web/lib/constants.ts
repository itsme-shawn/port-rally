export const NEXT_PUBLIC_API_SERVER_URL = process.env.NEXT_PUBLIC_API_SERVER_URL || "http://localhost";
export const NEXT_PUBLIC_API_SERVER_PORT = process.env.NEXT_PUBLIC_API_SERVER_PORT || "8080";

// 사용 편의를 위한 전체 도메인 조합
export const API_SERVER_DOMAIN = `${NEXT_PUBLIC_API_SERVER_URL}:${NEXT_PUBLIC_API_SERVER_PORT}`;
