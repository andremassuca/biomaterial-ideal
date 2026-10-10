// Campos do fluxo do doente. As condições e os limiares vêm das regras (data/perfis_doente.csv, em cada
// caso_*.json); aqui só se diz como perguntar cada dado. Nada é guardado nem enviado.
import type { Caso, Perfil } from "./tipos";

export type TipoCampo = "numero" | "simnao" | "opcoes";

export interface Campo {
  chave: string;
  rotulo: string;
  tipo: TipoCampo;
  grupo: "geral" | "especifico";
  unidade?: string;
  ajuda?: string;
  opcoes?: { valor: string; texto: string }[];
  /** Subgrupo para arrumar o formulário dos dados gerais. */
  secao?: "base" | "doencas" | "alergias" | "tratamentos";
}

export const CAMPOS: Campo[] = [
  { chave: "idade", rotulo: "Idade", tipo: "numero", unidade: "anos", grupo: "geral", secao: "base" },
  {
    chave: "sexo",
    rotulo: "Sexo",
    tipo: "opcoes",
    grupo: "geral",
    secao: "base",
    opcoes: [
      { valor: "F", texto: "Feminino" },
      { valor: "M", texto: "Masculino" },
    ],
    ajuda: "Não há nenhuma regra para o sexo: não muda o resultado.",
  },
  { chave: "imc", rotulo: "Índice de massa corporal (IMC)", tipo: "numero", unidade: "kg/m²", grupo: "geral", secao: "base" },
  {
    chave: "atividade",
    rotulo: "Atividade física",
    tipo: "opcoes",
    grupo: "geral",
    secao: "base",
    opcoes: [
      { valor: "baixa", texto: "Baixa" },
      { valor: "moderada", texto: "Moderada" },
      { valor: "alta", texto: "Alta" },
    ],
  },
  { chave: "tabagismo", rotulo: "Fuma", tipo: "simnao", grupo: "geral", secao: "base" },
  { chave: "diabetes", rotulo: "Diabetes", tipo: "simnao", grupo: "geral", secao: "doencas" },
  { chave: "hipertensao", rotulo: "Hipertensão arterial", tipo: "simnao", grupo: "geral", secao: "doencas" },
  { chave: "osteoporose", rotulo: "Osteoporose", tipo: "simnao", grupo: "geral", secao: "doencas" },
  {
    chave: "tfg",
    rotulo: "Função renal: taxa de filtração glomerular (TFG)",
    tipo: "numero",
    unidade: "mL/min/1,73 m²",
    grupo: "geral",
    secao: "doencas",
    ajuda: "Deixe em branco se a função renal for normal ou desconhecida.",
  },
  { chave: "dialise", rotulo: "Em hemodiálise", tipo: "simnao", grupo: "geral", secao: "doencas" },
  { chave: "periodontite", rotulo: "História de doença periodontal (periodontite)", tipo: "simnao", grupo: "geral", secao: "doencas" },
  { chave: "artrite_reumatoide", rotulo: "Artrite reumatoide", tipo: "simnao", grupo: "geral", secao: "doencas" },
  { chave: "doenca_tecido_conjuntivo", rotulo: "Doença do tecido conjuntivo associada", tipo: "simnao", grupo: "geral", secao: "doencas" },
  { chave: "alergia_niquel", rotulo: "Alergia ao níquel", tipo: "simnao", grupo: "geral", secao: "alergias" },
  { chave: "alergia_metais", rotulo: "Alergia a metais (níquel, cobalto ou crómio)", tipo: "simnao", grupo: "geral", secao: "alergias" },
  { chave: "alergia_cobalto_confirmada", rotulo: "Alergia ao cobalto confirmada por teste", tipo: "simnao", grupo: "geral", secao: "alergias" },
  { chave: "hipersens_cobalto_suspeita", rotulo: "Suspeita de hipersensibilidade ao cobalto, sem teste", tipo: "simnao", grupo: "geral", secao: "alergias" },
  { chave: "alergia_titanio_confirmada", rotulo: "Alergia ao titânio confirmada por teste", tipo: "simnao", grupo: "geral", secao: "alergias" },
  { chave: "hipersens_titanio_suspeita", rotulo: "Suspeita de hipersensibilidade ao titânio, sem teste", tipo: "simnao", grupo: "geral", secao: "alergias" },
  {
    chave: "corticoterapia",
    rotulo: "Corticoterapia prolongada",
    tipo: "simnao",
    grupo: "geral",
    secao: "tratamentos",
    ajuda: "Definição usada nas regras: ver a condição de cada regra no resultado.",
  },
  { chave: "rm_frequente", rotulo: "Precisa de ressonância magnética frequente", tipo: "simnao", grupo: "geral", secao: "tratamentos" },
  // Dados específicos de cada dispositivo
  { chave: "vaso_mm", rotulo: "Diâmetro do vaso", tipo: "numero", unidade: "mm", grupo: "especifico" },
  {
    chave: "defeito",
    rotulo: "O defeito ósseo suporta carga?",
    tipo: "opcoes",
    grupo: "especifico",
    opcoes: [
      { valor: "com_carga", texto: "Com carga" },
      { valor: "sem_carga", texto: "Sem carga" },
    ],
    ajuda: "Escolhe a leitura do problema crítico: com carga, a leitura ampla; sem carga, a literal.",
  },
  { chave: "gengiva_mm", rotulo: "Espessura da gengiva", tipo: "numero", unidade: "mm", grupo: "especifico" },
  { chave: "bruxismo", rotulo: "Bruxismo", tipo: "simnao", grupo: "especifico" },
  { chave: "radioterapia_cabeca_pescoco", rotulo: "Radioterapia prévia da cabeça e pescoço", tipo: "simnao", grupo: "especifico" },
];

export const NOMES_SECAO: Record<NonNullable<Campo["secao"]>, string> = {
  base: "Dados de base",
  doencas: "Doenças",
  alergias: "Alergias",
  tratamentos: "Tratamentos e exames",
};

/** Dados do doente usados nas condições das regras de um caso (ex.: "idade<60; atividade=alta"). */
export function chavesDoCaso(caso: Caso): Set<string> {
  const s = new Set<string>();
  for (const r of caso.regras) {
    for (const parte of r.condicao_codigo.split(";")) {
      const m = parte.trim().match(/^([A-Za-z0-9_]+)\s*(<=|>=|<|>|=)/);
      if (m) s.add(m[1]);
    }
  }
  return s;
}

/** Campos pedidos pelas regras que não estão na lista acima (aparecem como texto livre, para não faltar nenhum). */
export function camposEmFalta(caso: Caso): string[] {
  const conhecidos = new Set(CAMPOS.map((c) => c.chave));
  return [...chavesDoCaso(caso)].filter((k) => !conhecidos.has(k));
}

/** Tira os campos vazios (um dado em falta conta como "não se verifica" no núcleo). */
export function limparPerfil(p: Perfil): Perfil {
  const out: Perfil = {};
  for (const [k, v] of Object.entries(p)) {
    if (v === "" || v === null || v === undefined) continue;
    if (typeof v === "number" && !Number.isFinite(v)) continue;
    out[k] = v;
  }
  return out;
}
