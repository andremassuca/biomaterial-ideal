// Gera dois PDFs de exemplo do relatório (um caso e um doente) com o Chromium sem interface, a partir da versão
// web servida localmente. Uso: node e2e/gerar_pdfs.mjs [URL_BASE] [PASTA_SAIDA]
// Por omissão: http://127.0.0.1:5180/ e D:\LAB\_partilha\app_v2. Só escreve nessa pasta.
import { mkdirSync } from "node:fs";
import { resolve } from "node:path";
import { chromium } from "@playwright/test";

const base = process.argv[2] ?? "http://127.0.0.1:5180/";
const saida = process.argv[3] ?? "D:\\LAB\\_partilha\\app_v2";
mkdirSync(saida, { recursive: true });

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1440, height: 900 }, locale: "pt-PT" });
const erros = [];
page.on("pageerror", (e) => erros.push(String(e)));
page.on("console", (m) => m.type() === "error" && erros.push(m.text()));

async function pdf(nome) {
  await page.getByRole("button", { name: /Exportar PDF/ }).first().click();
  await page.getByRole("dialog", { name: "Relatório da análise" }).waitFor();
  const ficheiro = resolve(saida, nome);
  await page.pdf({ path: ficheiro, format: "A4", printBackground: true, margin: { top: "12mm", bottom: "12mm", left: "12mm", right: "12mm" } });
  console.log("PDF:", ficheiro);
  await page.getByRole("button", { name: "Fechar o relatório" }).click();
}

// 1) Caso: stent, cenário A, com Monte Carlo (10 000 repetições, propriedades)
await page.goto(`${base}#/stent`);
await page.waitForFunction(() => !document.querySelector("main .animate-pulse"), null, { timeout: 30_000 });
await page.getByRole("button", { name: "Correr" }).click();
await page.getByText(/repetições/).first().waitFor({ timeout: 120_000 });
await pdf("relatorio_caso_stent.pdf");

// 2) Doente: haste, perfil de exemplo "Idosa com osteoporose" (regras H-OST)
await page.goto(`${base}#/doente`);
await page.getByRole("button", { name: /H2/ }).click();
await page.getByRole("button", { name: /^4\s*Resultado/ }).click();
await page.waitForFunction(() => !document.querySelector("main .animate-pulse"), null, { timeout: 30_000 });
await pdf("relatorio_doente_haste_H2.pdf");

await browser.close();
if (erros.length) console.log("Erros na consola:", erros);
