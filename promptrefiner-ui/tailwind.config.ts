import type { Config } from "tailwindcss";

export default {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "var(--background)",
        foreground: "var(--foreground)",
      },
      keyframes: {
        shimmer: {
          "0%": { transform: "translateX(-100%)" },
          "100%": { transform: "translateX(100%)" },
        },
        float: {
          "0%, 100%": { transform: "translateY(0px)" },
          "50%": { transform: "translateY(-4px)" },
        },
        glow: {
          "0%, 100%": { filter: "drop-shadow(0 0 0.25rem rgba(56,189,248,0.35))" },
          "50%": { filter: "drop-shadow(0 0 0.75rem rgba(56,189,248,0.55))" },
        },
        pulseRing: {
          "0%": { transform: "scale(0.9)", opacity: "0.65" },
          "70%": { transform: "scale(1.15)", opacity: "0" },
          "100%": { transform: "scale(1.2)", opacity: "0" },
        },
        spinLine: {
          "0%": { transform: "rotate(0deg)" },
          "100%": { transform: "rotate(360deg)" },
        },
        dotPulse: {
          "0%, 80%, 100%": { opacity: "0.25", transform: "scale(0.75)" },
          "40%": { opacity: "1", transform: "scale(1)" },
        },
      },
      animation: {
        float: "float 6s ease-in-out infinite",
        glow: "glow 3.5s ease-in-out infinite",
        shimmer: "shimmer 1.8s linear infinite",
        pulseRing: "pulseRing 2.4s ease-out infinite",
        spinLine: "spinLine 1.8s linear infinite",
        dotPulse: "dotPulse 1.4s ease-in-out infinite",
      },
    },
  },
  plugins: [],
} satisfies Config;
