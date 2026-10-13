// @vitest-environment jsdom
// Ecrã "Simulação FEA e CFD": funções puras (imagem certa, razões ao intacto, números da CFD) conferidas com os ficheiros
// de results/, e o ecrã (separadores, seletores, ampliação da imagem, avisos, o que não existe).
import { existsSync } from "node:fs";
import { resolve } from "node:path";
import { cleanup, fireEvent, render, screen, within } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { Ampliavel } from "../src/componentes/simulacao/Ampliavel";
import { BarraFracao } from "../src/componentes/simulacao/SimulacaoCfd";
import { AVISO_SIMULACAO, Simulacao } from "../src/ecras/Simulacao";
import {
  LIMIAR_TAWSS_PA,
  MALHAS_SW,
  MATERIAIS_SW,
  comparacaoFluent,
  imagemSw,
  linhaSw,
  malhasCfd,
  materiaisCfd,
  urlSimulacao,
  variacaoPercentual,
  verificacoesCfd,
} from "../src/lib/simulacao";
import { CFD } from "../src/lib/dados";
import { APP_DIR, RESULTS, lerJson } from "./apoio";

afterEach(cleanup);

type SwJson = Record<string, unknown> & {
  casos: Record<string, Record<string, { zonas: Record<string, { energia_J: number }>; vm_max_MPa: number }>>;
};

describe("funções puras da simulação", () => {
  it("as malhas vão da mais fina para a mais grossa", () => {
    expect(MALHAS_SW).toEqual(["3.5", "5.0"]);
  });

  it("urlSimulacao junta a base e a pasta simulacao", () => {
    expect(urlSimulacao("cfd/tawss_mapas.png", "/")).toBe("/simulacao/cfd/tawss_mapas.png");
    expect(urlSimulacao("x.png", "/app")).toBe("/app/simulacao/x.png");
  });

  it("imagemSw escolhe o ficheiro pelo prefixo, malha e vista", () => {
    const m = MATERIAIS_SW.find((x) => x.prefixo === "Aco316L")!;
    expect(imagemSw(m, "3.5", "energia")).toBe("fea_sw/Aco316L_h3p5_densidade_energia.png");
    expect(imagemSw(m, "5.0", "malha")).toBe("fea_sw/Aco316L_h5p0_von_mises.png");
  });

  it("todas as imagens referenciadas existem em public/simulacao", () => {
    for (const m of MATERIAIS_SW)
      for (const h of MALHAS_SW)
        for (const v of ["energia", "malha"] as const)
          expect(existsSync(resolve(APP_DIR, "public", "simulacao", imagemSw(m, h, v)))).toBe(true);
    for (const f of ["fea_sw/gruen_razao_intacto.png", "fea/sed_corte_coronal.png", "fea/comparacao_ferramentas.png", "cfd/tawss_mapas.png", "cfd/poiseuille.png"])
      expect(existsSync(resolve(APP_DIR, "public", "simulacao", f))).toBe(true);
  });

  it("linhaSw bate com results/fea_haste_sw.json (energia, razão ao intacto, von Mises)", () => {
    const sw = lerJson<SwJson>(resolve(RESULTS, "fea_haste_sw.json"));
    for (const [nome, porMalha] of Object.entries(sw.casos)) {
      for (const [h, r] of Object.entries(porMalha)) {
        const l = linhaSw(nome, h)!;
        const ref = sw.casos["Intacto"][h];
        expect(l.g1_mJ).toBeCloseTo(r.zonas["1"].energia_J * 1000, 9);
        expect(l.razao7).toBeCloseTo(r.zonas["7"].energia_J / ref.zonas["7"].energia_J, 9);
        expect(l.vm_max_MPa).toBe(r.vm_max_MPa);
      }
    }
  });

  it("o fémur intacto tem razão 1 e o stress shielding é 1 menos a razão", () => {
    expect(linhaSw("Intacto", "3.5")!.razao1).toBe(1);
    const l = linhaSw("Aço inox 316L", "3.5")!;
    expect(l.shielding1).toBeCloseTo(1 - l.razao1, 12);
    expect(linhaSw("Inexistente", "3.5")).toBeNull();
    expect(linhaSw("Intacto", "9.9")).toBeNull();
  });

  it("variacaoPercentual compara duas malhas", () => {
    expect(variacaoPercentual(2, 2.2)).toBeCloseTo(10, 9);
    expect(variacaoPercentual(0, 1)).toBeNaN();
  });

  it("materiaisCfd ordena do strut mais fino para o mais grosso", () => {
    expect(materiaisCfd(CFD)).toEqual(["Pt-Cr", "316L"]);
    expect(materiaisCfd(null)).toEqual([]);
  });

  it("malhasCfd, comparacaoFluent e verificacoesCfd vêm dos resultados", () => {
    const m = malhasCfd("316L");
    expect(m.map((x) => x.malha)).toEqual(["grossa", "media", "fina"]);
    const f = comparacaoFluent("Pt-Cr")!;
    expect(f.diferencaFracaoPontos).toBeCloseTo((f.fracao_baixa - f.of_fracao_baixa) * 100, 9);
    expect(comparacaoFluent("nada")).toBeNull();
    const v = lerJson<{ poiseuille: { erro_tau: number } }>(resolve(RESULTS, "cfd_verificacoes.json"));
    expect(verificacoesCfd().erroTau).toBe(v.poiseuille.erro_tau);
  });

  it("o limiar de TAWSS é o de results/cfd_stent.md", () => {
    expect(LIMIAR_TAWSS_PA).toBe(0.4);
  });
});

