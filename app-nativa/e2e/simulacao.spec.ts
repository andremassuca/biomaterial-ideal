// Versão web (dist-web), ecrã "Simulação FEA e CFD": os resultados novos do relatório v11.1 (Carreau e micromovimento)
// batem com results/, o bloco de vídeo não aparece sem MP4, não há erros na consola nem deslocamento horizontal no
// telemóvel; e um percurso de utilizador pelo Início, caso, doente, Comparar, Simulação, PDF e modo apresentação.
// Capturas só se a variável CAPTURAS indicar uma pasta (não são versionadas).
import { mkdirSync, readFileSync } from "node:fs";
import { resolve } from "node:path";
import { expect, test, type Locator, type Page } from "@playwright/test";
import { num } from "../src/lib/formato";
import { RESULTS } from "../testes/apoio";

const limpo = (s: string) => s.replace(/[\s  ]+/g, " ").trim();
const CAPTURAS = process.env.CAPTURAS;

function vigiar(page: Page): string[] {
  const p: string[] = [];
  page.on("console", (m) => {
    if (/GroupMarkerNotSet|GL Driver Message|software WebGL/.test(m.text())) return;
    if (m.type() === "error" || m.type() === "warning") p.push(`[${m.type()}] ${m.text()}`);
  });
  page.on("pageerror", (e) => p.push(`[pageerror] ${e.message}`));
  // o navegador cancela (ERR_ABORTED) os pedidos de vídeo ao ler os metadados ou ao sair do ecrã: não é falha
  page.on("requestfailed", (r) => !(r.url().endsWith(".mp4") && r.failure()?.errorText === "net::ERR_ABORTED") && p.push(`[pedido falhado] ${r.url()} ${r.failure()?.errorText}`));
  page.on("response", (r) => r.status() >= 400 && p.push(`[${r.status()}] ${r.url()}`));
  return p;
}

async function ecra(page: Page, rota: string) {
  await page.goto(`./#/${rota}`);
  await expect(page.locator("main h1")).toHaveCount(1);
  await expect(page.locator("main .animate-pulse")).toHaveCount(0, { timeout: 15_000 });
  await page.waitForTimeout(500);
}

/** Captura da janela, ou só do elemento indicado (a página rola dentro de <main>, por isso a página inteira não serve). */
async function captura(page: Page, nome: string, elemento?: Locator) {
  if (!CAPTURAS) return;
  mkdirSync(CAPTURAS, { recursive: true });
  const caminho = resolve(CAPTURAS, `${test.info().project.name}_${nome}.png`);
  if (elemento) await elemento.screenshot({ path: caminho });
  else await page.screenshot({ path: caminho });
}

