// Fluxo do doente em passos: dispositivo, dados gerais, dados do dispositivo e resultado com
// "o que mudou face ao caso de base" (cada alteração com a fonte). Nada é guardado nem enviado.
import { ResumoResultado } from "@/componentes/ResumoResultado";
import { useEffect, useMemo, useState, type ReactNode } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { ArrowDown, ArrowLeft, ArrowRight, ArrowUp, Check, ChevronDown, Minus, UserRound } from "lucide-react";
import { AcoesAnalise } from "@/componentes/AcoesAnalise";
import { Aviso, CabecalhoEcra, EstadoValor, Fonte, Ilustracao, Informacao, NomeMaterial } from "@/componentes/comuns";
import { RankingAnimado } from "@/componentes/RankingAnimado";
import { PainelImpacto } from "@/componentes/doente/PainelImpacto";
import { Botao } from "@/componentes/ui/botao";
import { Cartao, DescricaoCartao, Etiqueta, TituloCartao } from "@/componentes/ui/cartao";
import { Opcoes } from "@/componentes/ui/controlos";
import { criarAnalise } from "@/lib/analise";
import { CAMPOS, NOMES_SECAO, camposEmFalta, chavesDoCaso, limparPerfil, type Campo } from "@/lib/campos";
import { CASOS, ILUSTRACAO_CASO, SEMIQUANTITATIVOS, TITULO_CASO, cenarios, descricaoCenario, nomeSimples, type IdCaso } from "@/lib/dados";
import { num, pct, decimalPt } from "@/lib/formato";
import { avaliarDoente, mensagemErro, modoNucleo } from "@/lib/nucleo";
import { textoPublico } from "@/lib/publico";
import type { Perfil, Regra, RespostaDoente } from "@/lib/tipos";
import { cn } from "@/lib/utils";

const PASSOS = ["Dispositivo", "Dados gerais", "Dados do dispositivo", "Resultado"] as const;
const DISPOSITIVOS: IdCaso[] = ["Haste", "Par articular", "Stent", "Scaffold", "Implante dentário"];

export function Doente() {
  const [passo, setPasso] = useState(0);
  const [id, setId] = useState<IdCaso>("Haste");
  const caso = CASOS[id];
  const [cenario, setCenario] = useState("A");
  const [perfil, setPerfil] = useState<Perfil>({});
  const chaves = useMemo(() => chavesDoCaso(caso), [caso]);

  useEffect(() => {
    if (!caso.cenarios[cenario]) setCenario(cenarios(caso)[0]);
  }, [caso, cenario]);

  const mudar = (k: string, v: string | number | "") => setPerfil((p) => ({ ...p, [k]: v }));

  return (
    <div className="space-y-6">
      <CabecalhoEcra
        titulo="Doente"
        subtitulo="Os dados do doente mudam os pesos dos critérios, acrescentam critérios ou excluem materiais, segundo regras com fonte. Nada é guardado nem enviado; não há campos de identificação."
      />
      <ol className="flex flex-wrap gap-2" aria-label="Passos">
        {PASSOS.map((p, k) => (
          <li key={p}>
            <button
              type="button"
              onClick={() => setPasso(k)}
              aria-current={k === passo ? "step" : undefined}
              className={cn(
                "flex items-center gap-2 rounded-full border px-3 py-1.5 text-sm",
                k === passo ? "border-acento bg-acento/10 font-bold text-texto" : "border-linha text-texto2 hover:text-texto",
              )}
            >
              <span
                className={cn(
                  "flex h-5 w-5 items-center justify-center rounded-full text-xs",
                  k < passo ? "bg-acento text-white" : "bg-superficie2",
                )}
              >
                {k < passo ? <Check className="h-3 w-3" /> : k + 1}
              </span>
              {p}
            </button>
          </li>
        ))}
      </ol>

      {/* painel lateral em tempo real nos passos de preenchimento: ao lado em ecrãs largos, por baixo nos estreitos */}
      <div className={cn("grid gap-6 [&>*]:min-w-0", passo < 3 && "xl:grid-cols-[minmax(0,1fr)_26rem]")}>
      <AnimatePresence mode="wait">
        <motion.div
          key={passo}
          initial={{ opacity: 0, x: 16 }}
          animate={{ opacity: 1, x: 0 }}
          exit={{ opacity: 0, x: -16 }}
          transition={{ duration: 0.22 }}
        >
          {passo === 0 && (
            <PassoDispositivo
              id={id}
              setId={(n) => {
                setId(n);
                setPerfil({});
              }}
              cenario={cenario}
              setCenario={setCenario}
              aplicarExemplo={(p) => {
                setPerfil(p);
                setPasso(3);
              }}
            />
          )}
          {passo === 1 && <PassoCampos campos={CAMPOS.filter((c) => c.grupo === "geral")} chaves={chaves} perfil={perfil} mudar={mudar} seccoes />}
          {passo === 2 && <PassoEspecifico id={id} chaves={chaves} perfil={perfil} mudar={mudar} />}
          {passo === 3 && <PassoResultado id={id} cenario={cenario} perfil={perfil} />}
        </motion.div>
      </AnimatePresence>
      {passo < 3 && (
        <div className="xl:sticky xl:top-4 xl:max-h-[calc(100vh-2rem)] xl:self-start xl:overflow-y-auto">
          <PainelImpacto id={id} cenario={cenario} perfil={perfil} />
        </div>
      )}
      </div>

      <div className="flex justify-between">
        <Botao variante="contorno" onClick={() => setPasso((p) => Math.max(0, p - 1))} disabled={passo === 0}>
          <ArrowLeft className="h-4 w-4" /> Anterior
        </Botao>
        {passo < PASSOS.length - 1 ? (
          <Botao onClick={() => setPasso((p) => Math.min(PASSOS.length - 1, p + 1))}>
            Seguinte <ArrowRight className="h-4 w-4" />
          </Botao>
        ) : (
          <Botao
            variante="secundario"
            onClick={() => {
              setPerfil({});
              setPasso(1);
            }}
          >
            Limpar os dados
          </Botao>
        )}
      </div>
    </div>
  );
}

