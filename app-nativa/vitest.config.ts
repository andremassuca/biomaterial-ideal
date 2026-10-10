// Configuração dos testes da interface (vitest): reutiliza a do Vite (aliases @ e @dados).
// Os testes de números correm em Node; o teste de fumo dos ecrãs pede o jsdom no próprio ficheiro.
// Os testes do navegador (Playwright) ficam em e2e/ e não correm aqui.
import { fileURLToPath } from "node:url";
import { defineConfig, mergeConfig } from "vitest/config";
import vite from "./vite.config";

export default mergeConfig(
  vite,
  defineConfig({
    resolve: {
      mainFields: ["module", "jsnext:main", "jsnext", "main"],
      // o React Three Fiber e o drei só têm "main" (CommonJS) e "module" (ESM); o Node escolhia o CommonJS, que carrega uma
      // segunda cópia do three.js (aviso "Multiple instances of Three.js"). Nos testes usa-se o ESM, como no navegador.
      alias: [
        {
          find: /^@react-three\/fiber$/,
          replacement: fileURLToPath(new URL("./node_modules/@react-three/fiber/dist/react-three-fiber.esm.js", import.meta.url)),
        },
        { find: /^@react-three\/drei$/, replacement: fileURLToPath(new URL("./node_modules/@react-three/drei/index.js", import.meta.url)) },
      ],
    },
    test: {
      include: ["testes/**/*.test.{ts,tsx}"],
      environment: "node",
      testTimeout: 120_000,
      hookTimeout: 120_000,
      // os pacotes que importam o three.js passam pelo Vite (ESM), para haver uma só cópia do three.js
      server: { deps: { inline: [/three/, /@react-three/, /stats-gl/, /maath/, /@monogrid/, /troika/, /@react-spring/, /meshline/, /camera-controls/] } },
    },
  }),
);
