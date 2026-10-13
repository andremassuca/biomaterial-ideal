// @vitest-environment jsdom
// Ecrã "Simulação FEA e CFD": funções puras (imagem certa, razões ao intacto, números da CFD) conferidas com os ficheiros
// de results/, e o ecrã (separadores, seletores, ampliação da imagem, avisos, o que não existe).
import { existsSync, readFileSync } from "node:fs";
import { resolve } from "node:path";
import { cleanup, fireEvent, render, screen, within } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { Ampliavel } from "../src/componentes/simulacao/Ampliavel";
import { BarraFracao } from "../src/componentes/simulacao/SimulacaoCfd";
import { AVISO_SIMULACAO, Simulacao } from "../src/ecras/Simulacao";
import {
  ESCALA_MAPDL,
  IMAGEM_COMPARACAO_MAPDL,
  LIMIAR_TAWSS_PA,
  MALHAS_SW,
  MALHA_MAPDL,
  MATERIAIS_SW,
  comparacaoFluent,
  imagemMapdl,
  imagemSw,
  linhaMapdl,
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
    expect(imagemSw(m, "5.0", "malha")).toBe("fea_sw/Aco316L_h5p0_malha.png");
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
    expect(src.some((s) => s.endsWith("Ti6Al4V_poroso_h5p0_malha.png"))).toBe(true);
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

describe("mapas de von Mises do MAPDL", () => {
  const CORTES = ["frente", "corte_coronal"] as const;

  it("imagemMapdl escolhe o ficheiro pelo prefixo e pelo corte", () => {
    const m = MATERIAIS_SW.find((x) => x.prefixo === "Aco316L")!;
    expect(imagemMapdl(m, "corte_coronal")).toBe("fea_mapdl/Aco316L_von_mises_corte_coronal.png");
    expect(imagemMapdl(m, "frente")).toBe("fea_mapdl/Aco316L_von_mises_frente.png");
  });

  it("todas as imagens e a montagem existem em public/simulacao", () => {
    for (const m of MATERIAIS_SW)
      for (const c of CORTES) expect(existsSync(resolve(APP_DIR, "public", "simulacao", imagemMapdl(m, c))), `${m.prefixo} ${c}`).toBe(true);
    expect(existsSync(resolve(APP_DIR, "public", "simulacao", IMAGEM_COMPARACAO_MAPDL))).toBe(true);
  });

  it("o JSON da aplicação é igual ao results/fea_haste_mapdl_mapas.json", () => {
    const a = readFileSync(resolve(APP_DIR, "src", "componentes", "simulacao", "mapas_von_mises.json"), "utf-8");
    const r = readFileSync(resolve(RESULTS, "fea_haste_mapdl_mapas.json"), "utf-8");
    expect(JSON.parse(a)).toEqual(JSON.parse(r));
  });

  it("linhaMapdl lê os máximos por corpo e reproduz os valores publicados (results/fea_haste_mapdl.md, ramo extensoes)", () => {
    // máximos globais publicados (MPa): intacto 48,3; 316L 171,9; Co-Cr-Mo 172,4; Ti-6Al-4V 167,1; Ti poroso 163,9
    const publicados: Record<string, number> = { Intacto: 48.3, Aco316L: 171.9, CoCrMo: 172.4, Ti6Al4V: 167.1, Ti6Al4V_poroso: 163.9 };
    for (const [prefixo, v] of Object.entries(publicados)) {
      const l = linhaMapdl(prefixo)!;
      expect(l.vmGlobal, prefixo).toBeCloseTo(v, 0);
      expect(l.vmCortical).toBeGreaterThan(0);
    }
    expect(linhaMapdl("Intacto")!.vmHaste).toBeNull();
    expect(linhaMapdl("Aco316L")!.eHasteGPa).toBeCloseTo(207.5, 1);
    expect(linhaMapdl("não existe")).toBeNull();
  });

  it("a escala é comum (0 a 130 MPa) e a malha é de 3,0 mm", () => {
    expect(ESCALA_MAPDL.min).toBe(0);
    expect(ESCALA_MAPDL.max).toBe(ESCALA_MAPDL.saturacao);
    expect(MALHA_MAPDL).toBe(3);
  });

  it("o separador 'Tensão de von Mises' mostra a imagem do MAPDL, o corte, os máximos e a nota da malha", () => {
    render(<Simulacao />);
    fireEvent.click(screen.getByRole("radio", { name: "Tensão de von Mises" }));
    const src = () => screen.getAllByRole("img").map((i) => i.getAttribute("src") ?? "");
    expect(src().some((s) => s.endsWith("fea_mapdl/Aco316L_von_mises_corte_coronal.png"))).toBe(true);
    expect(src().some((s) => s.endsWith(IMAGEM_COMPARACAO_MAPDL))).toBe(true);
    // o seletor da malha da SOLIDWORKS desaparece: estes mapas são do MAPDL (malha de 3,0 mm)
    expect(screen.queryByRole("radio", { name: /Malha 5,0 mm/ })).toBeNull();
    fireEvent.click(screen.getByRole("radio", { name: "Vista de frente" }));
    expect(src().some((s) => s.endsWith("fea_mapdl/Aco316L_von_mises_frente.png"))).toBe(true);
    fireEvent.click(screen.getByRole("radio", { name: "Ti-6Al-4V poroso" }));
    expect(src().some((s) => s.endsWith("fea_mapdl/Ti6Al4V_poroso_von_mises_frente.png"))).toBe(true);
    expect(screen.getAllByText(/dependem da malha/i).length).toBeGreaterThan(0);
    expect(document.querySelector("[data-mapdl]")?.textContent).toContain("von Mises máxima na haste");
    // a explicação da razão ao intacto é da SOLIDWORKS e não aparece nesta vista
    expect(screen.queryByText(/Razão ao intacto: energia de deformação do osso/)).toBeNull();
    // o fémur intacto não tem haste
    fireEvent.click(screen.getByRole("radio", { name: "Fémur intacto" }));
    expect(document.querySelector("[data-mapdl]")?.textContent).not.toContain("na haste");
  });

  it("voltar à malha repõe o seletor de malha da SOLIDWORKS", () => {
    render(<Simulacao />);
    fireEvent.click(screen.getByRole("radio", { name: "Tensão de von Mises" }));
    fireEvent.click(screen.getByRole("radio", { name: "Malha" }));
    expect(screen.getByRole("radio", { name: /Malha 5,0 mm/ })).toBeTruthy();
  });
});
