// "Como funciona": o caminho dos dados até à resposta, em linguagem simples, para quem chega pelo QR do poster.
// Todos os números vêm de dados/ (fichas, problemas dos casos, espectro) ou são calculados aqui com o port do TOPSIS
// (lib/topsis.ts, igual ao núcleo Rust) e com o próprio núcleo (avaliarCaso).
import { Fragment, useEffect, useMemo, useState, type ComponentType, type ReactNode } from "react";
import { motion, useReducedMotion } from "framer-motion";
import { ArrowDown, ArrowRight, Database, Dices, ListOrdered, Target, Trophy } from "lucide-react";
import { Aviso, CabecalhoEcra, EstadoValor, NomeMaterial } from "@/componentes/comuns";
import { Cartao, DescricaoCartao, Etiqueta, TituloCartao } from "@/componentes/ui/cartao";
import { APP, CASOS, nomeSimples } from "@/lib/dados";
import { num, pct, valor } from "@/lib/formato";
import { avaliarCaso } from "@/lib/nucleo";
import { textoPublico } from "@/lib/publico";
import { renormalizar, topsisPassos, type PassosTopsis } from "@/lib/topsis";
import type { LinhaMaterial, LinhaTecido, TipoCriterio } from "@/lib/tipos";

// ------------------------------------------------------------------ textos fixos (sem números)

/** Grupo de cada método: o que faz no trabalho. */
export type GrupoMetodo = "principal" | "consenso" | "robustez" | "confirmacao";

export const ROTULO_GRUPO: Record<GrupoMetodo, string> = {
  principal: "Método principal",
  consenso: "Junta os três",
  robustez: "Robustez",
  confirmacao: "Confirmação",
};

/**
 * Uma frase simples por método. Os três primeiros fazem o ranking; o Borda junta-os; o Monte Carlo e o Sobol testam a
 * robustez; o PROMETHEE II, o MOORA e o CODAS foram corridos no trabalho adicional, à parte desta aplicação.
 */
export const METODOS_SIMPLES: { nome: string; grupo: GrupoMetodo; frase: string }[] = [
  {
    nome: "TOPSIS",
    grupo: "principal",
    frase: "Imagina o material ideal e o pior possível; ganha o que fica mais perto do ideal e mais longe do pior.",
  },
  {
    nome: "WASPAS",
    grupo: "principal",
    frase: "Dá a cada material uma nota que soma e multiplica as notas dos critérios com os seus pesos; um critério muito fraco puxa a nota para baixo.",
  },
  {
    nome: "VIKOR",
    grupo: "principal",
    frase: "Procura o melhor compromisso: olha para o desvio total de cada material e para o seu pior critério, e ganha quem se desvia menos.",
  },
  {
    nome: "Borda",
    grupo: "consenso",
    frase: "Não é um quarto método nem uma validação: resume as três ordens como numa votação (mais pontos a quem fica mais acima) e dá o consenso.",
  },
  {
    nome: "Monte Carlo",
    grupo: "robustez",
    frase: "Análise de robustez: repete o cálculo milhares de vezes com as propriedades a variar dentro dos intervalos das fontes e conta quantas vezes cada material fica em 1.º.",
  },
  {
    nome: "Sobol",
    grupo: "robustez",
    frase: "Análise de robustez dos pesos, feita no trabalho adicional: muda todos os pesos ao mesmo tempo e mede qual deles mais mexe na vantagem do 1.º.",
  },
  {
    nome: "PROMETHEE II",
    grupo: "confirmacao",
    frase: "Método de confirmação do trabalho adicional: compara os materiais dois a dois, critério a critério, e ordena-os pelo saldo das preferências.",
  },
  {
    nome: "MOORA",
    grupo: "confirmacao",
    frase: "Método de confirmação do trabalho adicional: põe tudo na mesma escala, soma o que é bom e subtrai o que é mau.",
  },
  {
    nome: "CODAS",
    grupo: "confirmacao",
    frase: "Método de confirmação do trabalho adicional: ganha o material que fica mais longe do pior caso, medido de duas maneiras.",
  },
];

