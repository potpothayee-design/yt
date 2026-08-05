import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: "class",
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        brand: {
          50: "#eef6ff",
          100: "#d9eaff",
          200: "#bcdbff",
          300: "#8ec3ff",
          400: "#599eff",
          500: "#4d96ff",
          600: "#2f6fe0",
          700: "#2658b4",
          800: "#234a90",
          900: "#223f74",
        },
        candy: {
          pink: "#ff6b9d",
          yellow: "#ffd93d",
          coral: "#ff6b6b",
          leaf: "#6bcb77",
          grape: "#9b72cf",
        },
      },
      fontFamily: {
        sans: [
          "ui-sans-serif",
          "system-ui",
          "-apple-system",
          "Segoe UI",
          "Roboto",
          "Helvetica Neue",
          "Arial",
          "sans-serif",
        ],
      },
      keyframes: {
        "fade-in": {
          from: { opacity: "0", transform: "translateY(6px)" },
          to: { opacity: "1", transform: "translateY(0)" },
        },
        wiggle: {
          "0%, 100%": { transform: "rotate(-3deg)" },
          "50%": { transform: "rotate(3deg)" },
        },
      },
      animation: {
        "fade-in": "fade-in 0.35s ease-out both",
        wiggle: "wiggle 1.2s ease-in-out infinite",
      },
    },
  },
  plugins: [],
};
export default config;
