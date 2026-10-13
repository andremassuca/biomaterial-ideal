// @vitest-environment jsdom
// Testes do ecrã "Comparar materiais": funções puras (src/lib/comparar.ts) e componentes.
import { cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, beforeAll, describe, expect, it, vi } from "vitest";
import { LinhaComparar, regraCriterio } from "../src/componentes/comparar/LinhaComparar";
import { RadarComparacao, dadosRadar, rotuloCurto } from "../src/componentes/comparar/RadarComparacao";
import {
  compararMateriais,
  diferenca,
  fracaoBarra,
  linhasDoCaso,
  melhorLado,
  pontuacaoRadar,
  resumoComparacao,
  temValor,
  valorDoProblema,
} from "../src/lib/comparar";
import { CASOS, fichaMaterial } from "../src/lib/dados";
import type { LinhaMaterial, Problema } from "../src/lib/tipos";
import { Comparar } from "../src/ecras/Comparar";

afterEach(cleanup);

beforeAll(() => {
  class Obs {
    observe() {}
    unobserve() {}
    disconnect() {}
  }
  vi.stubGlobal("ResizeObserver", Obs);
});

const problema: Problema = {
  alternativas: ["X", "Y", "Z"],
  criterios: ["Rigidez", "Custo", "Módulo"],
  tipos: ["benefit", "cost", "target"],
  alvos: [null, null, 17],
  pesos: [0.4, 0.3, 0.3],
  x_min: [[1, 1, 10], [2, 4, 20], [3, 5, 30]],
  x_max: [[1, 1, 10], [2, 4, 20], [3, 5, 30]],
  x_tipico: [[1, 3, 10], [2, 4, 20], [3, 5, 30]],
  ordinal: [false, true, false],
};

describe("melhorLado", () => {
  it("benefit: ganha o maior", () => {
    expect(melhorLado("benefit", 5, 3)).toBe("a");
    expect(melhorLado("benefit", 3, 5)).toBe("b");
  });
  it("cost: ganha o menor", () => {
    expect(melhorLado("cost", 5, 3)).toBe("b");
    expect(melhorLado("cost", 3, 5)).toBe("a");
  });
  it("target: ganha o mais perto do alvo", () => {
    expect(melhorLado("target", 10, 30, 17)).toBe("a");
    expect(melhorLado("target", 20, 10, 17)).toBe("a");
    expect(melhorLado("target", 14, 20, 17)).toBe("empate");
  });
  it("empate quando valem o mesmo", () => {
    expect(melhorLado("benefit", 2, 2)).toBe("empate");
    expect(melhorLado("cost", 0.1 + 0.2, 0.3)).toBe("empate");
  });
  it("valores em falta ou critério-alvo sem alvo: não se compara", () => {
    expect(melhorLado("benefit", null, 3)).toBeNull();
    expect(melhorLado("cost", 3, NaN)).toBeNull();
    expect(melhorLado("target", 3, 4, null)).toBeNull();
  });
});

describe("diferenca", () => {
  it("absoluta e relativa ao maior módulo", () => {
    expect(diferenca(50, 100)).toEqual({ absoluta: 50, relativa: 0.5 });
    expect(diferenca(-4, 4)).toEqual({ absoluta: 8, relativa: 2 });
  });
  it("zero e zero: relativa nula; em falta: nada", () => {
    expect(diferenca(0, 0)).toEqual({ absoluta: 0, relativa: null });
    expect(diferenca(null, 3)).toBeNull();
  });
});

describe("resumoComparacao, fracaoBarra, temValor", () => {
  it("conta vitórias, empates e não comparáveis", () => {
    const r = resumoComparacao(["a", "a", "b", "empate", null]);
    expect(r).toEqual({ a: 2, b: 1, empates: 1, comparaveis: 4, total: 5 });
  });
  it("a barra usa o maior módulo dos dois como 100 %", () => {
    expect(fracaoBarra(50, 50, 100)).toBe(0.5);
    expect(fracaoBarra(100, 50, 100)).toBe(1);
    expect(fracaoBarra(null, 50, 100)).toBe(0);
    expect(fracaoBarra(5, 0, 0)).toBe(0);
  });
  it("temValor", () => {
    expect(temValor(0)).toBe(true);
    expect(temValor(null)).toBe(false);
    expect(temValor(Infinity)).toBe(false);
  });
});

describe("pontuacaoRadar", () => {
  it("benefit, cost e target ficam entre 0 e 1", () => {
    expect(pontuacaoRadar("benefit", 3, [1, 2, 3])).toBe(1);
    expect(pontuacaoRadar("benefit", 1, [1, 2, 3])).toBe(0);
    expect(pontuacaoRadar("cost", 1, [1, 2, 3])).toBe(1);
    expect(pontuacaoRadar("target", 17, [10, 17, 30], 17)).toBe(1);
    expect(pontuacaoRadar("target", 30, [10, 17, 30], 17)).toBe(0);
  });
  it("em falta: null; todos iguais: 1", () => {
    expect(pontuacaoRadar("benefit", null, [1, 2])).toBeNull();
    expect(pontuacaoRadar("benefit", 2, [2, 2])).toBe(1);
    expect(pontuacaoRadar("target", 2, [2, 3], null)).toBeNull();
  });
});

