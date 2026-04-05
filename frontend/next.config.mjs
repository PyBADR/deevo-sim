import path from "path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "standalone",
  eslint: { ignoreDuringBuilds: true },
  typescript: { ignoreBuildErrors: false },
  images: { unoptimized: true },
  // Silence workspace-root inference warning when multiple lockfiles are detected
  outputFileTracingRoot: path.join(__dirname, "../../"),
};

export default nextConfig;
