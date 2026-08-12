/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./index.html", "./src/**/*.{ts,tsx,js,jsx}"],
  theme: {
    extend: {
      colors: {
        bg: "rgb(248 250 252)",
        "bg-alt": "rgb(255 255 255)",
        "text-primary": "rgb(17 24 39)",
        "text-secondary": "rgb(107 114 128)",
        "text-tertiary": "rgb(149 156 169)",
        border: "rgb(229 231 235)",
        "border-dark": "rgb(209 213 219)",
        accent: "rgb(59 130 223)",
        "accent-hover": "rgb(37 99 235)",
        success: "rgb(34 197 94)",
        error: "rgb(239 68 68)",
        surface: "rgb(255 255 255)",
      },
      fontFamily: {
        body: ["Inter", "SF Pro Text", "system-ui", "sans-serif"],
        mono: ['SF Mono', 'Fira Code', 'monospace'],
      },
      boxShadow: {
        subtle: "0 1px 3px 0 rgb(0 0 0 / 0.04), 0 1px 2px -1px rgb(0 0 0 / 0.04)",
        card: "0 1px 3px 0 rgb(0 0 0 / 0.03), 0 1px 2px -1px rgb(0 0 0 / 0.03)",
        elevated: "0 4px 6px -1px rgb(0 0 0 / 0.03), 0 2px 4px -2px rgb(0 0 0 / 0.03)",
      },
    },
  },
  plugins: [],
};