function PassoDispositivo({
  id,
  setId,
  cenario,
  setCenario,
  aplicarExemplo,
}: {
  id: IdCaso;
  setId: (id: IdCaso) => void;
  cenario: string;
  setCenario: (c: string) => void;
  aplicarExemplo: (p: Perfil) => void;
}) {
  const caso = CASOS[id];
  const exemplos = Object.entries(caso.perfis_referencia);
  return (
    <div className="space-y-6">
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
        {DISPOSITIVOS.map((d) => (
          <button
            key={d}
            type="button"
            onClick={() => setId(d)}
            aria-pressed={d === id}
            className={cn(
              "flex flex-col items-center gap-2 rounded-lg border p-4 text-center",
              d === id ? "border-acento bg-acento/10" : "border-linha bg-superficie hover:border-acento/50",
            )}
          >
            <Ilustracao nome={ILUSTRACAO_CASO[d]} className="h-16 w-16 text-acento" />
            <span className="text-sm font-bold">{TITULO_CASO[d]}</span>
            {SEMIQUANTITATIVOS.includes(d) && <Etiqueta>semiquantitativo</Etiqueta>}
          </button>
        ))}
      </div>
      <Cartao>
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <TituloCartao>Cenário</TituloCartao>
            <DescricaoCartao>{descricaoCenario(cenario)}</DescricaoCartao>
          </div>
          <Opcoes rotulo="Cenário" valor={cenario} aoMudar={setCenario} opcoes={cenarios(caso).map((c) => ({ valor: c, texto: `Cenário ${c}` }))} />
        </div>
      </Cartao>
      {exemplos.length > 0 && (
        <Cartao>
          <TituloCartao>Perfis de exemplo</TituloCartao>
          <DescricaoCartao>Um toque preenche os dados e mostra o resultado.</DescricaoCartao>
          <div className="mt-3 flex flex-wrap gap-2">
            {exemplos.map(([pid, e]) => (
              <Botao key={pid} variante="contorno" onClick={() => aplicarExemplo(e.perfil)}>
                <UserRound className="h-4 w-4" /> {pid}: {e.descricao}
              </Botao>
            ))}
          </div>
        </Cartao>
      )}
      {SEMIQUANTITATIVOS.includes(id) && (
        <Informacao>
          Caso semiquantitativo: os critérios ordinais (escala de 1 a 5) pesam mais de metade, por isso o ranking é só uma
          indicação.
        </Informacao>
      )}
    </div>
  );
}

