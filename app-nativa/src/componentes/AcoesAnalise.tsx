// Botões "Guardar no histórico" e "Exportar PDF" de uma análise. Cada ecrã diz como se monta a análise.
import { useState } from "react";
import { Check, FileText, History } from "lucide-react";
import { Botao } from "@/componentes/ui/botao";
import type { Analise } from "@/lib/analise";
import { guardarAnalise } from "@/lib/historico";
import { abrirRelatorio } from "@/lib/relatorio";

/**
 * Dois botões que usam a análise do momento.
 * Em linguagem simples: "montar" cria a análise com o que o ecrã mostra agora (ou devolve null se ainda não há
 * resultado); "Guardar" põe-na no histórico local e "Exportar PDF" abre o relatório pronto a imprimir.
 */
export function AcoesAnalise({ montar }: { montar: () => Analise | null }) {
  const [guardada, setGuardada] = useState(false);
  const pronto = montar() !== null;
  return (
    <div className="flex flex-wrap items-center gap-2">
      <Botao
        variante="contorno"
        tamanho="pequeno"
        disabled={!pronto}
        onClick={() => {
          const a = montar();
          if (!a) return;
          guardarAnalise(a);
          setGuardada(true);
          setTimeout(() => setGuardada(false), 2500);
        }}
      >
        {guardada ? <Check className="h-3.5 w-3.5" /> : <History className="h-3.5 w-3.5" />}
        {guardada ? "Guardada" : "Guardar no histórico"}
      </Botao>
      <Botao
        variante="secundario"
        tamanho="pequeno"
        disabled={!pronto}
        onClick={() => {
          const a = montar();
          if (a) abrirRelatorio(a);
        }}
      >
        <FileText className="h-3.5 w-3.5" /> Exportar PDF
      </Botao>
    </div>
  );
}
