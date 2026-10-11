// Testes da versão web (dist-web) que completam web.spec.ts com as decisões de 11 out e os pontos da revisão que o
// visitante vê: frases únicas do stent e do scaffold, docente da unidade curricular no Sobre, perfil do doente que
// troca o vencedor do scaffold (results/perfis_referencia.csv) e notas internas fora das fichas do implante dentário
// (R88).
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { expect, test, type Page } from "@playwright/test";
import { num } from "../src/lib/formato";
import { APP_DIR, RESULTS, lerCsv } from "../testes/apoio";

const APP = JSON.parse(readFileSync(resolve(APP_DIR, "dados", "app.json"), "utf-8")) as {
  nomes: Record<string, { nome: string; codigo: string }>;
};
const CASO_SCAFFOLD = JSON.parse(readFileSync(resolve(APP_DIR, "dados", "caso_scaffold.json"), "utf-8")) as {
  perfis_referencia: Record<string, { descricao: string }>;
};
const nome = (m: string) => APP.nomes[m]?.nome ?? m;
const codigo = (m: string) => APP.nomes[m]?.codigo ?? "";
const limpo = (s: string) => s.replace(/[\s  ]+/g, " ").trim();

const STENT =
  "Pt-Cr e L605 praticamente equivalentes: o Pt-Cr é favorecido pelo TOPSIS, pelo VIKOR e pela radiopacidade; o L605 pelo WASPAS e por ter todas as propriedades em fichas de fornecedor. Sem vencedor universal.";
const STENT_CURTA = "Stent: Pt-Cr e L605 praticamente equivalentes";
const SCAFFOLD_CURTA = "Scaffold: depende da carga (compósito com carga; β-TCP sem carga)";
const SCAFFOLD =
  "Depende da carga: compósito PCL/β-TCP impresso quando o defeito suporta carga (1.º no ranking direto em 5 das 6 combinações); β-TCP poroso quando não suporta (mais vezes 1.º na incerteza dos dados).";

/** Erros e avisos da consola e erros da página. */
function vigiar(page: Page): string[] {
  const p: string[] = [];
  page.on("console", (m) => {
    if (/GroupMarkerNotSet|GL Driver Message|software WebGL/.test(m.text())) return;
    if (m.type() === "error" || m.type() === "warning") p.push(`[${m.type()}] ${m.text()}`);
  });
  page.on("pageerror", (e) => p.push(`[pageerror] ${e.message}`));
  return p;
}

async function abrir(page: Page) {
  await page.goto("./");
  await expect(page.getByRole("navigation", { name: "Ecrãs" })).toBeVisible();
  await expect(page.getByText("Modo navegador: só o TOPSIS")).toHaveCount(0);
}

async function irPara(page: Page, texto: string) {
  const botao = page.getByRole("navigation", { name: "Ecrãs" }).getByRole("button", { name: texto, exact: true });
  await botao.click();
  await expect(botao).toHaveAttribute("aria-current", "page");
  await expect(page.locator("main .animate-pulse")).toHaveCount(0, { timeout: 15_000 });
  await page.waitForTimeout(400);
}

