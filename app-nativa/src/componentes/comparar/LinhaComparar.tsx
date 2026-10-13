// Uma propriedade na comparação: o valor de cada material (típico, intervalo, barra), a fonte, o estado e a diferença.
import { Check } from "lucide-react";
import { EstadoValor, Fonte } from "@/componentes/comuns";
import { Etiqueta } from "@/componentes/ui/cartao";
import { fracaoBarra, temValor, type LinhaComparacao, type ValorProp } from "@/lib/comparar";
import { intervalo, pct, valor } from "@/lib/formato";
import type { LinhaMaterial } from "@/lib/tipos";
import { textoPublico } from "@/lib/publico";
import { cn } from "@/lib/utils";

/** Frase curta com a regra de "melhor" do critério (vem do tipo e do alvo dos dados). */
export function regraCriterio(l: Pick<LinhaComparacao, "tipo" | "alvo" | "unidade">): string {
  if (l.tipo === "benefit") return "maior é melhor";
  if (l.tipo === "cost") return "menor é melhor";
  const un = l.unidade && l.unidade !== "-" ? ` ${l.unidade}` : "";
  return l.alvo === null ? "critério-alvo sem alvo definido" : `mais perto do alvo (${valor(l.alvo)}${un}) é melhor`;
}

function unidadeTexto(u: string | null): string {
  return u && u !== "-" ? ` ${u}` : "";
}

/** Célula de um material: valor, intervalo, barra, estado e fonte; "Sem valor na base" quando não há número. */
export function CelulaValor({
  rotulo,
  v,
  ficha,
  unidade,
  fracao,
  ganha,
  empate,
}: {
  rotulo: string;
  v: ValorProp;
  ficha: LinhaMaterial | null;
  unidade: string | null;
  fracao: number;
  ganha: boolean;
  empate: boolean;
}) {
  const tem = temValor(v.tipico);
  const comIntervalo = tem && temValor(v.min) && temValor(v.max) && v.min !== v.max;
  return (
    <div
      data-lado={rotulo}
      className={cn("min-w-0 rounded-md border p-3", ganha ? "border-sucesso/60 bg-sucesso/5" : "border-linha bg-superficie")}
    >
      {tem ? (
        <>
          <div className="flex flex-wrap items-baseline justify-between gap-2">
            <span className="numero text-lg font-bold">
              {valor(v.tipico)}
              <span className="text-xs font-normal text-texto2">{unidadeTexto(unidade)}</span>
            </span>
            {ganha && (
              <Etiqueta tom="sucesso">
                <Check aria-hidden className="mr-1 h-3 w-3" />
                Melhor
              </Etiqueta>
            )}
            {empate && <Etiqueta>Empate</Etiqueta>}
          </div>
          {comIntervalo && <div className="numero text-xs text-texto2">intervalo {intervalo(v.min, v.max, 2)}</div>}
          <div className="mt-2 h-2 w-full overflow-hidden rounded-full bg-superficie2" aria-hidden>
            <div
              className={cn("h-full rounded-full", ganha ? "bg-sucesso" : "bg-acento")}
              style={{ width: `${Math.max(2, fracao * 100)}%` }}
            />
          </div>
        </>
      ) : (
        <div className="text-sm font-medium text-texto2">Sem valor na base</div>
      )}
      <div className="mt-2 flex flex-wrap items-start gap-2">
        {ficha ? <EstadoValor estado={ficha.estado} /> : tem ? <Etiqueta>valor derivado dos dados do caso</Etiqueta> : null}
      </div>
      {ficha && (
        <div className="mt-1.5">
          <Fonte referencia={ficha.referencia} doi={ficha.doi_url} className="flex" />
          {textoPublico(ficha.notas) && <p className="mt-1 text-xs leading-relaxed text-texto2">{textoPublico(ficha.notas)}</p>}
        </div>
      )}
    </div>
  );
}

/** Linha completa: nome da propriedade e regra, as duas células e a diferença calculada. */
export function LinhaComparar({ linha: l }: { linha: LinhaComparacao }) {
  const un = unidadeTexto(l.unidade);
  return (
    <li className="py-4" data-criterio={l.criterio}>
      <div className="mb-2 flex flex-wrap items-baseline justify-between gap-2">
        <h4 className="text-sm font-bold">{l.criterio}</h4>
        <span className="text-xs text-texto2">{regraCriterio(l)}</span>
      </div>
      <div className="grid gap-3 [&>*]:min-w-0 md:grid-cols-2">
        <CelulaValor
          rotulo="a"
          v={l.a}
          ficha={l.fichaA}
          unidade={l.unidade}
          fracao={fracaoBarra(l.a.tipico, l.a.tipico, l.b.tipico)}
          ganha={l.melhor === "a"}
          empate={l.melhor === "empate"}
        />
        <CelulaValor
          rotulo="b"
          v={l.b}
          ficha={l.fichaB}
          unidade={l.unidade}
          fracao={fracaoBarra(l.b.tipico, l.a.tipico, l.b.tipico)}
          ganha={l.melhor === "b"}
          empate={l.melhor === "empate"}
        />
      </div>
      <p className="numero mt-2 text-xs text-texto2">
        {l.diferenca
          ? `Diferença: ${valor(l.diferenca.absoluta)}${un}${l.diferenca.relativa === null ? "" : ` (${pct(l.diferenca.relativa * 100)} do maior)`}`
          : "Diferença: sem valor dos dois materiais, não se compara."}
      </p>
    </li>
  );
}
