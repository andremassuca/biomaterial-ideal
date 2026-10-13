// @vitest-environment jsdom
// Verifica o port em TypeScript (WASPAS, VIKOR, Borda) contra o núcleo Rust em WebAssembly, em todos os casos
// quantitativos e cenários, e funções auxiliares.
import { beforeAll, describe, expect, it } from "vitest";
import { iniciarWasm } from "./apoio_wasm";

beforeAll(() => iniciarWasm());

describe("port TypeScript dos métodos", () => {
  it("dá os mesmos números do núcleo Rust em todos os casos e cenários", async () => {
    const { prepararNucleo, avaliarCaso } = await import("../src/lib/nucleo");
    const { CASOS, QUANTITATIVOS, cenarios } = await import("../src/lib/dados");
    const { avaliarLocal } = await import("../src/lib/metodos");
    await prepararNucleo();
    let comparados = 0;
    for (const id of QUANTITATIVOS) {
      for (const c of cenarios(CASOS[id])) {
        const rust = await avaliarCaso({ caso: id, cenario: c });
        const ts = avaliarLocal(rust.problema);
        for (const campo of ["c_topsis", "q_waspas", "s_vikor", "r_vikor", "p_vikor"] as const) {
          ts[campo].forEach((v, i) => expect(v).toBeCloseTo(rust.ranking[campo][i], 9));
        }
        for (const campo of ["pos_topsis", "pos_waspas", "pos_vikor", "pontos_borda", "pos_borda"] as const) {
          expect(ts[campo]).toEqual(rust.ranking[campo]);
        }
        comparados++;
      }
    }
    expect(comparados).toBeGreaterThanOrEqual(6);
  });

  it("borda desempata pela posição no TOPSIS", async () => {
    const { borda } = await import("../src/lib/metodos");
    const r = borda([[1, 2], [2, 1], [1, 2]], [1, 2]);
    expect(r.pontos).toEqual([2, 1]);
    expect(r.posicoes).toEqual([1, 2]);
    // empate em pontos (2 e 2): ganha quem tem melhor posição no TOPSIS
    const empate = borda([[1, 2], [2, 1], [1, 1]], [2, 1]);
    expect(empate.posicoes[1]).toBe(1);
  });

  it("a normalização do WASPAS dá 1 ao melhor valor de benefício e de custo", async () => {
    const { normalizarWaspas } = await import("../src/lib/metodos");
    const r = normalizarWaspas([[10, 4], [5, 2]], ["benefit", "cost"], [null, null]);
    expect(r[0][0]).toBe(1);
    expect(r[1][1]).toBe(1);
    expect(r[1][0]).toBe(0.5);
    expect(r[0][1]).toBe(0.5);
  });
});
