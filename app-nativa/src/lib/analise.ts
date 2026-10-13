// Uma análise guardável: o que o utilizador viu (caso, perfil, pesos, rankings, Monte Carlo) mais a data e a versão
// dos dados. Serve o histórico local e o relatório em PDF. Nenhum número é escrito à mão: tudo vem dos resultados.
import { APP, CASOS, type IdCaso } from "./dados";
import type { Perfil, Problema, Ranking, Regra, ResumoMonteCarlo } from "./tipos";
import pacote from "../../package.json";

/** Critério com o peso de base e o peso usado nesta análise. */
export interface CriterioAnalise {
  nome: string;
  tipo: "benefit" | "cost" | "target";
  alvo: number | null;
  pesoBase: number | null;
  peso: number;
  /** Verdadeiro para um critério acrescentado por uma regra (não existe no caso de base). */
  novo: boolean;
}

/** Regra do perfil que se ativou, com a justificação escrita e a fonte. */
export interface RegraAnalise {
  id: string;
  condicao: string | null;
  efeito: string;
  alvo: string;
  valor: string | null;
  justificacao: string | null;
  fonte: string | null;
  estado: string | null;
}

export interface Analise {
  id: string;
  /** Data e hora de criação (ISO 8601). */
  criadaEm: string;
  /** Impressão digital dos dados da aplicação nesse momento (muda quando um valor da base muda). */
  versaoDados: string;
  versaoApp: string;
  caso: IdCaso;
  cenario: string;
  perfil: Perfil | null;
  eta: number | null;
  criterios: CriterioAnalise[];
  regras: RegraAnalise[];
  excluidos: string[];
  notas: string[];
  ranking: Ranking;
  apenasTopsis: boolean;
  monteCarlo: ResumoMonteCarlo | null;
  /** O que variou no Monte Carlo ("propriedades" ou "pesos"). */
  monteCarloVariou: "propriedades" | "pesos" | null;
}

/**
 * Impressão digital curta (8 caracteres hexadecimais) de um texto, pelo método FNV-1a.
 * Em linguagem simples: dois textos iguais dão sempre o mesmo código e, se um valor mudar, o código muda.
 */
export function impressaoDigital(texto: string): string {
  let h = 0x811c9dc5;
  for (let i = 0; i < texto.length; i++) {
    h ^= texto.charCodeAt(i);
    h = Math.imul(h, 0x01000193) >>> 0;
  }
  return h.toString(16).padStart(8, "0");
}

let versaoGuardada: string | null = null;

/**
 * Versão dos dados desta aplicação: a impressão digital dos casos e das fichas dos materiais.
 * Em linguagem simples: identifica a base de dados usada, para saber se uma análise antiga foi feita com os
 * mesmos valores de hoje. Calcula-se uma vez e guarda-se.
 */
export function versaoDados(): string {
  if (versaoGuardada === null) {
    versaoGuardada = impressaoDigital(JSON.stringify([CASOS, APP.fichas.materiais]));
  }
  return versaoGuardada;
}

/**
 * Junta os critérios do problema usado com os pesos de base.
 * Em linguagem simples: para cada critério mostra o peso original (se existir) e o peso final; os critérios que só
 * existem no problema ajustado (acrescentados por uma regra) ficam marcados como novos.
 */
export function criteriosAnalise(base: Problema, usado: Problema): CriterioAnalise[] {
  return usado.criterios.map((nome, j) => {
    const i = base.criterios.indexOf(nome);
    return {
      nome,
      tipo: usado.tipos[j],
      alvo: usado.alvos[j] ?? null,
      pesoBase: i >= 0 ? base.pesos[i] : null,
      peso: usado.pesos[j],
      novo: i < 0,
    };
  });
}

/** Resume uma regra do perfil para o relatório (sem os campos internos). */
export function regraAnalise(r: Regra): RegraAnalise {
  return {
    id: r.id,
    condicao: r.condicao,
    efeito: r.efeito,
    alvo: r.alvo_do_efeito,
    valor: r.valor,
    justificacao: r.justificacao,
    fonte: r.fonte,
    estado: r.estado,
  };
}

export interface EntradaAnalise {
  caso: IdCaso;
  cenario: string;
  problemaBase: Problema;
  problemaUsado: Problema;
  ranking: Ranking;
  apenasTopsis?: boolean;
  perfil?: Perfil | null;
  regras?: Regra[];
  excluidos?: string[];
  notas?: string[];
  eta?: number | null;
  monteCarlo?: ResumoMonteCarlo | null;
  monteCarloVariou?: "propriedades" | "pesos" | null;
}

/**
 * Cria a análise a guardar ou a exportar, com data, versão dos dados e versão da aplicação.
 * Em linguagem simples: recolhe tudo o que o ecrã mostra num único objeto que se pode guardar e imprimir.
 */
export function criarAnalise(e: EntradaAnalise, agora: Date = new Date()): Analise {
  return {
    id: `${agora.getTime().toString(36)}-${Math.random().toString(36).slice(2, 7)}`,
    criadaEm: agora.toISOString(),
    versaoDados: versaoDados(),
    versaoApp: pacote.version,
    caso: e.caso,
    cenario: e.cenario,
    perfil: e.perfil && Object.keys(e.perfil).length > 0 ? e.perfil : null,
    eta: e.eta ?? null,
    criterios: criteriosAnalise(e.problemaBase, e.problemaUsado),
    regras: (e.regras ?? []).map(regraAnalise),
    excluidos: e.excluidos ?? [],
    notas: e.notas ?? [],
    ranking: e.ranking,
    apenasTopsis: e.apenasTopsis ?? false,
    monteCarlo: e.monteCarlo ?? null,
    monteCarloVariou: e.monteCarlo ? (e.monteCarloVariou ?? null) : null,
  };
}

/** Material em 1.º lugar de cada método (TOPSIS, WASPAS, VIKOR) e do consenso de Borda; vazio se o método não foi calculado. */
export function primeiros(r: Ranking): { metodo: string; material: string }[] {
  const em = (pos: number[], rotulo: string) => {
    const i = pos.indexOf(1);
    return i >= 0 ? { metodo: rotulo, material: r.alternativas[i] } : null;
  };
  return [em(r.pos_topsis, "TOPSIS"), em(r.pos_waspas, "WASPAS"), em(r.pos_vikor, "VIKOR"), em(r.pos_borda, "Borda")].filter(
    (x): x is { metodo: string; material: string } => x !== null,
  );
}
