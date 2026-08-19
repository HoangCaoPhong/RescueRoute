/** @type {import('tailwindcss').Config} */
export default {
  darkMode: "class",
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: ["Inter", "ui-sans-serif", "system-ui", "sans-serif"],
      },
      colors: {
        route: {
          50: "#e8f0fe",
          100: "#d2e3fc",
          600: "#1a73e8",
          700: "#1967d2",
          800: "#185abc",
        },
        traffic: {
          green: "#34a853",
          amber: "#f9ab00",
          red: "#ea4335",
        },
      },
      boxShadow: {
        panel: "0 18px 45px -30px rgb(15 23 42 / 0.45)",
      },
    },
  },
  plugins: [],
};
