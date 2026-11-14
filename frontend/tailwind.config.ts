import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        lara: {
          bg: "#050811",
          card: "rgba(10, 16, 31, 0.75)",
          border: "rgba(0, 240, 255, 0.18)",
          primary: "#00F0FF",
          secondary: "#00A8FF",
          accent: "#7000FF",
          text: "#E2E8F0",
          muted: "#94A3B8",
        },
      },
      fontFamily: {
        mono: ["var(--font-mono)", "JetBrains Mono", "Courier New", "monospace"],
        sans: ["var(--font-sans)", "Inter", "sans-serif"],
      },
      boxShadow: {
        glow: "0 0 25px -5px rgba(0, 240, 255, 0.3)",
        "glow-sm": "0 0 10px -2px rgba(0, 240, 255, 0.4)",
        "glow-purple": "0 0 25px -5px rgba(112, 0, 255, 0.35)",
      },
      animation: {
        "pulse-slow": "pulse 4s cubic-bezier(0.4, 0, 0.6, 1) infinite",
        "spin-slow": "spin 20s linear infinite",
      },
    },
  },
  plugins: [],
};

export default config;