function PassoEspecifico({ id, chaves, perfil, mudar }: { id: IdCaso; chaves: Set<string>; perfil: Perfil; mudar: (k: string, v: string | number | "") => void }) {
  const caso = CASOS[id];
  const campos = CAMPOS.filter((c) => c.grupo === "especifico" && chaves.has(c.chave));
  const extra: Campo[] = camposEmFalta(caso).map((k) => ({ chave: k, rotulo: k, tipo: "opcoes", grupo: "especifico" }));
  const todos = [...campos, ...extra];
  if (!todos.length) {
    return (
      <Informacao>
        Não há dados específicos para {TITULO_CASO[id].toLowerCase()} nas regras: só os dados gerais contam. Siga para o
        resultado.
      </Informacao>
    );
  }
  return <PassoCampos campos={todos} chaves={chaves} perfil={perfil} mudar={mudar} />;
}

function PassoCampos({
  campos,
  chaves,
  perfil,
  mudar,
  seccoes = false,
}: {
  campos: Campo[];
  chaves: Set<string>;
  perfil: Perfil;
  mudar: (k: string, v: string | number | "") => void;
  seccoes?: boolean;
}) {
  const grupos: [string, Campo[]][] = seccoes
    ? (Object.keys(NOMES_SECAO) as (keyof typeof NOMES_SECAO)[]).map((s) => [NOMES_SECAO[s], campos.filter((c) => c.secao === s)])
    : [["", campos]];
  return (
    <div className="space-y-4">
      {grupos.map(([titulo, lista]) =>
        lista.length ? (
          <Cartao key={titulo || "campos"}>
            {titulo && <TituloCartao>{titulo}</TituloCartao>}
            <div className="mt-3 grid gap-4 md:grid-cols-2">
              {lista.map((c) => (
                <CampoDoente key={c.chave} campo={c} valor={perfil[c.chave]} conta={chaves.has(c.chave)} mudar={mudar} />
              ))}
            </div>
          </Cartao>
        ) : null,
      )}
    </div>
  );
}

function CampoDoente({
  campo: c,
  valor,
  conta,
  mudar,
}: {
  campo: Campo;
  valor: string | number | undefined;
  conta: boolean;
  mudar: (k: string, v: string | number | "") => void;
}) {
  const id = `campo-${c.chave}`;
  let controlo: ReactNode;
  if (c.tipo === "numero") {
    controlo = (
      <div className="flex items-center gap-2">
        <input
          id={id}
          type="number"
          inputMode="decimal"
          value={valor ?? ""}
          onChange={(e) => mudar(c.chave, e.target.value === "" ? "" : Number(e.target.value))}
          className="h-9 w-32 rounded-md border border-linha bg-superficie2 px-2 text-sm"
        />
        {c.unidade && <span className="text-xs text-texto2">{c.unidade}</span>}
      </div>
    );
  } else if (c.tipo === "simnao") {
    controlo = (
      <Opcoes
        rotulo={c.rotulo}
        valor={valor === "sim" ? "sim" : valor === "não" ? "não" : "?"}
        aoMudar={(v) => mudar(c.chave, v === "?" ? "" : v)}
        opcoes={[
          { valor: "?", texto: "Não sei" },
          { valor: "não", texto: "Não" },
          { valor: "sim", texto: "Sim" },
        ]}
      />
    );
  } else if (c.opcoes) {
    controlo = (
      <Opcoes
        rotulo={c.rotulo}
        valor={typeof valor === "string" && valor ? valor : "?"}
        aoMudar={(v) => mudar(c.chave, v === "?" ? "" : v)}
        opcoes={[{ valor: "?", texto: "Não indicado" }, ...c.opcoes]}
      />
    );
  } else {
    controlo = (
      <input
        id={id}
        value={valor ?? ""}
        onChange={(e) => mudar(c.chave, e.target.value)}
        className="h-9 w-48 rounded-md border border-linha bg-superficie2 px-2 text-sm"
      />
    );
  }
  return (
    <div>
      <div className="mb-1 flex flex-wrap items-center gap-2">
        <label htmlFor={id} className="text-sm font-medium">
          {c.rotulo}
        </label>
        {conta ? <Etiqueta tom="acento">conta neste dispositivo</Etiqueta> : <Etiqueta>sem regra neste dispositivo</Etiqueta>}
      </div>
      {controlo}
      {c.ajuda && <p className="mt-1 text-xs text-texto2">{c.ajuda}</p>}
    </div>
  );
}

