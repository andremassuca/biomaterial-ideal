// @vitest-environment jsdom
// Funções pequenas dos componentes: rótulos do gráfico do Monte Carlo, modelos 3D disponíveis e deteção de WebGL.
import { describe, expect, it } from "vitest";
import { rotulosEixo } from "../src/componentes/GraficoMC";
import { existeModelo, temWebGL } from "../src/componentes/Visualizador3D";
import { CASOS, nomeSimples } from "../src/lib/dados";

describe("rotulosEixo", () => {
  it("usa o nome simples quando não se repete", () => {
    const alt = CASOS.Haste.cenarios.A.alternativas;
    expect(rotulosEixo(alt)).toEqual(alt.map(nomeSimples));
  });

  it("acrescenta o código quando dois materiais têm o mesmo nome simples (scaffold, cenário B)", () => {
    const alt = CASOS.Scaffold.cenarios.B.alternativas;
    const r = rotulosEixo(alt);
    expect(new Set(r).size).toBe(alt.length);
    expect(r).toContain("Polímero (PCL)");
    expect(r).toContain("Polímero (PLLA)");
  });
});

describe("existeModelo", () => {
  it("só dá verdadeiro para os modelos da lista", () => {
    expect(existeModelo("haste", ["haste", "stent"])).toBe(true);
    expect(existeModelo("par", ["haste", "stent"])).toBe(false);
    expect(existeModelo("haste", [])).toBe(false);
  });

  it("a lista vem do vite.config.ts (public/modelos)", () => {
    expect(Array.isArray(__MODELOS_GLB__)).toBe(true);
  });
});

describe("temWebGL", () => {
  it("dá falso quando o navegador não cria contexto WebGL (o jsdom não tem)", () => {
    expect(temWebGL()).toBe(false);
  });
});

describe("decimalPt", () => {
  it("troca o ponto decimal por vírgula e deixa o resto igual", async () => {
    const { decimalPt } = await import("../src/lib/formato");
    expect(decimalPt("0.20")).toBe("0,20");
    expect(decimalPt("peso 0.20 (custo) e 2")).toBe("peso 0,20 (custo) e 2");
    expect(decimalPt("Fim. Início")).toBe("Fim. Início");
    expect(decimalPt(null)).toBe("");
  });
});
