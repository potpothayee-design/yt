import type { Metadata, Viewport } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'Tiny Workers Studio — Free AI Image & Video Generator',
  description:
    'Generate Tiny Workers, Cardboard Puzzle and Pixar-style 4K images and cinematic videos. Free forever, no credits, no watermark, no login.',
  keywords: [
    'AI image generator',
    'free AI video',
    'tiny workers',
    'cardboard puzzle',
    'pixar style',
    'youtube shorts',
    'no watermark',
  ],
  openGraph: {
    title: 'Tiny Workers Studio',
    description: 'Free unlimited AI generator for Tiny Workers, Cardboard Puzzle & Pixar videos. No credits. No login.',
    type: 'website',
  },
  robots: { index: true, follow: true },
}

export const viewport: Viewport = {
  themeColor: '#07070b',
  width: 'device-width',
  initialScale: 1,
  maximumScale: 5,
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark">
      <body className="bg-studio min-h-screen bg-ink-950 antialiased">
        <div className="grid-lines pointer-events-none fixed inset-0 z-0" />
        <div className="relative z-10">{children}</div>
      </body>
    </html>
  )
}
