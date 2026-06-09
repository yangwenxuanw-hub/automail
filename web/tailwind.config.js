/** @type {import('tailwindcss').Config} */

export default {
  darkMode: "class",
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    container: {
      center: true,
    },
    extend: {
      fontFamily: {
        sans: ["Noto Sans SC", "ui-sans-serif", "system-ui"],
        serif: ["Noto Serif SC", "ui-serif", "Georgia"],
      },
      colors: {
        ink: {
          950: "#070A12",
          900: "#0A0F1F",
          850: "#0E1530",
          800: "#111B3A",
          700: "#1B2A57",
        },
        ledger: {
          100: "#E7EAF2",
          200: "#C7CEDF",
          300: "#A5B1CC",
          400: "#7B8AAE",
        },
        accent: {
          500: "#F2B705",
          600: "#D89F00",
        },
        mint: {
          500: "#19D3A2",
          600: "#12B78B",
        },
        risk: {
          500: "#F43F5E",
          600: "#E11D48",
        },
      },
      boxShadow: {
        paper: "0 12px 30px rgba(0, 0, 0, 0.45)",
        glow: "0 0 0 1px rgba(242, 183, 5, 0.25), 0 18px 60px rgba(0, 0, 0, 0.6)",
      },
    },
  },
  plugins: [],
};
