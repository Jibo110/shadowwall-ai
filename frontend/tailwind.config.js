/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // ShadowWall AI color system
        // Dark cyber aesthetic — professional, not gimmicky
        cyber: {
          bg:       "#0a0e1a",   // Page background
          surface:  "#0f1729",   // Card background
          border:   "#1e2d4a",   // Card borders
          accent:   "#00d4ff",   // Primary accent — cyan
          accent2:  "#7c3aed",   // Secondary accent — purple
          success:  "#10b981",   // Green — active/safe
          warning:  "#f59e0b",   // Amber — medium severity
          danger:   "#ef4444",   // Red — high severity
          critical: "#dc2626",   // Darker red — critical
          muted:    "#4a5568",   // Muted text
          text:     "#e2e8f0",   // Primary text
          subtext:  "#94a3b8",   // Secondary text
        },
      },
      fontFamily: {
        mono: ["JetBrains Mono", "Fira Code", "monospace"],
      },
      animation: {
        "pulse-slow": "pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite",
        "fade-in": "fadeIn 0.3s ease-in-out",
        "slide-in": "slideIn 0.3s ease-out",
        "glow": "glow 2s ease-in-out infinite alternate",
      },
      keyframes: {
        fadeIn: {
          "0%": { opacity: "0" },
          "100%": { opacity: "1" },
        },
        slideIn: {
          "0%": { transform: "translateX(-10px)", opacity: "0" },
          "100%": { transform: "translateX(0)", opacity: "1" },
        },
        glow: {
          "0%": { boxShadow: "0 0 5px #00d4ff33" },
          "100%": { boxShadow: "0 0 20px #00d4ff66, 0 0 40px #00d4ff22" },
        },
      },
    },
  },
  plugins: [],
}