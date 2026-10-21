import path from "node:path";
import { fileURLToPath } from "node:url";

const here = path.dirname(fileURLToPath(import.meta.url));

/** Static export: the FastAPI backend serves the built site, so the whole app is one container. */
const nextConfig = {
  output: "export",
  images: { unoptimized: true },
  reactStrictMode: true,
  // pin the workspace root: a stray lockfile in a parent folder (e.g. ~/pnpm-lock.yaml) must not be picked up
  outputFileTracingRoot: here,
};

export default nextConfig;
