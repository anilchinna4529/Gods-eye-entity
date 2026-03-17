import type { Config } from "tailwindcss";

export default {
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: {
          50: "#f7f7fb",
          100: "#ececf7",
          200: "#cfcfe6",
          300: "#a8a8cc",
          400: "#7a7aa6",
          500: "#57577e",
          600: "#3d3d5f",
          700: "#2b2b46",
          800: "#1b1b2f",
          900: "#0f0f1f"
        },
        neon: {
          300: "#7fffd4",
          400: "#2ee6a6",
          500: "#11c98a"
        },
        ember: {
          300: "#ffd18a",
          400: "#ffb454",
          500: "#ff8a2a"
        }
      }
    }
  },
  plugins: []
} satisfies Config;

