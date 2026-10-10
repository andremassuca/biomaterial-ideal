// Testes da versão web (dist-web) com o Chromium sem interface, servida localmente no subcaminho do GitHub Pages.
// Antes: `npm run build:web`. Nada é publicado: o servidor só escuta em 127.0.0.1.
import { defineConfig } from "@playwright/test";

const PORTA = Number(process.env.PORTA ?? 4317);

export default defineConfig({
  testDir: "e2e",
  testMatch: "**/*.spec.ts",
  timeout: 120_000,
  fullyParallel: false,
  workers: 1,
  reporter: [["list"]],
  use: {
    baseURL: `http://127.0.0.1:${PORTA}/biomaterial-ideal/`,
    headless: true,
    locale: "pt-PT",
    colorScheme: "light",
  },
  projects: [
    { name: "telemovel", use: { browserName: "chromium", viewport: { width: 390, height: 844 }, deviceScaleFactor: 3, hasTouch: true } },
    { name: "computador", use: { browserName: "chromium", viewport: { width: 1440, height: 900 } } },
  ],
  webServer: {
    command: `node e2e/servidor.mjs ${PORTA}`,
    url: `http://127.0.0.1:${PORTA}/biomaterial-ideal/`,
    reuseExistingServer: false,
    timeout: 30_000,
  },
});
