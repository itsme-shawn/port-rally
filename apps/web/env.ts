/**
 * 환경변수 중앙 관리
 *
 * 모든 환경변수는 이 파일에서만 접근하고,
 * 다른 파일에서는 이 파일을 import하여 사용
 */

/**
 * API 서버 URL
 * - API_SERVER_URL: 서버 사이드에서 사용
 * - NEXT_PUBLIC_API_SERVER_URL: 클라이언트 사이드에서 사용 (서버 사이드에서도 사용은 가능)
 */

export const API_SERVER_URL = process.env.API_SERVER_URL
export const NEXT_PUBLIC_API_SERVER_URL = process.env.NEXT_PUBLIC_API_SERVER_URL
