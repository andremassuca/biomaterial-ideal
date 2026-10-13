// Os números que a aplicação mostra batem com os ficheiros de results/?
// Usa o núcleo WebAssembly de src/wasm (o mesmo da versão web, compilado do mesmo crate Rust que a aplicação
// nativa) e os JSON de dados/ que a interface lê; compara-os com os CSV e JSON de results/.
import { existsSync, readFileSync } from "node:fs";
import { resolve } from "node:path";
import { beforeAll, describe, expect, it } from "vitest";
import { avaliar_caso, avaliar_doente, monte_carlo_web } from "../src/wasm/mcdm_wasm.js";
import { posicoes, topsisPassos } from "../src/lib/topsis";
import type { Caso, DadosApp, RespostaCaso, RespostaDoente, ResumoMonteCarlo } from "../src/lib/tipos";
import { APP_DIR, RESULTS, lerCsv, lerJson } from "./apoio";
import { iniciarWasm } from "./apoio_wasm";

const DADOS = resolve(APP_DIR, "dados");
const FICHEIRO_CASO: Record<string, string> = {
  Haste: "caso_haste.json",
  Stent: "caso_stent.json",
  Scaffold: "caso_scaffold.json",
  "Par articular": "caso_par_articular.json",
  "Implante dentário": "caso_implante_dentario.json",
};
const caso = (id: string) => lerJson<Caso>(resolve(DADOS, FICHEIRO_CASO[id]));
const APP = lerJson<DadosApp>(resolve(DADOS, "app.json"));

/** Tolerância das pontuações (o núcleo Rust reproduz o Python até ~1e-12). */
const TOL = 1e-9;

function grupos<T extends Record<string, string>>(linhas: T[], chave: (l: T) => string): Map<string, T[]> {
  const m = new Map<string, T[]>();
  for (const l of linhas) m.set(chave(l), [...(m.get(chave(l)) ?? []), l]);
  return m;
}

function pedirCaso(id: string, cenario: string): RespostaCaso {
  const eta = caso(id).parametros.eta ?? 1;
  return JSON.parse(avaliar_caso(JSON.stringify({ caso: id, cenario, pesos: null, eta, excluir: [] })));
}

beforeAll(() => iniciarWasm());

describe("rankings e pontuações (results/pontuacoes.csv)", () => {
  const linhas = lerCsv(resolve(RESULTS, "pontuacoes.csv"));
  for (const [chave, g] of grupos(linhas, (l) => `${l.caso}|${l.cenario}`)) {
    const [id, cenario] = chave.split("|");
    it(`${id}, cenário ${cenario}: TOPSIS, WASPAS, VIKOR e Borda`, () => {
      const r = pedirCaso(id, cenario).ranking;
      expect([...r.alternativas].sort()).toEqual(g.map((l) => l.material).sort());
      for (const l of g) {
        const i = r.alternativas.indexOf(l.material);
        expect(r.c_topsis[i]).toBeCloseTo(Number(l.C_TOPSIS), 9);
        expect(r.q_waspas[i]).toBeCloseTo(Number(l.Q_WASPAS), 9);
        expect(r.p_vikor[i]).toBeCloseTo(Number(l.P_VIKOR), 9);
        expect(r.pos_topsis[i]).toBe(Number(l.pos_TOPSIS));
        expect(r.pos_waspas[i]).toBe(Number(l.pos_WASPAS));
        expect(r.pos_vikor[i]).toBe(Number(l.pos_VIKOR));
        expect(r.pontos_borda[i]).toBe(Number(l.pontos_Borda));
        expect(r.pos_borda[i]).toBe(Number(l.pos_Borda));
      }
    });

    it(`${id}, cenário ${cenario}: o TOPSIS em TypeScript (ecrã "Porquê" e modo navegador) dá o mesmo C`, () => {
      const p = caso(id).cenarios[cenario];
      const { c } = topsisPassos(p.x_tipico, p.pesos, p.tipos, p.alvos);
      const pos = posicoes(c, true);
      for (const l of g) {
        const i = p.alternativas.indexOf(l.material);
        expect(Math.abs(c[i] - Number(l.C_TOPSIS))).toBeLessThan(TOL);
        expect(pos[i]).toBe(Number(l.pos_TOPSIS));
      }
    });
  }
});

