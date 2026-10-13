// Comparar materiais: dois materiais do mesmo caso lado a lado, propriedade a propriedade, com fonte, estado,
// quem é melhor segundo o tipo do critério e a posição de cada um no ranking de referência.
import { useEffect, useMemo, useState } from "react";
import { ArrowLeftRight } from "lucide-react";
import { RadarComparacao } from "@/componentes/comparar/RadarComparacao";
import { LinhaComparar } from "@/componentes/comparar/LinhaComparar";
import { CabecalhoEcra, Informacao, NomeMaterial } from "@/componentes/comuns";
import { Botao } from "@/componentes/ui/botao";
import { Cartao, DescricaoCartao, TituloCartao } from "@/componentes/ui/cartao";
import { compararMateriais, linhasDoCaso, resumoComparacao } from "@/lib/comparar";
import { CASOS, TITULO_CASO, cenarios, descricaoCenario, fichaMaterial, rotuloMaterial, type IdCaso } from "@/lib/dados";
import { ordinal } from "@/lib/formato";
import { avaliarCaso } from "@/lib/nucleo";
import type { Ranking } from "@/lib/tipos";
import { cn } from "@/lib/utils";

const CASOS_ID = Object.keys(CASOS) as IdCaso[];

const CLASSE_SELECAO =
  "h-9 w-full rounded-md border border-linha bg-superficie2 px-2 text-sm text-texto outline-none focus:border-acento focus:ring-2 focus:ring-acento";

/** Cenário com mais materiais (o mais completo), para começar com a lista inteira. */
function cenarioCompleto(caso: IdCaso): string {
  const c = CASOS[caso];
  return cenarios(c).reduce((m, k) => (c.cenarios[k].alternativas.length > c.cenarios[m].alternativas.length ? k : m));
}