function PassoResultado({ id, cenario, perfil }: { id: IdCaso; cenario: string; perfil: Perfil }) {
  const [resposta, setResposta] = useState<RespostaDoente | null>(null);
  const [erro, setErro] = useState<string | null>(null);
  const limpo = useMemo(() => limparPerfil(perfil), [perfil]);

  useEffect(() => {
    let ativo = true;
    setResposta(null);
    setErro(null);
    avaliarDoente(id, cenario, limpo)
      .then((r) => ativo && setResposta(r))
      .catch((e) => ativo && setErro(mensagemErro(e)));
    return () => {
      ativo = false;
    };
  }, [id, cenario, limpo]);

  // a versão web também calcula o perfil (núcleo em WebAssembly); só o modo sem núcleo pede a aplicação nativa
  if (modoNucleo() === "topsis") {
    return (
      <div className="space-y-4">
        <Informacao>O resultado do perfil é calculado pelo núcleo Rust: abra a aplicação nativa.</Informacao>
        <Aviso />
      </div>
    );
  }
  if (erro) return <p className="text-sm text-perigo">{erro}</p>;
  if (!resposta) return <div className="h-64 animate-pulse rounded-lg bg-superficie2" />;

  const { base_problema, resultado } = resposta;
  return (
    <div className="space-y-6">
      <div className="flex justify-end">
        <AcoesAnalise
          montar={() =>
            criarAnalise({
              caso: id,
              cenario,
              problemaBase: base_problema,
              problemaUsado: resultado.problema,
              ranking: resultado.ranking,
              perfil: limpo,
              regras: resultado.regras,
              excluidos: resultado.excluidos,
              notas: resultado.notas,
            })
          }
        />
      </div>
      <ResumoResultado ranking={resultado.ranking} prefixo="1.º com este perfil" />
      <div className="grid gap-6 [&>*]:min-w-0 xl:grid-cols-2">
        <Cartao>
          <TituloCartao>Com os dados do doente</TituloCartao>
          <DescricaoCartao>
            {TITULO_CASO[id]}, {descricaoCenario(cenario).replace(/^C/, "c")}
          </DescricaoCartao>
          <div className="mt-4">
            <RankingAnimado caso={id} ranking={resultado.ranking} />
          </div>
        </Cartao>
        <Cartao>
          <TituloCartao>Lado a lado com o caso de base</TituloCartao>
          <DescricaoCartao>Posição no consenso (Borda) e nos três métodos: base → doente.</DescricaoCartao>
          <Comparacao resposta={resposta} />
        </Cartao>
      </div>
      {sensibilidadePerfil(id, resposta) && (
        <Informacao>
          <span data-sensibilidade>
            Com este perfil, o TOPSIS põe {nomeSimples(sensibilidadePerfil(id, resposta) ?? "")} em 1.º. Lê-se como
            sensibilidade ao fator do perfil (um valor de desenho), não como recomendação.
          </span>
        </Informacao>
      )}

      <Cartao>
        <TituloCartao>O que mudou face ao caso de base</TituloCartao>
        {resultado.regras.length === 0 ? (
          <p className="mt-2 text-sm text-texto2">Nenhuma regra se aplica a estes dados: o resultado é igual ao caso de base.</p>
        ) : (
          <ul className="mt-3 space-y-2">
            {resultado.regras.map((r) => (
              <RegraAtiva key={r.id} regra={r} />
            ))}
          </ul>
        )}
        {resultado.excluidos.length > 0 && (
          <p className="mt-3 text-sm">
            <strong>Materiais excluídos:</strong>{" "}
            {resultado.excluidos.map((m, k) => (
              <span key={m}>
                {k > 0 && ", "}
                <NomeMaterial material={m} linha />
              </span>
            ))}
          </p>
        )}
        {resultado.notas.length > 0 && (
          <ul className="mt-3 space-y-1 text-sm">
            {resultado.notas.map((n) => (
              <li key={n} className="rounded-md bg-superficie2 px-3 py-2">
                <strong>Nota:</strong> {textoPublico(n)}
              </li>
            ))}
          </ul>
        )}
        <TabelaPesos antes={base_problema} depois={resultado.problema} />
      </Cartao>
      {notaFixacao(id, perfil) && (
        <Cartao>
          <div className="flex flex-wrap items-center justify-between gap-2">
            <TituloCartao>Antes do material: o modo de fixação</TituloCartao>
            <EstadoValor estado="A verificar" />
          </div>
          <p className="mt-2 text-sm leading-relaxed">{NOTA_FIXACAO}</p>
          <p className="mt-2 text-xs text-texto2">Nota sem efeito no ranking.</p>
        </Cartao>
      )}
      <Aviso />
    </div>
  );
}

