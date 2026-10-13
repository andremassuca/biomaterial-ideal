// @vitest-environment jsdom
// Painel de impacto do ecrã Doente: funções puras (pesos, exclusões, posições, efeito das regras) e o painel com o
// núcleo WebAssembly verdadeiro (regra S-NI do stent, recálculo ao mudar um campo, aviso sempre visível).
import { act, cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterAll, beforeAll, describe, expect, it, vi } from "vitest";
import type { Problema, Ranking, Regra } from "../src/lib/tipos";
import { iniciarWasm } from "./apoio_wasm";

type Painel = typeof import("../src/componentes/doente/PainelImpacto");
let P: Painel;
let Prov: typeof import("../src/lib/definicoes")["ProvedorDefinicoes"];
let Dicas: typeof import("../src/componentes/ui/controlos")["ProvedorDicas"];
let Doente: typeof import("../src/ecras/Doente")["Doente"];

beforeAll(async () => {
  iniciarWasm();
  vi.stubGlobal("fetch", async () => new Response("", { status: 404, headers: { "content-type": "text/html" } }));
  vi.stubGlobal(
    "matchMedia",
    (q: string) =>
      ({ matches: false, media: q, onchange: null, addEventListener() {}, removeEventListener() {}, addListener() {}, removeListener() {}, dispatchEvent: () => false }) as MediaQueryList,
  );
  const { prepararNucleo } = await import("../src/lib/nucleo");
  await prepararNucleo();
  P = await import("../src/componentes/doente/PainelImpacto");
  ({ Doente } = await import("../src/ecras/Doente"));
  ({ ProvedorDicas: Dicas } = await import("../src/componentes/ui/controlos"));
  ({ ProvedorDefinicoes: Prov } = await import("../src/lib/definicoes"));
});

afterAll(() => {
  cleanup();
  vi.unstubAllGlobals();
});

const problema = (criterios: string[], pesos: number[]): Problema => ({
  alternativas: [],
  criterios,
  tipos: criterios.map(() => "benefit" as const),
  alvos: criterios.map(() => null),
  pesos,
  x_min: [],
  x_max: [],
  x_tipico: [],
  ordinal: criterios.map(() => false),
});

const regra = (extra: Partial<Regra>): Regra => ({
  id: "X",
  dispositivo: "Stent",
  condicao: null,
  condicao_codigo: "c=sim",
  efeito: "nota",
  alvo_do_efeito: "texto",
  valor: null,
  justificacao: null,
  fonte: null,
  doi_url: null,
  estado: null,
  ...extra,
});

