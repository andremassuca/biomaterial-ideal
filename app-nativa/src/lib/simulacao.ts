// Funções puras do ecrã "Simulação FEA e CFD": escolher a imagem certa, calcular razões a partir das energias e
// ler os números da CFD por material. Nenhum resultado é escrito à mão: tudo vem de results/ (via
// componentes/simulacao/dados_simulacao.json, extraído de results/fea_haste_sw.json, cfd_fluent.json,
// cfd_verificacoes.json e cfd_malhas.csv) e dos dados da aplicação.
import dados from "@/componentes/simulacao/dados_simulacao.json";

/** Limiar de tensão de corte na parede (Pa) usado como referência da CFD (docs/CFD_STENT.md: limiar operacional). */
export const LIMIAR_TAWSS_PA = 0.4;

/** Vistas guardadas de cada estudo da SOLIDWORKS: energia de deformação (com barra de cores) e malha. */
export type VistaSw = "energia" | "malha";

/** Material do estudo da SOLIDWORKS: nome no ficheiro de resultados, prefixo das imagens e nome para mostrar. */
export interface MaterialSw {
  chave: string;
  prefixo: string;
  nome: string;
  /** nome na base de dados da aplicação (APP.fea, nomes dos materiais); null no fémur intacto */
  materialBase: string | null;
}

export const MATERIAIS_SW: MaterialSw[] = [
  { chave: "Intacto", prefixo: "Intacto", nome: "Fémur intacto", materialBase: null },
  { chave: "Aço inox 316L", prefixo: "Aco316L", nome: "Aço inox 316L", materialBase: "Aço inox 316L" },
  { chave: "Co-Cr-Mo forjado", prefixo: "CoCrMo", nome: "Co-Cr-Mo forjado", materialBase: "Co-Cr-Mo forjado" },
  { chave: "Ti-6Al-4V ELI", prefixo: "Ti6Al4V", nome: "Ti-6Al-4V ELI", materialBase: "Ti-6Al-4V ELI" },
  { chave: "Ti-6Al-4V poroso", prefixo: "Ti6Al4V_poroso", nome: "Ti-6Al-4V poroso", materialBase: "Ti-6Al-4V poroso" },
];

/** Malhas da SOLIDWORKS disponíveis (mm), da mais fina para a mais grossa, como texto ("3.5", "5.0"). */
export const MALHAS_SW: string[] = [...(dados.sw.malhas_mm as number[])].sort((a, b) => a - b).map((h) => h.toFixed(1));

/**
 * Caminho público de uma imagem copiada para public/simulacao/.
 * Em linguagem simples: junta a pasta base da aplicação com o caminho relativo da imagem.
 */
export function urlSimulacao(relativo: string, base: string = import.meta.env.BASE_URL): string {
  const b = base.endsWith("/") ? base : `${base}/`;
  return `${b}simulacao/${relativo}`;
}

/**
 * Ficheiro (relativo a public/simulacao/) da imagem de um material numa malha e vista.
 * Em linguagem simples: por exemplo "fea_sw/Aco316L_h3p5_densidade_energia.png".
 */
export function imagemSw(material: MaterialSw, malha: string, vista: VistaSw): string {
  const h = `h${malha.replace(".", "p")}`;
  const sufixo = vista === "energia" ? "densidade_energia" : "von_mises";
  return `fea_sw/${material.prefixo}_${h}_${sufixo}.png`;
}

/** Números de um estudo da SOLIDWORKS, com as razões ao fémur intacto da mesma malha. */
export interface LinhaSw {
  material: string;
  malha: string;
  nos: number;
  elementos: number;
  g1_mJ: number;
  g7_mJ: number;
  /** energia na zona de Gruen 1 (ou 7) a dividir pela do fémur intacto, mesma malha */
  razao1: number;
  razao7: number;
  /** stress shielding = 1 - razão (negativo: mais energia que o osso intacto) */
  shielding1: number;
  shielding7: number;
  vm_max_MPa: number;
  ures_max_mm: number;
}

