import type { Config } from "tailwindcss"

const config: Config = {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        // Apple Liquid Glass 色彩系统
        "apple-glass": {
          50: "rgba(255, 255, 255, 0.05)",
          100: "rgba(255, 255, 255, 0.1)",
          200: "rgba(255, 255, 255, 0.15)",
          300: "rgba(255, 255, 255, 0.2)",
        },
        "apple-accent": {
          blue: "#007AFF",
          green: "#34C759",
          red: "#FF3B30",
          orange: "#FF9500",
          gray: "#8E8E93",
          lightGray: "#F2F2F7",
          dark: "#1C1C1E",
        }
      },
      fontFamily: {
        // SF Pro 风格字体栈
        sf: [
          "-apple-system",
          "BlinkMacSystemFont",
          '"Segoe UI"',
          "Roboto",
          '"Helvetica Neue"',
          "Arial",
          "sans-serif",
        ],
        mono: [
          '"SF Mono"',
          "Monaco",
          "Inconsolata",
          '"Fira Code"',
          "monospace",
        ],
      },
      backdropBlur: {
        xs: "2px",
        "apple": "20px",
        "apple-lg": "40px",
      },
      boxShadow: {
        "apple": "0 8px 32px rgba(0, 0, 0, 0.08)",
        "apple-lg": "0 20px 60px rgba(0, 0, 0, 0.12)",
        "glass": "0 8px 32px rgba(0, 0, 0, 0.04)",
      },
      animation: {
        "fade-in": "fadeIn 0.3s ease-out",
        "slide-up": "slideUp 0.4s ease-out",
        "pulse-soft": "pulseSoft 2s cubic-bezier(0.4, 0, 0.6, 1) infinite",
        "shimmer": "shimmer 2s linear infinite",
      },
      keyframes: {
        fadeIn: {
          "0%": { opacity: "0" },
          "100%": { opacity: "1" },
        },
        slideUp: {
          "0%": { opacity: "0", transform: "translateY(10px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        pulseSoft: {
          "0%, 100%": { opacity: "1" },
          "50%": { opacity: "0.5" },
        },
        shimmer: {
          "0%": { backgroundPosition: "-1000px 0" },
          "100%": { backgroundPosition: "1000px 0" },
        },
      },
    },
  },
  plugins: [],
}
export default config