// Painel lateral do ecrã Doente: mostra, em tempo real, o que os dados do doente fazem ao problema de decisão
// (regras ativas, pesos antes e depois, materiais excluídos, rankings e notas). Tudo vem do resultado do núcleo;
// nada é guardado nem enviado.
import { useEffect, useMemo, useState, type ReactNode } from "react";
import { ArrowDown, ArrowUp, Minus } from "lucide-react";
import { Aviso, EstadoValor, Fonte, Informacao, NomeMaterial } from "@/componentes/comuns";
import { RankingAnimado } from "@/componentes/RankingAnimado";
import { Cartao, Etiqueta, TituloCartao } from "@/componentes/ui/cartao";
import { limparPerfil } from "@/lib/campos";
import type { IdCaso } from "@/lib/dados";
import { pct, decimalPt } from "@/lib/formato";
import { avaliarDoente, mensagemErro, modoNucleo } from "@/lib/nucleo";
import { textoPublico } from "@/lib/publico";
import type { Perfil, Problema, Ranking, Regra, RespostaDoente } from "@/lib/tipos";
import { cn } from "@/lib/utils";

/** Atraso (em milissegundos) entre a última alteração de um campo e o recálculo. */
export const ATRASO_RECALCULO_MS = 250;

/**
 * Avalia o perfil sempre que um campo muda, esperando um instante para não recalcular a cada tecla.
 * Em linguagem simples: devolve a última resposta pronta, se está a recalcular e o erro (se houver). Enquanto
 * recalcula mantém a resposta anterior no ecrã, para o painel não piscar.
 */
export function useAvaliacaoDoente(id: IdCaso, cenario: string, perfil: Perfil, atrasoMs = ATRASO_RECALCULO_MS) {
  const [resposta, setResposta] = useState<RespostaDoente | null>(null);
  const [erro, setErro] = useState<string | null>(null);
  const [aCalcular, setACalcular] = useState(true);
  // a chave de texto evita recalcular quando o objeto muda mas o conteúdo é o mesmo
  const chave = JSON.stringify(limparPerfil(perfil));

  useEffect(() => {
    if (modoNucleo() === "topsis") return;
    let ativo = true;
    setACalcular(true);
    const t = setTimeout(() => {
      avaliarDoente(id, cenario, JSON.parse(chave) as Perfil)
        .then((r) => {
          if (!ativo) return;
          setResposta(r);
          setErro(null);
          setACalcular(false);
        })
        .catch((e) => {
          if (!ativo) return;
          setErro(mensagemErro(e));
          setACalcular(false);
        });
    }, atrasoMs);
    return () => {
      ativo = false;
      clearTimeout(t);
    };
  }, [id, cenario, chave, atrasoMs]);

  return { resposta, erro, aCalcular };
}

export type EstadoPeso = "novo" | "sobe" | "desce" | "igual" | "removido";

export interface LinhaPeso {
  criterio: string;
  antes: number | null;
  depois: number | null;
  estado: EstadoPeso;
}

/**
 * Compara os pesos do caso de base com os pesos depois das regras.
 * Em linguagem simples: para cada critério diz se é novo, se o peso subiu, desceu, ficou igual ou se saiu.
 */
export function variacaoPesos(antes: Problema, depois: Problema): LinhaPeso[] {
  const linhas: LinhaPeso[] = depois.criterios.map((c, j) => {
    const k = antes.criterios.indexOf(c);
    const wa = k >= 0 ? antes.pesos[k] : null;
    const wd = depois.pesos[j];
    const estado: EstadoPeso = wa === null ? "novo" : wd > wa + 1e-9 ? "sobe" : wd < wa - 1e-9 ? "desce" : "igual";
    return { criterio: c, antes: wa, depois: wd, estado };
  });
  antes.criterios.forEach((c, k) => {
    if (!depois.criterios.includes(c)) linhas.push({ criterio: c, antes: antes.pesos[k], depois: null, estado: "removido" });
  });
  return linhas;
}

/** Descreve o efeito de uma regra com os valores que vêm dos dados (sem números escritos à mão). */
export function descreverEfeito(r: Regra): string {
  switch (r.efeito) {
    case "peso multiplicado":
      return `peso de “${r.alvo_do_efeito}” × ${decimalPt(r.valor)} (fator: valor de desenho)`;
    case "critério acrescentado":
      return `entra “${r.alvo_do_efeito}” com peso ${decimalPt(r.valor)} (valor de desenho)`;
    case "leitura do problema":
      return `${r.alvo_do_efeito} (fator ${decimalPt(r.valor)})`;
    case "exclusão":
      return `saem: ${r.alvo_do_efeito}`;
    default:
      return r.alvo_do_efeito;
  }
}

/**
 * Encontra a regra de exclusão que retira um material.
 * Em linguagem simples: lê a lista de materiais de cada regra de exclusão e devolve a que o nomeia; se nenhuma o
 * nomear mas só existir uma regra de exclusão, devolve essa.
 */
