module.exports = {
  content: ["./index.html", "./src/**/*.{ts,tsx,js,jsx}"],
  theme: {
    extend: {
      colors: {
        bg: "rgb(17 20 32)",
        "bg-alt": "rgb(24 28 45)",
        accent: "rgb(217 179 5)",
      },
      fontFamily: {
        display: ["Playfair Display", "Georgia", "serif"],
        body: ["Source Serif Pro", "Georgia", "serif"],
      },
    },
  },
  plugins: [],
};
