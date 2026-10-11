// Apoio aos testes: leitura dos CSV e JSON de results/. O arranque do núcleo WebAssembly está em apoio_wasm.ts
// (os testes e2e do Playwright importam este ficheiro e não podem importar módulos .js: com o Node 24, o
// Playwright 1.48 fica parado ao carregá-los).
import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const AQUI = dirname(fileURLToPath(import.meta.url));

/**
 * Pasta app-nativa/ e pasta results/ do repositório. Os CSV de results/ não são versionados; num worktree sem eles,
 * a variável RESULTS_DIR indica outra cópia (por exemplo a do repositório principal).
 */
export const APP_DIR = resolve(AQUI, "..");
export const RESULTS = process.env.RESULTS_DIR ? resolve(process.env.RESULTS_DIR) : resolve(APP_DIR, "..", "results");

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
