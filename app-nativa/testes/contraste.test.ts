// Contraste das cores de texto do tema (WCAG 2.x): selos (Etiqueta), texto azul pequeno e texto secundário,
// nos temas claro e escuro, sobre a superfície e sobre a superfície 2, lido de src/estilos/tema.css.
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";
import { APP_DIR } from "./apoio";

type Rgb = [number, number, number];

/** Variáveis "r g b" de um bloco do tema (claro ou escuro). */
function variaveis(tema: "claro" | "escuro"): Record<string, Rgb> {
  const css = readFileSync(resolve(APP_DIR, "src", "estilos", "tema.css"), "utf-8");
  const seletor = tema === "claro" ? /:root,\s*:root\[data-tema="claro"\]\s*\{([^}]*)\}/ : /:root\[data-tema="escuro"\]\s*\{([^}]*)\}/;
  const bloco = css.match(seletor)?.[1] ?? "";
  const out: Record<string, Rgb> = {};
  for (const m of bloco.matchAll(/--([\w-]+):\s*(\d+)\s+(\d+)\s+(\d+);/g)) out[m[1]] = [Number(m[2]), Number(m[3]), Number(m[4])];
  return out;
}

/** Luminância relativa e razão de contraste (WCAG 2.x). */
function luminancia([r, g, b]: Rgb): number {
  const f = (v: number) => {
    const c = v / 255;
    return c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4;
  };
  return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b);
}
export function contraste(a: Rgb, b: Rgb): number {
  const [x, y] = [luminancia(a), luminancia(b)].sort((p, q) => q - p);
  return (x + 0.05) / (y + 0.05);
}
/** Cor `cor` com opacidade `alfa` sobre o fundo (como bg-aviso/15 do Tailwind). */
function sobre(cor: Rgb, fundo: Rgb, alfa: number): Rgb {
  return cor.map((v, i) => v * alfa + fundo[i] * (1 - alfa)) as Rgb;
}

describe.each(["claro", "escuro"] as const)("tema %s", (tema) => {
  const v = variaveis(tema);
  const fundos = { superficie: v.superficie, "superficie-2": v["superficie-2"], fundo: v.fundo };

  it("lê as variáveis do tema", () => {
    for (const k of ["superficie", "superficie-2", "fundo", "texto", "texto-2", "acento", "acento-texto", "aviso", "perigo", "sucesso"]) {
      expect(v[k], k).toBeDefined();
    }
  });

  it.each(Object.entries(fundos))("selos com pelo menos 4,5:1 sobre %s", (_, fundo) => {
    const selos: [string, Rgb, Rgb][] = [
      ["acento", v["acento-texto"], v.acento],
      ["aviso", v.aviso, v.aviso],
      ["perigo", v.perigo, v.perigo],
      ["sucesso", v.sucesso, v.sucesso],
    ];
    for (const [nome, texto, tinta] of selos) {
      expect(contraste(texto, sobre(tinta, fundo, 0.15)), nome).toBeGreaterThanOrEqual(4.5);
    }
    expect(contraste(v["texto-2"], fundo), "neutro").toBeGreaterThanOrEqual(4.5);
  });

  it.each(Object.entries(fundos))("texto azul pequeno e texto secundário com pelo menos 4,5:1 sobre %s", (_, fundo) => {
    expect(contraste(v["acento-texto"], fundo)).toBeGreaterThanOrEqual(4.5);
    // item ativo do menu e material escolhido: fundo acento a 10 %
    expect(contraste(v["acento-texto"], sobre(v.acento, fundo, 0.1))).toBeGreaterThanOrEqual(4.5);
    expect(contraste(v["texto-2"], fundo)).toBeGreaterThanOrEqual(4.5);
  });

  it("o acento puro (títulos grandes, 28 px negrito) dá pelo menos 3:1", () => {
    expect(contraste(v.acento, v.fundo)).toBeGreaterThanOrEqual(3);
  });
});
