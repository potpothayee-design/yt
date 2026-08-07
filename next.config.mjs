/** @type {import('next').NextConfig} */

// Set NEXT_PUBLIC_BASE_PATH="/<repo-name>" when deploying to GitHub Pages
// (e.g. "/yt"). Leave empty for Vercel / local dev.
const basePath = process.env.NEXT_PUBLIC_BASE_PATH || ''

// STATIC_EXPORT=1 produces a fully static ./out folder for GitHub Pages.
const isStaticExport = process.env.STATIC_EXPORT === '1'

const nextConfig = {
  reactStrictMode: true,
  ...(isStaticExport ? { output: 'export' } : {}),
  basePath: basePath || undefined,
  assetPrefix: basePath || undefined,
  images: {
    unoptimized: true,
  },
  eslint: {
    ignoreDuringBuilds: true,
  },
}

export default nextConfig
