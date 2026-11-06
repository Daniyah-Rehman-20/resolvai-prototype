import type { NextConfig } from "next";

const pages = process.env.GITHUB_PAGES === "true";
const nextConfig: NextConfig = {
  output: pages ? "export" : "standalone",
  ...(pages ? {
    basePath: "/resolvai-prototype",
    trailingSlash: true,
    images: { unoptimized: true },
  } : {}),
};

export default nextConfig;
