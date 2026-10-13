// Números no formato português (vírgula decimal, espaço nos milhares).

const cache = new Map<number, Intl.NumberFormat>();

function formatador(casas: number): Intl.NumberFormat {
  let f = cache.get(casas);
  if (!f) {
    f = new Intl.NumberFormat("pt-PT", { minimumFractionDigits: casas, maximumFractionDigits: casas, useGrouping: true });
    cache.set(casas, f);
  }
  return f;
}

/** Número com um número fixo de casas decimais (ex.: 0,752). */
export function num(x: number | null | undefined, casas = 2): string {
  if (x === null || x === undefined || !Number.isFinite(x)) return "n.d.";
  return formatador(casas).format(x);
}

/** Percentagem; com duas casas quando o arredondamento daria 0 ou 100 sem o ser (ex.: 99,99 %). */
export function pct(x: number | null | undefined): string {
  if (x === null || x === undefined || !Number.isFinite(x)) return "n.d.";
  const casas = (x >= 99.5 && x < 100) || (x > 0 && x < 0.5) ? 2 : 0;
  return `${num(x, casas)} %`;
}

/** Intervalo "mín. a máx." ou um só valor quando são iguais. */
export function intervalo(min: number | null, max: number | null, casas = 1): string {
  if (min === null && max === null) return "n.d.";
  if (min === null || max === null || min === max) return num(min ?? max, casas);
  return `${num(min, casas)} a ${num(max, casas)}`;
}

/** Número de casas razoável para um valor de propriedade. */
export function casasPara(x: number): number {
  const a = Math.abs(x);
  if (a === 0) return 0;
  if (a >= 100) return 0;
  if (a >= 10) return 1;
  if (a >= 1) return 2;
  return 3;
}

/** Valor de propriedade com casas automáticas. */
export function valor(x: number | null | undefined): string {
  if (x === null || x === undefined || !Number.isFinite(x)) return "n.d.";
  return num(x, casasPara(x));
}

/** Ordinal português (1.º, 2.º). */
export function ordinal(k: number): string {
  return `${k}.º`;
}

/**
 * Número escrito com ponto decimal nos dados ("0.20") passa a vírgula ("0,20"), como no resto da interface.
 * Em linguagem simples: só troca o ponto entre dois algarismos; o resto do texto fica igual.
 */
export function decimalPt(texto: string | null | undefined): string {
  return (texto ?? "").replace(/(\d)\.(\d)/g, "$1,$2");
}
