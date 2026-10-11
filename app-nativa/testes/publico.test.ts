// O texto público das notas e das fontes não mostra marcas internas de trabalho, e os dados ficam iguais.
import { readFileSync, readdirSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";
import { textoPublico } from "../src/lib/publico";
import { APP_DIR } from "./apoio";

/** Todos os textos dos JSON de dados/ (notas, fontes, justificações, textos de apoio). */
function textosDosDados(): string[] {
  const out: string[] = [];
  const andar = (o: unknown) => {
    if (typeof o === "string") out.push(o);
    else if (Array.isArray(o)) o.forEach(andar);
    else if (o && typeof o === "object") Object.values(o).forEach(andar);
  };
  const pasta = resolve(APP_DIR, "dados");
  for (const f of readdirSync(pasta).filter((n) => n.endsWith(".json"))) {
    const t = readFileSync(resolve(pasta, f), "utf-8").trim();
    if (t) andar(JSON.parse(t));
  }
  return out;
}

describe("textoPublico", () => {
  it("tira a lista interna do estatuto e a instrução de trabalho", () => {
    expect(
      textoPublico(
        "valor anterior: 1-10 MPa; Muito dependente da geometria/porosidade: registar a porosidade do estudo de onde vem o valor; Estatuto [confirmar]: Rezwan et al. 2006; uso clínico",
      ),
    ).toBe("valor anterior: 1-10 MPa; Muito dependente da geometria/porosidade");
    expect(textoPublico("Estatuto [confirmar]: fonte a indicar")).toBe("");
  });

  it("troca as marcas [confirmar] e ': confirmar' pela palavra do selo (a verificar)", () => {
    expect(textoPublico("Navarro et al. 2008; Karageorgiou & Kaplan 2005: confirmar")).toBe(
      "Navarro et al. 2008; Karageorgiou & Kaplan 2005 (a verificar)",
    );
    expect(textoPublico("5 µm/ano depois do 3.º [confirmar: só o resumo]; valores abaixo")).toBe(
      "5 µm/ano depois do 3.º (a verificar); valores abaixo",
    );
    expect(textoPublico("magnetização fraca [confirmar]. Esterilização")).toBe("magnetização fraca (a verificar). Esterilização");
    expect(textoPublico("o resumo não diz que o BioGran é 45S5 (a confirmar); valor")).toBe(
      "o resumo não diz que o BioGran é 45S5 (a verificar); valor",
    );
  });

  it("'valor a confirmar' passa a 'valor a verificar'", () => {
    expect(textoPublico("tempo de reabsorção: valor a confirmar na fonte")).toBe(
      "tempo de reabsorção: valor a verificar na fonte",
    );
  });

  it("'por confirmar' passa a 'por verificar' (nota do MP35N, 11 out)", () => {
    expect(textoPublico("não foram avaliadas; espessura do Onyx por confirmar")).toBe(
      "não foram avaliadas; espessura do Onyx por verificar",
    );
  });

  it("não mexe em texto sem marcas nem em 'confirmado'", () => {
    const t = "material L-605 confirmado no FDA SSED P070015; alergia ao titânio confirmada por teste";
    expect(textoPublico(t)).toBe(t);
    expect(textoPublico(null)).toBeNull();
  });

  it("nenhum texto dos dados fica com marcas internas depois de limpo", () => {
    const textos = textosDosDados();
    expect(textos.some((t) => t.includes("[confirmar"))).toBe(true); // os dados continuam com a informação
    for (const t of textos) {
      const p = textoPublico(t);
      expect(p).not.toMatch(/\[confirmar/);
      expect(p).not.toMatch(/Estatuto \[/);
      expect(p).not.toMatch(/registar a porosidade/);
      // "confirmar" só fica em frases que não são marcas (ex.: "não foi possível confirmar")
      for (const m of p.matchAll(/.{0,30}\bconfirmar\b/g)) expect(m[0]).toMatch(/possível confirmar/);
    }
  });
});
