// @vitest-environment jsdom
// Testes do modo apresentação (botão rápido no cabeçalho) e dos botões "Guardar no histórico" e "Exportar PDF".
import { act, cleanup, fireEvent, render, screen, within } from "@testing-library/react";
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
});

beforeEach(() => localStorage.clear());
afterEach(async () => {
  cleanup();
  (await import("../src/lib/relatorio")).fecharRelatorio();
});

describe("modo apresentação", () => {
  it("o botão do cabeçalho liga e desliga a vista de apresentação e guarda a escolha", async () => {
    const { prepararNucleo } = await import("../src/lib/nucleo");
    await prepararNucleo();
    const { default: App } = await import("../src/App");
    const { ProvedorDefinicoes } = await import("../src/lib/definicoes");
    render(
      <ProvedorDefinicoes>
        <App />
      </ProvedorDefinicoes>,
    );
    expect(document.documentElement.dataset.apresentacao).toBe("nao");
    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: "Entrar no modo apresentação" }));
    });
    expect(document.documentElement.dataset.apresentacao).toBe("sim");
    expect(document.documentElement.dataset.letra).toBe("muito-grande");
    expect(localStorage.getItem("biomat.apresentacao")).toBe("sim");
    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: "Sair do modo apresentação" }));
    });
    expect(document.documentElement.dataset.apresentacao).toBe("nao");
  });
});

describe("botões da análise", () => {
  it("ficam desativados sem resultado", async () => {
    const { AcoesAnalise } = await import("../src/componentes/AcoesAnalise");
    render(<AcoesAnalise montar={() => null} />);
    expect((screen.getByRole("button", { name: /Guardar no histórico/ }) as HTMLButtonElement).disabled).toBe(true);
    expect((screen.getByRole("button", { name: /Exportar PDF/ }) as HTMLButtonElement).disabled).toBe(true);
  });

  it("guardam no histórico e abrem o relatório", async () => {
    const { prepararNucleo, avaliarCaso } = await import("../src/lib/nucleo");
    const { CASOS } = await import("../src/lib/dados");
    const { criarAnalise } = await import("../src/lib/analise");
    const { AcoesAnalise } = await import("../src/componentes/AcoesAnalise");
    const { ModalRelatorio } = await import("../src/componentes/Relatorio");
    const { lerHistorico } = await import("../src/lib/historico");
    await prepararNucleo();
    const r = await avaliarCaso({ caso: "Stent", cenario: "A" });
    const montar = () =>
      criarAnalise({ caso: "Stent", cenario: "A", problemaBase: CASOS.Stent.cenarios.A, problemaUsado: r.problema, ranking: r.ranking });
    render(
      <>
        <AcoesAnalise montar={montar} />
        <ModalRelatorio />
      </>,
    );
    fireEvent.click(screen.getByRole("button", { name: /Guardar no histórico/ }));
    expect(lerHistorico()).toHaveLength(1);
    expect(lerHistorico()[0].caso).toBe("Stent");
    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: /Exportar PDF/ }));
    });
    const dialogo = screen.getByRole("dialog", { name: "Relatório da análise" });
    expect(within(dialogo).getByRole("heading", { level: 1 }).textContent).toBe("Stent expansível por balão");
  });
});
