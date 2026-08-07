#!/usr/bin/env node
/**
 * Builds a fully static site into ./out for GitHub Pages.
 *
 * Usage:
 *   BASE_PATH=/yt npm run build:static
 *
 * BASE_PATH must match your repository name when publishing to
 * https://<user>.github.io/<repo>/. Omit it for a custom domain or
 * a <user>.github.io repo.
 */
import { execSync } from 'node:child_process'
import { writeFileSync, mkdirSync } from 'node:fs'

const basePath = process.env.BASE_PATH || ''

console.log(`\n▶ Static export${basePath ? ` with basePath "${basePath}"` : ''}…\n`)

execSync('next build', {
  stdio: 'inherit',
  env: {
    ...process.env,
    STATIC_EXPORT: '1',
    NEXT_PUBLIC_BASE_PATH: basePath,
  },
})

mkdirSync('out', { recursive: true })
// Stops GitHub Pages from stripping /_next/ assets.
writeFileSync('out/.nojekyll', '')
console.log('\n✔ Static site ready in ./out\n')
