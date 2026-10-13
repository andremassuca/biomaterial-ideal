// @vitest-environment jsdom
// Testes dos materiais personalizados: validação, acrescentar ao problema sem tocar na base e o ecrã do caso.
import { act, cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, beforeAll, beforeEach, describe, expect, it, vi } from "vitest";
import { iniciarWasm } from "./apoio_wasm";

class ObservadorTamanho {
  constructor(private f: ResizeObserverCallback) {}
  observe(el: Element) {
    const r = { width: 1200, height: 800, top: 0, left: 0, bottom: 800, right: 1200, x: 0, y: 0 };
    this.f([{ target: el, contentRect: r } as unknown as ResizeObserverEntry], this as unknown as ResizeObserver);
  }
  unobserve() {}
  disconnect() {}
}

beforeAll(() => {
  iniciarWasm();
  vi.stubGlobal("ResizeObserver", ObservadorTamanho);
  vi.stubGlobal("matchMedia", (q: string) => ({ matches: false, media: q, addEventListener() {}, removeEventListener() {}, addListener() {}, removeListener() {} }) as unknown as MediaQueryList);
  vi.stubGlobal("fetch", async () => new Response("", { status: 404, headers: { "content-type": "text/html" } }));
  HTMLCanvasElement.prototype.getContext = (() => null) as typeof HTMLCanvasElement.prototype.getContext;
  HTMLElement.prototype.scrollIntoView = () => {};
  Element.prototype.hasPointerCapture = () => false;
  Element.prototype.releasePointerCapture = () => {};
});

beforeEach(() => localStorage.clear());
afterEach(() => cleanup());

async function problemaHaste() {
  const { CASOS } = await import("../src/lib/dados");
  return CASOS.Haste.cenarios.A;
}

/** Rascunho com o valor típico (e só ele) de cada critério, igual ao de um material real da base. */
function rascunhoDe(p: Awaited<ReturnType<typeof problemaHaste>>, i = 0) {
  return Object.fromEntries(p.criterios.map((c, j) => [c, { tipico: String(p.x_tipico[i][j]), min: "", max: "" }]));
}

