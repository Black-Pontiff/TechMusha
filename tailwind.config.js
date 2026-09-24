module.exports = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: { 900: "#0a0a0a", 800: "#121212", 700: "#1c1c1c", 600: "#262626" },
        accent: { DEFAULT: "#22c55e", soft: "#16a34a" },
      },
    },
  },
  plugins: [],
};

