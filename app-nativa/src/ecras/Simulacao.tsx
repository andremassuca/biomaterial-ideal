// Ecrã "Simulação FEA e CFD": resultados já existentes da haste (SOLIDWORKS e Python) e do stent (OpenFOAM e Fluent).
import { Aviso, CabecalhoEcra } from "@/componentes/comuns";
import { SimulacaoCfd } from "@/componentes/simulacao/SimulacaoCfd";
import { SimulacaoFea } from "@/componentes/simulacao/SimulacaoFea";
import { ConteudoSeparador, ListaSeparadores, Separador, Separadores } from "@/componentes/ui/controlos";

/** Aviso específico das simulações (além do aviso geral da aplicação). */
export const AVISO_SIMULACAO = "Verificação numérica cruzada, não validação clínica.";

export function Simulacao() {
  return (
    <div className="space-y-6">
      <CabecalhoEcra
        titulo="Simulação FEA e CFD"
        subtitulo="Resultados das simulações da haste femoral (elementos finitos) e do stent (dinâmica de fluidos), com imagens, escalas e números dos ficheiros de resultados."
      />
      <p role="note" className="rounded-md border border-aviso/40 bg-aviso/10 px-3 py-2 text-sm font-medium text-texto">
        {AVISO_SIMULACAO} Modelos idealizados, comparados entre ferramentas; a ordem dos materiais é a leitura que se retém.
      </p>
      <Separadores defaultValue="fea" className="space-y-6">
        <ListaSeparadores>
          <Separador value="fea">Haste femoral (FEA)</Separador>
          <Separador value="cfd">Stent (CFD)</Separador>
        </ListaSeparadores>
        <ConteudoSeparador value="fea">
          <SimulacaoFea />
        </ConteudoSeparador>
        <ConteudoSeparador value="cfd">
          <SimulacaoCfd />
        </ConteudoSeparador>
      </Separadores>
      <Aviso />
    </div>
  );
}
