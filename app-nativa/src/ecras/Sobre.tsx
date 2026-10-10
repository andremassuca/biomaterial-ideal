// Sobre: versão, autoria, enquadramento académico e o aviso fixo.
import { Aviso, CabecalhoEcra } from "@/componentes/comuns";
import { Cartao } from "@/componentes/ui/cartao";
import pacote from "../../package.json";

const LINHAS: [string, string][] = [
  ["Versão", pacote.version],
  ["Autor", "André Oliveira Massuça"],
  ["Instituição", "Universidade Lusófona, Faculdade de Engenharia"],
  ["Unidade curricular", "Próteses e Órgãos Artificiais"],
  ["Trabalho", "TP2: Qual é o biomaterial ideal?"],
  ["Método", "TOPSIS, WASPAS e VIKOR com critérios-alvo (Petković et al., Appl. Sci. 2025, 15(16), 9198), consenso de Borda e Monte Carlo"],
  ["Letra", "Inter (SIL Open Font License)"],
];

export function Sobre() {
  return (
    <div className="max-w-3xl space-y-4">
      <CabecalhoEcra titulo="Biomaterial Ideal" subtitulo="Exploração educativa da seleção multicritério de biomateriais." />
      <Cartao>
        <dl className="grid gap-x-6 gap-y-3 sm:grid-cols-[180px_1fr]">
          {LINHAS.map(([k, v]) => (
            <div key={k} className="contents">
              <dt className="text-sm text-texto2">{k}</dt>
              <dd className="text-sm font-medium">{v}</dd>
            </div>
          ))}
        </dl>
      </Cartao>
      <Aviso />
      <p className="text-xs text-texto2">
        Os dados vêm da base verificada do trabalho (data/ e results/), com a fonte e o estado de cada valor nas fichas
        dos materiais. Os dados do doente não são guardados nem enviados; só as definições ficam neste computador.
      </p>
    </div>
  );
}
