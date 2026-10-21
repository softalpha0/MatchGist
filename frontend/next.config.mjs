/** Static export: the FastAPI backend serves the built site, so the whole app is one container. */
const nextConfig = {
  output: "export",
  images: { unoptimized: true },
  reactStrictMode: true,
};

export default nextConfig;
