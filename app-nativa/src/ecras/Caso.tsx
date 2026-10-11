// Ecrã de um caso quantitativo (haste, stent, scaffold): ranking animado, pesos ajustáveis, η e Monte Carlo em direto.
import { useEffect, useMemo, useRef, useState } from "react";
import { Play, RotateCcw, Square } from "lucide-react";
import { Aviso, CabecalhoEcra, Informacao, NomeMaterial } from "@/componentes/comuns";
import { GraficoMC } from "@/componentes/GraficoMC";
import { RankingAnimado } from "@/componentes/RankingAnimado";
import { Botao } from "@/componentes/ui/botao";
import { Cartao, DescricaoCartao, Etiqueta, TituloCartao } from "@/componentes/ui/cartao";
import { Cursor, Dica, Opcoes, Progresso } from "@/componentes/ui/controlos";
import { APP, CASOS, RECOMENDACAO, TITULO_CASO, cenarios, descricaoCenario, type IdCaso } from "@/lib/dados";
import { num, pct, valor } from "@/lib/formato";
import { avaliarCaso, mensagemErro, modoNucleo, monteCarlo, pararMonteCarlo } from "@/lib/nucleo";
import type { Problema, RespostaCaso, ResumoMonteCarlo } from "@/lib/tipos";

/** Texto do tipo de critério, com o valor-alvo quando existe. */
export function textoTipo(p: Problema, j: number): string {
  const t = p.tipos[j];
  if (t === "benefit") return "benefício (maior é melhor)";
  if (t === "cost") return "custo (menor é melhor)";
  return `alvo: ${valor(p.alvos[j])} (mais perto é melhor)`;
}

function iguais(a: number[], b: number[]): boolean {
  return a.length === b.length && a.every((v, i) => Math.abs(v - b[i]) < 1e-12);
}

const ITERACOES = [1_000, 10_000, 100_000];