export function regraQueExclui(material: string, regras: Regra[]): Regra | null {
  const exclusoes = regras.filter((r) => r.efeito === "exclusão");
  const nomeada = exclusoes.find((r) => r.alvo_do_efeito.split(";").some((a) => a.trim() === material));
  return nomeada ?? (exclusoes.length === 1 ? exclusoes[0] : null);
}

export interface MudancaPosicao {
  material: string;
  antes: number | undefined;
  depois: number | undefined;
}

/**
 * Posição de cada material no consenso (Borda) antes e depois, só dos que mudam.
 * Em linguagem simples: lista os materiais que subiram, desceram ou saíram do ranking face ao caso de base.
 */
export function mudancasPosicao(base: Ranking, depois: Ranking): MudancaPosicao[] {
  const pos = (r: Ranking, m: string) => {
    const i = r.alternativas.indexOf(m);
    return i < 0 ? undefined : r.pos_borda[i];
  };
  return base.alternativas
    .map((m) => ({ material: m, antes: pos(base, m), depois: pos(depois, m) }))
    .filter((x) => x.antes !== x.depois)
    .sort((a, b) => (a.depois ?? Infinity) - (b.depois ?? Infinity));
}

const ROTULO_ESTADO: Record<EstadoPeso, string> = {
  novo: "novo",
  sobe: "sobe",
  desce: "desce",
  igual: "igual",
  removido: "removido",
};

/** Barras dos pesos: a barra clara é o caso de base, a barra cheia é o peso com os dados do doente. */
export function BarrasPesos({ linhas }: { linhas: LinhaPeso[] }) {
  const maximo = Math.max(1e-9, ...linhas.flatMap((l) => [l.antes ?? 0, l.depois ?? 0]));
  const largura = (w: number | null) => `${w === null ? 0 : (100 * w) / maximo}%`;
  return (
    <ul className="space-y-3" aria-label="Pesos dos critérios, base e doente">
      {linhas.map((l) => (
        <li key={l.criterio} data-estado={l.estado}>
          <div className="mb-1 flex items-center justify-between gap-2 text-sm">
            <span className={cn("min-w-0 break-words leading-tight", l.estado !== "igual" && "font-medium")}>{l.criterio}</span>
            {l.estado !== "igual" && (
              <Etiqueta tom={l.estado === "desce" || l.estado === "removido" ? "neutro" : "acento"}>{ROTULO_ESTADO[l.estado]}</Etiqueta>
            )}
          </div>
          <div aria-hidden className="space-y-1">
            <div className="h-1.5 rounded-full bg-superficie2">
              <div className="h-full rounded-full bg-texto2/40" style={{ width: largura(l.antes) }} />
            </div>
            <div className="h-2 rounded-full bg-superficie2">
              <div
                className={cn("h-full rounded-full transition-[width] duration-300", l.estado === "sobe" || l.estado === "novo" ? "bg-acento" : "bg-texto2")}
                style={{ width: largura(l.depois) }}
              />
            </div>
          </div>
          <div className="numero mt-1 flex justify-between text-xs text-texto2">
            <span>Base: {l.antes === null ? "novo" : pct(100 * l.antes)}</span>
            <span className={cn((l.estado === "sobe" || l.estado === "novo") && "font-medium text-acento-texto")}>
              Doente: {l.depois === null ? "removido" : pct(100 * l.depois)}
            </span>
          </div>
        </li>
      ))}
    </ul>
  );
}

/** Uma regra ativa, com condição, efeito, justificação, fonte e estado sempre visíveis. */
export function RegraPainel({ regra: r }: { regra: Regra }) {
  return (
    <li className="rounded-md border border-linha p-3" data-regra={r.id}>
      <div className="flex items-start gap-2">
        <Etiqueta tom="acento">{r.id}</Etiqueta>
        <div className="min-w-0 flex-1 text-sm">
          <div className="font-medium">{r.condicao ?? r.condicao_codigo}</div>
          <div className="text-texto2">
            {r.efeito}: {descreverEfeito(r)}
          </div>
        </div>
        <EstadoValor estado={r.estado} />
      </div>
      {r.justificacao && <p className="mt-2 text-xs leading-relaxed">{textoPublico(r.justificacao)}</p>}
      <Fonte referencia={r.fonte} doi={r.doi_url} className="mt-1 flex" />
    </li>
  );
}

function SetaPosicao({ m }: { m: MudancaPosicao }) {
  if (m.depois === undefined) return <span className="text-texto2">excluído</span>;
  if (m.antes === undefined) return <span className="numero">{m.depois}.º</span>;
  const Icone = m.depois < m.antes ? ArrowUp : m.depois > m.antes ? ArrowDown : Minus;
  const cor = m.depois < m.antes ? "text-sucesso" : "text-perigo";
  return (
    <span className="numero inline-flex items-center gap-1">
      {m.antes}.º → {m.depois}.º <Icone aria-hidden className={cn("h-3.5 w-3.5", cor)} />
    </span>
  );
}

