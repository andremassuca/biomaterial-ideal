// Ranking animado dos três métodos e do consenso de Borda; os materiais trocam de lugar com uma mola.
import { motion } from "framer-motion";
import { Crown } from "lucide-react";
import { APP, type IdCaso } from "@/lib/dados";
import { corMaterial } from "@/lib/cores";
import { useDefinicoes } from "@/lib/definicoes";
import { num } from "@/lib/formato";
import type { Ranking } from "@/lib/tipos";
import { cn } from "@/lib/utils";
import { NomeMaterial } from "./comuns";
import { Dica } from "./ui/controlos";

interface Coluna {
  titulo: string;
  dica: string;
  posicoes: number[];
  pontuacoes: number[];
  rotulo: string;
  casas: number;
}

function colunas(r: Ranking, apenasTopsis: boolean): Coluna[] {
  const c: Coluna[] = [
    {
      titulo: "TOPSIS",
      dica: "Proximidade à solução ideal (C): 1 seria o material ideal em todos os critérios, 0 o pior. Maior é melhor.",
      posicoes: r.pos_topsis,
      pontuacoes: r.c_topsis,
      rotulo: "C",
      casas: 3,
    },
  ];
  if (apenasTopsis) return c;
  return [
    ...c,
    {
      titulo: "WASPAS",
      dica: "Média de uma soma pesada e de um produto pesado das pontuações normalizadas (Q). Maior é melhor.",
      posicoes: r.pos_waspas,
      pontuacoes: r.q_waspas,
      rotulo: "Q",
      casas: 3,
    },
    {
      titulo: "VIKOR",
      dica: "Compromisso entre o desempenho de conjunto e o pior critério de cada material (P). Menor é melhor.",
      posicoes: r.pos_vikor,
      pontuacoes: r.p_vikor,
      rotulo: "P",
      casas: 3,
    },
    {
      titulo: "Consenso (Borda)",
      dica: "Cada método dá pontos pela posição (o último recebe 0); ganha quem soma mais. Empates desfeitos pelo TOPSIS.",
      posicoes: r.pos_borda,
      pontuacoes: r.pontos_borda,
      rotulo: "pontos",
      casas: 0,
    },
  ];
}

export function RankingAnimado({ caso, ranking, apenasTopsis = false }: { caso: IdCaso; ranking: Ranking; apenasTopsis?: boolean }) {
  const { escuro } = useDefinicoes();
  const cols = colunas(ranking, apenasTopsis);
  // ΔC do TOPSIS entre o 1.º e o 2.º: abaixo do limiar do relatório conta como empate.
  const ordemC = [...ranking.c_topsis].sort((a, b) => b - a);
  const deltaC = ordemC.length > 1 ? ordemC[0] - ordemC[1] : null;
  const empate = deltaC !== null && deltaC < APP.limiar_empate;

  return (
    <div className="ranking-caixa">
      {/* colunas pela largura do próprio cartão (container query em tema.css), não pela da janela: a 1920 px, no
          ecrã do doente ou ao lado dos pesos, quatro colunas ficavam com o nome por cima da pontuação */}
      <div className={cn("grid gap-3", apenasTopsis ? "grid-cols-1" : "ranking-grelha")}>
        {cols.map((col) => {
          const ordem = ranking.alternativas
            .map((a, i) => ({ a, i, pos: col.posicoes[i], v: col.pontuacoes[i] }))
            .sort((x, y) => x.pos - y.pos || x.i - y.i);
          return (
            <section key={col.titulo} className="min-w-0 rounded-lg border border-linha bg-superficie p-3" aria-label={`Ranking ${col.titulo}`}>
              <Dica texto={col.dica}>
                <h4 className="mb-2 cursor-help text-sm font-bold text-texto underline decoration-dotted underline-offset-4">
                  {col.titulo}
                </h4>
              </Dica>
              <ol className="space-y-1.5">
                {ordem.map(({ a, i, pos, v }) => (
                  <motion.li
                    key={a}
                    layout
                    transition={{ type: "spring", stiffness: 420, damping: 34 }}
                    className={cn(
                      "flex items-center gap-2 rounded-md border px-2 py-1.5",
                      pos === 1 ? "border-acento/50 bg-acento/10" : "border-transparent bg-superficie2",
                    )}
                  >
                    <span className="numero w-6 shrink-0 text-right text-sm font-bold text-texto2">{pos}.º</span>
                    <span
                      aria-hidden
                      className="h-3 w-3 shrink-0 rounded-full"
                      style={{ background: corMaterial(caso, a, i, escuro) }}
                    />
                    <NomeMaterial material={a} className="min-w-0 flex-1 text-sm" />
                    <span data-pontuacao className="numero shrink-0 whitespace-nowrap text-xs text-texto2">
                      {col.rotulo} {num(v, col.casas)}
                    </span>
                    {pos === 1 && <Crown aria-label="vencedor" className="h-4 w-4 shrink-0 text-acento" />}
                  </motion.li>
                ))}
              </ol>
            </section>
          );
        })}
      </div>
      {deltaC !== null && (
        <p className={cn("mt-2 text-xs", empate ? "text-aviso" : "text-texto2")}>
          ΔC do TOPSIS entre o 1.º e o 2.º: {num(deltaC, 3)}
          {empate ? ` (abaixo de ${num(APP.limiar_empate, 2)}: conta como empate)` : ""}.
        </p>
      )}
    </div>
  );
}