describe("posições nos cenários de base (results/rankings_cenarios.csv e semiquantitativos.csv)", () => {
  const linhas = [
    ...lerCsv(resolve(RESULTS, "rankings_cenarios.csv")),
    ...lerCsv(resolve(RESULTS, "semiquantitativos.csv")),
  ].filter((l) => l.variante === l.cenario && (l.cenario === "A" || l.cenario === "B") && FICHEIRO_CASO[l.caso]);
  for (const [chave, g] of grupos(linhas, (l) => `${l.caso}|${l.cenario}|${l.metodo}`)) {
    const [id, cenario, metodo] = chave.split("|");
    it(`${id}, cenário ${cenario}, ${metodo}`, () => {
      const r = pedirCaso(id, cenario).ranking;
      const pos = { TOPSIS: r.pos_topsis, WASPAS: r.pos_waspas, VIKOR: r.pos_vikor, Borda: r.pos_borda }[metodo];
      expect(pos, `método ${metodo}`).toBeDefined();
      for (const l of g) expect(pos![r.alternativas.indexOf(l.material)], l.material).toBe(Number(l.posicao));
    });
  }
});

describe("perfis de doente (results/perfis_referencia.csv)", () => {
  const linhas = lerCsv(resolve(RESULTS, "perfis_referencia.csv"));
  for (const [chave, g] of grupos(linhas, (l) => `${l.perfil}|${l.caso}|${l.cenario}`)) {
    const [pid, id, cenario] = chave.split("|");
    it(`${pid} (${g[0].descricao}), ${id}, cenário ${cenario}`, () => {
      const perfil = caso(id).perfis_referencia[pid]?.perfil;
      expect(perfil, `perfil ${pid} em dados/`).toBeDefined();
      const r: RespostaDoente = JSON.parse(avaliar_doente(JSON.stringify({ caso: id, cenario, perfil })));
      const rr = r.resultado.ranking;
      const excl = g[0].excluidos ? g[0].excluidos.split("; ").filter(Boolean) : [];
      expect([...r.resultado.excluidos].sort()).toEqual([...excl].sort());
      for (const l of g) {
        const i = rr.alternativas.indexOf(l.material);
        const ib = r.base.alternativas.indexOf(l.material);
        expect(i, l.material).toBeGreaterThanOrEqual(0);
        expect(rr.c_topsis[i]).toBeCloseTo(Number(l.C_TOPSIS), 9);
        expect(rr.q_waspas[i]).toBeCloseTo(Number(l.Q_WASPAS), 9);
        expect(rr.p_vikor[i]).toBeCloseTo(Number(l.P_VIKOR), 9);
        expect(rr.pos_topsis[i]).toBe(Number(l.pos_TOPSIS));
        expect(rr.pos_waspas[i]).toBe(Number(l.pos_WASPAS));
        expect(rr.pos_vikor[i]).toBe(Number(l.pos_VIKOR));
        expect(rr.pos_borda[i]).toBe(Number(l.pos_Borda));
        expect(r.base.pos_topsis[ib]).toBe(Number(l.pos_ref_TOPSIS));
        expect(r.base.pos_borda[ib]).toBe(Number(l.pos_ref_Borda));
      }
    });
  }
});

