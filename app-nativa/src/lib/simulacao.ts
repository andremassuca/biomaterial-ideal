// Funções puras do ecrã "Simulação FEA e CFD": escolher a imagem certa, calcular razões a partir das energias e
// ler os números da CFD por material. Nenhum resultado é escrito à mão: tudo vem de results/ (via
// componentes/simulacao/dados_simulacao.json, extraído de results/fea_haste_sw.json, cfd_fluent.json,
// cfd_verificacoes.json e cfd_malhas.csv) e dos dados da aplicação.
import dados from "@/componentes/simulacao/dados_simulacao.json";
import mapas from "@/componentes/simulacao/mapas_von_mises.json";
import { APP } from "./dados";
import type { CfdCarreau, Micromovimento } from "./tipos";

/** Limiar de tensão de corte na parede (Pa) usado como referência da CFD (docs/CFD_STENT.md: limiar operacional). */
export const LIMIAR_TAWSS_PA = 0.4;

/** Vistas guardadas de cada estudo da SOLIDWORKS: energia de deformação (com barra de cores) e malha. */
export type VistaSw = "energia" | "malha";

/** Vistas do separador da haste: as da SOLIDWORKS mais os mapas de von Mises do MAPDL. */
export type VistaFea = VistaSw | "tensao";

/** Cortes dos mapas de von Mises: vista de frente do conjunto e corte coronal pelo canal medular. */
export type CorteMapdl = "frente" | "corte_coronal";

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
  const sufixo = vista === "energia" ? "densidade_energia" : "malha";
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

// ------------------------------------------------------------------------------ MAPDL (von Mises)

/** Escala de cores comum dos mapas de von Mises (MPa): de `min` a `max`; acima de `saturacao` a cor satura. */
export const ESCALA_MAPDL = mapas.escala_MPa as { min: number; max: number; saturacao: number };

/** Malha dos mapas de von Mises (mm). */
export const MALHA_MAPDL = mapas.malha_mm as number;

/** Nota sobre os picos de tensão (a mesma das figuras): dependem da malha e ficam em cantos e interfaces. */
export const NOTA_MAPDL = mapas.nota as string;

/**
 * Ficheiro (relativo a public/simulacao/) do mapa de von Mises de um material e corte.
 * Em linguagem simples: por exemplo "fea_mapdl/Aco316L_von_mises_corte_coronal.png".
 */
export function imagemMapdl(material: MaterialSw, corte: CorteMapdl): string {
  return `fea_mapdl/${material.prefixo}_von_mises_${corte}.png`;
}

/** Ficheiro da montagem com os cinco materiais lado a lado (mesma escala de cores). */
export const IMAGEM_COMPARACAO_MAPDL = `fea_mapdl/${mapas.ficheiro_comparacao as string}`;

/** Números de um material nos resultados do MAPDL (máximos de von Mises por corpo, em MPa). */
export interface LinhaMapdl {
  material: string;
  eHasteGPa: number | null;
  vmHaste: number | null;
  vmCortical: number;
  vmTrabecular: number;
  vmGlobal: number;
  nos: number;
  elementos: number;
}

type CasoMapdl = {
  material: string;
  E_haste_GPa: number | null;
  vm_max_MPa: Record<string, number | null>;
  nos: number;
  elementos: number;
};

/**
 * Números do MAPDL de um material (chave igual ao prefixo das imagens, por exemplo "Aco316L").
 * Em linguagem simples: lê o JSON gerado a partir dos resultados do MAPDL; devolve null se o material não existir.
 */
export function linhaMapdl(prefixo: string): LinhaMapdl | null {
  const c = (mapas.casos as Record<string, CasoMapdl>)[prefixo];
  if (!c) return null;
  return {
    material: c.material,
    eHasteGPa: c.E_haste_GPa,
    vmHaste: c.vm_max_MPa["Haste"] ?? null,
    vmCortical: c.vm_max_MPa["Osso cortical"] ?? NaN,
    vmTrabecular: c.vm_max_MPa["Osso trabecular"] ?? NaN,
    vmGlobal: c.vm_max_MPa["Global"] ?? NaN,
    nos: c.nos,
    elementos: c.elementos,
  };
}

// ---------------------------------------------------------------- verificações adicionais do relatório v11.1

/** Nota que acompanha os resultados novos (a mesma ideia do relatório: verificação adicional, não previsão clínica). */
export const NOTA_VERIFICACAO = "Verificação, não previsão clínica.";

