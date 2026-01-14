import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'
import { API_SERVER_URL } from '@/env';

export function proxy(request: NextRequest) {
  if (request.nextUrl.pathname.startsWith('/api')) {

    const backendUrl = `${API_SERVER_URL}${request.nextUrl.pathname}${request.nextUrl.search}`;

    const cookies = request.cookies.getAll();
    const cookieHeader = request.headers.get('cookie');

    console.log(`\n[Proxy] API Request`);
    console.log(`  ├─ ${request.method} ${request.url}`);
    console.log(`  ├─ Will be rewritten to: ${backendUrl}`);
  }
  return NextResponse.next();
}

export const config = {
  matcher: '/api/:path*',
}
