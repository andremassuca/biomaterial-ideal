// Paleta de Okabe e Ito (segura para daltónicos), igual à das figuras (scripts/figuras.py, COR_MATERIAL).
// No tema escuro usa-se a mesma cor de base com mais luminância, para manter o contraste sobre #0b1b2e.
import type { IdCaso } from "./dados";

type Base = "azul" | "laranja" | "verde" | "cinza" | "ceu" | "vermelhao" | "rosa" | "amarelo";

const CLARO: Record<Base, string> = {
  azul: "#0072B2",
  laranja: "#E69F00",
  verde: "#009E73",
  cinza: "#999999",
  ceu: "#56B4E9",
  vermelhao: "#D55E00",
  rosa: "#CC79A7",
  amarelo: "#F0E442",
};

const ESCURO: Record<Base, string> = {
  azul: "#3C9BDB",
  laranja: "#F2B33D",
  verde: "#2EC79B",
  cinza: "#B5B5B5",
  ceu: "#7CC6EF",
  vermelhao: "#F07A33",
  rosa: "#DE9CC2",
  amarelo: "#F4EA6E",
};

const POR_MATERIAL: Partial<Record<IdCaso, Record<string, Base>>> = {
  Haste: {
    "Ti-6Al-4V ELI": "azul",
    "Co-Cr-Mo forjado": "laranja",
    "Ti-13Nb-13Zr": "verde",
    "Aço inox 316L": "cinza",
    "Ti cp grau 4": "amarelo",
    "Ti-35Nb-7Zr-5Ta (TNZT)": "rosa",
  },
  Stent: {
    "Pt-Cr": "azul",
    "Co-Cr L605": "laranja",
    "Co-Ni-Cr-Mo MP35N": "verde",
    "Aço inox 316L": "cinza",
    "Liga de Mg WE43 (bioabsorvível)": "vermelhao",
    "PLLA (bioabsorvível)": "rosa",
    "Nitinol (autoexpansível)": "amarelo",
  },
  Scaffold: {
    "β-TCP poroso": "azul",
    "Compósito PCL/β-TCP (impressão 3D)": "laranja",
    "Vidro bioativo 45S5 poroso": "verde",
    "Quitosano/HA (liofilizado)": "cinza",
    PCL: "ceu",
    "Hidroxiapatite (HA) porosa": "vermelhao",
    PLLA: "rosa",
    "PLGA 50:50": "amarelo",
  },
};

const ORDEM: Base[] = ["azul", "laranja", "verde", "vermelhao", "rosa", "ceu", "amarelo", "cinza"];

/** Cor de um material num caso; nos casos sem tabela, pela ordem dos materiais. */
export function corMaterial(caso: IdCaso, material: string, indice: number, escuro: boolean): string {
  const base = POR_MATERIAL[caso]?.[material] ?? ORDEM[indice % ORDEM.length];
  return (escuro ? ESCURO : CLARO)[base];
}

/** Cores dos três métodos e do consenso (tons do tema, distintos das cores dos materiais). */
export const COR_METODO = {
  TOPSIS: "var(--cor-topsis)",
  WASPAS: "var(--cor-waspas)",
  VIKOR: "var(--cor-vikor)",
  Borda: "var(--cor-borda)",
} as const;
