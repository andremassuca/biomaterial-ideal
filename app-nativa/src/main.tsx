import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import App from "./App";
import { ProvedorDefinicoes } from "./lib/definicoes";
import { prepararNucleo } from "./lib/nucleo";
import "./estilos/tema.css";

// na versão web, espera pelo núcleo em WebAssembly antes de desenhar (na aplicação nativa não espera)
void prepararNucleo().then(() =>
  createRoot(document.getElementById("raiz")!).render(
    <StrictMode>
      <ProvedorDefinicoes>
        <App />
      </ProvedorDefinicoes>
    </StrictMode>,
  ),
);
