/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./index.html", "./src/**/*.{ts,tsx,js,jsx}"],
  theme: {
    extend: {
      colors: {
        bg: "rgb(var(--color-bg))",
        "bg-alt": "rgb(var(--color-bg-alt))",
        "text-primary": "rgb(var(--color-text))",
        "text-secondary": "rgb(var(--color-text-secondary))",
        "text-tertiary": "rgb(var(--color-text-tertiary))",
        border: "rgb(var(--color-border))",
        "border-dark": "rgb(var(--color-border-dark, 209 213 219))",
        accent: "rgb(var(--color-accent))",
        "accent-hover": "rgb(var(--color-accent-hover))",
        success: "rgb(var(--color-success))",
        error: "rgb(var(--color-error))",
        surface: "rgb(var(--color-surface, 255 255 255))",
      },
      fontFamily: {
        body: ["Inter", "SF Pro Text", "system-ui", "sans-serif"],
        mono: ["SF Mono", "Fira Code", "monospace"],
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
