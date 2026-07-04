/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        paper: "#F7F3EA",
        "paper-dark": "#14120F",
        ink: "#211E1A",
        "ink-soft": "#5B564C",
        rule: "#DCD3BE",
        "rule-dark": "#3A362E",
        indigo: {
          DEFAULT: "#2C3454",
          light: "#465080",
        },
        sienna: {
          DEFAULT: "#B5563C",
          light: "#D97A5F",
        },
      },
      fontFamily: {
        display: ["'Source Serif 4'", "Georgia", "serif"],
        body: ["'Inter'", "system-ui", "sans-serif"],
        mono: ["'JetBrains Mono'", "ui-monospace", "monospace"],
      },
      borderRadius: {
        card: "6px",
      },
    },
  },
  plugins: [],
};