/** O que quer dizer cada estado da base (legenda de data/leia_me.md, em linguagem simples). */
export const SIGNIFICADO_ESTADO: Record<string, string> = {
  Verificado: "Confirmado na fonte original indicada (artigo ou norma).",
  "Verificado (fornecedor)": "Confirmado na página de um fornecedor que declara cumprir a norma, não no texto da norma.",
  "Verificado (derivado)": "Calculado a partir de valores da fonte, com o cálculo na nota.",
  "Verificado (composição química)": "Resulta da composição química do material (por exemplo, 0 % de níquel num polímero sem metais).",
  "Verificado (composição nominal)": "Resulta da composição nominal do material, indicada na fonte.",
  "Valor de modelação":
    "Número escolhido por uma regra do trabalho: a fonte confirma o comportamento, não o número. Não conta como verificado.",
  "A verificar": "Valor de partida (manual, revisão ou fonte secundária) ainda não confirmado na fonte original.",
};

// ------------------------------------------------------------------ funções (testadas em testes/como_funciona.test.tsx)

export interface ContagemEstado {
  estado: string;
  n: number;
  significado: string;
}

/**
 * Conta os valores da base por estado.
 * Em linguagem simples: percorre as linhas das fichas, junta-as pelo estado ("Verificado", "A verificar", ...) e
 * devolve quantas há de cada, primeiro os verificados, depois os outros, cada grupo do maior para o menor.
 */
export function contarEstados(linhas: Pick<LinhaMaterial, "estado">[]): ContagemEstado[] {
  const conta = new Map<string, number>();
  for (const l of linhas) {
    const e = l.estado ?? "sem estado";
    conta.set(e, (conta.get(e) ?? 0) + 1);
  }
  const ordem = (e: string) => (e.startsWith("Verificado") ? 0 : e === "Valor de modelação" ? 1 : 2);
  return [...conta.entries()]
    .map(([estado, n]) => ({ estado, n, significado: SIGNIFICADO_ESTADO[estado] ?? "Estado da base de dados (ver data/leia_me.md)." }))
    .sort((a, b) => ordem(a.estado) - ordem(b.estado) || b.n - a.n);
}

export interface AlvoRigidez {
  criterio: string;
  alvo: number;
  peso: number;
  tecido: LinhaTecido | null;
}

/**
 * Critério-alvo da rigidez na haste: o valor-alvo do módulo de Young (data/criterios.csv, através de caso_haste.json)
 * e a linha do osso cortical (data/tecido.csv) com a sua fonte e estado.
 */
export function alvoRigidez(): AlvoRigidez {
  const p = CASOS.Haste.cenarios.A;
  const j = p.criterios.findIndex((c, k) => p.tipos[k] === "target" && /módulo de young/i.test(c));
  if (j < 0 || p.alvos[j] === null) throw new Error("a haste não tem o critério-alvo do módulo de Young");
  const tecido =
    APP.fichas.tecido.find((t) => t.tecido === "Osso cortical" && t.propriedade === "Módulo de Young") ?? null;
  return { criterio: p.criterios[j], alvo: p.alvos[j] as number, peso: p.pesos[j], tecido };
}

/** Materiais e critérios do exemplo passo a passo (nomes iguais aos de data/; os números vêm dos dados). */
export const EXEMPLO_MATERIAIS = ["Ti-6Al-4V ELI", "Co-Cr-Mo forjado", "Aço inox 316L"];
export const EXEMPLO_CRITERIOS: { padrao: RegExp; curto: string; unidade: string }[] = [
  { padrao: /^Módulo de Young/, curto: "Rigidez", unidade: "GPa" },
  { padrao: /^Resistência à fadiga/, curto: "Fadiga", unidade: "MPa" },
  { padrao: /^Densidade/, curto: "Densidade", unidade: "g/cm³" },
];

export interface ExemploHaste {
  materiais: string[];
  criterios: { nome: string; curto: string; unidade: string; tipo: TipoCriterio; alvo: number | null; pesoRelatorio: number; peso: number }[];
  /** Valores típicos (uma linha por material). */
  x: number[][];
  passos: PassosTopsis;
  /** Índices dos materiais do maior para o menor C. */
  ordem: number[];
}

