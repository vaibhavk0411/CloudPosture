/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        brand: {
          50: "#eef4ff",
          100: "#dbe7ff",
          200: "#bdd1ff",
          300: "#93b1ff",
          400: "#6485ff",
          500: "#4060ff",
          600: "#2a3df0",
          700: "#1f2dca",
          800: "#1c2aa0",
          900: "#1d2980",
        },
        ink: {
          950: "#0b1120",
          900: "#0f172a",
          800: "#111c30",
          700: "#1c2840",
          600: "#2a3a55",
        },
      },
      fontFamily: {
        sans: ["Inter", "ui-sans-serif", "system-ui", "sans-serif"],
      },
      boxShadow: {
        glow: "0 0 0 1px rgba(64,96,255,0.25), 0 8px 30px rgba(64,96,255,0.15)",
      },
    },
  },
  plugins: [],
};
