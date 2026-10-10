// Port mínimo do TOPSIS do núcleo Rust (crates/mcdm/src/normalizacao.rs e metodos.rs).
// Serve para o modo navegador (sem Tauri) e para o exemplo passo a passo do ecrã "Porquê".
// Os outros métodos (WASPAS, VIKOR, Borda), o Monte Carlo e os perfis só existem no núcleo Rust.
import type { Problema, TipoCriterio } from "./tipos";

/** Valor de referência T: máximo (benefício), mínimo (custo) ou o valor-alvo. */
export function valorReferencia(coluna: number[], tipo: TipoCriterio, alvo: number | null): number {
  if (tipo === "benefit") return Math.max(...coluna);
  if (tipo === "cost") return Math.min(...coluna);
  if (alvo === null) throw new Error("critério-alvo sem valor-alvo");
  return alvo;
}

/** Normalização com critérios-alvo (eq. 2 de Petković et al. 2025): 1 = melhor, 0 = pior. */
export function normalizarColuna(coluna: number[], tipo: TipoCriterio, alvo: number | null): number[] {
  const t = valorReferencia(coluna, tipo, alvo);
  const denom = Math.max(Math.max(...coluna), t) - Math.min(Math.min(...coluna), t);
  if (denom === 0) return coluna.map(() => 1);
  return coluna.map((x) => 1 - Math.abs(x - t) / denom);
}

export interface PassosTopsis {
  normalizada: number[][];
  pesada: number[][];
  ideal: number[];
  antiIdeal: number[];
  dMais: number[];
  dMenos: number[];
  c: number[];
}

/** TOPSIS com todos os passos intermédios (para explicar o cálculo). */
export function topsisPassos(x: number[][], pesos: number[], tipos: TipoCriterio[], alvos: (number | null)[]): PassosTopsis {
  const m = x.length;
  const n = pesos.length;
  const normalizada: number[][] = Array.from({ length: m }, () => new Array(n).fill(0));
  for (let j = 0; j < n; j++) {
    const col = normalizarColuna(x.map((l) => l[j]), tipos[j], alvos[j]);
    for (let i = 0; i < m; i++) normalizada[i][j] = col[i];
  }
  const pesada = normalizada.map((l) => l.map((r, j) => r * pesos[j]));
  const ideal = Array.from({ length: n }, (_, j) => Math.max(...pesada.map((l) => l[j])));
  const antiIdeal = Array.from({ length: n }, (_, j) => Math.min(...pesada.map((l) => l[j])));
  const dMais = pesada.map((l) => Math.sqrt(l.reduce((s, v, j) => s + (v - ideal[j]) ** 2, 0)));
  const dMenos = pesada.map((l) => Math.sqrt(l.reduce((s, v, j) => s + (v - antiIdeal[j]) ** 2, 0)));
  const c = dMenos.map((dn, i) => dn / (dMais[i] + dn));
  return { normalizada, pesada, ideal, antiIdeal, dMais, dMenos, c };
}

/** Posições (1 = melhor) com empates na menor posição, como no núcleo. */
export function posicoes(pontuacoes: number[], maiorEMelhor: boolean): number[] {
  return pontuacoes.map((a) => 1 + pontuacoes.filter((b) => (maiorEMelhor ? b > a : b < a)).length);
}

/** Divide os pesos pela soma. */
export function renormalizar(pesos: number[]): number[] {
  const s = pesos.reduce((a, b) => a + b, 0);
  return pesos.map((w) => w / s);
}

/** Tira materiais de um problema (como perfis::excluir); erro se ficarem menos de dois. */
export function excluirMateriais(p: Problema, materiais: string[]): { problema: Problema; saem: string[] } {
  const ficam = p.alternativas.map((_, i) => i).filter((i) => !materiais.includes(p.alternativas[i]));
  if (ficam.length < 2) throw new Error("a exclusão deixa menos de dois materiais");
  return {
    problema: {
      ...p,
      alternativas: ficam.map((i) => p.alternativas[i]),
      x_min: ficam.map((i) => p.x_min[i]),
      x_max: ficam.map((i) => p.x_max[i]),
      x_tipico: ficam.map((i) => p.x_tipico[i]),
    },
    saem: p.alternativas.filter((a) => materiais.includes(a)),
  };
}