/**
 * Exemplo pequeno com os dados reais da haste (cenário A): três materiais, três critérios.
 * Em linguagem simples: tira da base os valores típicos, passa cada coluna para uma escala de 0 a 1 (1 = melhor),
 * usa os pesos do relatório desses três critérios (divididos pela soma, para somarem 100 %) e calcula o C do TOPSIS
 * com o mesmo código que a aplicação usa. Não substitui o caso completo: só mostra o mecanismo.
 */
export function exemploHaste(): ExemploHaste {
  const p = CASOS.Haste.cenarios.A;
  const linhas = EXEMPLO_MATERIAIS.map((m) => {
    const i = p.alternativas.indexOf(m);
    if (i < 0) throw new Error(`material do exemplo fora da haste: ${m}`);
    return i;
  });
  const colunas = EXEMPLO_CRITERIOS.map((c) => {
    const j = p.criterios.findIndex((n) => c.padrao.test(n));
    if (j < 0) throw new Error(`critério do exemplo fora da haste: ${c.curto}`);
    return j;
  });
  const pesosRelatorio = colunas.map((j) => p.pesos[j]);
  const pesos = renormalizar(pesosRelatorio);
  const x = linhas.map((i) => colunas.map((j) => p.x_tipico[i][j]));
  const tipos = colunas.map((j) => p.tipos[j]);
  const alvos = colunas.map((j) => p.alvos[j]);
  const passos = topsisPassos(x, pesos, tipos, alvos);
  const ordem = passos.c.map((_, i) => i).sort((a, b) => passos.c[b] - passos.c[a]);
  return {
    materiais: EXEMPLO_MATERIAIS,
    criterios: colunas.map((j, k) => ({
      nome: p.criterios[j],
      curto: EXEMPLO_CRITERIOS[k].curto,
      unidade: EXEMPLO_CRITERIOS[k].unidade,
      tipo: p.tipos[j],
      alvo: p.alvos[j],
      pesoRelatorio: pesosRelatorio[k],
      peso: pesos[k],
    })),
    x,
    passos,
    ordem,
  };
}

/** Frase curta do tipo de critério. */
export function regraCriterio(tipo: TipoCriterio, alvo: number | null, unidade: string): string {
  if (tipo === "benefit") return "mais é melhor";
  if (tipo === "cost") return "menos é melhor";
  return `perto de ${valor(alvo)} ${unidade} é melhor`;
}

// ------------------------------------------------------------------ ecrã

export function ComoFunciona() {
  return (
    <div className="space-y-6">
      <CabecalhoEcra
        titulo="Como funciona"
        subtitulo="Do valor medido num artigo até ao material em 1.º lugar, em cinco passos. Sem fórmulas: só a ideia de cada passo e um exemplo com os números reais."
      />
      <Fluxo />
      <div className="grid gap-6 [&>*]:min-w-0 lg:grid-cols-2">
        <OQueEMcdm />
        <CriterioAlvo />
      </div>
      <Metodos />
      <Exemplo />
      <Estados />
      <Aviso />
    </div>
  );
}

// ------------------------------------------------------------------ (a) esquema de fluxo

interface PassoFluxo {
  titulo: string;
  texto: string;
  Icone: ComponentType<{ className?: string }>;
}

