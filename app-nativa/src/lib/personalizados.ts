// Materiais definidos pelo utilizador: entram só na análise de quem os criou, ficam guardados neste computador e
// nunca alteram a base de dados (data/ e app.json). Aparecem sempre marcados "Definido pelo utilizador".
import type { IdCaso } from "./dados";
import { gravar, ler } from "./utils";
import type { Problema } from "./tipos";

const CHAVE = "biomat.personalizados";
const EVENTO = "biomat-personalizados";
/** Texto que marca um material criado pelo utilizador (vai no nome, por isso aparece em todos os ecrãs e no PDF). */
export const MARCA_UTILIZADOR = "definido pelo utilizador";

/** Valores de um critério: mínimo, máximo e típico (o típico é o que entra no ranking). */
export interface ValorPersonalizado {
  min: number;
  max: number;
  tipico: number;
}

export interface MaterialPersonalizado {
  id: string;
  caso: IdCaso;
  /** Nome escolhido pelo utilizador, sem a marca. */
  nome: string;
  /** Valores por nome do critério (o mesmo texto de Problema.criterios). */
  valores: Record<string, ValorPersonalizado>;
}

/** Nome com a marca: "O meu material (definido pelo utilizador)". */
export function nomeMarcado(nome: string): string {
  return `${nome.trim()} (${MARCA_UTILIZADOR})`;
}

/** Diz se um nome de material é de um material personalizado. */
export function ehPersonalizado(nome: string): boolean {
  return nome.endsWith(`(${MARCA_UTILIZADOR})`);
}

function lerTodos(): MaterialPersonalizado[] {
  const t = ler(CHAVE);
  if (!t) return [];
  try {
    const l: unknown = JSON.parse(t);
    return Array.isArray(l)
      ? l.filter((m): m is MaterialPersonalizado => typeof m?.id === "string" && typeof m?.nome === "string" && typeof m?.caso === "string" && typeof m?.valores === "object" && m.valores !== null)
      : [];
  } catch {
    return [];
  }
}

function escrever(l: MaterialPersonalizado[]): void {
  gravar(CHAVE, JSON.stringify(l));
  try {
    window.dispatchEvent(new Event(EVENTO));
  } catch {
    // sem janela: ninguém a avisar
  }
}

/** Materiais personalizados de um caso, pela ordem em que foram criados. */
export function lerPersonalizados(caso: IdCaso): MaterialPersonalizado[] {
  return lerTodos().filter((m) => m.caso === caso);
}

/** Guarda um material personalizado novo (ou substitui o que tem o mesmo id). */
export function guardarPersonalizado(m: MaterialPersonalizado): void {
  escrever([...lerTodos().filter((x) => x.id !== m.id), m]);
}

/** Apaga um material personalizado. */
export function removerPersonalizado(id: string): void {
  escrever(lerTodos().filter((x) => x.id !== id));
}

/** Subscreve as mudanças aos materiais personalizados; devolve a função que cancela. */
export function aoMudarPersonalizados(f: () => void): () => void {
  window.addEventListener(EVENTO, f);
  window.addEventListener("storage", f);
  return () => {
    window.removeEventListener(EVENTO, f);
    window.removeEventListener("storage", f);
  };
}

/** Rascunho de um valor, como texto escrito no formulário. */
export interface RascunhoValor {
  tipico: string;
  min: string;
  max: string;
}

/** Converte texto com vírgula ou ponto decimal em número; null se não for um número. */
export function lerNumero(texto: string): number | null {
  const t = texto.trim().replace(",", ".");
  if (t === "") return null;
  const n = Number(t);
  return Number.isFinite(n) ? n : null;
}

/**
 * Valida o formulário e devolve os valores prontos, ou a lista de erros em português.
 * Em linguagem simples: confirma que o nome é novo, que todos os critérios têm valor típico, que o mínimo e o
 * máximo (se escritos) rodeiam o típico, que os critérios ordinais são inteiros de 1 a 5 e que os de custo não
 * são negativos. O mínimo e o máximo em falta ficam iguais ao típico.
 */
export function validarFormulario(
  problema: Problema,
  nome: string,
  rascunho: Record<string, RascunhoValor>,
  nomesExistentes: string[],
): { valores: Record<string, ValorPersonalizado> | null; erros: string[] } {
  const erros: string[] = [];
  const n = nome.trim();
  if (n === "") erros.push("Escreva o nome do material.");
  else if (nomesExistentes.some((x) => x.trim().toLowerCase() === n.toLowerCase() || x.trim().toLowerCase() === nomeMarcado(n).toLowerCase()))
    erros.push("Já existe um material com este nome.");
  const valores: Record<string, ValorPersonalizado> = {};
  problema.criterios.forEach((c, j) => {
    const r = rascunho[c] ?? { tipico: "", min: "", max: "" };
    const tipico = lerNumero(r.tipico);
    if (tipico === null) {
      erros.push(`${c}: falta o valor típico.`);
      return;
    }
    const min = lerNumero(r.min) ?? tipico;
    const max = lerNumero(r.max) ?? tipico;
    if (min > tipico || tipico > max) {
      erros.push(`${c}: o mínimo, o típico e o máximo têm de estar por esta ordem.`);
      return;
    }
    if (problema.ordinal[j] && ![tipico, min, max].every((v) => Number.isInteger(v) && v >= 1 && v <= 5)) {
      erros.push(`${c}: critério ordinal, use números inteiros de 1 a 5.`);
      return;
    }
    if (problema.tipos[j] === "cost" && min < 0) {
      erros.push(`${c}: critério de custo, o valor não pode ser negativo.`);
      return;
    }
    valores[c] = { min, max, tipico };
  });
  return { valores: erros.length ? null : valores, erros };
}

/** Critérios do problema para os quais o material não tem valor (por exemplo, num cenário com critérios a mais). */
export function criteriosEmFalta(problema: Problema, m: MaterialPersonalizado): string[] {
  return problema.criterios.filter((c) => !m.valores[c]);
}

/**
 * Acrescenta ao problema os materiais personalizados que têm valor em todos os critérios do problema.
 * Em linguagem simples: devolve um problema novo com uma linha a mais por material do utilizador, com o nome
 * marcado; a base e o problema original não mudam. Devolve também os nomes dos que ficaram de fora (e porquê).
 */
export function acrescentarMateriais(
  problema: Problema,
  lista: MaterialPersonalizado[],
): { problema: Problema; incluidos: string[]; deFora: { nome: string; falta: string[] }[] } {
  const incluidos: string[] = [];
  const deFora: { nome: string; falta: string[] }[] = [];
  const alternativas = [...problema.alternativas];
  const x_min = problema.x_min.map((l) => [...l]);
  const x_max = problema.x_max.map((l) => [...l]);
  const x_tipico = problema.x_tipico.map((l) => [...l]);
  for (const m of lista) {
    const falta = criteriosEmFalta(problema, m);
    if (falta.length) {
      deFora.push({ nome: m.nome, falta });
      continue;
    }
    const nome = nomeMarcado(m.nome);
    alternativas.push(nome);
    x_min.push(problema.criterios.map((c) => m.valores[c].min));
    x_max.push(problema.criterios.map((c) => m.valores[c].max));
    x_tipico.push(problema.criterios.map((c) => m.valores[c].tipico));
    incluidos.push(nome);
  }
  return { problema: { ...problema, alternativas, x_min, x_max, x_tipico }, incluidos, deFora };
}
