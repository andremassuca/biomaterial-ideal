// @vitest-environment jsdom
// Testes da análise guardável, do histórico local, do relatório em PDF e do ecrã Histórico.
import { act, cleanup, fireEvent, render, screen, within } from "@testing-library/react";
import { afterEach, beforeAll, beforeEach, describe, expect, it, vi } from "vitest";
import { iniciarWasm } from "./apoio_wasm";

beforeAll(() => {
  iniciarWasm();
  vi.stubGlobal("fetch", async () => new Response("", { status: 404, headers: { "content-type": "text/html" } }));
});

beforeEach(() => {
  localStorage.clear();
});

afterEach(async () => {
  cleanup();
  const { fecharRelatorio } = await import("../src/lib/relatorio");
  fecharRelatorio();
});

/** Análise real do caso da haste, calculada pelo núcleo WebAssembly. */
async function analiseHaste(agora = new Date("2026-10-13T17:00:00Z")) {
  const { prepararNucleo, avaliarCaso } = await import("../src/lib/nucleo");
  const { CASOS } = await import("../src/lib/dados");
  const { criarAnalise } = await import("../src/lib/analise");
  await prepararNucleo();
  const r = await avaliarCaso({ caso: "Haste", cenario: "A" });
  return criarAnalise({
    caso: "Haste",
    cenario: "A",
    problemaBase: CASOS.Haste.cenarios.A,
    problemaUsado: r.problema,
    ranking: r.ranking,
    eta: 1,
  }, agora);
}

describe("análise", () => {
  it("a impressão digital é estável e muda com o texto", async () => {
    const { impressaoDigital } = await import("../src/lib/analise");
    expect(impressaoDigital("abc")).toBe(impressaoDigital("abc"));
    expect(impressaoDigital("abc")).not.toBe(impressaoDigital("abd"));
    expect(impressaoDigital("")).toMatch(/^[0-9a-f]{8}$/);
  });

  it("a versão dos dados tem 8 caracteres e é sempre a mesma", async () => {
    const { versaoDados } = await import("../src/lib/analise");
    expect(versaoDados()).toMatch(/^[0-9a-f]{8}$/);
    expect(versaoDados()).toBe(versaoDados());
  });

  it("criarAnalise guarda data, versões, pesos que somam 1 e o 1.º lugar de cada método", async () => {
    const { primeiros, versaoDados } = await import("../src/lib/analise");
    const a = await analiseHaste();
    expect(a.criadaEm).toBe("2026-10-13T17:00:00.000Z");
    expect(a.versaoDados).toBe(versaoDados());
    expect(a.perfil).toBeNull();
    expect(a.criterios.reduce((s, c) => s + c.peso, 0)).toBeCloseTo(1, 9);
    expect(a.criterios.every((c) => !c.novo && c.pesoBase !== null)).toBe(true);
    expect(primeiros(a.ranking).map((p) => p.metodo)).toEqual(["TOPSIS", "WASPAS", "VIKOR", "Borda"]);
  });

  it("criteriosAnalise marca como novo um critério que não existe na base", async () => {
    const { criteriosAnalise } = await import("../src/lib/analise");
    const { CASOS } = await import("../src/lib/dados");
    const base = CASOS.Haste.cenarios.A;
    const usado = { ...base, criterios: [...base.criterios, "Teor de níquel"], tipos: [...base.tipos, "cost" as const], alvos: [...base.alvos, null], pesos: [...base.pesos, 0.1] };
    const c = criteriosAnalise(base, usado);
    expect(c[c.length - 1]).toMatchObject({ nome: "Teor de níquel", novo: true, pesoBase: null });
  });
});

describe("histórico local", () => {
  it("guarda, lê, remove e limpa", async () => {
    const h = await import("../src/lib/historico");
    const a = await analiseHaste();
    expect(h.lerHistorico()).toEqual([]);
    h.guardarAnalise(a);
    expect(h.lerHistorico().map((x) => x.id)).toEqual([a.id]);
    h.removerAnalise(a.id);
    expect(h.lerHistorico()).toEqual([]);
    h.guardarAnalise(a);
    h.limparHistorico();
    expect(h.lerHistorico()).toEqual([]);
  });

  it("a análise mais recente fica primeiro e o máximo é respeitado", async () => {
    const h = await import("../src/lib/historico");
    const a = await analiseHaste();
    for (let i = 0; i < h.MAXIMO_HISTORICO + 5; i++) h.guardarAnalise({ ...a, id: `x${i}` });
    const lista = h.lerHistorico();
    expect(lista).toHaveLength(h.MAXIMO_HISTORICO);
    expect(lista[0].id).toBe(`x${h.MAXIMO_HISTORICO + 4}`);
  });

  it("ignora dados estragados ou de formato antigo", async () => {
    const h = await import("../src/lib/historico");
    localStorage.setItem("biomat.historico", "isto não é JSON");
    expect(h.lerHistorico()).toEqual([]);
    localStorage.setItem("biomat.historico", JSON.stringify([{ id: 1 }, null, "x"]));
    expect(h.lerHistorico()).toEqual([]);
    expect(h.analiseValida({})).toBe(false);
  });

  it("avisa quem está à escuta quando o histórico muda", async () => {
    const h = await import("../src/lib/historico");
    const a = await analiseHaste();
    const f = vi.fn();
    const parar = h.aoMudarHistorico(f);
    h.guardarAnalise(a);
    expect(f).toHaveBeenCalled();
    parar();
  });
});

