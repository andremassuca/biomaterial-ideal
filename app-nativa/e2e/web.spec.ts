// Versão web (dist-web) no Chromium sem interface, em largura de telemóvel e de computador: todos os ecrãs abrem,
// sem erros nem avisos na consola, sem pedidos falhados, sem deslocamento horizontal no telemóvel, e os números
// mostrados batem com results/ (e com o núcleo da aplicação nativa, que é o mesmo crate Rust).
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { expect, test, type Page } from "@playwright/test";
import { num, pct, valor } from "../src/lib/formato";
import { APP_DIR, RESULTS, lerCsv } from "../testes/apoio";

const APP = JSON.parse(readFileSync(resolve(APP_DIR, "dados", "app.json"), "utf-8")) as {
  nomes: Record<string, { nome: string; codigo: string }>;
  fea: { malha_mm: number; zonas: { material: string; material_base: string | null; zona: number; razao: number; stress_shielding: number }[] };
};
const CASO_HASTE = JSON.parse(readFileSync(resolve(APP_DIR, "dados", "caso_haste.json"), "utf-8")) as {
  perfis_referencia: Record<string, { descricao: string }>;
};
const nome = (m: string) => APP.nomes[m]?.nome ?? m;
const codigo = (m: string) => APP.nomes[m]?.codigo ?? "";
/** Texto com os espaços normalizados (o Intl usa espaços finos nos milhares). */
const limpo = (s: string) => s.replace(/[\s  ]+/g, " ").trim();

const MENU = [
  "Início",
  "Como funciona",
  "Haste femoral",
  "Stent",
  "Scaffold ósseo",
  "Gibson e Ashby",
  "Fichas dos materiais",
  "Base de triagem",
  "Doente",
  "Filtros",
  "Porquê",
  "Definições",
  "Sobre",
];

interface Problemas {
  consola: string[];
}

/** Regista erros e avisos da consola, erros da página e pedidos falhados (incluindo respostas 4xx e 5xx). */
function vigiar(page: Page): Problemas {
  const p: Problemas = { consola: [] };
  page.on("console", (m) => {
    // avisos do WebGL por software do Chromium sem GPU (do navegador de teste, não da aplicação)
    if (/GroupMarkerNotSet|GL Driver Message|software WebGL/.test(m.text())) return;
    if (m.type() === "error" || m.type() === "warning") p.consola.push(`[${m.type()}] ${m.text()}`);
  });
  page.on("pageerror", (e) => p.consola.push(`[pageerror] ${e.message}`));
  page.on("requestfailed", (r) => p.consola.push(`[requestfailed] ${r.url()} ${r.failure()?.errorText ?? ""}`));
  page.on("response", (r) => {
    if (r.status() >= 400) p.consola.push(`[http ${r.status()}] ${r.url()}`);
  });
  return p;
}

async function abrir(page: Page) {
  await page.goto("./");
  await expect(page.getByRole("navigation", { name: "Ecrãs" })).toBeVisible();
  // o núcleo WebAssembly carregou (sem ele aparece "Modo navegador: só o TOPSIS")
  await expect(page.getByText("Modo navegador: só o TOPSIS")).toHaveCount(0);
}

async function irPara(page: Page, texto: string) {
  const botao = page.getByRole("navigation", { name: "Ecrãs" }).getByRole("button", { name: texto, exact: true });
  await botao.click();
  await expect(botao).toHaveAttribute("aria-current", "page");
  await expect(page.locator("main h1")).toHaveCount(1);
  await esperarCalmo(page);
}

/** Espera que não haja esqueletos de carregamento e que as animações de entrada acabem. */
async function esperarCalmo(page: Page) {
  await expect(page.locator("main .animate-pulse")).toHaveCount(0, { timeout: 15_000 });
  await page.waitForTimeout(500);
}

