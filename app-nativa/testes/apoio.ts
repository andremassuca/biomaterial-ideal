// Apoio aos testes: leitura dos CSV e JSON de results/ e arranque do núcleo WebAssembly a partir do disco.
import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { initSync } from "../src/wasm/mcdm_wasm.js";

const AQUI = dirname(fileURLToPath(import.meta.url));

/** Pasta app-nativa/ e pasta results/ do repositório. */
export const APP_DIR = resolve(AQUI, "..");
export const RESULTS = resolve(APP_DIR, "..", "results");

/**
 * Lê um CSV com cabeçalho (campos entre aspas, com vírgulas ou aspas duplicadas lá dentro).
 * Em linguagem simples: devolve uma lista de linhas, cada uma um objeto coluna -> texto.
 */
export function lerCsv(caminho: string): Record<string, string>[] {
  const texto = readFileSync(caminho, "utf-8").replace(/^﻿/, "");
  const linhas: string[][] = [];
  let campo = "";
  let linha: string[] = [];
  let aspas = false;
  for (let i = 0; i < texto.length; i++) {
    const ch = texto[i];
    if (aspas) {
      if (ch === '"' && texto[i + 1] === '"') {
        campo += '"';
        i++;
      } else if (ch === '"') aspas = false;
      else campo += ch;
    } else if (ch === '"') aspas = true;
    else if (ch === ",") {
      linha.push(campo);
      campo = "";
    } else if (ch === "\n" || ch === "\r") {
      if (ch === "\r" && texto[i + 1] === "\n") i++;
      linha.push(campo);
      campo = "";
      if (linha.length > 1 || linha[0] !== "") linhas.push(linha);
      linha = [];
    } else campo += ch;
  }
  if (campo !== "" || linha.length) {
    linha.push(campo);
    linhas.push(linha);
  }
  const [cab, ...resto] = linhas;
  return resto.map((l) => Object.fromEntries(cab.map((c, k) => [c, l[k] ?? ""])));
}

/** Lê um JSON de results/ ou de dados/. */
export function lerJson<T = unknown>(caminho: string): T {
  return JSON.parse(readFileSync(caminho, "utf-8")) as T;
}

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