type CasoSw = Record<string, { nos: number; elementos: number; g1_J: number; g7_J: number; vm_max_MPa: number; ures_max_mm: number }>;
const CASOS_SW = dados.sw.casos as Record<string, CasoSw>;

/**
 * Números de um material numa malha (energia em mJ, razão ao intacto, tensão e deslocamento máximos).
 * Em linguagem simples: lê o resultado da SOLIDWORKS e divide pela energia do fémur intacto; devolve null se o
 * material ou a malha não existirem nos resultados.
 */
export function linhaSw(material: string, malha: string): LinhaSw | null {
  const r = CASOS_SW[material]?.[malha];
  const ref = CASOS_SW["Intacto"]?.[malha];
  if (!r || !ref) return null;
  const razao1 = r.g1_J / ref.g1_J;
  const razao7 = r.g7_J / ref.g7_J;
  return {
    material,
    malha,
    nos: r.nos,
    elementos: r.elementos,
    g1_mJ: r.g1_J * 1000,
    g7_mJ: r.g7_J * 1000,
    razao1,
    razao7,
    shielding1: 1 - razao1,
    shielding7: 1 - razao7,
    vm_max_MPa: r.vm_max_MPa,
    ures_max_mm: r.ures_max_mm,
  };
}

/** Variação relativa (em %) entre duas malhas de uma grandeza, para mostrar a sensibilidade à malha. */
export function variacaoPercentual(a: number, b: number): number {
  return a === 0 ? NaN : (Math.abs(a - b) / Math.abs(a)) * 100;
}

// --------------------------------------------------------------------------------------------- CFD

/** Resultado de um strut na CFD pulsátil (formato de dados/cfd_stent.json). */
export interface ResultadoCfd {
  espessura_um: number;
  tau_media: number;
  fracao_baixa: number;
  osi_media: number;
  fracao_osi: number;
  area_mm2: number;
}

/**
 * Materiais da CFD por ordem de strut mais fino primeiro (Pt-Cr, 316L).
 * Em linguagem simples: ordena as entradas pela espessura do strut, do mais fino para o mais grosso.
 */
export function materiaisCfd(cfd: Record<string, ResultadoCfd> | null | undefined): string[] {
  if (!cfd) return [];
  return Object.entries(cfd)
    .sort((a, b) => a[1].espessura_um - b[1].espessura_um)
    .map(([m]) => m);
}

/** Resultado de uma malha na convergência (results/cfd_malhas.csv). */
export interface LinhaMalhaCfd {
  material: string;
  malha: string;
  celulas: number;
  delta_um: number;
  tau_media: number;
  fracao_baixa: number;
}

/** Linhas da convergência de malha de um material, da malha mais grossa para a mais fina. */
export function malhasCfd(material: string): LinhaMalhaCfd[] {
  return (dados.cfd.malhas as LinhaMalhaCfd[]).filter((l) => l.material === material).sort((a, b) => a.celulas - b.celulas);
}

/** Comparação OpenFOAM e Fluent (escoamento estacionário, malha média) de um material; null se não existir. */
export function comparacaoFluent(material: string) {
  const f = (dados.cfd.fluent as Record<string, { tau_media: number; fracao_baixa: number; faces: number; of_tau_media: number; of_fracao_baixa: number }>)[material];
  if (!f) return null;
  return {
    ...f,
    /** diferença da fração abaixo do limiar, em pontos percentuais (Fluent menos OpenFOAM) */
    diferencaFracaoPontos: (f.fracao_baixa - f.of_fracao_baixa) * 100,
  };
}

/** Erros do teste de Poiseuille (tubo sem stent) e variações de verificação, em fração (0,0024 = 0,24 %). */
export function verificacoesCfd() {
  const v = dados.cfd.verificacoes;
  return {
    erroTau: v.poiseuille.erro_tau,
    erroQuedaPressao: v.poiseuille.erro_dp,
    erroPerfilMax: v.poiseuille.erro_perfil_max,
    variacaoMalhaArea: v.malha_max_variacao_area,
    variacaoPassoArea: v.passo_variacao_area,
    diferencaCiclos: v.ciclos_max,
  };
}