describe("relatório", () => {
  it("estadoBase agrupa 'Verificado (fornecedor)' em 'Verificado'", async () => {
    const { estadoBase } = await import("../src/lib/relatorio");
    expect(estadoBase("Verificado (fornecedor)")).toBe("Verificado");
    expect(estadoBase("A verificar")).toBe("A verificar");
    expect(estadoBase(null)).toBe("Sem estado");
  });

  it("contagemEstados conta os valores da base de cada material", async () => {
    const { contagemEstados } = await import("../src/lib/relatorio");
    const a = await analiseHaste();
    const c = contagemEstados("Haste", a.ranking.alternativas);
    expect(c).toHaveLength(a.ranking.alternativas.length);
    for (const x of c) expect(Object.values(x.porEstado).reduce((s, n) => s + n, 0)).toBe(x.total);
    expect(c.some((x) => x.total > 0)).toBe(true);
  });

  it("a folha mostra caso, pesos, rankings, Monte Carlo em falta, fontes, limitações e o aviso", async () => {
    const { Relatorio, LIMITACOES } = await import("../src/componentes/Relatorio");
    const { TEXTO_AVISO } = await import("../src/componentes/comuns");
    const a = await analiseHaste();
    render(<Relatorio analise={a} />);
    const folha = document.querySelector("[data-relatorio]") as HTMLElement;
    expect(folha).not.toBeNull();
    expect(within(folha).getByRole("heading", { level: 1 }).textContent).toBe("Haste femoral");
    for (const t of ["Perfil do doente", "Pesos dos critérios", "Rankings", "Robustez: Monte Carlo", "Fontes e estado dos dados", "Limitações"]) {
      expect(within(folha).getByRole("heading", { name: t })).toBeTruthy();
    }
    expect(folha.textContent).toContain(TEXTO_AVISO);
    expect(folha.textContent).toContain(a.versaoDados);
    expect(folha.textContent).toContain("O Monte Carlo não foi corrido");
    expect(folha.textContent).toContain("Petković");
    for (const l of LIMITACOES) expect(folha.textContent).toContain(l);
    expect(folha.textContent).not.toContain("—");
  });

  it("o modal abre com abrirRelatorio e fecha com o botão", async () => {
    const { ModalRelatorio } = await import("../src/componentes/Relatorio");
    const { abrirRelatorio } = await import("../src/lib/relatorio");
    const a = await analiseHaste();
    render(<ModalRelatorio />);
    expect(screen.queryByRole("dialog")).toBeNull();
    await act(async () => abrirRelatorio(a));
    expect(screen.getByRole("dialog", { name: "Relatório da análise" })).toBeTruthy();
    const imprimir = vi.fn();
    vi.stubGlobal("print", imprimir);
    fireEvent.click(screen.getByRole("button", { name: /Imprimir ou guardar em PDF/ }));
    expect(imprimir).toHaveBeenCalled();
    fireEvent.click(screen.getByRole("button", { name: "Fechar o relatório" }));
    expect(screen.queryByRole("dialog")).toBeNull();
  });
});

describe("ecrã Histórico", () => {
  it("mostra a mensagem vazia e depois a análise guardada, e permite apagar", async () => {
    const { Historico, resumoPerfil } = await import("../src/ecras/Historico");
    const { guardarAnalise } = await import("../src/lib/historico");
    const a = await analiseHaste();
    expect(resumoPerfil(a)).toBe("Sem perfil");
    render(<Historico />);
    expect(screen.getByText(/Ainda não há análises guardadas/)).toBeTruthy();
    await act(async () => {
      guardarAnalise(a);
    });
    expect(screen.getByText(/Haste femoral/)).toBeTruthy();
    expect(screen.getAllByText(new RegExp(a.versaoDados)).length).toBeGreaterThan(0);
    fireEvent.click(screen.getByRole("button", { name: "Apagar esta análise" }));
    expect(screen.getByText(/Ainda não há análises guardadas/)).toBeTruthy();
  });

  it("avisa quando os dados mudaram desde a análise", async () => {
    const { Historico } = await import("../src/ecras/Historico");
    const { guardarAnalise } = await import("../src/lib/historico");
    const a = await analiseHaste();
    guardarAnalise({ ...a, versaoDados: "00000000" });
    render(<Historico />);
    expect(screen.getByText(/Os dados mudaram desde esta análise/)).toBeTruthy();
  });
});
