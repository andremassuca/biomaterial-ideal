// Port em TypeScript do WASPAS, do VIKOR e do consenso de Borda do núcleo Rust (crates/mcdm/src/metodos.rs), junto
// com o TOPSIS de topsis.ts. Serve só para analisar materiais personalizados (que o núcleo Rust não conhece) e é
// verificado contra o núcleo em testes/metodos.test.ts: para os materiais da base dá os mesmos números.
import { posicoes, topsisPassos, valorReferencia } from "./topsis";
import type { Problema, Ranking, TipoCriterio } from "./tipos";

const coluna = (x: number[][], j: number): number[] => x.map((l) => l[j]);

/**
 * Normalização própria do WASPAS (eqs. 9-13 de Petković et al. 2025): 1 = melhor.
 * Em linguagem simples: cada valor passa a um número entre 0 e 1 conforme o critério seja de benefício (quanto
 * maior melhor), de custo (quanto menor melhor) ou de alvo (quanto mais perto do valor-alvo melhor).
 */
export function normalizarWaspas(x: number[][], tipos: TipoCriterio[], alvos: (number | null)[]): number[][] {
  const r = x.map((l) => new Array<number>(l.length).fill(0));
  tipos.forEach((t, j) => {
    const c = coluna(x, j);
    const lo = Math.min(...c);
    const hi = Math.max(...c);
    const tv = valorReferencia(c, t, alvos[j]);
    c.forEach((xi, i) => {
      if (t === "benefit" || (t === "target" && tv === hi)) r[i][j] = xi / hi;
      else if (t === "cost" && lo <= 0) r[i][j] = hi > 0 ? 1 - xi / hi : 1;
      else if (t === "cost" || (t === "target" && tv === lo)) r[i][j] = lo / xi;
      else if (tv < lo) r[i][j] = 1 - (xi - tv) / hi;
      else if (tv > hi) r[i][j] = 1 - (tv - xi) / tv;
      else r[i][j] = 1 - Math.abs(xi - tv) / (hi - lo);
    });
  });
  return r;
}

/** WASPAS com λ = 0,5: Q = λ·soma pesada + (1 - λ)·produto pesado; maior Q = melhor. */
export function waspas(x: number[][], pesos: number[], tipos: TipoCriterio[], alvos: (number | null)[], lam = 0.5): number[] {
  return normalizarWaspas(x, tipos, alvos).map((l) => {
    const q1 = l.reduce((s, a, j) => s + a * pesos[j], 0);
    const q2 = l.reduce((p, a, j) => p * Math.pow(a, pesos[j]), 1);
    return lam * q1 + (1 - lam) * q2;
  });
}

/** Igual a numpy.isclose com as tolerâncias por omissão (rtol 1e-5, atol 1e-8). */
function quaseIgual(a: number, b: number): boolean {
  return Math.abs(a - b) <= 1e-8 + 1e-5 * Math.abs(b);
}

/**
 * VIKOR abrangente com critérios-alvo (eqs. 17-19), com v = 0,5.
 * Em linguagem simples: mede a distância de cada material ao valor ideal de cada critério; S soma as distâncias
 * pesadas, R guarda a pior e P mistura as duas (menor é melhor nos três).
 */
export function vikor(x: number[][], pesos: number[], tipos: TipoCriterio[], alvos: (number | null)[]): { s: number[]; r: number[]; p: number[] } {
  const m = x.length;
  const n = pesos.length;
  const t: number[] = [];
  const a: number[] = [];
  for (let j = 0; j < n; j++) {
    const c = coluna(x, j);
    t[j] = valorReferencia(c, tipos[j], alvos[j]);
    const aj = Math.max(Math.max(...c), t[j]) - Math.min(Math.min(...c), t[j]);
    a[j] = aj === 0 ? 1 : aj;
  }
  const s = new Array<number>(m).fill(0);
  const r = new Array<number>(m).fill(-Infinity);
  for (let i = 0; i < m; i++) {
    for (let j = 0; j < n; j++) {
      const e = pesos[j] * (1 - Math.exp(-Math.abs(x[i][j] - t[j]) / a[j]));
      s[i] += e;
      r[i] = Math.max(r[i], e);
    }
  }
  const [sMin, sMax, rMin, rMax] = [Math.min(...s), Math.max(...s), Math.min(...r), Math.max(...r)];
  const sConst = quaseIgual(sMax, sMin);
  const rConst = quaseIgual(rMax, rMin);
  const v = 0.5;
  const p = s.map((si, i) => {
    if (sConst && rConst) return 0;
    if (sConst) return (r[i] - rMin) / (rMax - rMin);
    if (rConst) return (si - sMin) / (sMax - sMin);
    return ((si - sMin) / (sMax - sMin)) * v + ((r[i] - rMin) / (rMax - rMin)) * (1 - v);
  });
  return { s, r, p };
}

/**
 * Consenso de Borda: cada método dá (m - posição) pontos; ordena pela soma e, em caso de empate, pela posição no
 * TOPSIS (e depois pela ordem dos materiais). Devolve os pontos e as posições.
 */
export function borda(pos: [number[], number[], number[]], posTopsis: number[]): { pontos: number[]; posicoes: number[] } {
  const m = posTopsis.length;
  const pontos = posTopsis.map((_, i) => pos.reduce((s, p) => s + (m - p[i]), 0));
  const ordem = pontos.map((_, i) => i).sort((a, b) => pontos[b] - pontos[a] || posTopsis[a] - posTopsis[b] || a - b);
  const posicoesBorda = new Array<number>(m).fill(0);
  ordem.forEach((i, k) => (posicoesBorda[i] = k + 1));
  return { pontos, posicoes: posicoesBorda };
}

/**
 * Corre os três métodos e o consenso de Borda sobre um problema, com os pesos do próprio problema.
 * Em linguagem simples: faz o mesmo que o núcleo Rust, para problemas com materiais acrescentados pelo utilizador.
 */
export function avaliarLocal(p: Problema): Ranking {
  const { x_tipico: x, pesos, tipos, alvos } = p;
  const c = topsisPassos(x, pesos, tipos, alvos).c;
  const q = waspas(x, pesos, tipos, alvos);
  const v = vikor(x, pesos, tipos, alvos);
  const [pt, pw, pv] = [posicoes(c, true), posicoes(q, true), posicoes(v.p, false)];
  const b = borda([pt, pw, pv], pt);
  return {
    alternativas: p.alternativas,
    c_topsis: c,
    q_waspas: q,
    s_vikor: v.s,
    r_vikor: v.r,
    p_vikor: v.p,
    pos_topsis: pt,
    pos_waspas: pw,
    pos_vikor: pv,
    pontos_borda: b.pontos,
    pos_borda: b.posicoes,
  };
}