/** Largura que transborda da janela (página inteira e área principal com deslocamento próprio). */
async function transbordo(page: Page) {
  return page.evaluate(() => {
    const doc = document.documentElement;
    const main = document.querySelector("main")!;
    const largos = [...document.querySelectorAll("main *")]
      .filter((e) => e.getBoundingClientRect().right > window.innerWidth + 1 && getComputedStyle(e).position !== "fixed")
      .filter((e) => !e.closest(".overflow-x-auto"))
      .slice(0, 5)
      .map((e) => `${e.tagName.toLowerCase()}.${String((e as HTMLElement).className).slice(0, 60)}`);
    return { pagina: doc.scrollWidth - doc.clientWidth, main: main.scrollWidth - main.clientWidth, largos };
  });
}

test.describe("versão web", () => {
  test("todos os ecrãs abrem sem erros, sem avisos e sem deslocamento horizontal", async ({ page }, info) => {
    const problemas = vigiar(page);
    await abrir(page);
    for (const texto of MENU) {
      await irPara(page, texto);
      const t = await transbordo(page);
      if (info.project.name === "telemovel") {
        expect(t, `deslocamento horizontal no ecrã ${texto}`).toEqual({ pagina: 0, main: 0, largos: [] });
      } else {
        expect(t.pagina, `deslocamento horizontal no ecrã ${texto}`).toBe(0);
      }
      expect(problemas.consola, `consola no ecrã ${texto}`).toEqual([]);
    }
  });

  for (const id of ["Haste", "Stent", "Scaffold"] as const) {
    test(`${id}: rankings e pontuações batem com results/pontuacoes.csv (cenários A e B)`, async ({ page }) => {
      const problemas = vigiar(page);
      await abrir(page);
      await irPara(page, { Haste: "Haste femoral", Stent: "Stent", Scaffold: "Scaffold ósseo" }[id]);
      const pont = lerCsv(resolve(RESULTS, "pontuacoes.csv")).filter((l) => l.caso === id);
      for (const cenario of ["A", "B"]) {
        if (cenario !== "A") {
          await page.getByRole("radio", { name: `Cenário ${cenario}` }).click();
          await esperarCalmo(page);
        }
        const g = pont.filter((l) => l.cenario === cenario);
        const colunas = [
          { titulo: "TOPSIS", pos: "pos_TOPSIS", v: "C_TOPSIS", rot: "C", casas: 3 },
          { titulo: "WASPAS", pos: "pos_WASPAS", v: "Q_WASPAS", rot: "Q", casas: 3 },
          { titulo: "VIKOR", pos: "pos_VIKOR", v: "P_VIKOR", rot: "P", casas: 3 },
          { titulo: "Consenso (Borda)", pos: "pos_Borda", v: "pontos_Borda", rot: "pontos", casas: 0 },
        ];
        for (const c of colunas) {
          const esperado = [...g]
            .sort((a, b) => Number(a[c.pos]) - Number(b[c.pos]) || pont.indexOf(a) - pont.indexOf(b))
            .map((l) => limpo(`${l[c.pos]}.º ${nome(l.material)} ${codigo(l.material)} ${c.rot} ${num(Number(l[c.v]), c.casas)}`));
          const regiao = page.getByRole("region", { name: `Ranking ${c.titulo}` });
          await expect
            .poll(async () => (await regiao.locator("li").allInnerTexts()).map(limpo), { message: `${id} ${cenario} ${c.titulo}` })
            .toEqual(esperado);
        }
      }
      expect(problemas.consola).toEqual([]);
    });
  }

  test("haste: o Monte Carlo em direto bate com o relatório (results/monte_carlo.csv)", async ({ page }) => {
    const problemas = vigiar(page);
    await abrir(page);
    await irPara(page, "Haste femoral");
    await page.getByRole("button", { name: "Correr" }).click();
    const tabela = page.locator("table").filter({ hasText: "app / relatório" });
    await expect(tabela).toBeVisible({ timeout: 60_000 });
    const celulas = await tabela.locator("tbody td.numero").allInnerTexts();
    expect(celulas.length).toBeGreaterThan(0);
    for (const t of celulas) {
      const [app, rel] = t.split("/").map((s) => Number(limpo(s).replace(" %", "").replace(",", ".")));
      expect(Math.abs(app - rel), `célula ${t}`).toBeLessThan(2);
    }
    // os números do relatório na tabela são os de results/monte_carlo.csv (% em 1.º, cenário A)
    const mc = lerCsv(resolve(RESULTS, "monte_carlo.csv")).filter((l) => l.caso === "Haste" && l.analise === "MC propriedades");
    const texto = limpo(await tabela.innerText());
    for (const l of mc) expect(texto).toContain(limpo(pct(Number(l.pct_primeiro))));
    expect(await transbordo(page).then((t) => t.pagina)).toBe(0);
    expect(problemas.consola).toEqual([]);
  });

  test("doente: o perfil H1 (jovem ativo) muda o vencedor do TOPSIS na haste, como em results/perfis_referencia.csv", async ({ page }) => {
    const problemas = vigiar(page);
    await abrir(page);
    await irPara(page, "Doente");
    const desc = CASO_HASTE.perfis_referencia.H1.descricao;
    await page.getByRole("button", { name: `H1: ${desc}` }).click();
    await expect(page.getByText("Com os dados do doente")).toBeVisible();
    await esperarCalmo(page);
    const linhas = lerCsv(resolve(RESULTS, "perfis_referencia.csv")).filter((l) => l.perfil === "H1");
    const esperado = [...linhas]
      .sort((a, b) => Number(a.pos_TOPSIS) - Number(b.pos_TOPSIS))
      .map((l) => limpo(`${l.pos_TOPSIS}.º ${nome(l.material)} ${codigo(l.material)} C ${num(Number(l.C_TOPSIS), 3)}`));
    const regiao = page.getByRole("region", { name: "Ranking TOPSIS" }).first();
    await expect.poll(async () => (await regiao.locator("li").allInnerTexts()).map(limpo)).toEqual(esperado);
    const vencedorRef = linhas.find((l) => l.pos_ref_TOPSIS === "1")!.material;
    const vencedor = linhas.find((l) => l.pos_TOPSIS === "1")!.material;
    expect(vencedor).not.toBe(vencedorRef);
    expect(await transbordo(page).then((t) => t.pagina)).toBe(0);
    expect(problemas.consola).toEqual([]);
  });

  test("Porquê: FEA da haste e CFD do stent batem com results/", async ({ page }) => {
    const problemas = vigiar(page);
    await abrir(page);
    await irPara(page, "Porquê");

    await page.getByRole("tab", { name: "FEA da haste" }).click();
    const fea = lerCsv(resolve(RESULTS, "fea_haste.csv"));
    const fina = Math.min(...fea.map((l) => Number(l.malha_mm)));
    const tabelaFea = page.locator("table").filter({ hasText: "Razão Gruen 1" });
    await expect(tabelaFea).toBeVisible();
    const textoFea = limpo(await tabelaFea.innerText());
    for (const l of fea.filter((x) => Number(x.malha_mm) === fina && x.material !== "Fémur intacto" && (x.zona === "1" || x.zona === "7"))) {
      expect(textoFea, `${l.material} zona ${l.zona}`).toContain(limpo(num(Number(l.razao), 2)));
      expect(textoFea, `${l.material} zona ${l.zona}`).toContain(limpo(pct(100 * Number(l.stress_shielding))));
      if (l.zona === "1" && l.E_haste_GPa) expect(textoFea).toContain(limpo(valor(Number(l.E_haste_GPa))));
    }

    await page.getByRole("tab", { name: "CFD do stent" }).click();
    const cfd = JSON.parse(readFileSync(resolve(RESULTS, "cfd_pulsatil.json"), "utf-8")) as Record<
      string,
      { espessura_um: number; tau_media: number; fracao_baixa: number; osi_media: number; fracao_osi: number }
    >;
    const tabelaCfd = page.locator("table").filter({ hasText: "TAWSS média" });
    await expect(tabelaCfd).toBeVisible();
    const linhasCfd = (await tabelaCfd.locator("tbody tr").allInnerTexts()).map(limpo);
    expect(linhasCfd.length).toBe(Object.keys(cfd).length);
    Object.values(cfd).forEach((r, k) => {
      for (const v of [num(r.espessura_um, 0), num(r.tau_media, 3), pct(100 * r.fracao_baixa), num(r.osi_media, 3), pct(100 * r.fracao_osi)])
        expect(linhasCfd[k]).toContain(limpo(v));
    });
    expect(problemas.consola).toEqual([]);
  });

  test("base de triagem: o total de materiais do caso bate com results/base_triagem.csv", async ({ page }) => {
    const problemas = vigiar(page);
    await abrir(page);
    await irPara(page, "Base de triagem");
    const base = lerCsv(resolve(RESULTS, "base_triagem.csv"));
    // o ecrã abre no caso da haste
    const n = new Set(base.filter((l) => l.caso === "haste").map((l) => l.chave)).size;
    await expect(page.locator("main")).toContainText(num(n, 0));
    expect(problemas.consola).toEqual([]);
  });
});