describe("Monte Carlo (results/monte_carlo.csv)", () => {
  const linhas = lerCsv(resolve(RESULTS, "monte_carlo.csv"));

  it("a tabela de referência da aplicação (app.json) é a do relatório", () => {
    expect(APP.monte_carlo_referencia.length).toBe(linhas.length);
    for (const l of linhas) {
      const a = APP.monte_carlo_referencia.find(
        (x) => x.caso === l.caso && x.analise === l.analise && x.metodo === l.metodo && x.material === l.material,
      );
      expect(a, `${l.caso} ${l.analise} ${l.metodo} ${l.material}`).toBeDefined();
      expect(a!.pct_primeiro).toBeCloseTo(Number(l.pct_primeiro), 9);
      expect(a!.pct_segundo).toBeCloseTo(Number(l.pct_segundo), 9);
      expect(a!.posicao_media).toBeCloseTo(Number(l.posicao_media), 9);
      expect(a!.n_iter).toBe(Number(l.n_iter));
    }
  });

  // O gerador do Rust não é o do numpy: compara-se a estatística com uma margem (4 desvios-padrão de uma
  // proporção com n = 10 000 dá no máximo 2 pontos percentuais).
  for (const [chave, g] of grupos(linhas, (l) => `${l.caso}|${l.analise}`)) {
    const [id, analise] = chave.split("|");
    const variar = analise.startsWith("MC propriedades") ? "propriedades" : analise.startsWith("W pesos") ? "pesos" : null;
    if (!variar) continue;
    it(`${id}, ${analise}: o Monte Carlo da aplicação reproduz o do relatório`, () => {
      const n = Number(g[0].n_iter);
      const r: ResumoMonteCarlo = JSON.parse(
        monte_carlo_web(
          JSON.stringify({ caso: id, cenario: "A", pesos: null, eta: caso(id).parametros.eta ?? 1, excluir: [], n_iter: n, variar }),
        ),
      );
      expect(r.feitas).toBe(n);
      for (const l of g) {
        const m = r.metodos.find((x) => x.metodo === l.metodo)!;
        const i = r.alternativas.indexOf(l.material);
        expect(Math.abs(m.pct_primeiro[i] - Number(l.pct_primeiro)), `${l.metodo} ${l.material} % 1.º`).toBeLessThan(2);
        expect(Math.abs(m.pct_segundo[i] - Number(l.pct_segundo)), `${l.metodo} ${l.material} % 2.º`).toBeLessThan(2);
        expect(Math.abs(m.posicao_media[i] - Number(l.posicao_media)), `${l.metodo} ${l.material} posição média`).toBeLessThan(0.05);
      }
    });
  }
});

describe("espectro de confiança (app.json contra pontuacoes.csv e monte_carlo.csv)", () => {
  const pont = lerCsv(resolve(RESULTS, "pontuacoes.csv")).filter((l) => l.cenario === "A");
  for (const e of APP.espectro.filter((x) => !x.semiquantitativo)) {
    it(`${e.caso}: vencedor, 2.º e ΔC`, () => {
      const g = pont.filter((l) => l.caso === e.caso).sort((a, b) => Number(b.C_TOPSIS) - Number(a.C_TOPSIS));
      expect(e.vencedor).toBe(g[0].material);
      expect(e.segundo).toBe(g[1].material);
      expect(e.delta_c).toBeCloseTo(Number(g[0].C_TOPSIS) - Number(g[1].C_TOPSIS), 9);
    });
  }
});

describe("FEA da haste (results/fea_haste.csv e fea_haste_sw.json)", () => {
  const linhas = lerCsv(resolve(RESULTS, "fea_haste.csv"));
  const fina = Math.min(...linhas.map((l) => Number(l.malha_mm)));
  it("zonas de Gruen 1 e 7 na malha mais fina", () => {
    const fea = APP.fea!;
    expect(fea.malha_mm).toBe(fina);
    const ref = linhas.filter((l) => Number(l.malha_mm) === fina && (l.zona === "1" || l.zona === "7"));
    expect(fea.zonas.length).toBe(ref.length);
    for (const l of ref) {
      const z = fea.zonas.find((x) => x.material === l.material && x.zona === Number(l.zona))!;
      expect(z, `${l.material} zona ${l.zona}`).toBeDefined();
      expect(z.energia_mJ).toBeCloseTo(Number(l.energia_mJ), 9);
      expect(z.razao).toBeCloseTo(Number(l.razao), 9);
      expect(z.stress_shielding).toBeCloseTo(Number(l.stress_shielding), 9);
      expect(z.elementos).toBe(Number(l.elementos));
    }
  });
  it("comparação Python contra SOLIDWORKS: a coluna Python é a razão da malha fina", () => {
    const comp = APP.fea!.comparacao ?? [];
    expect(comp.length).toBeGreaterThan(0);
    for (const c of comp as unknown as Record<string, number | string>[]) {
      const z1 = APP.fea!.zonas.find((x) => x.material_base === c.material && x.zona === 1);
      if (z1) expect(Number(c.G1_python)).toBeCloseTo(z1.razao, 9);
    }
  });
});

describe("massa da haste (results/massa_haste.csv)", () => {
  it("massa e densidade por material", () => {
    const ref = lerCsv(resolve(RESULTS, "massa_haste.csv"));
    const m = APP.massa!.materiais as unknown as Record<string, number | string>[];
    expect(m.length).toBe(ref.length);
    for (const l of ref) {
      const a = m.find((x) => x.material === l.material)!;
      expect(Number(a.massa_g)).toBeCloseTo(Number(l.massa_g), 9);
      expect(Number(a.densidade_g_cm3)).toBeCloseTo(Number(l.densidade_g_cm3), 9);
    }
  });
});

