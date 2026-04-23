import type { NextConfig } from "next";

const isDocker = process.env.DOCKER === "true";

const nextConfig: NextConfig = {
  ...(isDocker && { output: "standalone" }),
};

export default nextConfig;
