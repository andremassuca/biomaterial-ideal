// Cartão de resposta no topo dos resultados: quem fica em 1.º e quantos métodos concordam, antes da tabela.
import { CheckCircle2, Scale } from "lucide-react";
import type { ReactNode } from "react";
import { nomeSimples } from "@/lib/dados";
import type { Ranking } from "@/lib/tipos";
import { cn } from "@/lib/utils";
import { NomeMaterial } from "./comuns";

export interface Consenso {
  /** Material em 1.º no consenso (Borda). */
  vencedor: string;
  /** Quantos métodos põem esse material em 1.º. */
  concordam: number;
  /** Quantos métodos foram calculados (1 no modo navegador, 3 com o núcleo completo). */
  total: number;
  /** Para cada método, o seu 1.º e se concorda com o consenso. */
  metodos: { nome: string; primeiro: string; concorda: boolean }[];
}

/** Material com a melhor posição (a mais baixa) numa lista de posições; desempata pela ordem da lista. */
function primeiroDe(alternativas: string[], posicoes: number[]): string {
  let melhor = 0;
  posicoes.forEach((p, i) => {
    if (p < posicoes[melhor]) melhor = i;
  });
  return alternativas[melhor];
}

/**
 * Calcula o consenso a partir das posições do ranking: o 1.º da Borda (ou do TOPSIS, quando só há TOPSIS) e quantos
 * dos métodos TOPSIS, WASPAS e VIKOR o põem também em 1.º. Em linguagem simples: conta quantos métodos votam no mesmo
 * material que ganha no consenso.
 */
export function consenso(r: Ranking, apenasTopsis = false): Consenso {
  const lista = [{ nome: "TOPSIS", pos: r.pos_topsis }];
  if (!apenasTopsis) lista.push({ nome: "WASPAS", pos: r.pos_waspas }, { nome: "VIKOR", pos: r.pos_vikor });
  const vencedor = apenasTopsis ? primeiroDe(r.alternativas, r.pos_topsis) : primeiroDe(r.alternativas, r.pos_borda);
  const metodos = lista.map((m) => {
    const primeiro = primeiroDe(r.alternativas, m.pos);
    return { nome: m.nome, primeiro, concorda: primeiro === vencedor };
  });
  return { vencedor, concordam: metodos.filter((m) => m.concorda).length, total: metodos.length, metodos };
}

/** Frase do consenso: "Os três métodos concordam" / "2 de 3 métodos concordam". */
export function fraseConsenso(c: Consenso): string {
  if (c.total === 1) return "Só o TOPSIS foi calculado (modo navegador).";
  if (c.concordam === c.total) return `Os ${c.total} métodos concordam no 1.º lugar.`;
  return `${c.concordam} de ${c.total} métodos concordam no 1.º lugar.`;
}

/**
 * Cartão de resumo. Com `recomendacao` (a frase do projeto, que não se reescreve) mostra "Sem vencedor universal" e
 * essa frase; sem ela, mostra o material em 1.º. Em ambos os casos mostra o consenso entre os métodos.
 */
export function ResumoResultado({
  ranking,
  apenasTopsis = false,
  recomendacao,
  prefixo = "1.º no consenso",
  filhos,
}: {
  ranking: Ranking;
  apenasTopsis?: boolean;
  recomendacao?: ReactNode;
  prefixo?: string;
  filhos?: ReactNode;
}) {
  const c = consenso(ranking, apenasTopsis);
  const unanime = c.concordam === c.total;
  return (
    <section
      aria-label="Resumo do resultado"
      data-resumo
      className="rounded-lg border border-acento/40 bg-gradient-to-br from-acento/10 to-superficie p-4 shadow-sm sm:p-5"
    >
      <div className="flex flex-wrap items-start gap-4">
        <span
          aria-hidden
          className={cn(
            "flex h-11 w-11 shrink-0 items-center justify-center rounded-full",
            recomendacao ? "bg-aviso/15 text-aviso" : "bg-sucesso/15 text-sucesso",
          )}
        >
          {recomendacao ? <Scale className="h-6 w-6" /> : <CheckCircle2 className="h-6 w-6" />}
        </span>
        <div className="min-w-0 flex-1">
          {recomendacao ? (
            <h2 className="text-lg font-bold leading-tight text-texto" data-titulo-resumo>
              Sem vencedor universal
            </h2>
          ) : (
            <h2 className="flex flex-wrap items-baseline gap-x-2 text-lg font-bold leading-tight text-texto" data-titulo-resumo>
              <span className="text-sm font-medium text-texto2">{prefixo}:</span>
              <NomeMaterial material={c.vencedor} linha className="text-lg" />
            </h2>
          )}
          {recomendacao && <div className="mt-1 text-sm">{recomendacao}</div>}
          <p className="mt-2 flex flex-wrap items-center gap-x-3 gap-y-1 text-sm text-texto2" data-consenso>
            <span className={cn("font-medium", unanime ? "text-sucesso" : "text-aviso")}>{fraseConsenso(c)}</span>
            {recomendacao && (
              <span>
                1.º no consenso (Borda): <span className="font-medium text-texto">{nomeSimples(c.vencedor)}</span>
              </span>
            )}
          </p>
          <ul className="mt-2 flex flex-wrap gap-1.5" aria-label="1.º lugar de cada método">
            {c.metodos.map((m) => (
              <li
                key={m.nome}
                data-metodo={m.nome}
                data-concorda={m.concorda ? "sim" : "nao"}
                className={cn(
                  "rounded-sm border px-2 py-0.5 text-xs",
                  m.concorda ? "border-sucesso/40 bg-sucesso/10 text-texto" : "border-aviso/50 bg-aviso/10 text-texto",
                )}
              >
                <span className="font-bold">{m.nome}</span> {nomeSimples(m.primeiro)}
              </li>
            ))}
          </ul>
        </div>
      </div>
      {filhos}
    </section>
  );
}
