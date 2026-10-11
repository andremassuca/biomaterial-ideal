// Arranque do núcleo WebAssembly nos testes do vitest, a partir do disco. Fica separado de apoio.ts porque os testes
// e2e do Playwright importam apoio.ts e não podem importar módulos .js (com o Node 24, o Playwright 1.48 fica parado).
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { initSync } from "../src/wasm/mcdm_wasm.js";
import { APP_DIR } from "./apoio";

let iniciado = false;

/**
 * Arranca o núcleo WebAssembly (src/wasm, o mesmo que a versão web publica) com os bytes lidos do disco.
 * Depois disto, o `default()` que a interface chama já não vai buscar o ficheiro à rede.
 */
export function iniciarWasm(): void {
  if (iniciado) return;
  initSync({ module: readFileSync(resolve(APP_DIR, "src", "wasm", "mcdm_wasm_bg.wasm")) });
  iniciado = true;
}
