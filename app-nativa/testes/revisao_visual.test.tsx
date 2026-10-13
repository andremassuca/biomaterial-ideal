// @vitest-environment jsdom
// Revisão visual (item 8): consenso entre métodos, cartão de resumo, imagem do dispositivo com recurso à ilustração.
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { larguraEixo } from "../src/componentes/GraficoMC";
import { ProvedorDefinicoes } from "../src/lib/definicoes";
import { EXTENSOES_IMAGEM, ImagemDispositivo, urlImagem } from "../src/componentes/ImagemDispositivo";
import { ResumoResultado, consenso, fraseConsenso } from "../src/componentes/ResumoResultado";
import type { Ranking } from "../src/lib/tipos";

afterEach(cleanup);

/** Ranking pequeno de três materiais: A ganha no TOPSIS e na Borda, B ganha no WASPAS e no VIKOR. */
const R = {
  alternativas: ["Material A (A1)", "Material B (B1)", "Material C (C1)"],
  pos_topsis: [1, 2, 3],
  pos_waspas: [2, 1, 3],
  pos_vikor: [2, 1, 3],
  pos_borda: [1, 2, 3],
} as unknown as Ranking;

describe("consenso", () => {
  it("o vencedor é o 1.º da Borda e conta os métodos que concordam", () => {
    const c = consenso(R);
    expect(c.vencedor).toBe("Material A (A1)");
    expect(c.concordam).toBe(1);
    expect(c.total).toBe(3);
    expect(c.metodos.map((m) => m.concorda)).toEqual([true, false, false]);
  });
  it("só com o TOPSIS (modo navegador) há um método", () => {
    const c = consenso(R, true);
    expect(c.total).toBe(1);
    expect(fraseConsenso(c)).toContain("Só o TOPSIS");
  });
  it("a frase diz se todos ou só alguns concordam", () => {
    expect(fraseConsenso({ vencedor: "", concordam: 3, total: 3, metodos: [] })).toBe("Os 3 métodos concordam no 1.º lugar.");
    expect(fraseConsenso({ vencedor: "", concordam: 2, total: 3, metodos: [] })).toBe("2 de 3 métodos concordam no 1.º lugar.");
  });
});

describe("ResumoResultado", () => {
  it("sem recomendação mostra o material em 1.º", () => {
    render(<ResumoResultado ranking={R} />);
    expect(screen.getByRole("region", { name: "Resumo do resultado" })).toBeTruthy();
    expect(screen.queryByText("Sem vencedor universal")).toBeNull();
    expect(document.querySelector("[data-consenso]")?.textContent).toContain("1 de 3");
  });
  it("com recomendação mostra 'Sem vencedor universal' e a frase recebida, sem a reescrever", () => {
    render(<ResumoResultado ranking={R} recomendacao={<p>Frase do projeto.</p>} />);
    expect(screen.getByText("Sem vencedor universal")).toBeTruthy();
    expect(screen.getByText("Frase do projeto.")).toBeTruthy();
  });
});

describe("ImagemDispositivo", () => {
  it("procura webp primeiro e png depois, e dá null sem imagem", () => {
    expect(EXTENSOES_IMAGEM).toEqual(["webp", "png"]);
    expect(urlImagem("haste", {})).toBeNull();
    expect(urlImagem("haste", { "../imagens/inicio/haste.png": "/p.png" })).toBe("/p.png");
    expect(urlImagem("haste", { "../imagens/inicio/haste.png": "/p.png", "../imagens/inicio/haste.webp": "/w.webp" })).toBe("/w.webp");
  });
  it("prefere a imagem do tema (escura ou clara) e cai para a genérica", () => {
    const im = { "../imagens/inicio/stent_escura.webp": "/e.webp", "../imagens/inicio/stent_clara.webp": "/c.webp", "../imagens/inicio/stent.png": "/g.png" };
    expect(urlImagem("stent", im, true)).toBe("/e.webp");
    expect(urlImagem("stent", im, false)).toBe("/c.webp");
    expect(urlImagem("stent", { "../imagens/inicio/stent.png": "/g.png" }, true)).toBe("/g.png");
  });
  it("sem imagem mostra a ilustração SVG e não pede nenhum ficheiro", () => {
    const { container } = render(
      <ProvedorDefinicoes>
        <ImagemDispositivo id="haste" ilustracao="haste" imagens={{}} />
      </ProvedorDefinicoes>,
    );
    expect(container.querySelector("img")).toBeNull();
    expect(container.querySelector("svg")).not.toBeNull();
  });
  it("com imagem mostra-a", () => {
    const { container } = render(
      <ProvedorDefinicoes>
        <ImagemDispositivo id="haste" ilustracao="haste" imagens={{ "../imagens/inicio/haste.png": "/p.png" }} />
      </ProvedorDefinicoes>,
    );
    expect((container.querySelector("img") as HTMLImageElement).src).toContain("/p.png");
  });
});

describe("larguraEixo", () => {
  it("é mais estreita no telemóvel", () => {
    expect(larguraEixo(390)).toBeLessThan(larguraEixo(1440));
  });
});
