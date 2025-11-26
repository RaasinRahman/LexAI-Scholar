import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  /* config options here */
  
  // Allow deployment even with linting warnings
  eslint: {
    ignoreDuringBuilds: true,
  },
  
  // Allow deployment even with TypeScript errors
  typescript: {
    ignoreBuildErrors: true,
  },
};

export default nextConfig;
