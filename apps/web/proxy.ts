import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'
import { API_SERVER_URL } from '@/env';
import { logger } from '@/lib/logger';

export function proxy(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // 정적 파일 및 내부 요청 제외
  if (
    pathname.startsWith('/_next') || 
    pathname.startsWith('/static') || 
    pathname.startsWith('/favicon.ico') ||
    pathname.match(/\.(png|jpg|jpeg|gif|svg|ico)$/)
  ) {
    return NextResponse.next();
  }

  const method = request.method;

  if (pathname.startsWith('/api')) {
    // API 프록시 요청 로깅
    const backendUrl = `${API_SERVER_URL}${pathname}${request.nextUrl.search}`;
    // 상세 정보는 필요하다면 logger.debug 등으로 처리
    logger.info('Proxy', `▶▶▶ [API Proxy] ${method} ${pathname} -> ${backendUrl}`);
  } else {
    // 일반 페이지 요청 로깅
    logger.info('Proxy', `▶▶▶ [Page Req] ${method} ${pathname}`);
  }

  return NextResponse.next();
}

export const config = {
  matcher: '/:path*',
}