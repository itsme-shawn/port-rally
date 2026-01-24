import type { NextConfig } from "next";
import { API_SERVER_URL } from "@/env";

const nextConfig: NextConfig = {
  output: "standalone",
  // 클라이언트 코드에는 노출하지 않음 (Proxy 사용 강제)
  env: {
    // 필요한 경우 여기에 추가
  },
  async rewrites() {
    // rewrites()는 브라우저가 아닌 Next.js 서버(Node.js)에서 실행된다.
    // 클라이언트에서 온 요청을 Next.js 서버가 받아서
    // 백엔드 api 서버로 전달하는 역할을 한다.
    console.log(`\n[Next.js Config] Rewrites enabled`);
    console.log(`  └─ /api/* → ${API_SERVER_URL}/api/*\n`);

    return [
      {
        source: "/api/:path*",
        destination: `${API_SERVER_URL}/api/:path*`,
      },
    ];
  },
};

export default nextConfig;