// Texto público das notas e das fontes: tira as marcas internas de trabalho ("[confirmar]", "Estatuto [confirmar]: ...",
// "registar a porosidade ...") sem mexer nos dados. Os ficheiros de dados/ e de data/ ficam como estão; só o que se
// mostra no ecrã muda. O estado de cada valor continua visível no selo ("Verificado", "A verificar").

/**
 * Devolve o texto sem as notas internas de trabalho.
 * Em linguagem simples:
 * - "Estatuto [confirmar]: ..." (lista interna das fontes do estatuto) sai até ao fim do texto;
 * - a instrução "registar a porosidade do estudo de onde vem o valor" sai;
 * - pedidos para confirmar ("confirmar no PDF", "confirmar no texto o método ...") saem;
 * - "por confirmar" passa a "por verificar";
 * - as marcas "[confirmar]", "[confirmar: só o resumo]", ": confirmar" e "(a confirmar)" passam a "(a verificar)",
 *   a mesma palavra do selo de estado, para não parecer confirmado o que não está.
 */
export function textoPublico(texto: string): string;
export function textoPublico(texto: string | null | undefined): string | null | undefined;
export function textoPublico(texto: string | null | undefined): string | null | undefined {
  if (texto === null || texto === undefined) return texto;
  let t = texto;
  // lista interna do estatuto, sempre no fim da nota
  t = t.replace(/;?\s*Estatuto \[confirmar\][^\n]*$/gm, "");
  // instrução de trabalho
  t = t.replace(/:\s*registar a porosidade do estudo de onde vem o valor/g, "");
  // pedidos para confirmar dentro de parênteses ou depois de vírgula/ponto e vírgula
  t = t.replace(/,\s*confirmar no PDF/g, "");
  t = t.replace(/;\s*confirmar no texto [^.;\[]*/g, "");
  // marcas que passam à palavra pública
  t = t.replace(/\s*\[confirmar[^\]]*\]/g, " (a verificar)");
  t = t.replace(/\(a confirmar\)/g, "(a verificar)");
  t = t.replace(/:\s*confirmar(?=$|[;.\n])/gm, " (a verificar)");
  t = t.replace(/(^|[;(]\s*)a confirmar:/gm, "$1a verificar:");
  t = t.replace(/\bvalor a confirmar\b/g, "valor a verificar");
  t = t.replace(/\bpor confirmar\b/g, "por verificar");
  // "(a verificar) (a verificar)" ou espaços e pontuação que ficaram soltos
  t = t.replace(/(\(a verificar\)\s*)+/g, "(a verificar) ");
  t = t.replace(/\s+([.;,])/g, "$1");
  t = t.replace(/[ \t]{2,}/g, " ");
  return t.trim();
}
