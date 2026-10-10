// Definições: tema, tamanho da letra, movimento e modo apresentação (guardados entre sessões).
import { CabecalhoEcra } from "@/componentes/comuns";
import { Cartao, DescricaoCartao, TituloCartao } from "@/componentes/ui/cartao";
import { Interruptor, Opcoes } from "@/componentes/ui/controlos";
import { useDefinicoes, type Letra, type Movimento, type Tema } from "@/lib/definicoes";

export function Definicoes() {
  const d = useDefinicoes();
  return (
    <div className="max-w-3xl space-y-4">
      <CabecalhoEcra titulo="Definições" subtitulo="As escolhas ficam guardadas neste computador e não saem dele." />
      <Cartao className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <TituloCartao>Tema</TituloCartao>
          <DescricaoCartao>“Sistema” segue o tema do Windows.</DescricaoCartao>
        </div>
        <Opcoes<Tema>
          rotulo="Tema"
          valor={d.tema}
          aoMudar={(tema) => d.definir({ tema })}
          opcoes={[
            { valor: "sistema", texto: "Sistema" },
            { valor: "claro", texto: "Claro" },
            { valor: "escuro", texto: "Escuro" },
          ]}
        />
      </Cartao>
      <Cartao className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <TituloCartao>Tamanho da letra</TituloCartao>
          <DescricaoCartao>Toda a interface acompanha.</DescricaoCartao>
        </div>
        <Opcoes<Letra>
          rotulo="Tamanho da letra"
          valor={d.letra}
          aoMudar={(letra) => d.definir({ letra })}
          opcoes={[
            { valor: "normal", texto: "Normal" },
            { valor: "grande", texto: "Grande" },
            { valor: "muito-grande", texto: "Muito grande" },
          ]}
        />
      </Cartao>
      <Cartao className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <TituloCartao>Movimento</TituloCartao>
          <DescricaoCartao>“Reduzido” tira as animações e a rotação dos modelos 3D.</DescricaoCartao>
        </div>
        <Opcoes<Movimento>
          rotulo="Movimento"
          valor={d.movimento}
          aoMudar={(movimento) => d.definir({ movimento })}
          opcoes={[
            { valor: "sistema", texto: "Sistema" },
            { valor: "completo", texto: "Completo" },
            { valor: "reduzido", texto: "Reduzido" },
          ]}
        />
      </Cartao>
      <Cartao className="flex items-center justify-between gap-4">
        <div>
          <TituloCartao>Modo apresentação</TituloCartao>
          <DescricaoCartao>Letra e gráficos maiores e barra lateral só com ícones, para projetar.</DescricaoCartao>
        </div>
        <Interruptor checked={d.apresentacao} onCheckedChange={(apresentacao) => d.definir({ apresentacao })} aria-label="Modo apresentação" />
      </Cartao>
      <p className="text-xs text-texto2">Idioma: português. A estrutura está preparada para outras línguas, ativadas só a pedido.</p>
    </div>
  );
}
