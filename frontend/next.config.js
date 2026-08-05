/** @type {import('next').NextConfig} */
// API_PROXY_TARGET is a server-side-only value: the browser always calls
// same-origin relative URLs under /backend/* and Next rewrites them to the
// backend service. This keeps the app working from any browser, including
// remote preview tunnels where "localhost" would be wrong.
const API_PROXY_TARGET = process.env.API_PROXY_TARGET || "http://localhost:8000";

const nextConfig = {
  reactStrictMode: true,
  eslint: { ignoreDuringBuilds: true },
  async rewrites() {
    return [
      { source: "/backend/:path*", destination: `${API_PROXY_TARGET}/:path*` },
    ];
  },
};

module.exports = nextConfig;