/** Uma linha da comparação newtoniano contra Carreau: um material (strut), com fração e TAWSS dos dois modelos de sangue. */
export interface LinhaCarreau {
  material: string;
  espessura_um: number;
  fracaoNewtoniano: number;
  fracaoCarreau: number;
  tauNewtoniano: number;
  tauCarreau: number;
}

/**
 * Linhas da comparação com o sangue de Carreau, do strut mais fino para o mais grosso.
 * Em linguagem simples: lê o que o exportador gravou e devolve, por material, a fração da parede com TAWSS baixo e a
 * TAWSS média nos dois modelos; devolve lista vazia se esses resultados não existirem.
 */
export function linhasCarreau(c: CfdCarreau | null | undefined = APP.cfd_carreau): LinhaCarreau[] {
  if (!c) return [];
  return Object.entries(c.casos)
    .map(([material, r]) => ({
      material,
      espessura_um: r.espessura_um,
      fracaoNewtoniano: r.newtoniano.fracao_baixa,
      fracaoCarreau: r.carreau.fracao_baixa,
      tauNewtoniano: r.newtoniano.tau_media,
      tauCarreau: r.carreau.tau_media,
    }))
    .sort((a, b) => a.espessura_um - b.espessura_um);
}

/** Valores do micromovimento prontos a mostrar (µm; fração em 0 a 1), ou null se não existirem. */
export interface ResumoMicromovimento {
  maxUm: number;
  medianaUm: number;
  intervaloMinUm: number;
  intervaloMaxUm: number;
  limiarUm: number;
  fracaoAcimaLimiar: number;
  mu: number;
  material: string;
}

/**
 * Resume o micromovimento da haste: máximo do caso principal, intervalo do máximo nas outras variantes e fração de nós
 * acima do limiar (a maior de todas as variantes, para não esconder um valor pior).
 */
export function resumoMicromovimento(m: Micromovimento | null | undefined = APP.micromovimento): ResumoMicromovimento | null {
  if (!m) return null;
  return {
    maxUm: m.principal.max_um,
    medianaUm: m.principal.mediana_um,
    intervaloMinUm: m.outras_max_min_um,
    intervaloMaxUm: m.outras_max_max_um,
    limiarUm: m.limiar_um,
    fracaoAcimaLimiar: Math.max(m.principal.fracao_acima_limiar, m.outras_fracao_acima_limiar_max),
    mu: m.mu,
    material: m.material,
  };
}

/** Vídeo da simulação que se mostra se o ficheiro existir em public/simulacao/videos. */
export interface VideoSimulacao {
  ficheiro: string;
  separador: "cfd" | "fea";
  titulo: string;
  legenda: string;
}

export const VIDEOS_SIMULACAO: VideoSimulacao[] = [
  {
    ficheiro: "cfd_stent_2ciclo_web.mp4",
    separador: "cfd",
    titulo: "Vídeo da simulação: escoamento pulsátil no stent",
    legenda: "TAWSS: média ao longo do ciclo cardíaco. Linhas de corrente: instante final do ciclo (t = 2,12 s). O cursor indica a fase do ciclo; o campo não varia no vídeo.",
  },
  {
    ficheiro: "fea_haste_4materiais_web.mp4",
    separador: "fea",
    titulo: "Vídeo da simulação: haste femoral com os quatro materiais",
    legenda: "Corte coronal, carga da marcha, interface colada. Deformação ampliada ×5. Verificação numérica, não previsão clínica.",
  },
];

/**
 * Vídeos de um separador que existem de facto.
 * Em linguagem simples: filtra a lista de vídeos previstos pelos ficheiros presentes em public/simulacao/videos
 * (lista lida quando o Vite arranca); sem ficheiro, não há bloco.
 */
export function videosDisponiveis(
  separador: "cfd" | "fea",
  existentes: readonly string[] = __VIDEOS_SIM__,
): VideoSimulacao[] {
  return VIDEOS_SIMULACAO.filter((v) => v.separador === separador && existentes.includes(v.ficheiro));
}

/** Caminho público de um vídeo (public/simulacao/videos/<ficheiro>). */
export function urlVideo(ficheiro: string, base: string = import.meta.env.BASE_URL): string {
  return urlSimulacao(`videos/${ficheiro}`, base);
}