test.describe("correções da revisão de 10 out", () => {
  test("ranking a 1440 px: a pontuação não fica por cima do nome nem do código", async ({ page }, info) => {
    test.skip(info.project.name !== "computador", "largura de portátil");
    await abrir(page);
    for (const texto of ["Haste femoral", "Stent", "Scaffold ósseo"]) {
      await irPara(page, texto);
      const sobrepostos = await page.evaluate(() =>
        [...document.querySelectorAll("[data-pontuacao]")]
          .filter((s) => {
            const nome = s.closest("li")?.querySelector(".inline-flex.flex-col");
            if (!nome) return true;
            const a = s.getBoundingClientRect();
            const b = nome.getBoundingClientRect();
            return a.left < b.right - 0.5 && a.right > b.left && a.top < b.bottom && a.bottom > b.top;
          })
          .map((s) => s.textContent),
      );
      expect(sobrepostos, texto).toEqual([]);
      // nenhum nome de material partido palavra a palavra: cada nome cabe em duas linhas no máximo
      const alturas = await page.locator("main [data-pontuacao]").evaluateAll((els) =>
        els.map((s) => (s.closest("li")!.querySelector(".inline-flex.flex-col > span") as HTMLElement).getClientRects().length),
      );
      expect(Math.max(...alturas), texto).toBeLessThanOrEqual(2);
    }
  });

  test("ao mudar de ecrã o conteúdo volta ao topo, com o título visível", async ({ page }) => {
    await abrir(page);
    await esperarCalmo(page);
    await page.locator("main").evaluate((m) => m.scrollTo(0, 900));
    await expect.poll(() => page.locator("main").evaluate((m) => m.scrollTop)).toBeGreaterThan(0);
    await irPara(page, "Haste femoral");
    expect(await page.locator("main").evaluate((m) => m.scrollTop)).toBe(0);
    await expect(page.locator("main h1")).toBeInViewport();
  });

  test("cada ecrã tem endereço próprio e o botão Voltar regressa ao ecrã anterior", async ({ page }) => {
    await abrir(page);
    await irPara(page, "Stent");
    expect(page.url()).toMatch(/#\/stent$/);
    await irPara(page, "Doente");
    await page.goBack();
    await expect(page.locator("main h1")).toHaveText(/Stent/);
    await page.goBack();
    await expect(page.locator("main h1")).toHaveText("Que material pôr dentro do corpo?");
    await page.goto("./#/scaffold");
    await expect(page.locator("main h1")).toHaveText(/Scaffold/);
  });

  test("telemóvel: Porquê e Doente sem deslocamento horizontal em todos os separadores e passos", async ({ page }, info) => {
    test.skip(info.project.name !== "telemovel", "só no telemóvel");
    await abrir(page);
    await irPara(page, "Porquê");
    for (const tab of await page.getByRole("tab").all()) {
      await tab.click();
      await esperarCalmo(page);
      expect(await transbordo(page), `separador ${await tab.innerText()}`).toEqual({ pagina: 0, main: 0, largos: [] });
    }
    await irPara(page, "Doente");
    for (const passo of await page.getByRole("list", { name: "Passos" }).getByRole("button").all()) {
      await passo.click();
      await esperarCalmo(page);
      expect(await transbordo(page), `passo ${await passo.innerText()}`).toEqual({ pagina: 0, main: 0, largos: [] });
    }
  });

  test("telemóvel: espectro em lista legível e menu com rótulos por baixo dos ícones", async ({ page }, info) => {
    test.skip(info.project.name !== "telemovel", "só no telemóvel");
    await abrir(page);
    await expect(page.locator("main svg[aria-label^='Espectro']")).toBeHidden();
    const lista = page.getByRole("list", { name: /Espectro de confiança/ });
    await expect(lista).toBeVisible();
    await expect(lista.getByRole("listitem")).toHaveCount(5);
    const letra = await lista.getByRole("listitem").first().evaluate((li) => parseFloat(getComputedStyle(li).fontSize));
    expect(letra).toBeGreaterThanOrEqual(14);
    const nav = page.getByRole("navigation", { name: "Ecrãs" });
    for (const r of ["Início", "Haste", "Stent", "Porquê", "Sobre"]) await expect(nav.locator(`span:text-is("${r}"):visible`)).toHaveCount(1);
  });

  test("campos de pesquisa com foco visível pelo teclado", async ({ page }) => {
    await abrir(page);
    for (const texto of ["Fichas dos materiais", "Base de triagem"]) {
      await irPara(page, texto);
      const campo = page.getByRole("textbox", { name: "Procurar material" });
      await campo.focus();
      await page.keyboard.press("Shift+Tab");
      await page.keyboard.press("Tab");
      await expect(campo).toBeFocused();
      const sombra = await campo.evaluate((i) => getComputedStyle(i.closest("label")!).boxShadow);
      expect(sombra, texto).not.toBe("none");
    }
  });

  test("sem notas internas de trabalho visíveis ([confirmar], Estatuto, registar)", async ({ page }) => {
    await abrir(page);
    await irPara(page, "Gibson e Ashby");
    await expect(page.locator("main")).not.toContainText("confirmar");
    await irPara(page, "Fichas dos materiais");
    await page.getByRole("textbox", { name: "Procurar material" }).fill("Quitosano");
    await page.locator("main nav button").first().click();
    const fechados = page.locator("main ul button[aria-expanded=false]");
    while ((await fechados.count()) > 0) await fechados.first().click();
    const texto = await page.locator("main").innerText();
    expect(texto).not.toMatch(/\[confirmar|Estatuto \[|registar a porosidade|:\s*confirmar\b/);
    expect(texto).toContain("Muito dependente da geometria/porosidade");
  });

  test("Início: a frase do scaffold usa o 1.º do TOPSIS e as percentagens do Monte Carlo (results/monte_carlo.csv)", async ({ page }) => {
    await abrir(page);
    const mc = lerCsv(resolve(RESULTS, "monte_carlo.csv")).filter(
      (l) => l.caso === "Scaffold" && l.analise === "MC propriedades",
    );
    const topo = mc
      .filter((l) => l.metodo === "TOPSIS")
      .reduce((a, b) => (Number(b.pct_primeiro) > Number(a.pct_primeiro) ? b : a));
    const doTopo = mc.filter((l) => l.material === topo.material).map((l) => Number(l.pct_primeiro));
    const legenda = page.locator("main figcaption");
    // o 1.º do TOPSIS (cenário A) é também o que o TOPSIS põe mais vezes em 1.º: a frase não acrescenta "com o TOPSIS"
    await expect(legenda).toContainText(
      limpo(`${nome(topo.material)} fica em 1.º em ${pct(Math.min(...doTopo))} a ${pct(Math.max(...doTopo))}`),
    );
    await expect(legenda).not.toContainText("com o TOPSIS");
  });
});
