// @vitest-environment jsdom
// Funções novas das correções da revisão: endereço de cada ecrã, marcas do eixo de Gibson e Ashby, frase do espectro
// e nota da fixação no doente com osteoporose.
import { describe, expect, it } from "vitest";
import { fraseEspectro, outroMaisFrequenteTopsis, posicoesRotulos } from "../src/componentes/Espectro";
import { notaFixacao, sensibilidadePerfil } from "../src/ecras/Doente";
import { marcasEixo } from "../src/ecras/GibsonAshby";
import { APP, RECOMENDACAO, RECOMENDACAO_CURTA, semPrefixo } from "../src/lib/dados";
import { ECRAS, ecraDoHash, hashDoEcra } from "../src/lib/navegacao";
import type { Ranking, RespostaDoente } from "../src/lib/tipos";

describe("endereço de cada ecrã", () => {
  it("lê o ecrã do endereço e volta ao Início quando é vazio ou desconhecido", () => {
    expect(ecraDoHash("#/stent")).toBe("stent");
    expect(ecraDoHash("#stent")).toBe("stent");
    expect(ecraDoHash("#/Scaffold")).toBe("scaffold");
    expect(ecraDoHash("")).toBe("inicio");
    expect(ecraDoHash("#/nada")).toBe("inicio");
  });

  it("ida e volta para todos os ecrãs", () => {
    for (const e of ECRAS) expect(ecraDoHash(hashDoEcra(e))).toBe(e);
  });
});

describe("marcasEixo", () => {
  it("dá marcas regulares acima do máximo (Ti-6Al-4V, 105,5 GPa)", () => {
    expect(marcasEixo(105.5 * 1.05)).toEqual({ max: 125, marcas: [0, 25, 50, 75, 100, 125] });
  });
  it("aço e Co-Cr (cerca de 225 GPa) com passo de 50", () => {
    expect(marcasEixo(225 * 1.05).marcas).toEqual([0, 50, 100, 150, 200, 250]);
  });
  it("valores pequenos não dão um eixo vazio", () => {
    expect(marcasEixo(3).max).toBeGreaterThanOrEqual(3);
  });
});

describe("frase do espectro", () => {
  const scaffold = APP.espectro.find((c) => c.caso === "Scaffold")!;
  const haste = APP.espectro.find((c) => c.caso === "Haste")!;

  it("no scaffold o vencedor (TOPSIS, cenário A) é também o mais frequente no Monte Carlo, e a frase não acrescenta nada", () => {
    const linhas = APP.monte_carlo_referencia.filter((l) => l.caso === "Scaffold" && l.analise === "MC propriedades" && l.metodo === "TOPSIS");
    const topo = linhas.reduce((a, b) => (b.pct_primeiro > a.pct_primeiro ? b : a));
    expect(topo.material).toBe(scaffold.vencedor);
    expect(outroMaisFrequenteTopsis("Scaffold", scaffold.vencedor)).toBeNull();
    expect(fraseEspectro(scaffold)).not.toContain("com o TOPSIS");
  });

  it("quando o vencedor não é o mais frequente, diz qual é, com o número de results/monte_carlo.csv", () => {
    const linhas = APP.monte_carlo_referencia.filter((l) => l.caso === "Scaffold" && l.analise === "MC propriedades" && l.metodo === "TOPSIS");
    const topo = linhas.reduce((a, b) => (b.pct_primeiro > a.pct_primeiro ? b : a));
    const outroMaterial = linhas.find((l) => l.material !== topo.material)!.material;
    expect(outroMaisFrequenteTopsis("Scaffold", outroMaterial)).toEqual({ material: topo.material, pct: topo.pct_primeiro });
    expect(fraseEspectro({ ...scaffold, vencedor: outroMaterial })).toMatch(/com o TOPSIS, .+ fica em 1\.º mais vezes \(\d+ %\)\.$/);
  });

  it("na haste não acrescenta nada (o vencedor é também o mais frequente)", () => {
    expect(outroMaisFrequenteTopsis("Haste", haste.vencedor)).toBeNull();
    expect(fraseEspectro(haste)).not.toContain("com o TOPSIS");
  });
});

describe("nota da fixação", () => {
  it("só aparece na haste e com osteoporose", () => {
    expect(notaFixacao("Haste", { osteoporose: "sim" })).toBe(true);
    expect(notaFixacao("Haste", { osteoporose: "não" })).toBe(false);
    expect(notaFixacao("Haste", {})).toBe(false);
    expect(notaFixacao("Stent", { osteoporose: "sim" })).toBe(false);
  });
});