describe("CFD do stent (results/cfd_pulsatil.json)", () => {
  it("dados/cfd_stent.json é igual ao resultado da CFD", () => {
    const app = lerJson(resolve(DADOS, "cfd_stent.json"));
    const ref = lerJson(resolve(RESULTS, "cfd_pulsatil.json"));
    expect(app).toEqual(ref);
  });
});

// results/base_triagem.csv é a origem da base de triagem e não está no Git (results/*.csv); sem ela, estes testes saltam
// (a página de triagem usa o triagem.json já exportado). Com o ficheiro presente, comparam o JSON com a origem.
const CSV_TRIAGEM = resolve(RESULTS, "base_triagem.csv");
describe.skipIf(!existsSync(CSV_TRIAGEM))("base de triagem (results/base_triagem.csv)", () => {
  // o corpo do describe corre mesmo quando o bloco salta: por isso só se lê o ficheiro se existir
  const base = existsSync(CSV_TRIAGEM) ? lerCsv(CSV_TRIAGEM) : [];
  const tri = lerJson<{ materiais: Record<string, unknown>[]; contagens: { caso: string; fonte_base: string; classe: string; materiais: number }[] }>(
    resolve(DADOS, "triagem.json"),
  );
  it("um registo por material e caso", () => {
    expect(tri.materiais.length).toBe(new Set(base.map((l) => `${l.chave}|${l.caso}`)).size);
  });
  it("contagens por caso, classe e fonte", () => {
    for (const c of tri.contagens) {
      const n = new Set(
        base.filter((l) => l.caso === c.caso && l.classe === c.classe && l.fonte_base === c.fonte_base).map((l) => l.chave),
      ).size;
      expect(n, `${c.caso} ${c.classe} ${c.fonte_base}`).toBe(c.materiais);
    }
  });
  it("densidades mostradas existem na base com o mesmo valor (4 casas)", () => {
    const porChave = grupos(base, (l) => `${l.chave}|${l.caso}`);
    let vistos = 0;
    for (const m of tri.materiais) {
      const d = m.densidade as number | null | undefined;
      if (d === null || d === undefined) continue;
      const linhas = porChave.get(`${m.chave}|${m.caso}`) ?? [];
      const valores = linhas.filter((l) => l.propriedade === "Densidade" && l.valor !== "").map((l) => Number(l.valor));
      expect(valores.some((v) => Math.abs(Math.round(v * 1e4) / 1e4 - d) < 1e-9), `${m.nome}`).toBe(true);
      vistos++;
    }
    expect(vistos).toBeGreaterThan(100);
  });
});

describe("dados embutidos no núcleo", () => {
  it("o WebAssembly foi compilado com os dados/ atuais (mesmos problemas de decisão)", () => {
    // o núcleo devolve o problema que tem embutido; tem de ser o de dados/caso_*.json
    for (const id of Object.keys(FICHEIRO_CASO)) {
      for (const cen of Object.keys(caso(id).cenarios)) {
        const r = pedirCaso(id, cen);
        const p = caso(id).cenarios[cen];
        expect(r.problema.alternativas, `${id} ${cen}`).toEqual(p.alternativas);
        // a conversão JSON do Rust pode mudar o último algarismo (1 ulp): compara-se com erro relativo de 1e-12
        r.problema.x_tipico.forEach((linha, i) =>
          linha.forEach((v, j) => {
            const ref = p.x_tipico[i][j];
            expect(Math.abs(v - ref) <= 1e-12 * Math.max(1, Math.abs(ref)), `${id} ${cen} [${i}][${j}]`).toBe(true);
          }),
        );
        expect(r.problema.pesos.map((w) => Math.round(w * 1e12))).toEqual(p.pesos.map((w) => Math.round(w * 1e12)));
      }
    }
  });
  it("o executável nativo embute os mesmos ficheiros de dados/ (include_str!)", () => {
    const lib = readFileSync(resolve(APP_DIR, "src-tauri", "src", "lib.rs"), "utf-8");
    for (const f of Object.values(FICHEIRO_CASO)) expect(lib).toContain(`dados/${f}`);
  });
});