export function Caso({ id }: { id: IdCaso }) {
  const caso = CASOS[id];
  const lista = cenarios(caso);
  const [cenario, setCenario] = useState(lista[0]);
  const base = caso.cenarios[cenario];
  const etaBase = caso.parametros.eta ?? 1;
  const [pesosGuardados, setPesos] = useState<number[]>(base.pesos);
  // Logo a seguir a mudar de cenário, o número de critérios pode ainda não bater: usam-se os de base.
  const pesos = pesosGuardados.length === base.pesos.length ? pesosGuardados : base.pesos;
  const [eta, setEta] = useState(etaBase);
  const [resposta, setResposta] = useState<RespostaCaso | null>(null);
  const [erro, setErro] = useState<string | null>(null);

  // Ao mudar de caso ou de cenário, volta aos pesos de base.
  useEffect(() => {
    setPesos(caso.cenarios[cenario].pesos);
    setEta(etaBase);
  }, [id, cenario, caso, etaBase]);

  const alterado = !iguais(pesos, base.pesos) || eta !== etaBase;

  // Recalcula o ranking (com uma pequena espera para não calcular a cada pixel do cursor).
  useEffect(() => {
    let ativo = true;
    const t = setTimeout(() => {
      avaliarCaso({ caso: id, cenario, pesos, eta })
        .then((r) => ativo && (setResposta(r), setErro(null)))
        .catch((e) => ativo && setErro(mensagemErro(e)));
    }, 120);
    return () => {
      ativo = false;
      clearTimeout(t);
    };
  }, [id, cenario, pesos, eta]);

  const soma = pesos.reduce((a, b) => a + b, 0) || 1;

  return (
    <div className="space-y-6">
      <CabecalhoEcra
        titulo={TITULO_CASO[id]}
        subtitulo="Mude os pesos dos critérios e veja os materiais trocarem de lugar nos três métodos. O Monte Carlo repete o cálculo milhares de vezes com as propriedades (ou os pesos) a variar dentro dos intervalos da base."
        acoes={
          <Opcoes
            rotulo="Cenário"
            valor={cenario}
            aoMudar={setCenario}
            opcoes={lista.map((c) => ({ valor: c, texto: `Cenário ${c}` }))}
          />
        }
      />
      <p className="-mt-4 text-xs text-texto2">{descricaoCenario(cenario)}</p>
      {RECOMENDACAO[id] && (
        <p className="rounded-lg border border-linha bg-superficie px-4 py-3 text-sm" data-recomendacao>
          <strong>Recomendação: </strong>
          {RECOMENDACAO[id]}
        </p>
      )}

      {modoNucleo() === "topsis" && (
        <Informacao>
          Modo navegador: só o TOPSIS é calculado aqui. WASPAS, VIKOR, Borda, η e Monte Carlo usam o núcleo Rust da
          aplicação nativa.
        </Informacao>
      )}

      <div className="grid gap-6 [&>*]:min-w-0 xl:grid-cols-[1fr_380px]">
        <div className="space-y-6">
          <Cartao>
            <TituloCartao>Ranking</TituloCartao>
            <DescricaoCartao>
              Materiais pelo nome simples, com o código em letra pequena. A coroa marca o 1.º de cada método.
            </DescricaoCartao>
            <div className="mt-4">
              {erro && <p className="mb-2 text-sm text-perigo">{erro}</p>}
              {resposta ? (
                <RankingAnimado caso={id} ranking={resposta.ranking} apenasTopsis={resposta.apenasTopsis} />
              ) : (
                <div className="h-48 animate-pulse rounded-md bg-superficie2" />
              )}
            </div>
          </Cartao>
          <PainelMonteCarlo id={id} cenario={cenario} pesos={pesos} eta={eta} alterado={alterado} />
          <Aviso />
        </div>

        <Cartao className="h-fit">
          <div className="flex items-center justify-between">
            <TituloCartao>Pesos dos critérios</TituloCartao>
            {alterado && (
              <Botao
                variante="fantasma"
                tamanho="pequeno"
                onClick={() => {
                  setPesos(base.pesos);
                  setEta(etaBase);
                }}
              >
                <RotateCcw className="h-3.5 w-3.5" /> Repor
              </Botao>
            )}
          </div>
          <DescricaoCartao>Os pesos são renormalizados para somar 100 %.</DescricaoCartao>
          <ul className="mt-4 space-y-4">
            {base.criterios.map((c, j) => (
              <li key={c}>
                <div className="flex items-baseline justify-between gap-2 text-sm">
                  <span className="font-medium leading-tight">{c}</span>
                  <span className="numero shrink-0 font-bold text-acento-texto">{pct((100 * pesos[j]) / soma)}</span>
                </div>
                <div className="flex items-center gap-2">
                  {base.tipos[j] === "target" ? (
                    <Dica texto="Critério-alvo: o melhor não é o maior nem o menor, é o mais próximo de um valor ideal (por exemplo, a rigidez do osso).">
                      <span className="cursor-help text-xs text-texto2 underline decoration-dotted">{textoTipo(base, j)}</span>
                    </Dica>
                  ) : (
                    <span className="text-xs text-texto2">{textoTipo(base, j)}</span>
                  )}
                </div>
                <Cursor
                  aria-label={`Peso de ${c}`}
                  min={0}
                  max={0.5}
                  step={0.01}
                  value={[pesos[j]]}
                  onValueChange={([v]) => setPesos((w) => w.map((x, k) => (k === j ? v : x)))}
                />
              </li>
            ))}
          </ul>
          <div className="mt-6 border-t border-linha pt-4">
            <div className="flex items-baseline justify-between text-sm">
              <Dica texto="η é a confiança nos pesos escolhidos: 1 usa só estes pesos; 0 usa só pesos objetivos, calculados pela dispersão dos dados (desvio-padrão). Resultado principal do relatório com η = 1.">
                <span className="cursor-help font-medium underline decoration-dotted">Nível de confiança η</span>
              </Dica>
              <span className="numero font-bold text-acento-texto">{num(eta, 1)}</span>
            </div>
            <Cursor
              aria-label="Nível de confiança η"
              min={0}
              max={1}
              step={0.1}
              value={[eta]}
              disabled={modoNucleo() === "topsis"}
              onValueChange={([v]) => setEta(Math.round(v * 10) / 10)}
            />
          </div>
        </Cartao>
      </div>
    </div>
  );
}