describe("lib/personalizados", () => {
  it("lerNumero aceita vírgula e rejeita texto", async () => {
    const { lerNumero } = await import("../src/lib/personalizados");
    expect(lerNumero("1,5")).toBe(1.5);
    expect(lerNumero(" 2 ")).toBe(2);
    expect(lerNumero("")).toBeNull();
    expect(lerNumero("abc")).toBeNull();
  });

  it("nomeMarcado e ehPersonalizado reconhecem a marca", async () => {
    const { nomeMarcado, ehPersonalizado } = await import("../src/lib/personalizados");
    expect(nomeMarcado(" Liga X ")).toBe("Liga X (definido pelo utilizador)");
    expect(ehPersonalizado(nomeMarcado("Liga X"))).toBe(true);
    expect(ehPersonalizado("Aço inox 316L")).toBe(false);
  });

  it("validarFormulario aceita um formulário completo e usa o típico quando falta o mínimo e o máximo", async () => {
    const { validarFormulario } = await import("../src/lib/personalizados");
    const p = await problemaHaste();
    const r = validarFormulario(p, "Liga X", rascunhoDe(p), p.alternativas);
    expect(r.erros).toEqual([]);
    const c = p.criterios[0];
    expect(r.valores![c]).toEqual({ min: p.x_tipico[0][0], max: p.x_tipico[0][0], tipico: p.x_tipico[0][0] });
  });

  it("validarFormulario recusa nome vazio, nome repetido, valor em falta, ordem errada, ordinal fora de 1-5 e custo negativo", async () => {
    const { validarFormulario } = await import("../src/lib/personalizados");
    const p = await problemaHaste();
    const ok = rascunhoDe(p);
    expect(validarFormulario(p, "  ", ok, []).erros[0]).toMatch(/nome/);
    expect(validarFormulario(p, p.alternativas[0], ok, p.alternativas).erros[0]).toMatch(/Já existe/);
    const c0 = p.criterios[0];
    expect(validarFormulario(p, "A", { ...ok, [c0]: { tipico: "", min: "", max: "" } }, []).erros[0]).toMatch(/falta o valor típico/);
    expect(validarFormulario(p, "A", { ...ok, [c0]: { tipico: "5", min: "6", max: "" } }, []).erros[0]).toMatch(/por esta ordem/);
    const jOrd = p.ordinal.indexOf(true);
    if (jOrd >= 0) {
      const c = p.criterios[jOrd];
      expect(validarFormulario(p, "A", { ...ok, [c]: { tipico: "7", min: "", max: "" } }, []).erros[0]).toMatch(/ordinal/);
    }
    const jCusto = p.tipos.indexOf("cost");
    if (jCusto >= 0) {
      const c = p.criterios[jCusto];
      expect(validarFormulario(p, "A", { ...ok, [c]: { tipico: "-1", min: "-1", max: "-1" } }, []).erros.length).toBeGreaterThan(0);
    }
  });

  it("guarda, lista por caso e apaga sem tocar na base", async () => {
    const m = await import("../src/lib/personalizados");
    const { CASOS } = await import("../src/lib/dados");
    const antes = JSON.stringify(CASOS.Haste);
    const p = await problemaHaste();
    const { valores } = m.validarFormulario(p, "Liga X", rascunhoDe(p), []);
    m.guardarPersonalizado({ id: "1", caso: "Haste", nome: "Liga X", valores: valores! });
    expect(m.lerPersonalizados("Haste")).toHaveLength(1);
    expect(m.lerPersonalizados("Stent")).toHaveLength(0);
    m.removerPersonalizado("1");
    expect(m.lerPersonalizados("Haste")).toHaveLength(0);
    expect(JSON.stringify(CASOS.Haste)).toBe(antes);
  });

  it("acrescentarMateriais devolve um problema novo com a linha marcada e deixa o original intacto", async () => {
    const m = await import("../src/lib/personalizados");
    const p = await problemaHaste();
    const copia = JSON.stringify(p);
    const { valores } = m.validarFormulario(p, "Liga X", rascunhoDe(p), []);
    const mat = { id: "1", caso: "Haste" as const, nome: "Liga X", valores: valores! };
    const r = m.acrescentarMateriais(p, [mat]);
    expect(r.incluidos).toEqual(["Liga X (definido pelo utilizador)"]);
    expect(r.problema.alternativas).toHaveLength(p.alternativas.length + 1);
    expect(r.problema.x_tipico[p.alternativas.length]).toEqual(p.x_tipico[0]);
    expect(JSON.stringify(p)).toBe(copia);
  });

  it("um material a que falta um critério fica de fora e diz qual", async () => {
    const m = await import("../src/lib/personalizados");
    const p = await problemaHaste();
    const { valores } = m.validarFormulario(p, "Liga X", rascunhoDe(p), []);
    const parcial = { ...valores! };
    delete parcial[p.criterios[0]];
    const r = m.acrescentarMateriais(p, [{ id: "1", caso: "Haste", nome: "Parcial", valores: parcial }]);
    expect(r.incluidos).toEqual([]);
    expect(r.deFora).toEqual([{ nome: "Parcial", falta: [p.criterios[0]] }]);
    expect(r.problema.alternativas).toEqual(p.alternativas);
  });

  it("um material igual ao 1.º da base fica com o mesmo ranking que ele", async () => {
    const m = await import("../src/lib/personalizados");
    const { avaliarLocal } = await import("../src/lib/metodos");
    const p = await problemaHaste();
    const { valores } = m.validarFormulario(p, "Gémeo", rascunhoDe(p, 0), []);
    const r = m.acrescentarMateriais(p, [{ id: "1", caso: "Haste", nome: "Gémeo", valores: valores! }]);
    const rk = avaliarLocal(r.problema);
    const n = p.alternativas.length;
    expect(rk.c_topsis[n]).toBeCloseTo(rk.c_topsis[0], 12);
    expect(rk.q_waspas[n]).toBeCloseTo(rk.q_waspas[0], 12);
  });
});

describe("ecrã do caso com um material personalizado", () => {
  it("o formulário acrescenta o material ao ranking, marcado, e permite apagá-lo", async () => {
    const { prepararNucleo } = await import("../src/lib/nucleo");
    await prepararNucleo();
    const { Caso } = await import("../src/ecras/Caso");
    const { ProvedorDefinicoes } = await import("../src/lib/definicoes");
    const { ProvedorDicas } = await import("../src/componentes/ui/controlos");
    const p = await problemaHaste();
    render(
      <ProvedorDefinicoes>
        <ProvedorDicas>
          <Caso id="Haste" />
        </ProvedorDicas>
      </ProvedorDefinicoes>,
    );
    await waitFor(() => expect(document.querySelector(".animate-pulse")).toBeNull(), { timeout: 10_000 });
    fireEvent.click(screen.getByRole("button", { name: /Novo material/ }));
    fireEvent.change(screen.getByLabelText("Nome do material"), { target: { value: "Liga de teste" } });
    p.criterios.forEach((c, j) => {
      fireEvent.change(screen.getByLabelText(`${c}: valor típico`), { target: { value: String(p.x_tipico[0][j]) } });
    });
    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: "Acrescentar ao ranking" }));
    });
    await waitFor(() => expect(screen.getAllByText(/Liga de teste/).length).toBeGreaterThan(0));
    expect(screen.getAllByText(/definido pelo utilizador/i).length).toBeGreaterThan(0);
    const cartao = document.querySelector("[data-personalizados]") as HTMLElement;
    await act(async () => {
      fireEvent.click(within(cartao).getByRole("button", { name: "Apagar Liga de teste" }));
    });
    await waitFor(() => expect(screen.queryAllByText(/Liga de teste/)).toHaveLength(0));
  });
});