/** Passos do esquema, com os números tirados dos dados. */
export function passosFluxo(): PassoFluxo[] {
  const nValores = APP.fichas.materiais.length;
  const iter = APP.espectro.find((c) => !c.semiquantitativo && c.n_iter)?.n_iter ?? null;
  return [
    {
      titulo: "Dados com fonte",
      texto: `${num(nValores, 0)} valores de propriedades dos materiais, cada um com a sua fonte e o seu estado.`,
      Icone: Database,
    },
    {
      titulo: "Critérios-alvo",
      texto: "Cada propriedade vira um critério: mais é melhor, menos é melhor, ou o mais perto possível de um alvo.",
      Icone: Target,
    },
    {
      titulo: "TOPSIS, WASPAS e VIKOR",
      texto: "Três métodos ordenam os materiais com os mesmos pesos; o Borda junta as três ordens.",
      Icone: ListOrdered,
    },
    {
      titulo: "Monte Carlo",
      texto: iter
        ? `Repete o cálculo ${num(iter, 0)} vezes com os valores a variar dentro dos intervalos das fontes.`
        : "Repete o cálculo muitas vezes com os valores a variar dentro dos intervalos das fontes.",
      Icone: Dices,
    },
    {
      titulo: "Resposta",
      texto: "O material em 1.º e quão firme é essa escolha: clara, renhida ou dependente do doente.",
      Icone: Trophy,
    },
  ];
}

function Fluxo() {
  const passos = useMemo(passosFluxo, []);
  const reduzir = useReducedMotion();
  return (
    <Cartao>
      <TituloCartao className="text-lg">Da fonte à resposta</TituloCartao>
      <DescricaoCartao>Cada passo usa o resultado do anterior.</DescricaoCartao>
      <ol aria-label="Passos do método, da fonte à resposta" className="mt-4 flex flex-col items-stretch gap-1 lg:flex-row lg:items-stretch lg:gap-0" data-fluxo>
        {passos.map((p, k) => (
          <Fragment key={p.titulo}>
            <motion.li
              initial={reduzir ? false : { opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.08 * k, duration: 0.3 }}
              className="flex min-w-0 flex-1 items-start gap-3 rounded-lg border border-linha bg-superficie2 p-3 lg:flex-col lg:gap-2 lg:p-4"
            >
              <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-acento/15 text-acento-texto">
                <p.Icone aria-hidden className="h-5 w-5" />
              </span>
              <span className="min-w-0">
                <span className="block text-xs font-bold uppercase tracking-wide text-texto2">Passo {k + 1}</span>
                <span className="block font-bold leading-tight">{p.titulo}</span>
                <span className="mt-1 block text-sm leading-snug text-texto2">{p.texto}</span>
              </span>
            </motion.li>
            {k < passos.length - 1 && (
              <li aria-hidden className="flex shrink-0 items-center justify-center text-acento lg:w-8">
                <ArrowDown className="h-5 w-5 lg:hidden" />
                <ArrowRight className="hidden h-5 w-5 lg:block" />
              </li>
            )}
          </Fragment>
        ))}
      </ol>
    </Cartao>
  );
}

// ------------------------------------------------------------------ (b) o que é o MCDM

function OQueEMcdm() {
  return (
    <Cartao className="space-y-2">
      <TituloCartao className="text-lg">O que é a decisão multicritério</TituloCartao>
      <p className="text-sm leading-relaxed">
        Escolher um material para dentro do corpo é pesar muitas coisas ao mesmo tempo: rigidez, resistência, corrosão,
        peso, custo. Nenhum material é o melhor em tudo.
      </p>
      <p className="text-sm leading-relaxed">
        A decisão multicritério (MCDM, em inglês) é um conjunto de métodos que põe todas essas propriedades na mesma
        escala, dá a cada uma um peso (quanto conta) e ordena os materiais de forma transparente e repetível.
      </p>
    </Cartao>
  );
}

// ------------------------------------------------------------------ (d) critério-alvo

