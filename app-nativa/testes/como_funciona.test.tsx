// @vitest-environment jsdom
// Ecrã "Como funciona": desenha-se, tem as nove frases dos métodos, o exemplo da haste usa os números dos dados (e não
// números escritos à mão) e as contagens dos estados batem com data/materiais.csv.
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { cleanup, render, screen, waitFor, within } from "@testing-library/react";
import { afterAll, beforeAll, describe, expect, it, vi } from "vitest";
import { num, valor } from "../src/lib/formato";
import { APP_DIR, RESULTS, lerCsv } from "./apoio";
import { iniciarWasm } from "./apoio_wasm";

const HASTE = JSON.parse(readFileSync(resolve(APP_DIR, "dados", "caso_haste.json"), "utf-8")) as {
  cenarios: { A: { alternativas: string[]; criterios: string[]; tipos: string[]; alvos: (number | null)[]; pesos: number[]; x_tipico: number[][] } };
};
const limpo = (s: string | null | undefined) => (s ?? "").replace(/[\s  ]+/g, " ").trim();

// O ecrã importa o núcleo (lib/nucleo.ts), que arranca o WebAssembly quando o módulo é carregado: o ecrã só se
// importa depois de iniciarWasm(), como no teste de fumo.
type Ecra = typeof import("../src/ecras/ComoFunciona");
let ComoFunciona: Ecra["ComoFunciona"];
let METODOS_SIMPLES: Ecra["METODOS_SIMPLES"];
let alvoRigidez: Ecra["alvoRigidez"];
let contarEstados: Ecra["contarEstados"];
let exemploHaste: Ecra["exemploHaste"];
let passosFluxo: Ecra["passosFluxo"];
let regraCriterio: Ecra["regraCriterio"];
let APP: typeof import("../src/lib/dados")["APP"];

beforeAll(async () => {
  iniciarWasm();
  vi.stubGlobal("fetch", async () => new Response("", { status: 404, headers: { "content-type": "text/html" } }));
  ({ ComoFunciona, METODOS_SIMPLES, alvoRigidez, contarEstados, exemploHaste, passosFluxo, regraCriterio } = await import(
    "../src/ecras/ComoFunciona"
  ));
  ({ APP } = await import("../src/lib/dados"));
  vi.stubGlobal(
    "matchMedia",
    (q: string) =>
      ({ matches: false, media: q, onchange: null, addEventListener() {}, removeEventListener() {}, addListener() {}, removeListener() {}, dispatchEvent: () => false }) as MediaQueryList,
  );
});

afterAll(() => {
  cleanup();
  vi.unstubAllGlobals();
});

describe("funções do ecrã Como funciona", () => {
  it("nove métodos, cada um com uma frase, e os grupos honestos (Borda junta, robustez, confirmação)", () => {
    expect(METODOS_SIMPLES.map((m) => m.nome)).toEqual([
      "TOPSIS",
      "WASPAS",
      "VIKOR",
      "Borda",
      "Monte Carlo",
      "Sobol",
      "PROMETHEE II",
      "MOORA",
      "CODAS",
    ]);
    const grupo = Object.fromEntries(METODOS_SIMPLES.map((m) => [m.nome, m.grupo]));
    expect(grupo.Borda).toBe("consenso");
    expect([grupo["Monte Carlo"], grupo.Sobol]).toEqual(["robustez", "robustez"]);
    expect([grupo["PROMETHEE II"], grupo.MOORA, grupo.CODAS]).toEqual(["confirmacao", "confirmacao", "confirmacao"]);
    for (const m of METODOS_SIMPLES) {
      expect(m.frase.length).toBeGreaterThan(40);
      expect(m.frase).not.toMatch(/[—–]/);
    }
  });

  it("contarEstados conta cada estado de data/materiais.csv e soma o total", () => {
    const csv = lerCsv(resolve(APP_DIR, "..", "data", "materiais.csv"));
    const esperado: Record<string, number> = {};
    for (const l of csv) esperado[l.estado] = (esperado[l.estado] ?? 0) + 1;
    const c = contarEstados(APP.fichas.materiais);
    expect(Object.fromEntries(c.map((x) => [x.estado, x.n]))).toEqual(esperado);
    expect(c.reduce((s, x) => s + x.n, 0)).toBe(csv.length);
    // os verificados vêm primeiro e todos os estados têm uma explicação
    expect(c[0].estado.startsWith("Verificado")).toBe(true);
    for (const x of c) expect(x.significado).not.toMatch(/^Estado da base/);
  });

  it("contarEstados ordena verificados, modelação e o resto, e explica estados desconhecidos", () => {
    const c = contarEstados([{ estado: "A verificar" }, { estado: "Verificado" }, { estado: "Valor de modelação" }, { estado: "Outro" }, { estado: "A verificar" }]);
    expect(c.map((x) => x.estado)).toEqual(["Verificado", "Valor de modelação", "A verificar", "Outro"]);
    expect(c.find((x) => x.estado === "Outro")!.significado).toMatch(/leia_me/);
  });

  it("alvoRigidez lê o alvo do módulo de Young da haste e o osso cortical de data/tecido.csv", () => {
    const a = alvoRigidez();
    const p = HASTE.cenarios.A;
    const j = p.criterios.indexOf("Módulo de Young");
    expect(p.tipos[j]).toBe("target");
    expect(a.alvo).toBe(p.alvos[j]);
    const tecido = lerCsv(resolve(APP_DIR, "..", "data", "tecido.csv")).find((l) => l.tecido === "Osso cortical" && l.propriedade === "Módulo de Young")!;
    expect(a.tecido?.min).toBe(Number(tecido.min));
    expect(a.tecido?.max).toBe(Number(tecido.max));
    expect(a.tecido?.estado).toBe(tecido.estado);
  });

  it("exemploHaste usa os valores típicos de caso_haste.json e a normalização com alvo de Petković (eq. 2)", () => {
    const e = exemploHaste();
    const p = HASTE.cenarios.A;
    e.materiais.forEach((m, i) => {
      const linha = p.alternativas.indexOf(m);
      e.criterios.forEach((c, k) => {
        const j = p.criterios.indexOf(c.nome);
        expect(e.x[i][k]).toBe(p.x_tipico[linha][j]);
        expect(c.pesoRelatorio).toBe(p.pesos[j]);
      });
    });
    // rigidez: 1 - |x - T| / (max(xmax, T) - min(xmin, T)), feita aqui à parte
    const k = e.criterios.findIndex((c) => c.tipo === "target");
    const col = e.x.map((l) => l[k]);
    const t = e.criterios[k].alvo!;
    const d = Math.max(...col, t) - Math.min(...col, t);
    col.forEach((x, i) => expect(e.passos.normalizada[i][k]).toBeCloseTo(1 - Math.abs(x - t) / d, 12));
    // pesos renormalizados somam 1 e o 1.º tem o maior C
    expect(e.criterios.reduce((s, c) => s + c.peso, 0)).toBeCloseTo(1, 12);
    expect(e.passos.c[e.ordem[0]]).toBe(Math.max(...e.passos.c));
  });

  it("regraCriterio e passosFluxo dizem o tipo e usam o número de valores e de repetições dos dados", () => {
    expect(regraCriterio("benefit", null, "MPa")).toBe("mais é melhor");
    expect(regraCriterio("cost", null, "g/cm³")).toBe("menos é melhor");
    expect(regraCriterio("target", 17, "GPa")).toBe(`perto de ${valor(17)} GPa é melhor`);
    const f = passosFluxo();
    expect(f).toHaveLength(5);
    expect(f[0].texto).toContain(num(APP.fichas.materiais.length, 0));
    const iter = APP.espectro.find((c) => !c.semiquantitativo)!.n_iter!;
    expect(f[3].texto).toContain(num(iter, 0));
  });
});

