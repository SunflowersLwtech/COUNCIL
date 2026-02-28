import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  transpilePackages: ["three", "@react-three/fiber", "@react-three/drei"],
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: "http://localhost:8000/api/:path*",
      },
    ];
  },
  // Keep connections alive for long-running proxy requests
  httpAgentOptions: {
    keepAlive: true,
  },
  experimental: {
    proxyTimeout: 300_000, // 5 minutes for long-running analysis
  },
};

export default nextConfig;