function CriterioAlvo() {
  const a = useMemo(alvoRigidez, []);
  const fonte = a.tecido ? textoPublico(a.tecido.fonte?.split("; ")[0] ?? "") : "";
  return (
    <Cartao className="space-y-2" data-criterio-alvo>
      <TituloCartao className="text-lg">O que é um critério-alvo</TituloCartao>
      <p className="text-sm leading-relaxed">
        Em muitos critérios, mais é melhor (a resistência) ou menos é melhor (o peso). Num <strong>critério-alvo</strong>, o
        melhor é ficar perto de um valor certo, nem acima nem abaixo.
      </p>
      <p className="text-sm leading-relaxed">
        Exemplo: a rigidez da haste da anca. Uma haste muito mais rígida do que o osso fica com a carga toda e o osso à
        volta, sem esforço, enfraquece (<em>stress shielding</em>). Por isso o alvo do módulo de Young da haste é{" "}
        <strong className="numero">{valor(a.alvo)} GPa</strong>, perto do osso cortical
        {a.tecido && (
          <>
            {" "}
            (<span className="numero">{num(a.tecido.min, 0)} a {num(a.tecido.max, 0)} {a.tecido.unidade}</span>)
          </>
        )}
        .
      </p>
      {a.tecido && (
        <p className="flex flex-wrap items-center gap-2 text-xs text-texto2">
          <span>Osso cortical: {fonte}</span>
          <EstadoValor estado={a.tecido.estado} />
        </p>
      )}
    </Cartao>
  );
}

// ------------------------------------------------------------------ (c) os métodos

function Metodos() {
  return (
    <Cartao>
      <TituloCartao className="text-lg">Os métodos, numa frase cada</TituloCartao>
      <DescricaoCartao>
        Os três métodos principais fazem o ranking que a aplicação mostra. O Monte Carlo corre aqui em direto. O Sobol, o
        PROMETHEE II, o MOORA e o CODAS foram corridos à parte, no trabalho adicional, para ver se o 1.º lugar se aguenta;
        não entram nas contas desta aplicação.
      </DescricaoCartao>
      <ul className="mt-4 grid gap-3 sm:grid-cols-2 xl:grid-cols-3" aria-label="Métodos">
        {METODOS_SIMPLES.map((m) => (
          <li key={m.nome} className="rounded-lg border border-linha p-3" data-metodo={m.nome}>
            <div className="flex flex-wrap items-center justify-between gap-2">
              <span className="font-bold">{m.nome}</span>
              <Etiqueta tom={m.grupo === "principal" ? "acento" : "neutro"}>{ROTULO_GRUPO[m.grupo]}</Etiqueta>
            </div>
            <p className="mt-1 text-sm leading-snug">{m.frase}</p>
          </li>
        ))}
      </ul>
    </Cartao>
  );
}

// ------------------------------------------------------------------ (e) exemplo passo a passo

/**
 * Tabela pequena do exemplo. No telemóvel (abaixo de sm) passa a uma lista, um bloco por material com os valores lado a
 * lado, para os números não ficarem cortados nos 390 px; a partir de sm é uma tabela normal.
 */
function Tabela({ legenda, cabecalho, linhas }: { legenda: string; cabecalho: string[]; linhas: ReactNode[][] }) {
  return (
    <>
      <ul className="space-y-2 sm:hidden" aria-label={legenda}>
        {linhas.map((l, i) => (
          <li key={i} className="border-t border-linha pt-2">
            <div className="text-sm">{l[0]}</div>
            <dl className="mt-1 grid grid-cols-3 gap-2">
              {l.slice(1).map((c, k) => (
                <div key={k} className="min-w-0">
                  <dt className="text-[0.6875rem] leading-tight text-texto2">{cabecalho[k + 1]}</dt>
                  <dd className="numero text-sm">{c}</dd>
                </div>
              ))}
            </dl>
          </li>
        ))}
      </ul>
      <TabelaLarga legenda={legenda} cabecalho={cabecalho} linhas={linhas} />
    </>
  );
}

