// @vitest-environment jsdom
// Teste de fumo: monta a aplicação inteira (com o núcleo WebAssembly verdadeiro), abre cada ecrã do menu e falha
// se aparecer algum erro ou aviso na consola (avisos do React incluídos) ou se um ecrã não chegar a desenhar.
import { act, cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { StrictMode } from "react";
import { afterAll, beforeAll, describe, expect, it, vi } from "vitest";
import { iniciarWasm } from "./apoio_wasm";

// O jsdom não faz paginação nem desenho: o ResizeObserver dá um tamanho fixo aos contentores dos gráficos (sem
// mexer nas medidas do texto, que o Recharts usa para os eixos) e o canvas não tem contexto WebGL (o visualizador
// 3D mostra uma nota em vez do modelo).
const LARGURA = 1200;
const ALTURA = 800;

class ObservadorTamanho {
  constructor(private f: ResizeObserverCallback) {}
  observe(el: Element) {
    const r = { width: LARGURA, height: ALTURA, top: 0, left: 0, bottom: ALTURA, right: LARGURA, x: 0, y: 0 };
    this.f([{ target: el, contentRect: r } as unknown as ResizeObserverEntry], this as unknown as ResizeObserver);
  }
  unobserve() {}
  disconnect() {}
}

const mensagens: string[] = [];

beforeAll(() => {
  iniciarWasm();
  vi.stubGlobal("ResizeObserver", ObservadorTamanho);
  vi.stubGlobal(
    "matchMedia",
    (q: string) =>
      ({ matches: false, media: q, onchange: null, addEventListener() {}, removeEventListener() {}, addListener() {}, removeListener() {}, dispatchEvent: () => false }) as MediaQueryList,
  );
  // modelos glTF: sem servidor, respondem "não existe" (o visualizador mostra a forma simplificada)
  vi.stubGlobal("fetch", async () => new Response("", { status: 404, headers: { "content-type": "text/html" } }));
  HTMLCanvasElement.prototype.getContext = (() => null) as typeof HTMLCanvasElement.prototype.getContext;
  HTMLElement.prototype.scrollIntoView = () => {};
  Element.prototype.hasPointerCapture = () => false;
  Element.prototype.releasePointerCapture = () => {};

  for (const nivel of ["error", "warn"] as const) {
    vi.spyOn(console, nivel).mockImplementation((...args: unknown[]) => {
      mensagens.push(`[${nivel}] ${args.map(String).join(" ")}`);
    });
  }
});

afterAll(() => {
  cleanup();
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
});

/** Espera que deixem de existir esqueletos de carregamento (animate-pulse) e que o ecrã estabilize. */
async function esperarEcra() {
  await waitFor(() => expect(document.querySelector("main .animate-pulse")).toBeNull(), { timeout: 10_000 });
  await act(async () => {
    await new Promise((r) => setTimeout(r, 400));
  });
}

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
  "Comparar materiais",
  "Simulação FEA e CFD",
  "Histórico",
  "Filtros",
  "Porquê",
  "Definições",
  "Sobre",
];

describe("teste de fumo dos ecrãs", () => {
  it("a aplicação arranca com o núcleo WebAssembly e abre todos os ecrãs sem erros nem avisos", async () => {
    const { prepararNucleo, modoNucleo } = await import("../src/lib/nucleo");
    await prepararNucleo();
    expect(modoNucleo()).toBe("web");
    const { default: App } = await import("../src/App");
    const { ProvedorDefinicoes } = await import("../src/lib/definicoes");

    render(
      <StrictMode>
        <ProvedorDefinicoes>
          <App />
        </ProvedorDefinicoes>
      </StrictMode>,
    );
    const nav = screen.getByRole("navigation", { name: "Ecrãs" });

    let titulo = "";
    for (const texto of MENU) {
      const botao = within(nav).getByRole("button", { name: texto });
      await act(async () => {
        fireEvent.click(botao);
      });
      await waitFor(() => expect(botao.getAttribute("aria-current")).toBe("page"));
      // o ecrã anterior sai com uma animação: espera-se pelo título novo
      await waitFor(
        () => {
          const h1 = screen.getAllByRole("heading", { level: 1 });
          expect(h1.length).toBe(1);
          if (texto !== "Início") expect(h1[0].textContent).not.toBe(titulo);
        },
        { timeout: 5_000 },
      );
      titulo = screen.getByRole("heading", { level: 1 }).textContent ?? "";
      await esperarEcra();
      expect(document.querySelector("main")!.textContent!.length, `ecrã ${texto} vazio`).toBeGreaterThan(50);
      expect(mensagens, `consola no ecrã ${texto}`).toEqual([]);
    }
  });

  it("haste: ranking com os três métodos e Monte Carlo em direto", async () => {
    const nav = screen.getByRole("navigation", { name: "Ecrãs" });
    await act(async () => {
      fireEvent.click(within(nav).getByRole("button", { name: "Haste femoral" }));
    });
    await waitFor(() => expect(screen.getByRole("region", { name: "Ranking TOPSIS" })).toBeTruthy(), { timeout: 10_000 });
    await esperarEcra();
    const main = document.querySelector("main")!;
    expect(screen.getByRole("region", { name: "Ranking WASPAS" })).toBeTruthy();
    expect(main.textContent).not.toContain("Modo navegador");
    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: /Correr/ }));
    });
    await waitFor(() => expect(main.textContent).toMatch(/repetições/), { timeout: 30_000 });
    await waitFor(() => expect(main.textContent).toContain("Comparação com o relatório"), { timeout: 30_000 });
    await esperarEcra();
    expect(mensagens, "consola no Monte Carlo").toEqual([]);
  });

  it("doente: os quatro passos até ao resultado", async () => {
    const nav = screen.getByRole("navigation", { name: "Ecrãs" });
    await act(async () => {
      fireEvent.click(within(nav).getByRole("button", { name: "Doente" }));
    });
    await esperarEcra();
    for (let k = 0; k < 3; k++) {
      await act(async () => {
        fireEvent.click(screen.getByRole("button", { name: /Seguinte/ }));
      });
      await esperarEcra();
    }
    expect(screen.getByRole("button", { name: /Limpar os dados/ })).toBeTruthy();
    expect(mensagens, "consola no ecrã do doente").toEqual([]);
  });
});
