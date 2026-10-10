/** Tailwind: todas as cores vêm das variáveis de tema (src/estilos/tema.css). */
/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  darkMode: ["class", '[data-tema="escuro"]'],
  theme: {
    extend: {
      fontFamily: {
        sans: ["Inter", "system-ui", "Segoe UI", "Roboto", "sans-serif"],
      },
      colors: {
        fundo: "rgb(var(--fundo) / <alpha-value>)",
        superficie: "rgb(var(--superficie) / <alpha-value>)",
        superficie2: "rgb(var(--superficie-2) / <alpha-value>)",
        texto: "rgb(var(--texto) / <alpha-value>)",
        texto2: "rgb(var(--texto-2) / <alpha-value>)",
        linha: "rgb(var(--linha) / <alpha-value>)",
        acento: "rgb(var(--acento) / <alpha-value>)",
        "acento-texto": "rgb(var(--acento-texto) / <alpha-value>)",
        aviso: "rgb(var(--aviso) / <alpha-value>)",
        perigo: "rgb(var(--perigo) / <alpha-value>)",
        sucesso: "rgb(var(--sucesso) / <alpha-value>)",
      },
      borderRadius: {
        lg: "12px",
        md: "8px",
        sm: "6px",
      },
      transitionDuration: {
        tema: "200ms",
      },
    },
  },
  plugins: [],
};