describe("compararMateriais e valorDoProblema", () => {
  it("lê os valores e decide quem é melhor por critério", () => {
    const l = compararMateriais(problema, "X", "Z", [], []);
    expect(l.map((x) => x.melhor)).toEqual(["b", "a", "a"]);
    expect(l[0].diferenca?.absoluta).toBe(2);
    expect(valorDoProblema(problema, "Y", "Custo")).toEqual({ tipico: 4, min: 4, max: 4 });
  });
  it("material ou critério desconhecido: sem valor", () => {
    expect(valorDoProblema(problema, "W", "Custo").tipico).toBeNull();
    const l = compararMateriais(problema, "X", "W", [], []);
    expect(l.every((x) => x.melhor === null && x.diferenca === null)).toBe(true);
  });
  it("valor ausente (null) numa matriz não vira zero", () => {
    const p = { ...problema, x_tipico: [[null as unknown as number, 3, 10], ...problema.x_tipico.slice(1)] };
    expect(valorDoProblema(p, "X", "Rigidez").tipico).toBeNull();
    expect(compararMateriais(p, "X", "Y", [], [])[0].melhor).toBeNull();
  });
});

describe("linhasDoCaso", () => {
  const l = (componente: string, propriedade: string) => ({ componente, propriedade }) as LinhaMaterial;
  it("escolhe o componente que cobre mais critérios", () => {
    const linhas = [l("Stent", "A"), l("Haste", "A"), l("Haste", "B"), l("Haste", "C")];
    expect(linhasDoCaso(linhas, ["A", "B"]).every((x) => x.componente === "Haste")).toBe(true);
    expect(linhasDoCaso(linhas, ["Z"])).toEqual([]);
  });
});

describe("dados verdadeiros", () => {
  it("todos os casos comparam dois materiais com uma linha por critério", () => {
    for (const caso of Object.values(CASOS)) {
      const p = Object.values(caso.cenarios).at(-1)!;
      const [a, b] = p.alternativas;
      const linhas = compararMateriais(p, a, b, linhasDoCaso(fichaMaterial(a), p.criterios), linhasDoCaso(fichaMaterial(b), p.criterios));
      expect(linhas.length).toBe(p.criterios.length);
      expect(linhas.some((x) => x.fichaA)).toBe(true);
    }
  });
});

describe("componentes", () => {
  it("regraCriterio descreve benefit, cost e target", () => {
    expect(regraCriterio({ tipo: "benefit", alvo: null, unidade: null })).toBe("maior é melhor");
    expect(regraCriterio({ tipo: "cost", alvo: null, unidade: null })).toBe("menor é melhor");
    expect(regraCriterio({ tipo: "target", alvo: 17, unidade: "GPa" })).toContain("alvo (17");
  });

  it("LinhaComparar mostra 'Sem valor na base' e a melhor etiqueta", () => {
    const linhas = compararMateriais(problema, "X", "W", [], []);
    render(<ul><LinhaComparar linha={linhas[0]} /></ul>);
    expect(screen.getByText("Sem valor na base")).toBeTruthy();
    cleanup();
    const ok = compararMateriais(problema, "X", "Z", [], []);
    render(<ul><LinhaComparar linha={ok[0]} /></ul>);
    expect(screen.getByText("Melhor")).toBeTruthy();
    expect(screen.getByText(/Diferença:/)).toBeTruthy();
  });

  it("rotuloCurto e dadosRadar", () => {
    expect(rotuloCurto("Fabricabilidade (ordinal 1-5)")).toBe("Fabricabilidade");
    const d = dadosRadar(problema, "X", "Z");
    expect(d.length).toBe(3);
    expect(d[0].b).toBe(1);
  });

  it("RadarComparacao desenha com a etiqueta acessível", () => {
    render(<RadarComparacao problema={problema} a="X" b="Y" />);
    expect(screen.getByRole("img").getAttribute("aria-label")).toContain("Radar");
  });

  it("ecrã: resumo, troca de materiais e ranking", async () => {
    render(<Comparar />);
    const resumo = screen.getByRole("region", { name: "Resumo da comparação" });
    expect(within(resumo).getByText(/propriedades comparáveis/)).toBeTruthy();
    const selA = screen.getByLabelText("Material A") as HTMLSelectElement;
    const selB = screen.getByLabelText("Material B") as HTMLSelectElement;
    const [a0, b0] = [selA.value, selB.value];
    fireEvent.click(screen.getByRole("button", { name: "Trocar os dois materiais" }));
    expect(selA.value).toBe(b0);
    expect(selB.value).toBe(a0);
    await waitFor(() => expect(document.querySelector("[data-ranking='A']")!.textContent).toMatch(/\d\.º|n\.d\./));
    fireEvent.change(selB, { target: { value: selA.value } });
    expect(screen.getByText("Escolheu o mesmo material nos dois lados.")).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Mostrar o radar" }));
    expect(screen.getByRole("img", { name: /Radar/ })).toBeTruthy();
  });

  it("ecrã: mudar de caso muda a lista de materiais", () => {
    render(<Comparar />);
    fireEvent.change(screen.getByLabelText("Caso"), { target: { value: "Stent" } });
    const opcoes = [...(screen.getByLabelText("Material A") as HTMLSelectElement).options].length;
    const cenarioCompleto = Object.values(CASOS.Stent.cenarios).reduce((m, p) => Math.max(m, p.alternativas.length), 0);
    expect(opcoes).toBe(cenarioCompleto);
  });
});

describe("rotuloMaterial", () => {
  it("junta o código ao nome simples e distingue materiais com o mesmo nome", async () => {
    const { rotuloMaterial, nomeSimples } = await import("../src/lib/dados");
    expect(nomeSimples("PCL")).toBe(nomeSimples("PLLA"));
    expect(rotuloMaterial("PCL")).not.toBe(rotuloMaterial("PLLA"));
    expect(rotuloMaterial("PLLA")).toBe(`${nomeSimples("PLLA")} (PLLA)`);
    // material sem código (por exemplo, um material do utilizador): só o nome
    expect(rotuloMaterial("Liga X (definido pelo utilizador)")).toBe("Liga X (definido pelo utilizador)");
  });
});