function Secao({ titulo, children }: { titulo: string; children: ReactNode }) {
  return (
    <Cartao>
      <TituloCartao>{titulo}</TituloCartao>
      <div className="mt-3">{children}</div>
    </Cartao>
  );
}

/** Conteúdo do painel para uma resposta já calculada (separado do cálculo para se poder testar). */
export function ConteudoPainel({ id, resposta }: { id: IdCaso; resposta: RespostaDoente }) {
  const { base_problema, base, resultado } = resposta;
  const linhas = useMemo(() => variacaoPesos(base_problema, resultado.problema), [base_problema, resultado.problema]);
  const mudancas = useMemo(() => mudancasPosicao(base, resultado.ranking), [base, resultado.ranking]);
  const pesosMudaram = linhas.some((l) => l.estado !== "igual");
  return (
    <div className="space-y-4">
      <Secao titulo="Regras ativas">
        {resultado.regras.length === 0 ? (
          <p className="text-sm text-texto2">Nenhuma regra se aplica a estes dados: o resultado é igual ao caso de base.</p>
        ) : (
          <ul className="space-y-2">
            {resultado.regras.map((r) => (
              <RegraPainel key={r.id} regra={r} />
            ))}
          </ul>
        )}
      </Secao>

      <Secao titulo="Impacto no peso dos critérios">
        {!pesosMudaram && <p className="mb-3 text-xs text-texto2">Os pesos não mudam face ao caso de base.</p>}
        <BarrasPesos linhas={linhas} />
      </Secao>

      {resultado.excluidos.length > 0 && (
        <Secao titulo="Materiais excluídos">
          <ul className="space-y-2 text-sm">
            {resultado.excluidos.map((m) => {
              const r = regraQueExclui(m, resultado.regras);
              return (
                <li key={m} className="rounded-md bg-superficie2 px-3 py-2" data-excluido={m}>
                  <NomeMaterial material={m} linha />
                  {r && (
                    <span className="block text-xs text-texto2">
                      Regra {r.id}: {r.condicao ?? r.condicao_codigo}
                    </span>
                  )}
                </li>
              );
            })}
          </ul>
        </Secao>
      )}

      <Secao titulo="Ranking com os dados do doente">
        <RankingAnimado caso={id} ranking={resultado.ranking} />
        {mudancas.length > 0 ? (
          <ul className="mt-3 space-y-1 border-t border-linha pt-3 text-sm" aria-label="Mudanças de posição no consenso (Borda)">
            {mudancas.map((m) => (
              <li key={m.material} className="flex items-center justify-between gap-2">
                <NomeMaterial material={m.material} />
                <SetaPosicao m={m} />
              </li>
            ))}
          </ul>
        ) : (
          <p className="mt-3 border-t border-linha pt-3 text-xs text-texto2">Nenhuma posição muda no consenso (Borda) face ao caso de base.</p>
        )}
      </Secao>

      {resultado.notas.length > 0 && (
        <Secao titulo="Notas">
          <ul className="space-y-2 text-sm">
            {resultado.notas.map((n) => (
              <li key={n} className="rounded-md bg-superficie2 px-3 py-2">
                {textoPublico(n)}
              </li>
            ))}
          </ul>
        </Secao>
      )}
    </div>
  );
}

/**
 * Painel lateral completo: calcula (com atraso) e mostra o impacto dos dados do doente.
 * O aviso de que não é uma ferramenta clínica está sempre visível, mesmo antes de haver resultado.
 */
export function PainelImpacto({ id, cenario, perfil }: { id: IdCaso; cenario: string; perfil: Perfil }) {
  const { resposta, erro, aCalcular } = useAvaliacaoDoente(id, cenario, perfil);
  const semNucleo = modoNucleo() === "topsis";
  return (
    <aside aria-label="Impacto dos dados do doente" className="space-y-4">
      <Aviso />
      <div className="flex items-center justify-between gap-2">
        <h2 className="text-base font-bold">Impacto dos dados</h2>
        <span role="status" className="text-xs text-texto2">
          {aCalcular && !semNucleo ? "a recalcular…" : "atualizado"}
        </span>
      </div>
      {semNucleo ? (
        <Informacao>O resultado do perfil é calculado pelo núcleo Rust: abra a aplicação nativa.</Informacao>
      ) : erro ? (
        <p className="text-sm text-perigo">{erro}</p>
      ) : !resposta ? (
        <div className="h-64 animate-pulse rounded-lg bg-superficie2" />
      ) : (
        <div className={cn("transition-opacity", aCalcular && "opacity-60")}>
          <ConteudoPainel id={id} resposta={resposta} />
        </div>
      )}
    </aside>
  );
}
