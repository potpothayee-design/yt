import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    './app/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './lib/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        ink: {
          950: '#07070b',
          900: '#0b0b12',
          850: '#101019',
          800: '#15151f',
          750: '#1b1b27',
          700: '#23232f',
          600: '#31313f',
        },
        brand: {
          50: '#fff7ed',
          200: '#fed7aa',
          300: '#fdba74',
          400: '#fb923c',
          500: '#f97316',
          600: '#ea580c',
          700: '#c2410c',
        },
      },
      fontFamily: {
        sans: ['var(--font-sans)', 'ui-sans-serif', 'system-ui', 'sans-serif'],
      },
      keyframes: {
        kenburns: {
          '0%': { transform: 'scale(1) translate3d(0,0,0)' },
          '50%': { transform: 'scale(1.18) translate3d(-2%, -2%, 0)' },
          '100%': { transform: 'scale(1) translate3d(0,0,0)' },
        },
        shimmer: {
          '100%': { transform: 'translateX(100%)' },
        },
        floaty: {
          '0%,100%': { transform: 'translateY(0)' },
          '50%': { transform: 'translateY(-6px)' },
        },
        fadeup: {
          '0%': { opacity: '0', transform: 'translateY(8px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
      },
      animation: {
        kenburns: 'kenburns 12s ease-in-out infinite',
        shimmer: 'shimmer 1.6s infinite',
        floaty: 'floaty 4s ease-in-out infinite',
        fadeup: 'fadeup .35s ease-out both',
      },
    },
  },
  plugins: [],
}

export default config