/**
 * Material que o TOPSIS passa a pôr em 1.º na haste com o perfil, quando é diferente do 1.º do TOPSIS no caso de base
 * (ex.: o jovem ativo, H1, com o cobalto-crómio). Em linguagem simples: na haste, esta troca vem só do fator de peso do
 * perfil, por isso a aplicação mostra-a como sensibilidade e não como recomendação. Devolve null se nada muda ou
 * noutro caso.
 */
export function sensibilidadePerfil(id: IdCaso, resposta: RespostaDoente): string | null {
  if (id !== "Haste") return null;
  const primeiro = (r: RespostaDoente["base"]) => r.alternativas[r.pos_topsis.indexOf(1)];
  const base = primeiro(resposta.base);
  const doente = primeiro(resposta.resultado.ranking);
  return doente && doente !== base ? doente : null;
}

/** Nota clínica da haste no doente com osteoporose (revisão clínica de 10 out; sem efeito no ranking). */
export const NOTA_FIXACAO =
  "No doente idoso com osteoporose, a decisão principal costuma ser o modo de fixação (haste cimentada ou não cimentada), antes do material. Este modelo compara materiais de hastes não cimentadas; numa haste cimentada polida o material é aço inoxidável ou Co-Cr, e o módulo de Young deixa de ser o critério determinante.";

/** Mostra a nota da fixação só na haste, quando o doente tem osteoporose. */
export function notaFixacao(id: IdCaso, perfil: Perfil): boolean {
  return id === "Haste" && perfil.osteoporose === "sim";
}

const EFEITO: Record<string, string> = {
  "peso multiplicado": "peso multiplicado",
  "critério acrescentado": "critério acrescentado",
  "leitura do problema": "leitura do problema",
  exclusão: "exclusão",
  nota: "nota",
};

function RegraAtiva({ regra: r }: { regra: Regra }) {
  const [aberta, setAberta] = useState(false);
  const efeito =
    r.efeito === "peso multiplicado"
      ? `peso de “${r.alvo_do_efeito}” × ${decimalPt(r.valor)} (fator: valor de desenho)`
      : r.efeito === "critério acrescentado"
        ? `entra “${r.alvo_do_efeito}” com peso ${decimalPt(r.valor)} (valor de desenho)`
        : r.efeito === "leitura do problema"
          ? `${r.alvo_do_efeito} (fator ${decimalPt(r.valor)})`
          : r.efeito === "exclusão"
            ? `saem: ${r.alvo_do_efeito}`
            : r.alvo_do_efeito;
  return (
    <li className="rounded-md border border-linha">
      <button type="button" onClick={() => setAberta((a) => !a)} aria-expanded={aberta} className="flex w-full items-start gap-3 px-3 py-2 text-left">
        <Etiqueta tom="acento">{r.id}</Etiqueta>
        <div className="min-w-0 flex-1 text-sm">
          <div className="font-medium">{r.condicao ?? r.condicao_codigo}</div>
          <div className="text-texto2">
            {EFEITO[r.efeito] ?? r.efeito}: {efeito}
          </div>
        </div>
        <EstadoValor estado={r.estado} />
        <ChevronDown aria-hidden className={cn("mt-0.5 h-4 w-4 text-texto2 transition-transform", aberta && "rotate-180")} />
      </button>
      {aberta && (
        <div className="space-y-2 border-t border-linha px-3 py-2">
          {r.justificacao && <p className="text-xs leading-relaxed">{textoPublico(r.justificacao)}</p>}
          <Fonte referencia={r.fonte} doi={r.doi_url} className="flex" />
        </div>
      )}
    </li>
  );
}

