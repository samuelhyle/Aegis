import type { NextConfig } from "next";

const BACKEND_URL = process.env.BACKEND_URL || process.env.NEXT_PUBLIC_API_URL || "";

const nextConfig: NextConfig = {
  images: {
    unoptimized: true,
  },
  env: {
    NEXT_PUBLIC_API_URL: BACKEND_URL,
    NEXT_PUBLIC_SOCKET_URL: BACKEND_URL,
    BACKEND_URL: BACKEND_URL,
  },
  // Rewrite API calls to the proxy route
  async rewrites() {
    if (!BACKEND_URL) return [];
    return [
      {
        source: "/api/proxy/:path*",
        destination: `${BACKEND_URL}/:path*`,
      },
    ];
  },
};

export default nextConfig;