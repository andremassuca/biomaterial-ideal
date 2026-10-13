// Funções puras do ecrã "Comparar materiais": quem é melhor em cada propriedade, diferenças e valores em falta.
// Nada aqui lê ficheiros nem desenha: recebe números e devolve números ou etiquetas, por isso é fácil de testar.
import type { LinhaMaterial, Problema, TipoCriterio } from "./tipos";

/** Resultado de uma comparação: "a" ou "b" ganha, "empate", ou null quando não se pode comparar. */
export type Lado = "a" | "b" | "empate" | null;

/** Um valor de propriedade: típico e intervalo; qualquer parte pode faltar. */
export interface ValorProp {
  tipico: number | null;
  min: number | null;
  max: number | null;
}

/** Diferença entre dois valores: absoluta e relativa (fração do maior valor em módulo). */
export interface Diferenca {
  absoluta: number;
  relativa: number | null;
}

/** Uma linha da comparação (uma propriedade dos dois materiais). */
export interface LinhaComparacao {
  criterio: string;
  tipo: TipoCriterio;
  alvo: number | null;
  ordinal: boolean;
  unidade: string | null;
  a: ValorProp;
  b: ValorProp;
  fichaA: LinhaMaterial | null;
  fichaB: LinhaMaterial | null;
  melhor: Lado;
  diferenca: Diferenca | null;
}

/** Diz se um valor é um número utilizável (nem em falta, nem NaN, nem infinito). */
export function temValor(x: number | null | undefined): x is number {
  return typeof x === "number" && Number.isFinite(x);
}

/** Dois números "iguais" para efeitos de empate (tolerância relativa minúscula, só para erros de arredondamento). */
function iguais(a: number, b: number): boolean {
  return Math.abs(a - b) <= 1e-9 * Math.max(1, Math.abs(a), Math.abs(b));
}

/**
 * Quem é melhor, conforme o tipo do critério: benefit, o maior; cost, o menor; target, o mais próximo do alvo.
 * Em linguagem simples: devolve "a" ou "b", "empate" se valerem o mesmo, ou null se faltar um valor
 * (ou o alvo, num critério-alvo), porque nesses casos não se inventa um vencedor.
 */
export function melhorLado(tipo: TipoCriterio, a: number | null, b: number | null, alvo: number | null = null): Lado {
  if (!temValor(a) || !temValor(b)) return null;
  if (tipo === "target") {
    if (!temValor(alvo)) return null;
    const da = Math.abs(a - alvo);
    const db = Math.abs(b - alvo);
    if (iguais(da, db)) return "empate";
    return da < db ? "a" : "b";
  }
  if (iguais(a, b)) return "empate";
  if (tipo === "benefit") return a > b ? "a" : "b";
  return a < b ? "a" : "b";
}

/**
 * Diferença absoluta (|a - b|) e relativa (|a - b| dividido pelo maior módulo dos dois; fica entre 0 e 1 quando os valores têm o mesmo sinal, até 2 se tiverem sinais opostos).
 * Devolve null se faltar um valor; a relativa é null quando os dois valores são zero.
 */
export function diferenca(a: number | null, b: number | null): Diferenca | null {
  if (!temValor(a) || !temValor(b)) return null;
  const absoluta = Math.abs(a - b);
  const maior = Math.max(Math.abs(a), Math.abs(b));
  return { absoluta, relativa: maior === 0 ? null : absoluta / maior };
}

/** Conta quantas propriedades cada lado ganha, os empates e as que não se podem comparar. */
export function resumoComparacao(lados: Lado[]): { a: number; b: number; empates: number; comparaveis: number; total: number } {
  const a = lados.filter((l) => l === "a").length;
  const b = lados.filter((l) => l === "b").length;
  const empates = lados.filter((l) => l === "empate").length;
  return { a, b, empates, comparaveis: a + b + empates, total: lados.length };
}

/**
 * Comprimento relativo (0 a 1) da barra de um valor, tendo o maior módulo dos dois como 100 %.
 * Valores em falta dão 0 (a interface escreve "Sem valor na base" em vez de uma barra).
 */