function TabelaPesos({ antes, depois }: { antes: RespostaDoente["base_problema"]; depois: RespostaDoente["base_problema"] }) {
  const mudou = depois.criterios.some((c, j) => {
    const k = antes.criterios.indexOf(c);
    return k < 0 || Math.abs(antes.pesos[k] - depois.pesos[j]) > 1e-9;
  });
  if (!mudou) return null;
  return (
    <div className="mt-4 overflow-x-auto">
      <table className="tabela-limpa w-full text-left text-sm">
        <caption className="mb-2 text-left text-xs text-texto2">Pesos dos critérios (somam 100 % antes e depois)</caption>
        <thead className="text-xs text-texto2">
          <tr>
            <th className="py-1 font-medium">Critério</th>
            <th className="py-1 font-medium">Base</th>
            <th className="py-1 font-medium">Doente</th>
          </tr>
        </thead>
        <tbody>
          {depois.criterios.map((c, j) => {
            const k = antes.criterios.indexOf(c);
            const wa = k >= 0 ? antes.pesos[k] : null;
            const wd = depois.pesos[j];
            const sobe = wa !== null && wd > wa + 1e-9;
            return (
              <tr key={c} className="border-t border-linha">
                <td className="py-1.5 pr-3">{c}</td>
                <td className="numero py-1.5">{wa === null ? "novo" : pct(100 * wa)}</td>
                <td className={cn("numero py-1.5 font-medium", (sobe || wa === null) && "text-acento-texto")}>{pct(100 * wd)}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

function Seta({ antes, depois }: { antes: number | undefined; depois: number | undefined }) {
  if (antes === undefined || depois === undefined) return <span className="text-texto2">excluído</span>;
  const Icone = depois < antes ? ArrowUp : depois > antes ? ArrowDown : Minus;
  const cor = depois < antes ? "text-sucesso" : depois > antes ? "text-perigo" : "text-texto2";
  return (
    <span className="numero inline-flex items-center gap-1">
      {antes}.º → {depois}.º <Icone aria-hidden className={cn("h-3.5 w-3.5", cor)} />
    </span>
  );
}

function Comparacao({ resposta }: { resposta: RespostaDoente }) {
  const { base, resultado } = resposta;
  const pos = (lista: string[], valores: number[], a: string) => {
    const i = lista.indexOf(a);
    return i < 0 ? undefined : valores[i];
  };
  const ordem = [...base.alternativas].sort(
    (a, b) => (pos(base.alternativas, base.pos_borda, a) ?? Infinity) - (pos(base.alternativas, base.pos_borda, b) ?? Infinity),
  );
  const r = resultado.ranking;
  return (
    <div className="mt-4 overflow-x-auto">
      <table className="tabela-limpa w-full text-left text-sm">
        <thead className="text-xs text-texto2">
          <tr>
            <th className="py-1 font-medium">Material</th>
            <th className="py-1 font-medium">Borda</th>
            <th className="py-1 font-medium">TOPSIS</th>
            <th className="py-1 font-medium">WASPAS</th>
            <th className="py-1 font-medium">VIKOR</th>
          </tr>
        </thead>
        <tbody>
          {ordem.map((a) => (
            <tr key={a} className="border-t border-linha">
              <td className="py-1.5 pr-2">
                <NomeMaterial material={a} />
              </td>
              <td className="py-1.5">
                <Seta antes={pos(base.alternativas, base.pos_borda, a)} depois={pos(r.alternativas, r.pos_borda, a)} />
              </td>
              <td className="py-1.5">
                <Seta antes={pos(base.alternativas, base.pos_topsis, a)} depois={pos(r.alternativas, r.pos_topsis, a)} />
              </td>
              <td className="py-1.5">
                <Seta antes={pos(base.alternativas, base.pos_waspas, a)} depois={pos(r.alternativas, r.pos_waspas, a)} />
              </td>
              <td className="py-1.5">
                <Seta antes={pos(base.alternativas, base.pos_vikor, a)} depois={pos(r.alternativas, r.pos_vikor, a)} />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      <p className="mt-2 text-xs text-texto2">
        C do TOPSIS do 1.º com o doente: {num(Math.max(...r.c_topsis), 3)}; no caso de base: {num(Math.max(...base.c_topsis), 3)}.
      </p>
    </div>
  );
}