describe("funções do painel de impacto", () => {
  it("variacaoPesos distingue novo, sobe, desce, igual e removido", () => {
    const antes = problema(["A", "B", "C", "D"], [0.4, 0.3, 0.2, 0.1]);
    const depois = problema(["A", "B", "C", "N"], [0.5, 0.2, 0.2, 0.1]);
    const r = P.variacaoPesos(antes, depois);
    const estado = Object.fromEntries(r.map((l) => [l.criterio, l.estado]));
    expect(estado).toEqual({ A: "sobe", B: "desce", C: "igual", N: "novo", D: "removido" });
    expect(r.find((l) => l.criterio === "N")?.antes).toBeNull();
    expect(r.find((l) => l.criterio === "D")?.depois).toBeNull();
  });

  it("descreverEfeito usa o valor e o alvo da regra", () => {
    expect(P.descreverEfeito(regra({ efeito: "critério acrescentado", alvo_do_efeito: "Teor", valor: "0,2" }))).toBe(
      "entra “Teor” com peso 0,2 (valor de desenho)",
    );
    expect(P.descreverEfeito(regra({ efeito: "exclusão", alvo_do_efeito: "M1; M2" }))).toBe("saem: M1; M2");
    expect(P.descreverEfeito(regra({ efeito: "nota", alvo_do_efeito: "só texto" }))).toBe("só texto");
  });

  it("regraQueExclui encontra a regra que nomeia o material", () => {
    const a = regra({ id: "A", efeito: "exclusão", alvo_do_efeito: "M1; M2" });
    const b = regra({ id: "B", efeito: "exclusão", alvo_do_efeito: "M3" });
    expect(P.regraQueExclui("M2", [a, b])?.id).toBe("A");
    expect(P.regraQueExclui("M3", [a, b])?.id).toBe("B");
    expect(P.regraQueExclui("M9", [a, b])).toBeNull();
    expect(P.regraQueExclui("M9", [b])?.id).toBe("B");
    expect(P.regraQueExclui("M1", [regra({})])).toBeNull();
  });

  it("mudancasPosicao lista só quem muda de posição ou sai", () => {
    const r = (alt: string[], borda: number[]) => ({ alternativas: alt, pos_borda: borda }) as unknown as Ranking;
    const m = P.mudancasPosicao(r(["a", "b", "c"], [1, 2, 3]), r(["a", "c"], [2, 1]));
    expect(m).toEqual([
      { material: "a", antes: 1, depois: 2 },
      { material: "b", antes: 2, depois: undefined },
      { material: "c", antes: 3, depois: 1 },
    ].sort((x, y) => (x.depois ?? Infinity) - (y.depois ?? Infinity)));
  });

  it("BarrasPesos mostra os valores de base e do doente e marca o critério novo", () => {
    const linhas = P.variacaoPesos(problema(["A"], [0.6]), problema(["A", "N"], [0.5, 0.5]));
    render(<P.BarrasPesos linhas={linhas} />);
    const novo = document.querySelector('[data-estado="novo"]') as HTMLElement;
    expect(within(novo).getByText("novo", { selector: "span" })).toBeTruthy();
    expect(novo.textContent).toContain("Base: novo");
    expect(document.querySelector('[data-estado="desce"]')).not.toBeNull();
    cleanup();
  });

  it("RegraPainel mostra justificação, fonte e estado sem abrir nada", () => {
    render(
      <ul>
        <P.RegraPainel
          regra={regra({ id: "S-TESTE", condicao: "Condição de teste", justificacao: "Porque sim.", fonte: "Autor 2020", estado: "A verificar" })}
        />
      </ul>,
    );
    expect(screen.getByText("S-TESTE")).toBeTruthy();
    expect(screen.getByText("Porque sim.")).toBeTruthy();
    expect(screen.getByText(/Autor 2020/)).toBeTruthy();
    expect(screen.getByText("A verificar")).toBeTruthy();
    cleanup();
  });
});

describe("painel de impacto com o núcleo", () => {
  it("o stent com alergia ao níquel acrescenta o critério (S-NI), não exclui materiais, e o aviso está sempre visível", async () => {
    render(<Prov><Dicas><P.PainelImpacto id="Stent" cenario="A" perfil={{ alergia_niquel: "sim" }} /></Dicas></Prov>);
    expect(screen.getByRole("note").textContent).toMatch(/Não é ferramenta clínica/);
    await waitFor(() => expect(document.querySelector('[data-regra="S-NI"]')).not.toBeNull(), { timeout: 10_000 });
    const novo = document.querySelector('[data-estado="novo"]') as HTMLElement;
    expect(novo.textContent).toContain("Teor de níquel");
    expect(screen.queryByText("Materiais excluídos")).toBeNull();
    cleanup();
  });

  it("sem dados, nenhuma regra e pesos iguais ao caso de base", async () => {
    render(<Prov><Dicas><P.PainelImpacto id="Stent" cenario="A" perfil={{}} /></Dicas></Prov>);
    await waitFor(() => expect(screen.getByText(/Nenhuma regra se aplica/)).toBeTruthy(), { timeout: 10_000 });
    expect(screen.getByText(/Os pesos não mudam/)).toBeTruthy();
    cleanup();
  });

  it("o ecrã Doente recalcula ao mudar um campo, sem precisar do passo final", async () => {
    render(<Prov><Dicas><Doente /></Dicas></Prov>);
    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: /^Stent/ }));
    });
    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: /Seguinte/ }));
    });
    expect(screen.getByRole("complementary", { name: "Impacto dos dados do doente" })).toBeTruthy();
    await waitFor(() => expect(screen.getByText(/Nenhuma regra se aplica/)).toBeTruthy(), { timeout: 10_000 });
    const grupo = await screen.findByRole("group", { name: "Alergia ao níquel" });
    await act(async () => {
      fireEvent.click(within(grupo).getByRole("radio", { name: "Sim" }));
    });
    await waitFor(() => expect(document.querySelector('[data-regra="S-NI"]')).not.toBeNull(), { timeout: 10_000 });
    cleanup();
  });
});
