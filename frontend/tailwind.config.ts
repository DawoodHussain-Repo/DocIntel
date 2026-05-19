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
        ink: "#F4F7F9",
        surface: "#FFFFFF",
        border: "#E2E5EA",
        accent: "#4F46E5",
        "accent-glow": "#6366F1",
        success: "#10B981",
        warning: "#F59E0B",
        danger: "#EF4444",
        muted: "#98A2B3",
        text: "#0F172A",
        "text-sub": "#64748B",
      },
      fontFamily: {
        serif: ["\"DM Serif Display\"", "ui-serif", "Georgia", "serif"],
        sans: ["Inter", "ui-sans-serif", "system-ui", "sans-serif"],
        mono: ["\"JetBrains Mono\"", "ui-monospace", "SFMono-Regular", "monospace"],
      },
      boxShadow: {
        card: "0 0 0 1px rgba(15,23,42,0.04), 0 8px 28px rgba(15,23,42,0.06)",
        "card-hover": "0 0 0 1px rgba(15,23,42,0.04), 0 20px 44px rgba(15,23,42,0.09)",
        "inner-soft": "inset 0 2px 4px rgba(15,23,42,0.06)",
      },
      keyframes: {
        pulseBorder: {
          "0%, 100%": { boxShadow: "0 0 0 0 rgba(79, 70, 229, 0.0)" },
          "50%": { boxShadow: "0 0 0 6px rgba(99, 102, 241, 0.15)" },
        },
        shimmer: {
          "0%": { backgroundPosition: "-200% 0" },
          "100%": { backgroundPosition: "200% 0" },
        },
      },
      animation: {
        "pulse-border": "pulseBorder 1.2s ease-in-out infinite",
        shimmer: "shimmer 1.5s ease-in-out infinite",
      },
    },
  },
  plugins: [],
};
export default config;
