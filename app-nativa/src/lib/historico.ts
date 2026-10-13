// Histórico de análises guardado só neste computador (localStorage). Nada é enviado para fora.
import type { Analise } from "./analise";
import { gravar, ler } from "./utils";

const CHAVE = "biomat.historico";
/** Máximo de análises guardadas; ao passar o limite, as mais antigas saem. */
export const MAXIMO_HISTORICO = 50;

/** Avisa os ecrãs abertos de que o histórico mudou. */
const EVENTO = "biomat-historico";

/** Uma análise tem a forma esperada? (protege contra dados antigos ou estragados no armazenamento) */
export function analiseValida(x: unknown): x is Analise {
  if (typeof x !== "object" || x === null) return false;
  const a = x as Record<string, unknown>;
  return (
    typeof a.id === "string" &&
    typeof a.criadaEm === "string" &&
    typeof a.versaoDados === "string" &&
    typeof a.caso === "string" &&
    typeof a.cenario === "string" &&
    Array.isArray(a.criterios) &&
    typeof a.ranking === "object" &&
    a.ranking !== null
  );
}

/**
 * Lê o histórico, da análise mais recente para a mais antiga.
 * Em linguagem simples: se não houver nada guardado, ou o que está guardado estiver estragado, devolve uma lista vazia.
 */
export function lerHistorico(): Analise[] {
  const texto = ler(CHAVE);
  if (!texto) return [];
  try {
    const lista: unknown = JSON.parse(texto);
    return Array.isArray(lista) ? lista.filter(analiseValida) : [];
  } catch {
    return [];
  }
}

function escrever(lista: Analise[]): void {
  gravar(CHAVE, JSON.stringify(lista));
  try {
    window.dispatchEvent(new Event(EVENTO));
  } catch {
    // sem janela (testes sem DOM): ninguém a avisar
  }
}

/** Guarda uma análise no início do histórico; devolve a lista nova. */
export function guardarAnalise(a: Analise): Analise[] {
  const lista = [a, ...lerHistorico().filter((x) => x.id !== a.id)].slice(0, MAXIMO_HISTORICO);
  escrever(lista);
  return lista;
}

/** Tira uma análise do histórico; devolve a lista nova. */
export function removerAnalise(id: string): Analise[] {
  const lista = lerHistorico().filter((x) => x.id !== id);
  escrever(lista);
  return lista;
}

/** Apaga todo o histórico. */
export function limparHistorico(): void {
  escrever([]);
}

/** Subscreve as mudanças ao histórico (a mesma janela ou outra aberta); devolve a função que cancela. */
export function aoMudarHistorico(f: () => void): () => void {
  window.addEventListener(EVENTO, f);
  window.addEventListener("storage", f);
  return () => {
    window.removeEventListener(EVENTO, f);
    window.removeEventListener("storage", f);
  };
}
