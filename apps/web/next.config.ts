import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  env: {
    API_SERVER_DOMAIN: process.env.API_SERVER_DOMAIN,
  },
};

export default nextConfig;