describe("recomendação do stent e do scaffold (decisões D1 e D7)", () => {
  it("usa as frases aprovadas, sem alterações", () => {
    expect(RECOMENDACAO.Stent).toBe(
      "Pt-Cr e L605 praticamente equivalentes: o Pt-Cr é favorecido pelo TOPSIS, pelo VIKOR e pela radiopacidade; o L605 pelo WASPAS e por ter todas as propriedades em fichas de fornecedor. Sem vencedor universal.",
    );
    expect(RECOMENDACAO.Scaffold).toBe(
      "Depende da carga: compósito PCL/β-TCP impresso quando o defeito suporta carga (1.º no ranking direto em 5 das 6 combinações); β-TCP poroso quando não suporta (mais vezes 1.º na incerteza dos dados).",
    );
  });
  it("as frases batem com o 1.º e o 2.º do espectro (cenário A)", () => {
    const e = Object.fromEntries(APP.espectro.map((c) => [c.caso, c]));
    expect(e.Stent.vencedor).toBe("Pt-Cr");
    expect(e.Stent.segundo).toBe("Co-Cr L605");
    // a frase do scaffold nomeia os dois primeiros (o 1.º do TOPSIS no cenário A é o β-TCP poroso, ΔC pequeno)
    expect([e.Scaffold.vencedor, e.Scaffold.segundo].sort()).toEqual(["Compósito PCL/β-TCP (impressão 3D)", "β-TCP poroso"].sort());
  });
  it("não há recomendação escrita à mão para os outros casos", () => {
    expect(Object.keys(RECOMENDACAO).sort()).toEqual(["Scaffold", "Stent"]);
    expect(Object.keys(RECOMENDACAO_CURTA).sort()).toEqual(["Scaffold", "Stent"]);
  });
  it("versões curtas iguais às da apresentação; sem o prefixo, o resto fica igual", () => {
    expect(RECOMENDACAO_CURTA.Stent).toBe("Stent: Pt-Cr e L605 praticamente equivalentes");
    expect(RECOMENDACAO_CURTA.Scaffold).toBe("Scaffold: depende da carga (compósito com carga; β-TCP sem carga)");
    expect(semPrefixo(RECOMENDACAO_CURTA.Stent!)).toBe("Pt-Cr e L605 praticamente equivalentes");
    expect(semPrefixo(RECOMENDACAO_CURTA.Scaffold!)).toBe("depende da carga (compósito com carga; β-TCP sem carga)");
    expect(semPrefixo("sem prefixo")).toBe("sem prefixo");
  });
});

describe("rótulos do espectro", () => {
  it("afasta rótulos do mesmo lado que ficavam juntos e não mexe nos do outro lado", () => {
    const r = posicoesRotulos([800, 790, 810], [true, false, true], 200, 100, 900);
    expect(r[1]).toBe(790);
    expect(r[2] - r[0]).toBeGreaterThanOrEqual(200);
    expect(Math.max(...r)).toBeLessThanOrEqual(900);
  });
  it("não sai das margens", () => {
    expect(posicoesRotulos([20, 990], [true, true], 100, 100, 900)).toEqual([100, 900]);
  });
  it("com os dados reais, os rótulos do mesmo lado ficam afastados", () => {
    const max = Math.max(...APP.espectro.map((c) => c.delta_c));
    const xs = APP.espectro.map((c) => 110 + ((max - c.delta_c) / max) * 780);
    const lado = APP.espectro.map((_, i) => i % 2 === 0);
    const r = posicoesRotulos(xs, lado, 210, 100, 900);
    for (let i = 0; i < r.length; i++)
      for (let j = i + 1; j < r.length; j++) if (lado[i] === lado[j]) expect(Math.abs(r[i] - r[j])).toBeGreaterThanOrEqual(210);
  });
});

describe("sensibilidade do perfil na haste", () => {
  const ranking = (alternativas: string[], pos_topsis: number[]): Ranking =>
    ({ alternativas, pos_topsis } as unknown as Ranking);
  const resposta = (base: number[], doente: number[]): RespostaDoente =>
    ({
      base: ranking(["Ti-6Al-4V ELI", "Co-Cr-Mo forjado"], base),
      resultado: { ranking: ranking(["Ti-6Al-4V ELI", "Co-Cr-Mo forjado"], doente) },
    } as unknown as RespostaDoente);
  it("mostra o novo 1.º do TOPSIS quando muda na haste (jovem ativo, H1)", () => {
    expect(sensibilidadePerfil("Haste", resposta([1, 2], [2, 1]))).toBe("Co-Cr-Mo forjado");
  });
  it("nada quando não muda ou noutro caso", () => {
    expect(sensibilidadePerfil("Haste", resposta([1, 2], [1, 2]))).toBeNull();
    expect(sensibilidadePerfil("Stent", resposta([1, 2], [2, 1]))).toBeNull();
  });
});
