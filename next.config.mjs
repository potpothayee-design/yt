/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // The app renders plain <img>/<canvas>; no server-side image optimizer needed.
  images: {
    unoptimized: true,
  },
  eslint: {
    ignoreDuringBuilds: true,
  },
}

export default nextConfig