function PainelMonteCarlo({
  id,
  cenario,
  pesos,
  eta,
  alterado,
}: {
  id: IdCaso;
  cenario: string;
  pesos: number[];
  eta: number;
  alterado: boolean;
}) {
  const [nIter, setNIter] = useState(String(ITERACOES[1]));
  const [variar, setVariar] = useState<"propriedades" | "pesos">("propriedades");
  const [progresso, setProgresso] = useState(0);
  const [aCorrer, setACorrer] = useState(false);
  const [resumo, setResumo] = useState<ResumoMonteCarlo | null>(null);
  const [erro, setErro] = useState<string | null>(null);
  const [tempo, setTempo] = useState<number | null>(null);
  const inicio = useRef(0);

  // Um resultado antigo deixa de valer quando o caso, o cenário ou os pesos mudam.
  useEffect(() => {
    setResumo(null);
    setProgresso(0);
  }, [id, cenario, pesos, eta, variar]);

  // Valores do relatório (results/monte_carlo.csv), só comparáveis com o caso de base no cenário A.
  const referencia = useMemo(() => {
    if (alterado || cenario !== "A") return null;
    const analise = variar === "propriedades" ? "MC propriedades" : "W pesos ±20 %";
    const linhas = APP.monte_carlo_referencia.filter((l) => l.caso === id && l.analise === analise);
    return linhas.length ? linhas : null;
  }, [alterado, cenario, variar, id]);

  const correr = async () => {
    setErro(null);
    setACorrer(true);
    setProgresso(0);
    inicio.current = performance.now();
    try {
      const r = await monteCarlo({ caso: id, cenario, pesos, eta, nIter: Number(nIter), variar }, (feitas, total) =>
        setProgresso((100 * feitas) / total),
      );
      setResumo(r);
      setTempo(performance.now() - inicio.current);
    } catch (e) {
      setErro(mensagemErro(e));
    } finally {
      setACorrer(false);
    }
  };

  return (
    <Cartao>
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <TituloCartao>Robustez: Monte Carlo em direto</TituloCartao>
          <DescricaoCartao>
            {variar === "propriedades"
              ? "Cada repetição sorteia cada propriedade entre o mínimo e o máximo da base (os ordinais não variam)."
              : "Cada repetição multiplica cada peso por um fator aleatório à volta de 1 e renormaliza."}
          </DescricaoCartao>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <Opcoes
            rotulo="O que varia"
            valor={variar}
            aoMudar={setVariar}
            opcoes={[
              { valor: "propriedades", texto: "Propriedades" },
              { valor: "pesos", texto: "Pesos" },
            ]}
          />
          <Opcoes
            rotulo="Número de repetições"
            valor={nIter}
            aoMudar={setNIter}
            opcoes={ITERACOES.map((n) => ({ valor: String(n), texto: num(n, 0) }))}
          />
          {aCorrer ? (
            <Botao variante="perigo" onClick={() => pararMonteCarlo()}>
              <Square className="h-4 w-4" /> Parar
            </Botao>
          ) : (
            <Botao onClick={correr} disabled={modoNucleo() === "topsis"}>
              <Play className="h-4 w-4" /> Correr
            </Botao>
          )}
        </div>
      </div>
      <div className="mt-4 space-y-3">
        {(aCorrer || resumo) && <Progresso valor={aCorrer ? progresso : 100} rotulo="Progresso do Monte Carlo" />}
        {modoNucleo() === "topsis" && <Informacao>O Monte Carlo corre no núcleo Rust: abra a aplicação nativa.</Informacao>}
        {erro && <p className="text-sm text-perigo">{erro}</p>}
        {resumo && (
          <>
            <p className="text-xs text-texto2">
              {num(resumo.feitas, 0)} de {num(resumo.pedidas, 0)} repetições
              {resumo.parado ? " (parado a pedido)" : ""}
              {tempo !== null ? ` em ${num(tempo / 1000, 2)} s` : ""}.
            </p>
            <GraficoMC resumo={resumo} />
            {referencia && !resumo.parado && (
              <div className="rounded-md border border-linha p-3">
                <p className="mb-2 text-xs text-texto2">
                  Comparação com o relatório (results/monte_carlo.csv, {num(referencia[0].n_iter, 0)} repetições, semente{" "}
                  {referencia[0].seed}): % em 1.º lugar.
                </p>
                <table className="w-full text-left text-xs">
                  <thead className="text-texto2">
                    <tr>
                      <th className="py-1 font-medium">Material</th>
                      {resumo.metodos.map((m) => (
                        <th key={m.metodo} className="py-1 font-medium">
                          {m.metodo}: app / relatório
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {resumo.alternativas.map((a, i) => (
                      <tr key={a} className="border-t border-linha">
                        <td className="py-1">
                          <NomeMaterial material={a} linha />
                        </td>
                        {resumo.metodos.map((m) => {
                          const ref = referencia.find((l) => l.material === a && l.metodo === m.metodo);
                          return (
                            <td key={m.metodo} className="numero py-1">
                              {pct(m.pct_primeiro[i])} / {ref ? pct(ref.pct_primeiro) : "n.d."}
                            </td>
                          );
                        })}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
            {alterado && <Etiqueta tom="aviso">Pesos ou η alterados: resultado diferente do relatório</Etiqueta>}
          </>
        )}
      </div>
    </Cartao>
  );
}
