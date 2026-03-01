import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  darkMode: "class",
  theme: {
    extend: {
      fontFamily: {
        display: ["var(--font-outfit)", "system-ui", "sans-serif"],
        body: ["var(--font-dm-sans)", "system-ui", "sans-serif"],
      },
      colors: {
        "ds-bg": "#faf8f5",
        "ds-card": "#ffffff",
        "ds-card-muted": "#f5f2ed",
        "ds-accent": "#0d9488",
        "ds-accent-soft": "#0f766e",
        "ds-accent-coral": "#e07c5e",
        "ds-text": "#2d2a26",
        "ds-text-muted": "#6b6560",
        "ds-border": "#e8e4df",
        "ds-danger": "#dc2626",
        "ds-warning": "#d97706",
        "ds-success": "#059669",
      },
      backgroundImage: {
        "ds-gradient":
          "radial-gradient(ellipse 80% 50% at 50% -20%, rgba(13, 148, 136, 0.12), transparent), radial-gradient(ellipse 60% 40% at 100% 50%, rgba(224, 124, 94, 0.08), transparent), radial-gradient(ellipse 60% 40% at 0% 50%, rgba(167, 139, 250, 0.06), transparent)",
      },
      boxShadow: {
        "ds-card": "0 1px 3px 0 rgba(45, 42, 38, 0.06), 0 4px 12px -2px rgba(45, 42, 38, 0.08)",
        "ds-card-hover": "0 4px 12px 0 rgba(45, 42, 38, 0.08), 0 12px 28px -4px rgba(45, 42, 38, 0.12)",
        "ds-btn": "0 2px 8px -2px rgba(13, 148, 136, 0.35)",
      },
    },
  },
  plugins: [],
};

export default config;
