// Leitura dos dados exportados para app-nativa/dados/ e utilitários de nomes.
// Nenhum número é escrito à mão na interface: tudo vem destes ficheiros.
import type { Caso, Cfd, DadosApp, Triagem } from "./tipos";

// import.meta.glob aceita ficheiros que podem não existir (cfd_stent.json só aparece quando a CFD acabar).
const ficheiros = import.meta.glob("../../dados/*.json", { eager: true, import: "default" }) as Record<string, unknown>;

function ficheiro<T>(nome: string): T | null {
  const chave = Object.keys(ficheiros).find((k) => k.endsWith(`/${nome}`));
  return chave ? (ficheiros[chave] as T) : null;
}

function obrigatorio<T>(nome: string): T {
  const d = ficheiro<T>(nome);
  if (!d) throw new Error(`Falta o ficheiro de dados ${nome}; corra scripts/exportar_app_json.py.`);
  return d;
}

/** Identificador de cada caso na interface (igual ao campo "caso" do JSON e ao nome usado no Rust). */
export type IdCaso = "Haste" | "Stent" | "Scaffold" | "Par articular" | "Implante dentário";

export const CASOS: Record<IdCaso, Caso> = {
  Haste: obrigatorio<Caso>("caso_haste.json"),
  Stent: obrigatorio<Caso>("caso_stent.json"),
  Scaffold: obrigatorio<Caso>("caso_scaffold.json"),
  "Par articular": obrigatorio<Caso>("caso_par_articular.json"),
  "Implante dentário": obrigatorio<Caso>("caso_implante_dentario.json"),
};

/** Casos quantitativos (MCDM completo) e semiquantitativos (ranking só como indicação). */
export const QUANTITATIVOS: IdCaso[] = ["Haste", "Stent", "Scaffold"];
export const SEMIQUANTITATIVOS: IdCaso[] = ["Par articular", "Implante dentário"];

/** Texto curto de cada dispositivo para a interface. */
export const TITULO_CASO: Record<IdCaso, string> = {
  Haste: "Haste femoral",
  Stent: "Stent expansível por balão",
  Scaffold: "Scaffold ósseo",
  "Par articular": "Par articular da anca",
  "Implante dentário": "Implante dentário",
};

/**
 * Recomendação final dos casos em que o ranking sozinho não diz tudo (decisões D1 e D7 do André, 11 out).
 * A frase é a mesma no relatório, na apresentação e na aplicação: não reescrever aqui.
 */
export const RECOMENDACAO: Partial<Record<IdCaso, string>> = {
  Stent:
    "Pt-Cr e L605 praticamente equivalentes: o Pt-Cr é favorecido pelo TOPSIS, pelo VIKOR e pela radiopacidade; o L605 pelo WASPAS e por ter todas as propriedades em fichas de fornecedor. Sem vencedor universal.",
  Scaffold:
    "Depende da carga: compósito PCL/β-TCP impresso quando o defeito suporta carga (1.º no ranking direto em 5 das 6 combinações); β-TCP poroso quando não suporta (mais vezes 1.º na incerteza dos dados).",
};

/**
 * Versão curta da mesma recomendação (cartões do Início e espectro), decidida pelo André a 11 out: igual à da
 * apresentação. Onde o nome do caso já aparece ao lado com dois pontos, usa-se o texto sem o prefixo (semPrefixo).
 */
export const RECOMENDACAO_CURTA: Partial<Record<IdCaso, string>> = {
  Stent: "Stent: Pt-Cr e L605 praticamente equivalentes",
  Scaffold: "Scaffold: depende da carga (compósito com carga; β-TCP sem carga)",
};

/** Tira o prefixo "Caso: " da versão curta (ex.: "Stent: Pt-Cr e L605..." -> "Pt-Cr e L605..."). */
export function semPrefixo(frase: string): string {
  const i = frase.indexOf(": ");
  return i < 0 ? frase : frase.slice(i + 2);
}

/** Ilustração (design/ilustracoes) de cada caso. */
export const ILUSTRACAO_CASO: Record<IdCaso, string> = {
  Haste: "haste",
  Stent: "stent",
  Scaffold: "scaffold",
  "Par articular": "par",
  "Implante dentário": "dentario",
};

export const APP: DadosApp = obrigatorio<DadosApp>("app.json");

/** Resultados da CFD do stent, ou null enquanto não existirem. */
export const CFD: Cfd | null = ficheiro<Cfd>("cfd_stent.json");

/** Base de triagem (triagem, não verificado), ou null enquanto não for gerada. */
export const TRIAGEM: Triagem | null = ficheiro<Triagem>("triagem.json");

/** Nome simples aprovado (scripts/nomes_simples.py); o próprio nome se não estiver na tabela. */
export function nomeSimples(material: string): string {
  return APP.nomes[material]?.nome ?? material;
}

/** Código técnico do material (vazio se não estiver na tabela). */
export function codigo(material: string): string {
  return APP.nomes[material]?.codigo ?? "";
}

/** Linhas da base de dados de um material (todas as propriedades, com fonte e estado). */
export function fichaMaterial(material: string) {
  return APP.fichas.materiais.filter((l) => l.material === material);
}

/** Valor típico de uma propriedade de um material num problema (null se não existir). */
export function valorProblema(caso: Caso, cenario: string, material: string, criterio: string): number | null {
  const p = caso.cenarios[cenario];
  if (!p) return null;
  const i = p.alternativas.indexOf(material);
  const j = p.criterios.indexOf(criterio);
  return i < 0 || j < 0 ? null : p.x_tipico[i][j];
}

/** Cenários disponíveis num caso, por ordem ("A", "B"). */
export function cenarios(caso: Caso): string[] {
  return Object.keys(caso.cenarios).sort();
}

/** Texto curto de um cenário. */
export function descricaoCenario(c: string): string {
  // Textos de data/cenarios.csv, encurtados.
  return c === "A"
    ? "Cenário A: só materiais em uso clínico"
    : c === "B"
      ? "Cenário B: inclui investigação e bioabsorvíveis"
      : `Cenário ${c}`;
}

/** Nome completo de um material a partir do nome ou do código curto (ex.: "316L" -> "Aço inox 316L"). */
export function resolverMaterial(chave: string): string {
  if (APP.nomes[chave]) return chave;
  const achado = Object.entries(APP.nomes).find(([, v]) => v.codigo === chave);
  return achado ? achado[0] : chave;
}
