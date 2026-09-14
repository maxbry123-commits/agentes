import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: "class",
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        background: "#0A0A0F",
        surface: "#12121A",
        border: "#1A1A2E",
        "surface-hover": "#1E1E30",
        accent: "#60A5FA",
        severity: {
          critical: "#EF4444",
          high: "#F97316",
          medium: "#EAB308",
          low: "#22C55E",
          info: "#6B7280",
        },
      },
      fontFamily: {
        mono: ["JetBrains Mono", "Fira Code", "monospace"],
      },
    },
  },
  plugins: [],
};

export default config;
