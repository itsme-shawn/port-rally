/**
 * 환경변수 중앙 관리
 *
 * 모든 환경변수는 이 파일에서만 접근하고,
 * 다른 파일에서는 이 파일을 import하여 사용
 */

/**
 * 앱 실행 환경
 * - local: 로컬 개발 환경 (localhost)
 * - remote: 원격 개발 환경
 * - dev: 개발 서버
 * - prod: 운영 서버
 */
export const NEXT_PUBLIC_APP_ENV = process.env.NEXT_PUBLIC_APP_ENV

/**
 * API 서버 URL
 * - API_SERVER_URL: 서버 사이드에서 사용
 * - NEXT_PUBLIC_API_SERVER_URL: 클라이언트 사이드에서 사용 (서버 사이드에서도 사용은 가능)
 */

let api_server_url, next_public_api_server_url

if (NEXT_PUBLIC_APP_ENV == 'local') {
  api_server_url = process.env.API_SERVER_URL_LOCAL
  next_public_api_server_url = process.env.NEXT_PUBLIC_API_SERVER_URL_LOCAL
}
else if (NEXT_PUBLIC_APP_ENV == 'remote') {
  api_server_url = process.env.API_SERVER_URL_REMOTE
  next_public_api_server_url = process.env.NEXT_PUBLIC_API_SERVER_URL_REMOTE
}

export const API_SERVER_URL = api_server_url 
export const NEXT_PUBLIC_API_SERVER_URL = next_public_api_server_url