test.describe("ecrã Simulação (relatório v11.1)", () => {
  test("Carreau e micromovimento batem com results/, sem vídeo e sem erros", async ({ page }) => {
    const problemas = vigiar(page);
    const carreau = JSON.parse(readFileSync(resolve(RESULTS, "cfd_pulsatil_carreau.json"), "utf-8")) as {
      casos: Record<string, { carreau: { fracao_baixa: number; tau_media: number }; newtoniano: { fracao_baixa: number } }>;
    };
    const micro = JSON.parse(readFileSync(resolve(RESULTS, "micromovimento_haste.json"), "utf-8")) as Record<
      string,
      { tangencial: { max_um: number; mediana_um: number } }
    >;

    await ecra(page, "simulacao");
    // separador da haste (por omissão): micromovimento
    const m = page.locator("[data-micromovimento]");
    await expect(m).toBeVisible();
    const tm = limpo(await m.innerText());
    const principal = micro["atrito04_Ti_fkn10"].tangencial;
    expect(tm).toContain(`${limpo(num(principal.max_um, 1))} µm`);
    expect(tm).toContain(`mediana é de ${limpo(num(principal.mediana_um, 1))} µm`);
    expect(tm).toContain("nenhum nó (0 %)");
    expect(tm).toContain("63,9 a 99,1 µm");
    expect(tm).toContain("Verificação, não previsão clínica.");
    await captura(page, "simulacao_fea_micromovimento", m);

    await page.getByRole("tab", { name: "Stent (CFD)" }).click();
    const c = page.locator("[data-carreau]");
    await expect(c).toBeVisible();
    const tc = limpo(await c.innerText());
    for (const [mat, r] of Object.entries(carreau.casos)) {
      expect(tc, mat).toContain(limpo(`${num(100 * r.carreau.fracao_baixa, 1)} %`));
      expect(tc, mat).toContain(limpo(`${num(100 * r.newtoniano.fracao_baixa, 1)} %`));
      expect(tc, mat).toContain(limpo(num(r.carreau.tau_media, 3)));
    }
    expect(tc).toContain("36,8 %");
    expect(tc).toContain("69,2 %");
    expect(tc).toContain("0,508 e 0,296 Pa");
    expect(tc).toContain("Verificação, não previsão clínica.");
    await captura(page, "simulacao_cfd_carreau", c);

    // o vídeo da CFD está neste separador, com a legenda aprovada e sem pedidos falhados
    const vc = page.locator('[data-video="cfd_stent_2ciclo_web.mp4"] video');
    await expect(vc).toHaveCount(1);
    await expect(page.locator("video")).toHaveCount(1);
    // o Chromium de teste não descodifica H.264: confere-se os atributos e que o ficheiro é servido como vídeo
    expect(await vc.evaluate((v: HTMLVideoElement) => [v.muted, v.loop, v.controls, v.preload])).toEqual([true, true, true, "metadata"]);
    const resposta = await page.request.get(await vc.evaluate((v: HTMLVideoElement) => v.src));
    expect(resposta.status()).toBe(200);
    expect(resposta.headers()["content-type"]).toBe("video/mp4");
    expect(tc + limpo(await page.locator('[data-video="cfd_stent_2ciclo_web.mp4"]').innerText())).toContain("(t = 2,12 s)");
    await page.getByRole("tab", { name: "Haste femoral (FEA)" }).click();
    await expect(page.locator('[data-video="fea_haste_4materiais_web.mp4"] video')).toHaveCount(1);
    await expect(page.locator("video")).toHaveCount(1);
    expect(problemas).toEqual([]);
  });

  test("sem deslocamento horizontal nos dois separadores", async ({ page }) => {
    await ecra(page, "simulacao");
    for (const separador of ["Haste femoral (FEA)", "Stent (CFD)"]) {
      await page.getByRole("tab", { name: separador }).click();
      await page.waitForTimeout(300);
      const largura = await page.evaluate(() => {
        const d = document.documentElement;
        const main = document.querySelector("main")!;
        return { pagina: d.scrollWidth - d.clientWidth, main: main.scrollWidth - main.clientWidth };
      });
      expect(largura, separador).toEqual({ pagina: 0, main: 0 });
    }
  });
});

test.describe("percurso de utilizador", () => {
  test("Início, caso, doente, Comparar, Simulação, exportar PDF e modo apresentação", async ({ page }) => {
    const problemas = vigiar(page);
    await ecra(page, "");
    await captura(page, "01_inicio");

    await ecra(page, "stent");
    await expect(page.locator("main h1")).toContainText(/stent/i);
    await captura(page, "02_caso_stent");

    await ecra(page, "doente");
    await page.getByRole("button", { name: /H2/ }).click();
    await page.getByRole("button", { name: /^4\s*Resultado/ }).click();
    await expect(page.locator("main .animate-pulse")).toHaveCount(0, { timeout: 15_000 });
    await captura(page, "03_doente_resultado");

    await ecra(page, "comparar");
    await captura(page, "04_comparar");

    await ecra(page, "simulacao");
    await captura(page, "05_simulacao");

    // exportar PDF a partir de um caso
    await ecra(page, "stent");
    await page.getByRole("button", { name: /Exportar PDF/ }).first().click();
    await expect(page.getByRole("dialog", { name: "Relatório da análise" })).toBeVisible();
    await captura(page, "06_pdf_relatorio");
    await page.getByRole("button", { name: "Fechar o relatório" }).click();

    // modo apresentação (liga, mostra a Simulação e desliga)
    await page.getByRole("button", { name: "Entrar no modo apresentação" }).click();
    await expect(page.getByRole("button", { name: "Sair do modo apresentação" })).toBeVisible();
    await ecra(page, "simulacao");
    await captura(page, "07_simulacao_apresentacao");
    await page.getByRole("button", { name: "Sair do modo apresentação" }).click();
    expect(problemas).toEqual([]);
  });
});
