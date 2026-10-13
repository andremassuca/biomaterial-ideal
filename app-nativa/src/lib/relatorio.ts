// Estado partilhado do relatório aberto (a análise que se vai imprimir ou guardar em PDF) e contagens para o relatório.
import { useSyncExternalStore } from "react";
import type { Analise } from "./analise";
import { APP, CASOS } from "./dados";

let atual: Analise | null = null;
const ouvintes = new Set<() => void>();

function avisar(): void {
  ouvintes.forEach((f) => f());
}

/** Abre o relatório de uma análise (aparece por cima da aplicação, pronto a imprimir). */
export function abrirRelatorio(a: Analise): void {
  atual = a;
  avisar();
}

/** Fecha o relatório. */
export function fecharRelatorio(): void {
  atual = null;
  avisar();
}

/** Hook: a análise aberta no relatório, ou null. */
export function useRelatorio(): Analise | null {
  return useSyncExternalStore(
    (f) => {
      ouvintes.add(f);
      return () => ouvintes.delete(f);
    },
    () => atual,
    () => null,
  );
}

/** Agrupa o estado de um valor da base na palavra principal ("Verificado (fornecedor)" conta como "Verificado"). */
export function estadoBase(estado: string | null): string {
  if (!estado) return "Sem estado";
  return estado.replace(/\s*\(.*\)\s*$/, "").trim() || "Sem estado";
}

/**
 * Conta, por material de uma análise, quantos valores da base têm cada estado.
 * Em linguagem simples: mostra no relatório quantos valores usados estão verificados e quantos ainda estão por
 * verificar, para quem lê saber quanto pode confiar neles.
 */
export function contagemEstados(
  caso: keyof typeof CASOS,
  materiais: string[],
): { material: string; total: number; porEstado: Record<string, number> }[] {
  const alvo = CASOS[caso].caso_componente;
  return materiais.map((material) => {
    const linhas = APP.fichas.materiais.filter((l) => `${l.caso} | ${l.componente}` === alvo && l.material === material);
    const porEstado: Record<string, number> = {};
    for (const l of linhas) {
      const e = estadoBase(l.estado);
      porEstado[e] = (porEstado[e] ?? 0) + 1;
    }
    return { material, total: linhas.length, porEstado };
  });
}
