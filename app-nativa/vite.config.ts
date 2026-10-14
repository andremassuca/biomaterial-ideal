import { readdirSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Configuração do Vite para o Tauri 2: porta fixa, sem limpar o ecrã (para ver os erros do Rust)
// e variáveis TAURI_ expostas à interface.
const host = process.env.TAURI_DEV_HOST;

/** Modelos glTF presentes em public/modelos (nomes sem .glb); a interface só pede à rede os que existem. */
function modelosGlb(): string[] {
  try {
    return readdirSync(fileURLToPath(new URL("./public/modelos", import.meta.url)))
      .filter((f) => f.toLowerCase().endsWith(".glb"))
      .map((f) => f.slice(0, -4));
  } catch {
    return [];
  }
}

/** Vídeos MP4 presentes em public/simulacao/videos; o ecrã Simulação só mostra o bloco dos que existem. */
function videosSimulacao(): string[] {
  try {
    return readdirSync(fileURLToPath(new URL("./public/simulacao/videos", import.meta.url))).filter((f) =>
      f.toLowerCase().endsWith(".mp4"),
    );
  } catch {
    return [];
  }
}

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": fileURLToPath(new URL("./src", import.meta.url)),
      "@dados": fileURLToPath(new URL("./dados", import.meta.url)),
    },
  },
  clearScreen: false,
  server: {
    port: 1420,
    strictPort: true,
    host: host || false,
    hmr: host ? { protocol: "ws", host, port: 1421 } : undefined,
    watch: { ignored: ["**/src-tauri/**", "**/crates/**"] },
    fs: { allow: [".."] },
  },
  envPrefix: ["VITE_", "TAURI_ENV_"],
  define: { __MODELOS_GLB__: JSON.stringify(modelosGlb()), __VIDEOS_SIM__: JSON.stringify(videosSimulacao()) },
  build: {
    target: "es2021",
    minify: !process.env.TAURI_ENV_DEBUG ? "esbuild" : false,
    sourcemap: !!process.env.TAURI_ENV_DEBUG,
    chunkSizeWarningLimit: 2000,
  },
});
