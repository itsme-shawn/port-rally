import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  env: {
    NEXT_PUBLIC_API_SERVER_URL: process.env.NEXT_PUBLIC_API_SERVER_URL,
    NEXT_PUBLIC_API_SERVER_PORT: process.env.NEXT_PUBLIC_API_SERVER_PORT,
  },
  async rewrites() {
    const url = process.env.NEXT_PUBLIC_API_SERVER_URL || "http://localhost";
    const port = process.env.NEXT_PUBLIC_API_SERVER_PORT || "8080";
    return [
      {
        source: "/api/:path*",
        destination: `${url}:${port}/api/:path*`,
      },
    ];
  },
};

export default nextConfig;
