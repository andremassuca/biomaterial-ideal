import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

/** Junta classes do Tailwind, resolvendo conflitos (padrão do shadcn/ui). */
export function cn(...entradas: ClassValue[]): string {
  return twMerge(clsx(entradas));
}

/** Lê do localStorage sem rebentar (modo privado, armazenamento bloqueado). */
export function ler(chave: string): string | null {
  try {
    return localStorage.getItem(chave);
  } catch {
    return null;
  }
}

/** Grava no localStorage sem rebentar. */
export function gravar(chave: string, valor: string): void {
  try {
    localStorage.setItem(chave, valor);
  } catch {
    // sem armazenamento: a preferência vale só nesta sessão
  }
}