describe("componentes", () => {
  it("Ampliavel abre a janela com a legenda e fecha com Esc", () => {
    render(<Ampliavel src="/a.png" alt="figura de teste" legenda="legenda de teste" />);
    expect(screen.queryByRole("dialog")).toBeNull();
    fireEvent.click(screen.getByRole("button", { name: /Ampliar: figura de teste/ }));
    const d = screen.getByRole("dialog");
    expect(within(d).getByText("legenda de teste")).toBeTruthy();
    fireEvent.keyDown(window, { key: "Escape" });
    expect(screen.queryByRole("dialog")).toBeNull();
  });

  it("BarraFracao mostra a percentagem", () => {
    render(<BarraFracao fracao={0.5} rotulo="teste" />);
    expect(screen.getByRole("img", { name: /teste/ })).toBeTruthy();
  });
});

describe("ecrã Simulação", () => {
  it("mostra o aviso, a imagem da haste e troca com os seletores", () => {
    render(<Simulacao />);
    expect(screen.getAllByText(new RegExp(AVISO_SIMULACAO.replace(".", "\\."))).length).toBeGreaterThan(0);
    const img = () => screen.getAllByRole("img").find((i) => i.getAttribute("src")?.includes("fea_sw/") && i.getAttribute("src")?.includes("h3p5"))!;
    expect(img().getAttribute("src")).toContain("Aco316L_h3p5_densidade_energia.png");
    fireEvent.click(screen.getByRole("radio", { name: "Ti-6Al-4V poroso" }));
    fireEvent.click(screen.getByRole("radio", { name: /Malha 5,0 mm/ }));
    fireEvent.click(screen.getByRole("radio", { name: "Malha" }));
    const src = screen.getAllByRole("img").map((i) => i.getAttribute("src") ?? "");
    expect(src.some((s) => s.endsWith("Ti6Al4V_poroso_h5p0_von_mises.png"))).toBe(true);
  });

  it("o separador do stent mostra os dados da CFD e o que não existe", () => {
    render(<Simulacao />);
    fireEvent.mouseDown(screen.getByRole("tab", { name: "Stent (CFD)" }), { button: 0 });
    expect(screen.getByText("O que ainda não existe nos resultados")).toBeTruthy();
    expect(screen.getByText(/Linhas de corrente/)).toBeTruthy();
    expect(screen.getByText(/Render em 4K/)).toBeTruthy();
    expect(screen.getAllByText("Pt-Cr").length).toBeGreaterThan(0);
  });
});
