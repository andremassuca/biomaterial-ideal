/// <reference types="vite/client" />

declare module "*.svg?raw" {
  const conteudo: string;
  export default conteudo;
}

/** Modelos glTF que existem em public/modelos (nomes sem .glb), lidos pelo vite.config.ts ao arrancar. */
declare const __MODELOS_GLB__: string[];
