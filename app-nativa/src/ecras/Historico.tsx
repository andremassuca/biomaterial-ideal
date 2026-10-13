// Histórico de análises: lista as análises guardadas neste computador, com a data e a versão dos dados.
import { useEffect, useState } from "react";
import { FileText, Trash2 } from "lucide-react";
import { CabecalhoEcra, Informacao, NomeMaterial } from "@/componentes/comuns";
import { dataLegivel } from "@/componentes/Relatorio";
import { Botao } from "@/componentes/ui/botao";
import { Cartao, Etiqueta } from "@/componentes/ui/cartao";
import { primeiros, versaoDados, type Analise } from "@/lib/analise";
import { TITULO_CASO, descricaoCenario } from "@/lib/dados";
import { aoMudarHistorico, lerHistorico, limparHistorico, removerAnalise } from "@/lib/historico";
import { abrirRelatorio } from "@/lib/relatorio";

/** Frase curta do perfil de uma análise ("Sem perfil" ou "N dados do doente, M regras"). */
export function resumoPerfil(a: Analise): string {
  const dados = a.perfil ? Object.keys(a.perfil).length : 0;
  if (dados === 0) return "Sem perfil";
  return `${dados} ${dados === 1 ? "dado" : "dados"} do doente, ${a.regras.length} ${a.regras.length === 1 ? "regra" : "regras"}`;
}

export function Historico() {
  const [lista, setLista] = useState<Analise[]>(() => lerHistorico());
  useEffect(() => aoMudarHistorico(() => setLista(lerHistorico())), []);
  const atual = versaoDados();

  return (
    <div className="space-y-6">
      <CabecalhoEcra
        titulo="Histórico"
        subtitulo="As análises que guardou, com a data e a versão dos dados. Ficam só neste computador: não são enviadas para lado nenhum."
        acoes={
          lista.length > 0 ? (
            <Botao variante="contorno" onClick={limparHistorico}>
              <Trash2 className="h-4 w-4" /> Apagar tudo
            </Botao>
          ) : undefined
        }
      />
      {lista.length === 0 ? (
        <Informacao>
          Ainda não há análises guardadas. Nos ecrãs dos casos e do doente, use "Guardar no histórico" depois de ver um
          resultado.
        </Informacao>
      ) : (
        <ul className="space-y-3">
          {lista.map((a) => (
            <li key={a.id}>
              <Cartao className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between md:gap-4" data-analise={a.id}>
                <div className="min-w-0 flex-1 space-y-1">
                  <p className="font-bold">
                    {TITULO_CASO[a.caso]} <span className="font-normal text-texto2">({descricaoCenario(a.cenario)})</span>
                  </p>
                  <p className="text-xs text-texto2">
                    {dataLegivel(a.criadaEm)}. Dados {a.versaoDados}, aplicação {a.versaoApp}. {resumoPerfil(a)}.
                  </p>
                  {a.versaoDados !== atual && (
                    <Etiqueta tom="aviso">Os dados mudaram desde esta análise (versão atual {atual})</Etiqueta>
                  )}
                  <ul className="flex flex-wrap gap-x-4 gap-y-1 pt-1 text-sm">
                    {primeiros(a.ranking).map((p) => (
                      <li key={p.metodo} className="flex items-baseline gap-1.5">
                        <span className="text-xs text-texto2">1.º {p.metodo}:</span>
                        <NomeMaterial material={p.material} linha />
                      </li>
                    ))}
                  </ul>
                </div>
                <div className="flex shrink-0 gap-2">
                  <Botao variante="secundario" tamanho="pequeno" onClick={() => abrirRelatorio(a)}>
                    <FileText className="h-3.5 w-3.5" /> Relatório PDF
                  </Botao>
                  <Botao variante="fantasma" tamanho="pequeno" onClick={() => removerAnalise(a.id)} aria-label="Apagar esta análise">
                    <Trash2 className="h-3.5 w-3.5" />
                  </Botao>
                </div>
              </Cartao>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
