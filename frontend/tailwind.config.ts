import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        ink: "#F5F5F7",
        surface: "#FFFFFF",
        border: "#E5E7EB",
        accent: "#2563EB",
        "accent-glow": "#3B82F6",
        success: "#10B981",
        warning: "#F59E0B",
        danger: "#EF4444",
        muted: "#98A2B3",
        text: "#111827",
        "text-sub": "#6B7280",
      },
      fontFamily: {
        serif: ["\"DM Serif Display\"", "ui-serif", "Georgia", "serif"],
        sans: ["Inter", "ui-sans-serif", "system-ui", "sans-serif"],
        mono: ["\"JetBrains Mono\"", "ui-monospace", "SFMono-Regular", "monospace"],
      },
      boxShadow: {
        card: "0 0 0 1px rgba(17,24,39,0.04), 0 12px 32px rgba(17,24,39,0.06)",
      },
      keyframes: {
        pulseBorder: {
          "0%, 100%": { boxShadow: "0 0 0 0 rgba(37, 99, 235, 0.0)" },
          "50%": { boxShadow: "0 0 0 6px rgba(59, 130, 246, 0.18)" },
        },
      },
      animation: {
        "pulse-border": "pulseBorder 1.2s ease-in-out infinite",
      },
    },
  },
  plugins: [],
};
export default config;