test.describe("decisões de 11 out", () => {
  test("frases únicas do stent e do scaffold no Início e no ecrã do caso", async ({ page }) => {
    const problemas = vigiar(page);
    await abrir(page);
    const inicio = (await page.locator("main [data-recomendacao]").allInnerTexts()).map(limpo);
    expect(inicio).toEqual(expect.arrayContaining([STENT_CURTA, SCAFFOLD_CURTA]));
    // a legenda do 3D não mostra notas de trabalho nem caminhos de ficheiros
    await expect(page.locator("main")).not.toContainText("public/modelos");
    await expect(page.locator("main")).not.toContainText("Blender");
    await irPara(page, "Stent");
    await expect(page.locator("main [data-recomendacao]")).toHaveText(`Recomendação: ${STENT}`);
    await irPara(page, "Scaffold ósseo");
    await expect(page.locator("main [data-recomendacao]")).toHaveText(`Recomendação: ${SCAFFOLD}`);
    await irPara(page, "Haste femoral");
    await expect(page.locator("main [data-recomendacao]")).toHaveCount(0);
    expect(problemas).toEqual([]);
  });

  test("Sobre: unidade curricular e docente", async ({ page }) => {
    await abrir(page);
    await irPara(page, "Sobre");
    const texto = limpo(await page.locator("main").innerText());
    expect(texto).toContain("Próteses e Órgãos Artificiais");
    expect(texto).toContain("Prof. Pedro Sampaio");
  });

  test("doente: o perfil C1 (defeito com carga) troca o vencedor do TOPSIS no scaffold, como em results/perfis_referencia.csv", async ({
    page,
  }) => {
    const problemas = vigiar(page);
    await abrir(page);
    await irPara(page, "Doente");
    await page.locator("main").getByRole("button", { name: /Scaffold ósseo/ }).click();
    await page.getByRole("button", { name: `C1: ${CASO_SCAFFOLD.perfis_referencia.C1.descricao}` }).click();
    await expect(page.getByText("Com os dados do doente")).toBeVisible();
    const linhas = lerCsv(resolve(RESULTS, "perfis_referencia.csv")).filter((l) => l.perfil === "C1");
    const esperado = [...linhas]
      .sort((a, b) => Number(a.pos_TOPSIS) - Number(b.pos_TOPSIS))
      .map((l) => limpo(`${l.pos_TOPSIS}.º ${nome(l.material)} ${codigo(l.material)} C ${num(Number(l.C_TOPSIS), 3)}`));
    const regiao = page.getByRole("region", { name: "Ranking TOPSIS" }).first();
    await expect.poll(async () => (await regiao.locator("li").allInnerTexts()).map(limpo)).toEqual(esperado);
    const antes = linhas.find((l) => l.pos_ref_TOPSIS === "1")!.material;
    const depois = linhas.find((l) => l.pos_TOPSIS === "1")!.material;
    expect(depois).not.toBe(antes);
    expect(problemas).toEqual([]);
  });

  test("doente: o jovem ativo (H1) aparece como sensibilidade ao fator do perfil, não como recomendação", async ({ page }) => {
    await abrir(page);
    await irPara(page, "Doente");
    await page.locator("main").getByRole("button", { name: /Haste femoral/ }).click();
    await page.getByRole("button", { name: /^H1:/ }).click();
    await expect(page.getByText("Com os dados do doente")).toBeVisible();
    const linhas = lerCsv(resolve(RESULTS, "perfis_referencia.csv")).filter((l) => l.perfil === "H1" && l.cenario === "A");
    const depois = linhas.find((l) => l.pos_TOPSIS === "1")!.material;
    const nota = page.locator("main [data-sensibilidade]");
    await expect(nota).toContainText(nome(depois));
    await expect(nota).toContainText("sensibilidade ao fator do perfil");
    await expect(nota).toContainText("não como recomendação");
  });

  for (const largura of [1366, 1920]) {
    test(`espectro a ${largura} px: pontos e rótulos não tapam a legenda do empate`, async ({ page }, info) => {
      test.skip(info.project.name !== "computador", "ecrã largo");
      await page.setViewportSize({ width: largura, height: 900 });
      await abrir(page);
      await page.waitForTimeout(900);
      const choques = await page.evaluate(() => {
        const svg = document.querySelector('main svg[aria-label="Espectro de confiança dos cinco casos"]');
        if (!svg) return ["sem SVG"];
        const empate = svg.querySelector("[data-rotulo-empate]")!.getBoundingClientRect();
        const caixas = [...svg.querySelectorAll("g text, g circle")].map((e) => ({ t: e.textContent ?? "círculo", r: e.getBoundingClientRect() }));
        const cruza = (a: DOMRect, b: DOMRect) => a.left < b.right && b.left < a.right && a.top < b.bottom && b.top < a.bottom;
        const saida = caixas.filter((c) => cruza(c.r, empate)).map((c) => `empate × ${c.t}`);
        const textos = caixas.filter((c) => c.t !== "círculo");
        for (let i = 0; i < textos.length; i++)
          for (let j = i + 1; j < textos.length; j++) if (cruza(textos[i].r, textos[j].r)) saida.push(`${textos[i].t} × ${textos[j].t}`);
        return saida;
      });
      expect(choques).toEqual([]);
    });
  }

  test("ranking a 1920 px: nome e pontuação sem sobreposição nos casos e no resultado do doente", async ({ page }, info) => {
    test.skip(info.project.name !== "computador", "ecrã largo");
    await page.setViewportSize({ width: 1920, height: 1080 });
    await abrir(page);
    const sobrepostos = () =>
      page.evaluate(() =>
        [...document.querySelectorAll("main [data-pontuacao]")]
          .filter((s) => {
            const nome = s.closest("li")?.querySelector(".inline-flex.flex-col");
            if (!nome) return true;
            const a = s.getBoundingClientRect();
            // o texto do nome (não só a caixa, que não cresce quando uma palavra transborda) não pode passar para cima
            // da pontuação
            const r = document.createRange();
            r.selectNodeContents(nome);
            const b = Math.max(...[...r.getClientRects()].map((q) => q.right));
            return a.left < b - 0.5;
          })
          .map((s) => s.textContent),
      );
    for (const texto of ["Haste femoral", "Stent", "Scaffold ósseo"]) {
      await irPara(page, texto);
      expect(await sobrepostos(), texto).toEqual([]);
    }
    await irPara(page, "Doente");
    await page.locator("main").getByRole("button", { name: /Scaffold ósseo/ }).click();
    await page.getByRole("button", { name: /^C2:/ }).click();
    await expect(page.getByText("Com os dados do doente")).toBeVisible();
    await page.waitForTimeout(800);
    expect(await sobrepostos(), "doente").toEqual([]);
  });

  test("fichas do implante dentário sem notas internas de trabalho (R88)", async ({ page }) => {
    await abrir(page);
    await irPara(page, "Fichas dos materiais");
    for (const m of ["Ti cp grau 4", "Zircónia"]) {
      await page.getByRole("textbox", { name: "Procurar material" }).fill(m);
      const botoes = page.locator("main nav button");
      const n = await botoes.count();
      expect(n, m).toBeGreaterThan(0);
      for (let k = 0; k < n; k++) {
        await botoes.nth(k).click();
        const fechados = page.locator("main ul button[aria-expanded=false]");
        while ((await fechados.count()) > 0) await fechados.first().click();
        expect(await page.locator("main").innerText(), `${m} ${k}`).not.toMatch(/confirmar/);
      }
    }
  });

  test("Início: o botão \"Como funciona?\" abre o ecrã novo, com o esquema e sem deslocamento horizontal", async ({ page }) => {
    const problemas = vigiar(page);
    await abrir(page);
    await page.locator("main").getByRole("button", { name: "Como funciona?" }).click();
    await expect(page).toHaveURL(/#\/como-funciona$/);
    await expect(page.getByRole("heading", { level: 1, name: "Como funciona" })).toBeVisible();
    await expect(page.getByRole("navigation", { name: "Ecrãs" }).getByRole("button", { name: "Como funciona", exact: true })).toHaveAttribute(
      "aria-current",
      "page",
    );
    await expect(page.getByRole("list", { name: /Passos do método/ }).getByRole("listitem")).toHaveCount(5);
    await expect(page.locator("[data-exemplo]")).toContainText("No caso completo");
    const largura = await page.evaluate(() => [document.documentElement.scrollWidth, document.documentElement.clientWidth]);
    expect(largura[0]).toBeLessThanOrEqual(largura[1]);
    expect(problemas).toEqual([]);
  });
});
