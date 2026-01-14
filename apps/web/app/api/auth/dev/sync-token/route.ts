/**
 * 개발 환경 전용: 8080 포트의 토큰을 3000 포트 쿠키로 설정
 *
 * Codespace에서는 포트별로 도메인이 달라 쿠키 공유가 불가능합니다.
 * 클라이언트에서 받은 토큰을 3000 포트 쿠키에 저장합니다.
 */

import { NextRequest, NextResponse } from 'next/server';

export async function POST(request: NextRequest) {
  try {
    const { accessToken, refreshToken } = await request.json();

    if (!accessToken || !refreshToken) {
      return NextResponse.json(
        { error: 'Missing tokens' },
        { status: 400 }
      );
    }

    console.log('[Dev Token Sync] Setting cookies on 3000 domain');

    // 3000 포트 도메인에 쿠키 설정
    const response = NextResponse.json({ success: true });

    // Access Token 쿠키
    response.cookies.set('access_token', accessToken, {
      httpOnly: true,
      secure: true,
      sameSite: 'lax',
      path: '/',
      maxAge: 60 * 60, // 1시간
    });

    // Refresh Token 쿠키
    response.cookies.set('refresh_token', refreshToken, {
      httpOnly: true,
      secure: true,
      sameSite: 'lax',
      path: '/api/v1/auth/refresh',
      maxAge: 60 * 60 * 24 * 7, // 7일
    });

    console.log('[Dev Token Sync] Cookies set successfully');

    return response;

  } catch (error) {
    console.error('[Dev Token Sync] Error:', error);
    return NextResponse.json(
      { error: 'Failed to sync token', message: String(error) },
      { status: 500 }
    );
  }
}
