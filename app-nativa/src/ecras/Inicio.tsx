// Início: a pergunta do trabalho, o espectro de confiança e o visualizador 3D dos dispositivos.
import { useState } from "react";
import { motion } from "framer-motion";
import { ArrowRight, Workflow } from "lucide-react";
import { Aviso, CabecalhoEcra, NomeMaterial } from "@/componentes/comuns";
import { ImagemDispositivo } from "@/componentes/ImagemDispositivo";
import { Espectro } from "@/componentes/Espectro";
import { Botao } from "@/componentes/ui/botao";
import { Visualizador3D, type ChaveModelo } from "@/componentes/Visualizador3D";
import { Cartao, DescricaoCartao, Etiqueta, TituloCartao } from "@/componentes/ui/cartao";
import { Opcoes } from "@/componentes/ui/controlos";
import { APP, ILUSTRACAO_CASO, RECOMENDACAO_CURTA, TITULO_CASO, type IdCaso } from "@/lib/dados";
import type { Ecra } from "@/App";

const MODELOS: { valor: ChaveModelo; texto: string }[] = [
  { valor: "haste", texto: "Haste" },
  { valor: "stent", texto: "Stent" },
  { valor: "scaffold", texto: "Scaffold" },
  { valor: "par", texto: "Par articular" },
  { valor: "dentario", texto: "Implante dentário" },
];

const ECRA_CASO: Partial<Record<IdCaso, Ecra>> = { Haste: "haste", Stent: "stent", Scaffold: "scaffold" };

export function Inicio({ irPara }: { irPara: (e: Ecra) => void }) {
  const [modelo, setModelo] = useState<ChaveModelo>("haste");
  return (
    <div className="space-y-6">
      <CabecalhoEcra
        titulo="Que material pôr dentro do corpo?"
        subtitulo="Cinco dispositivos, uma base de dados com fontes e três métodos de decisão multicritério com critérios-alvo. O espectro mostra quão clara é a escolha em cada caso."
        acoes={
          <Botao tamanho="grande" onClick={() => irPara("como-funciona")} className="font-bold" data-como-funciona>
            <Workflow aria-hidden className="h-4 w-4" />
            Como funciona?
            <ArrowRight aria-hidden className="h-4 w-4" />
          </Botao>
        }
      />

      <section aria-label="Escolha o dispositivo" className="grid grid-cols-1 gap-4 min-[480px]:grid-cols-2 lg:grid-cols-3 2xl:grid-cols-5">
        {APP.espectro.map((c, i) => {
          const id = c.caso as IdCaso;
          const destino = ECRA_CASO[id];
          return (
            <motion.button
              key={c.caso}
              type="button"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.05 * i }}
              onClick={() => irPara(destino ?? "doente")}
              data-cartao-dispositivo={id}
              className="group flex min-w-0 flex-col overflow-hidden rounded-lg border border-linha bg-superficie text-left shadow-sm transition-colors hover:border-acento/60"
            >
              <ImagemDispositivo id={ILUSTRACAO_CASO[id]} ilustracao={ILUSTRACAO_CASO[id]} className="aspect-[4/3] w-full" />
              <div className="flex min-w-0 flex-1 flex-col gap-1 p-4">
                <div className="flex items-start justify-between gap-2">
                  <span className="text-base font-bold leading-tight">{TITULO_CASO[id]}</span>
                  <ArrowRight aria-hidden className="mt-0.5 h-4 w-4 shrink-0 text-texto2 group-hover:text-acento" />
                </div>
                {c.semiquantitativo && <Etiqueta className="w-fit">semiquantitativo</Etiqueta>}
                {RECOMENDACAO_CURTA[id] ? (
                  <p className="text-sm text-texto2" data-recomendacao>
                    {RECOMENDACAO_CURTA[id]}
                  </p>
                ) : (
                  <NomeMaterial material={c.vencedor} linha className="flex-wrap text-sm" />
                )}
              </div>
            </motion.button>
          );
        })}
      </section>

      <Cartao>
        <TituloCartao>Espectro de confiança</TituloCartao>
        <DescricaoCartao>
          Distância entre o 1.º e o 2.º no TOPSIS (ΔC, cenário A). À esquerda, vencedores claros; à direita, escolhas que
          dependem dos dados.
        </DescricaoCartao>
        <div className="mt-4">
          <Espectro />
        </div>
      </Cartao>

      <Cartao className="flex flex-col">
        <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
          <TituloCartao>Os dispositivos em 3D</TituloCartao>
          <Opcoes rotulo="Dispositivo" valor={modelo} aoMudar={setModelo} opcoes={MODELOS} />
        </div>
        <Visualizador3D modelo={modelo} className="h-80" rotulo={`Modelo 3D: ${modelo}`} />
      </Cartao>
      <Aviso />
    </div>
  );
}