export function fracaoBarra(v: number | null, a: number | null, b: number | null): number {
  if (!temValor(v)) return 0;
  const maior = Math.max(temValor(a) ? Math.abs(a) : 0, temValor(b) ? Math.abs(b) : 0);
  return maior === 0 ? 0 : Math.min(1, Math.abs(v) / maior);
}

/**
 * Pontuação de 0 a 1 de um valor num critério, para o gráfico radar (1 = melhor entre os materiais do caso).
 * benefit: (v - mín) / (máx - mín); cost: o inverso; target: 1 menos a distância ao alvo sobre a maior distância.
 * Devolve null se o valor faltar; se todos valem o mesmo, 1 (ninguém fica pior).
 */
export function pontuacaoRadar(
  tipo: TipoCriterio,
  v: number | null,
  coluna: (number | null)[],
  alvo: number | null = null,
): number | null {
  if (!temValor(v)) return null;
  const vals = coluna.filter(temValor);
  if (tipo === "target") {
    if (!temValor(alvo)) return null;
    const maxDist = Math.max(...vals.map((x) => Math.abs(x - alvo)));
    return maxDist === 0 ? 1 : 1 - Math.abs(v - alvo) / maxDist;
  }
  const mn = Math.min(...vals);
  const mx = Math.max(...vals);
  if (mx === mn) return 1;
  const t = (v - mn) / (mx - mn);
  return tipo === "benefit" ? t : 1 - t;
}

/**
 * Escolhe, entre as linhas da base de um material, as do componente que cobre mais critérios do caso
 * (um material pode estar em vários dispositivos, por exemplo o 316L na haste e no stent).
 */
export function linhasDoCaso(linhas: LinhaMaterial[], criterios: string[]): LinhaMaterial[] {
  const contagem = new Map<string, number>();
  for (const l of linhas) if (criterios.includes(l.propriedade)) contagem.set(l.componente, (contagem.get(l.componente) ?? 0) + 1);
  let melhor: string | null = null;
  let n = 0;
  for (const [c, k] of contagem) {
    if (k > n) {
      melhor = c;
      n = k;
    }
  }
  return melhor === null ? [] : linhas.filter((l) => l.componente === melhor);
}

/** Lê o valor (típico, mínimo e máximo) de um material num critério do problema; tudo null se não existir. */
export function valorDoProblema(p: Problema, material: string, criterio: string): ValorProp {
  const i = p.alternativas.indexOf(material);
  const j = p.criterios.indexOf(criterio);
  if (i < 0 || j < 0) return { tipico: null, min: null, max: null };
  const lim = (m: number[][]) => (temValor(m[i]?.[j]) ? m[i][j] : null);
  return { tipico: lim(p.x_tipico), min: lim(p.x_min), max: lim(p.x_max) };
}

/**
 * Monta a comparação completa de dois materiais: uma linha por critério do problema, com os valores, as fichas
 * (fonte e estado), quem é melhor e a diferença. As fichas já vêm filtradas pelo caso (ver linhasDoCaso).
 */
export function compararMateriais(
  p: Problema,
  materialA: string,
  materialB: string,
  fichasA: LinhaMaterial[],
  fichasB: LinhaMaterial[],
): LinhaComparacao[] {
  return p.criterios.map((criterio, j) => {
    const a = valorDoProblema(p, materialA, criterio);
    const b = valorDoProblema(p, materialB, criterio);
    const fichaA = fichasA.find((l) => l.propriedade === criterio) ?? null;
    const fichaB = fichasB.find((l) => l.propriedade === criterio) ?? null;
    return {
      criterio,
      tipo: p.tipos[j],
      alvo: p.alvos[j] ?? null,
      ordinal: p.ordinal[j] ?? false,
      unidade: fichaA?.unidade ?? fichaB?.unidade ?? null,
      a,
      b,
      fichaA,
      fichaB,
      melhor: melhorLado(p.tipos[j], a.tipico, b.tipico, p.alvos[j] ?? null),
      diferenca: diferenca(a.tipico, b.tipico),
    };
  });
}
