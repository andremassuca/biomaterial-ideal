// Tipos dos JSON de app-nativa/dados/ (scripts/exportar_app_json.py) e das respostas dos comandos Rust.

export type TipoCriterio = "benefit" | "cost" | "target";

/** Problema de decisão: uma linha por material, uma coluna por critério. */
export interface Problema {
  alternativas: string[];
  criterios: string[];
  tipos: TipoCriterio[];
  alvos: (number | null)[];
  pesos: number[];
  x_min: number[][];
  x_max: number[][];
  x_tipico: number[][];
  ordinal: boolean[];
}

/** Uma regra de data/perfis_doente.csv. */
export interface Regra {
  id: string;
  dispositivo: string;
  condicao: string | null;
  condicao_codigo: string;
  efeito: string;
  alvo_do_efeito: string;
  valor: string | null;
  justificacao: string | null;
  fonte: string | null;
  doi_url: string | null;
  estado: string | null;
}

export type ValorPerfil = number | string;
export type Perfil = Record<string, ValorPerfil>;

export interface Intervalo {
  min: number;
  max: number;
  tipico: number;
}

/** Um ficheiro caso_*.json. */
export interface Caso {
  caso: string;
  caso_componente: string;
  parametros: Record<string, number>;
  cenarios: Record<string, Problema>;
  propriedades_extra: Record<string, Record<string, Intervalo>>;
  problemas_criticos: Record<string, string[]>;
  regras: Regra[];
  perfis_referencia: Record<string, { descricao: string; perfil: Perfil }>;
}

/** Ranking dos três métodos e do consenso de Borda (igual ao `Ranking` do núcleo Rust). */
export interface Ranking {
  alternativas: string[];
  c_topsis: number[];
  q_waspas: number[];
  s_vikor: number[];
  r_vikor: number[];
  p_vikor: number[];
  pos_topsis: number[];
  pos_waspas: number[];
  pos_vikor: number[];
  pontos_borda: number[];
  pos_borda: number[];
}

export interface RespostaCaso {
  problema: Problema;
  ranking: Ranking;
  excluidos: string[];
  /** Verdadeiro quando só o TOPSIS foi calculado (modo navegador, sem o núcleo Rust). */
  apenasTopsis?: boolean;
}

export interface ResultadoPerfil {
  problema: Problema;
  ranking: Ranking;
  regras: Regra[];
  excluidos: string[];
  notas: string[];
}

export interface RespostaDoente {
  base_problema: Problema;
  base: Ranking;
  resultado: ResultadoPerfil;
}

export interface ResumoMetodo {
  metodo: "TOPSIS" | "WASPAS" | "VIKOR";
  pct_primeiro: number[];
  pct_segundo: number[];
  posicao_media: number[];
}

export interface ResumoMonteCarlo {
  alternativas: string[];
  pedidas: number;
  feitas: number;
  parado: boolean;
  metodos: ResumoMetodo[];
}

// ------------------------------------------------------------------ app.json

export interface LinhaMaterial {
  caso: string;
  componente: string;
  material: string;
  norma: string | null;
  classe: string | null;
  estatuto: string | null;
  propriedade: string;
  unidade: string | null;
  min: number | null;
  max: number | null;
  referencia: string | null;
  doi_url: string | null;
  notas: string | null;
  tipico: number | null;
  estado: string | null;
  valor_texto: string | null;
}

export interface LinhaTecido {
  tecido: string;
  propriedade: string;
  unidade: string | null;
  min: number | null;
  max: number | null;
  notas: string | null;
  fonte: string | null;
  estado: string | null;
}

export interface FiltroMaterial {
  material: string;
  ferromagnetico: string;
  fonte_rm: string;
  vapor: string;
  oxido_etileno: string;
  radiacao_gama: string;
  fonte_esterilizacao: string;
  notas: string;
  estado: string;
  estatuto: string;
  rm: "passa" | "exclui" | "A verificar";
  iso10993: string;
}

export interface LinhaEsterilizacao {
  caso: string;
  cenario: string;
  metodo: string;
  saem: string;
  muda: boolean;
  [chave: string]: string | boolean;
}