export function Comparar() {
  const [caso, setCaso] = useState<IdCaso>("Haste");
  const [cenario, setCenario] = useState(() => cenarioCompleto("Haste"));
  const [a, setA] = useState(() => CASOS.Haste.cenarios[cenarioCompleto("Haste")].alternativas[0]);
  const [b, setB] = useState(() => CASOS.Haste.cenarios[cenarioCompleto("Haste")].alternativas[1]);
  const [radar, setRadar] = useState(false);
  const [ranking, setRanking] = useState<Ranking | null>(null);

  const problema = CASOS[caso].cenarios[cenario];
  const materiais = problema.alternativas;

  const mudarCaso = (novo: IdCaso) => {
    const c = cenarioCompleto(novo);
    const alts = CASOS[novo].cenarios[c].alternativas;
    setCaso(novo);
    setCenario(c);
    setA(alts[0]);
    setB(alts[1] ?? alts[0]);
  };
  const mudarCenario = (c: string) => {
    const alts = CASOS[caso].cenarios[c].alternativas;
    setCenario(c);
    if (!alts.includes(a)) setA(alts[0]);
    if (!alts.includes(b)) setB(alts[1] ?? alts[0]);
  };

  // Ranking de referência do caso (pesos de base), para mostrar a posição de cada material.
  useEffect(() => {
    let vivo = true;
    setRanking(null);
    avaliarCaso({ caso, cenario })
      .then((r) => vivo && setRanking(r.ranking))
      .catch(() => vivo && setRanking(null));
    return () => {
      vivo = false;
    };
  }, [caso, cenario]);

  const linhas = useMemo(() => {
    const fa = linhasDoCaso(fichaMaterial(a), problema.criterios);
    const fb = linhasDoCaso(fichaMaterial(b), problema.criterios);
    return compararMateriais(problema, a, b, fa, fb);
  }, [problema, a, b]);
  const resumo = resumoComparacao(linhas.map((l) => l.melhor));
  const nomeA = rotuloMaterial(a);
  const nomeB = rotuloMaterial(b);
  const mesmo = a === b;

  let frase: string;
  if (resumo.comparaveis === 0) frase = "Não há propriedades com valor nos dois materiais.";
  else if (resumo.a === resumo.b) frase = `${nomeA} e ${nomeB} estão empatados: cada um é melhor em ${resumo.a} de ${resumo.comparaveis} propriedades comparáveis.`;
  else {
    const [venc, n] = resumo.a > resumo.b ? [nomeA, resumo.a] : [nomeB, resumo.b];
    frase = `${venc} é melhor em ${n} de ${resumo.comparaveis} propriedades comparáveis.`;
  }

  return (
    <div className="space-y-6">
      <CabecalhoEcra
        titulo="Comparar materiais"
        subtitulo="Dois materiais do mesmo caso, propriedade a propriedade, com a fonte e o estado de cada valor. “Melhor” segue o tipo de cada critério (maior, menor ou mais perto do alvo)."
      />

      <Cartao>
        <div className="grid items-end gap-3 [&>*]:min-w-0 md:grid-cols-[1fr_1fr_auto_1fr_1fr]">
          <label className="space-y-1 text-xs font-medium text-texto2">
            Caso
            <select className={CLASSE_SELECAO} value={caso} onChange={(e) => mudarCaso(e.target.value as IdCaso)} aria-label="Caso">
              {CASOS_ID.map((c) => (
                <option key={c} value={c}>
                  {TITULO_CASO[c]}
                </option>
              ))}
            </select>
          </label>
          <label className="space-y-1 text-xs font-medium text-texto2">
            Cenário
            <select className={CLASSE_SELECAO} value={cenario} onChange={(e) => mudarCenario(e.target.value)} aria-label="Cenário">
              {cenarios(CASOS[caso]).map((c) => (
                <option key={c} value={c}>
                  {descricaoCenario(c)}
                </option>
              ))}
            </select>
          </label>
          <Botao variante="contorno" onClick={() => (setA(b), setB(a))} aria-label="Trocar os dois materiais">
            <ArrowLeftRight aria-hidden className="h-4 w-4" />
            Trocar
          </Botao>
          <label className="space-y-1 text-xs font-medium text-texto2">
            Material A
            <select className={CLASSE_SELECAO} value={a} onChange={(e) => setA(e.target.value)} aria-label="Material A">
              {materiais.map((m) => (
                <option key={m} value={m}>
                  {rotuloMaterial(m)}
                </option>
              ))}
            </select>
          </label>
          <label className="space-y-1 text-xs font-medium text-texto2">
            Material B
            <select className={CLASSE_SELECAO} value={b} onChange={(e) => setB(e.target.value)} aria-label="Material B">
              {materiais.map((m) => (
                <option key={m} value={m}>
                  {rotuloMaterial(m)}
                </option>
              ))}
            </select>
          </label>
        </div>
      </Cartao>

      <Cartao role="region" aria-label="Resumo da comparação">
        <p className="text-base font-bold" aria-live="polite">
          {mesmo ? "Escolheu o mesmo material nos dois lados." : frase}
        </p>
        {!mesmo && (
          <DescricaoCartao>
            {nomeA}: {resumo.a} · {nomeB}: {resumo.b} · empates: {resumo.empates} · sem valor num dos materiais: {resumo.total - resumo.comparaveis}
          </DescricaoCartao>
        )}
        <div className="mt-4 grid gap-3 [&>*]:min-w-0 md:grid-cols-2">
          {[a, b].map((m, k) => (
            <PosicaoRanking key={k} material={m} ranking={ranking} lado={k === 0 ? "A" : "B"} />
          ))}
        </div>
      </Cartao>

      <Cartao>
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <TituloCartao>Propriedade a propriedade</TituloCartao>
            <DescricaoCartao>
              {TITULO_CASO[caso]} · {descricaoCenario(cenario)}
            </DescricaoCartao>
          </div>
          <Botao variante="contorno" tamanho="pequeno" onClick={() => setRadar((r) => !r)} aria-pressed={radar}>
            {radar ? "Esconder o radar" : "Mostrar o radar"}
          </Botao>
        </div>
        {radar && (
          <div className="mt-4">
            <RadarComparacao problema={problema} a={a} b={b} />
            <p className="text-xs text-texto2">Pontuação de 0 a 1 em cada critério entre os materiais do cenário (1 é o melhor segundo o tipo do critério).</p>
          </div>
        )}
        <div className="mt-4 hidden gap-3 md:grid md:grid-cols-2">
          <div className="text-sm">
            <span className="text-xs font-bold text-texto2">A · </span>
            <NomeMaterial material={a} linha />
          </div>
          <div className="text-sm">
            <span className="text-xs font-bold text-texto2">B · </span>
            <NomeMaterial material={b} linha />
          </div>
        </div>
        <ul className="mt-2 divide-y divide-linha">
          {linhas.map((l) => (
            <LinhaComparar key={l.criterio} linha={l} />
          ))}
        </ul>
      </Cartao>
    </div>
  );
}

/** Posição de um material no ranking de referência do caso (TOPSIS, WASPAS, VIKOR e consenso de Borda). */
function PosicaoRanking({ material, ranking, lado }: { material: string; ranking: Ranking | null; lado: string }) {
  const i = ranking ? ranking.alternativas.indexOf(material) : -1;
  const pos = (v: number[]) => (i >= 0 && v.length > i ? ordinal(v[i]) : "n.d.");
  const itens: [string, number[]][] = ranking
    ? [
        ["TOPSIS", ranking.pos_topsis],
        ["WASPAS", ranking.pos_waspas],
        ["VIKOR", ranking.pos_vikor],
        ["Borda", ranking.pos_borda],
      ]
    : [];
  return (
    <div className="rounded-md bg-superficie2 p-3" data-ranking={lado}>
      <div className="text-xs font-bold text-texto2">
        {lado} · {rotuloMaterial(material)}
      </div>
      {ranking ? (
        <>
          <dl className="mt-1 flex flex-wrap gap-x-4 gap-y-1">
            {itens.map(([m, v]) => (
              <div key={m} className={cn("flex items-baseline gap-1.5")}>
                <dt className="text-xs text-texto2">{m}</dt>
                <dd className="numero text-sm font-bold">{pos(v)}</dd>
              </div>
            ))}
          </dl>
          {ranking.pos_borda.length === 0 && <Informacao className="mt-2 text-xs">Só o TOPSIS está disponível neste modo.</Informacao>}
        </>
      ) : (
        <p className="mt-1 text-sm text-texto2">Ranking de referência a calcular.</p>
      )}
    </div>
  );
}