function TabelaLarga({ legenda, cabecalho, linhas }: { legenda: string; cabecalho: string[]; linhas: ReactNode[][] }) {
  return (
    <div className="hidden overflow-x-auto sm:block">
      <table className="tabela-limpa w-full text-left text-sm">
        <caption className="sr-only">{legenda}</caption>
        <thead className="text-xs text-texto2">
          <tr>
            {cabecalho.map((c, k) => (
              <th key={k} scope="col" className={`py-1 pr-3 font-medium ${k > 0 ? "text-right" : ""}`}>
                {c}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {linhas.map((l, i) => (
            <tr key={i} className="border-t border-linha">
              {l.map((c, k) =>
                k === 0 ? (
                  <th key={k} scope="row" className="py-1.5 pr-3 text-left font-normal">
                    {c}
                  </th>
                ) : (
                  <td key={k} className="numero py-1.5 pr-3 text-right">
                    {c}
                  </td>
                ),
              )}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function Passo({ n, titulo, children }: { n: number; titulo: string; children: ReactNode }) {
  return (
    <li className="min-w-0 space-y-2 rounded-lg border border-linha p-3 sm:p-4">
      <div className="flex items-center gap-2">
        <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-acento-texto text-sm font-bold text-white dark:text-fundo">{n}</span>
        <span className="font-bold">{titulo}</span>
      </div>
      {children}
    </li>
  );
}

/** Ranking completo da haste (5 materiais, 8 critérios), calculado pelo núcleo. */
function useRankingCompleto() {
  const [r, setR] = useState<{ material: string; c: number; n: number; m: number } | null>(null);
  useEffect(() => {
    let ativo = true;
    avaliarCaso({ caso: "Haste", cenario: "A" })
      .then((x) => {
        if (!ativo) return;
        const i = x.ranking.pos_topsis.indexOf(1);
        setR({ material: x.ranking.alternativas[i], c: x.ranking.c_topsis[i], n: x.problema.alternativas.length, m: x.problema.criterios.length });
      })
      .catch(() => ativo && setR(null));
    return () => {
      ativo = false;
    };
  }, []);
  return r;
}

function Exemplo() {
  const e = useMemo(exemploHaste, []);
  const completo = useRankingCompleto();
  const nome = (i: number) => <NomeMaterial key={e.materiais[i]} material={e.materiais[i]} />;
  const cab = ["Material", ...e.criterios.map((c) => `${c.curto} (${c.unidade})`)];
  const vencedor = e.ordem[0];
  const cMax = Math.max(...e.passos.c);
  const maiorPeso = e.criterios.reduce((a, b) => (b.peso > a.peso ? b : a));
  return (
    <Cartao data-exemplo>
      <TituloCartao className="text-lg">Exemplo passo a passo: haste da anca</TituloCartao>
      <DescricaoCartao>
        Uma versão pequena do caso real, com três materiais e três critérios, para ver o mecanismo. Os valores são os
        típicos da base de dados; as contas são feitas aqui, com o mesmo código da aplicação.
      </DescricaoCartao>
      <ol className="mt-4 grid gap-4 [&>*]:min-w-0 xl:grid-cols-2">
        <Passo n={1} titulo="Os valores da base">
          <Tabela legenda="Valores típicos" cabecalho={cab} linhas={e.materiais.map((_, i) => [nome(i), ...e.x[i].map((v) => valor(v))])} />
          <ul className="text-xs text-texto2">
            {e.criterios.map((c) => (
              <li key={c.curto}>
                {c.curto}: {regraCriterio(c.tipo, c.alvo, c.unidade)}
              </li>
            ))}
          </ul>
        </Passo>
        <Passo n={2} titulo="Tudo na mesma escala, de 0 a 1">
          <p className="text-sm">1 é o melhor valor de cada coluna (ou o mais perto do alvo); 0 é o pior.</p>
          <Tabela
            legenda="Valores normalizados"
            cabecalho={cab.map((c, k) => (k === 0 ? c : c.replace(/ \(.*\)$/, "")))}
            linhas={e.materiais.map((_, i) => [nome(i), ...e.passos.normalizada[i].map((v) => num(v, 3))])}
          />
        </Passo>
        <Passo n={3} titulo="Os pesos dizem quanto conta cada critério">
          <p className="text-sm">
            Pesos do relatório para estes três critérios, divididos pela soma para darem 100 %:
          </p>
          <ul className="flex flex-wrap gap-2 text-sm">
            {e.criterios.map((c) => (
              <li key={c.curto} className="rounded-md bg-superficie2 px-2 py-1">
                {c.curto}: <span className="numero">{pct(c.pesoRelatorio * 100)}</span> →{" "}
                <strong className="numero">{pct(c.peso * 100)}</strong>
              </li>
            ))}
          </ul>
          <Tabela
            legenda="Valores normalizados vezes o peso"
            cabecalho={cab.map((c, k) => (k === 0 ? c : `${c.replace(/ \(.*\)$/, "")} × peso`))}
            linhas={e.materiais.map((_, i) => [nome(i), ...e.passos.pesada[i].map((v) => num(v, 3))])}
          />
        </Passo>
        <Passo n={4} titulo="Pontuação final (TOPSIS) e 1.º lugar">
          <p className="text-sm">
            C mede a proximidade ao material ideal: 1 seria o melhor em tudo, 0 o pior em tudo.
          </p>
          <ul className="space-y-2" aria-label="Pontuação C do exemplo">
            {e.ordem.map((i, k) => (
              <li key={e.materiais[i]} className="grid grid-cols-[2rem_minmax(0,1fr)_3.5rem] items-center gap-2 text-sm" data-c-exemplo={e.materiais[i]}>
                <span className="numero font-bold">{k + 1}.º</span>
                <span className="min-w-0">
                  <span className={i === vencedor ? "font-bold" : ""}>{nomeSimples(e.materiais[i])}</span>
                  <span className="mt-1 block h-2 rounded-full bg-superficie2">
                    <span
                      className={`block h-2 rounded-full ${i === vencedor ? "bg-acento" : "bg-texto2/50"}`}
                      style={{ width: `${(e.passos.c[i] / cMax) * 100}%` }}
                    />
                  </span>
                </span>
                <span className="numero text-right">{num(e.passos.c[i], 3)}</span>
              </li>
            ))}
          </ul>
          <p className="text-sm">
            <strong>{nomeSimples(e.materiais[vencedor])}</strong> ganha neste exemplo.
            {completo && (
              <>
                {" "}
                No caso completo ({completo.n} materiais, {completo.m} critérios), o núcleo de cálculo põe em 1.º{" "}
                <strong>{nomeSimples(completo.material)}</strong> (C = <span className="numero">{num(completo.c, 3)}</span>).
                {completo.material !== e.materiais[vencedor] && (
                  <>
                    {" "}
                    Com só três critérios, a {maiorPeso.curto.toLowerCase()} conta {pct(maiorPeso.peso * 100)}; no caso
                    completo entram mais {completo.m - e.criterios.length} critérios (por exemplo, a corrosão e a compatibilidade
                    com a ressonância magnética) e a ordem muda. É por isso que os critérios e os pesos se escolhem com cuidado e
                    se testam.
                  </>
                )}
              </>
            )}
          </p>
        </Passo>
      </ol>
    </Cartao>
  );
}

// ------------------------------------------------------------------ (f) estados dos valores

function Estados() {
  const linhas = APP.fichas.materiais;
  const contagem = useMemo(() => contarEstados(linhas), [linhas]);
  const verificados = contagem.filter((c) => c.estado.startsWith("Verificado")).reduce((s, c) => s + c.n, 0);
  return (
    <Cartao data-estados>
      <TituloCartao className="text-lg">“Verificado” e “A verificar”</TituloCartao>
      <DescricaoCartao>
        Cada valor da base tem um estado. Dos <span className="numero">{num(linhas.length, 0)}</span> valores,{" "}
        <strong className="numero">{num(verificados, 0)}</strong> estão verificados numa das formas abaixo; os outros ainda
        esperam pela fonte original ou são escolhas de modelação. É por isso que o Monte Carlo testa a escolha com os
        valores a variar.
      </DescricaoCartao>
      <ul className="mt-4 grid gap-2 md:grid-cols-2">
        {contagem.map((c) => (
          <li key={c.estado} className="flex items-start gap-3 rounded-lg border border-linha p-3" data-estado={c.estado}>
            <span className="numero w-10 shrink-0 text-right text-lg font-bold">{num(c.n, 0)}</span>
            <span className="min-w-0 space-y-1">
              <EstadoValor estado={c.estado} />
              <span className="block text-sm leading-snug text-texto2">{c.significado}</span>
            </span>
          </li>
        ))}
      </ul>
    </Cartao>
  );
}