export interface EntradaEspectro {
  caso: string;
  vencedor: string;
  segundo: string;
  delta_c: number;
  semiquantitativo: boolean;
  pct_primeiro_min?: number;
  pct_primeiro_max?: number;
  n_iter?: number;
  versoes_mantem?: number;
  versoes_total?: number;
}

export interface LinhaMonteCarloRef {
  caso: string;
  analise: string;
  metodo: string;
  material: string;
  pct_primeiro: number;
  pct_segundo: number;
  pct_terceiro: number;
  posicao_media: number;
  n_iter: number;
  seed: number;
  incerteza_valor_unico: number;
}

export interface ZonaFea {
  material: string;
  material_base: string | null;
  E_haste_GPa: number | null;
  zona: number;
  energia_mJ: number;
  razao: number;
  stress_shielding: number;
  elementos: number;
  graus_liberdade: number;
}

export interface Fea {
  malha_mm: number;
  malhas_mm: number[];
  zonas: ZonaFea[];
  comparacao?: { material: string; G1_python: number; G7_python: number; G1_solidworks: number; G7_solidworks: number }[];
}

export interface Massa {
  materiais: { material: string; densidade_g_cm3: number; massa_g: number }[];
  volume_cm3: number;
  diferenca_g: number;
  massa_corpo_kg: number;
  distancia_max_m: number;
  desvio_max_mm: number;
  excursao_vertical_cm: [number, number];
  excursao_lateral_cm: [number, number];
}

/** Resultado do fluxo pulsátil da CFD (results/cfd_pulsatil.json), quando existir. */
export type Cfd = Record<
  string,
  { espessura_um: number; tau_media: number; fracao_baixa: number; osi_media: number; fracao_osi: number; area_mm2: number }
>;

/** Repetição do fluxo pulsátil com sangue de Carreau (results/cfd_pulsatil_carreau.json). */
export interface CfdCarreau {
  limiar_pa: number;
  carreau: { mu0: number; muinf: number; lambda_s: number; n: number };
  casos: Record<
    string,
    {
      espessura_um: number;
      newtoniano: { tau_media: number; fracao_baixa: number };
      carreau: { tau_media: number; fracao_baixa: number };
      dif_fracao_pp: number;
      dif_tau_rel: number;
    }
  >;
  ordem_mantida: boolean;
}

/** Micromovimento da haste com contacto com atrito (results/micromovimento_haste.json), em µm (deslocamento tangencial). */
export interface Micromovimento {
  material: string;
  mu: number;
  limiar_um: number;
  nos: number;
  principal: { max_um: number; mediana_um: number; fracao_acima_limiar: number };
  outras_variantes: number;
  outras_max_min_um: number;
  outras_max_max_um: number;
  outras_fracao_acima_limiar_max: number;
}

export interface DadosApp {
  nomes: Record<string, { nome: string; codigo: string }>;
  fichas: { materiais: LinhaMaterial[]; tecido: LinhaTecido[] };
  filtros: { metodos: Record<string, string>; materiais: FiltroMaterial[]; esterilizacao: LinhaEsterilizacao[] };
  espectro: EntradaEspectro[];
  limiar_empate: number;
  monte_carlo_referencia: LinhaMonteCarloRef[];
  fea: Fea | null;
  massa: Massa | null;
  cfd_carreau?: CfdCarreau | null;
  micromovimento?: Micromovimento | null;
  textos: { ioes: string | null };
}

/** Base de triagem (scripts/base_triagem.py): candidatos de bases abertas, não verificados; não entram no MCDM. */
export interface MaterialTriagem {
  chave: string;
  nome: string;
  caso: string;
  familia: string;
  classe: string;
  fontes: string[];
  tipos: string[];
  densidade: number | null;
  modulo: number | null;
  hiato: number | null;
}

export interface Triagem {
  aviso: string;
  licencas: Record<string, string>;
  contagens: { caso: string; classe: string; fonte_base: string; materiais: number }[];
  cobertura: { caso: string; propriedade: string; com_valor: number; total: number; pct: number }[];
  materiais: MaterialTriagem[];
}