describe("ecrã Como funciona", () => {
  it("desenha o esquema, as nove frases, o exemplo com os números dos dados e as contagens", async () => {
    const { prepararNucleo, modoNucleo } = await import("../src/lib/nucleo");
    await prepararNucleo();
    expect(modoNucleo()).toBe("web");
    render(<ComoFunciona />);
    expect(screen.getByRole("heading", { level: 1, name: "Como funciona" })).toBeTruthy();

    // (a) esquema de fluxo: cinco passos visíveis aos leitores de ecrã
    const fluxo = screen.getByRole("list", { name: /Passos do método/ });
    expect(within(fluxo).getAllByRole("listitem")).toHaveLength(5);

    // (c) as nove frases
    const corpo = limpo(document.body.textContent);
    for (const m of METODOS_SIMPLES) expect(corpo).toContain(limpo(m.frase));

    // (d) alvo da rigidez
    const p = HASTE.cenarios.A;
    const alvo = p.alvos[p.criterios.indexOf("Módulo de Young")]!;
    expect(limpo(document.querySelector("[data-criterio-alvo]")!.textContent)).toContain(`${valor(alvo)} GPa`);

    // (e) exemplo: valores típicos e C calculados a partir dos dados
    const e = exemploHaste();
    const exemplo = limpo(document.querySelector("[data-exemplo]")!.textContent);
    for (const linha of e.x) for (const v of linha) expect(exemplo).toContain(valor(v));
    for (const [i, m] of e.materiais.entries()) {
      expect(limpo(document.querySelector(`[data-c-exemplo="${m}"]`)!.textContent)).toContain(num(e.passos.c[i], 3));
    }
    // caso completo calculado pelo núcleo WebAssembly: o 1.º e o C batem com results/pontuacoes.csv
    const csv = lerCsv(resolve(RESULTS, "pontuacoes.csv")).filter((l) => l.caso === "Haste" && l.cenario === "A");
    const primeiro = csv.find((l) => l.pos_TOPSIS === "1")!;
    await waitFor(() => expect(limpo(document.querySelector("[data-exemplo]")!.textContent)).toContain("No caso completo"), { timeout: 10_000 });
    expect(limpo(document.querySelector("[data-exemplo]")!.textContent)).toContain(`C = ${num(Number(primeiro.C_TOPSIS), 3)}`);

    // (f) contagens dos estados
    for (const c of contarEstados(APP.fichas.materiais)) {
      expect(limpo(document.querySelector(`[data-estado="${c.estado}"]`)!.textContent)).toContain(num(c.n, 0));
    }
    expect(corpo).not.toMatch(/[—–]/);
  });
});
