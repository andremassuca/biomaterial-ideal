// Gibson e Ashby: módulo de uma estrutura porosa, E = E maciço × (1 - p)², contra o alvo da haste e o osso cortical.
// E maciço e alvo vêm de caso_haste.json; a faixa do osso cortical vem de data/tecido.csv (app.json).
import { useMemo, useState } from "react";
import { Area, CartesianGrid, ComposedChart, Line, ReferenceArea, ReferenceDot, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { CabecalhoEcra, Fonte, NomeMaterial } from "@/componentes/comuns";
import { Visualizador3D } from "@/componentes/Visualizador3D";
import { Cartao, DescricaoCartao, Etiqueta, TituloCartao } from "@/componentes/ui/cartao";
import { Cursor } from "@/componentes/ui/controlos";
import { APP, CASOS, nomeSimples } from "@/lib/dados";
import { num } from "@/lib/formato";

const CRITERIO_MODULO = "Módulo de Young";

/** E = E_s (1 - p)² (Gibson e Ashby, espumas de células abertas, constante 1). */
export function moduloPoroso(eMacico: number, p: number): number {
  return eMacico * (1 - p) ** 2;
}

/**
 * Marcas regulares do eixo do módulo: passo de 5, 10, 25 ou 50 GPa, com 4 a 6 marcas até acima do máximo.
 * Em linguagem simples: em vez de 0, 30, 60, 114, o eixo fica 0, 25, 50, 75, 100, 125.
 */
export function marcasEixo(maximo: number): { max: number; marcas: number[] } {
  const passo = [5, 10, 25, 50, 100].find((p) => maximo / p <= 5) ?? 100;
  const max = Math.max(passo, Math.ceil(maximo / passo) * passo);
  return { max, marcas: Array.from({ length: max / passo + 1 }, (_, k) => k * passo) };
}

/** Porosidade com que se chega ao módulo E: p = 1 - √(E / E_s). */
export function porosidadePara(e: number, eMacico: number): number {
  return 1 - Math.sqrt(e / eMacico);
}

export function GibsonAshby() {
  // Cenário com mais materiais da haste (inclui os de investigação).
  const p = CASOS.Haste.cenarios.B ?? CASOS.Haste.cenarios.A;
  const j = p.criterios.indexOf(CRITERIO_MODULO);
  const alvo = p.alvos[j] ?? null;
  const cortical = APP.fichas.tecido.find((t) => t.tecido === "Osso cortical" && t.propriedade === CRITERIO_MODULO) ?? null;
  const faixa = cortical && cortical.min !== null && cortical.max !== null ? { min: cortical.min, max: cortical.max } : null;
  const [material, setMaterial] = useState(p.alternativas.includes("Ti-6Al-4V ELI") ? "Ti-6Al-4V ELI" : p.alternativas[0]);
  const eMacico = p.x_tipico[p.alternativas.indexOf(material)][j];
  const pAlvo = alvo !== null ? porosidadePara(alvo, eMacico) : null;
  const [porosidade, setPorosidade] = useState(() => Math.round((pAlvo ?? 0.5) * 100) / 100);
  const e = moduloPoroso(eMacico, porosidade);

  const curva = useMemo(
    () => Array.from({ length: 91 }, (_, k) => ({ p: k, E: moduloPoroso(eMacico, k / 100) })),
    [eMacico],
  );
  const eixoY = useMemo(() => marcasEixo(eMacico * 1.05), [eMacico]);
  const dentroOsso = faixa !== null && e >= faixa.min && e <= faixa.max;

  return (
    <div className="space-y-6">
      <CabecalhoEcra
        titulo="Gibson e Ashby"
        subtitulo="Um metal maciço é muito mais rígido do que o osso. Abrir poros baixa a rigidez: o módulo cai com o quadrado da fração sólida."
      />
      <div className="grid gap-6 [&>*]:min-w-0 xl:grid-cols-[1fr_360px]">
        <Cartao>
          <TituloCartao>Módulo efetivo contra a porosidade</TituloCartao>
          <DescricaoCartao>
            E = E maciço × (1 − p)². Linha tracejada: alvo da haste{alvo !== null ? ` (${num(alvo, 0)} GPa)` : ""}. Faixa: osso
            cortical{faixa ? ` (${num(faixa.min, 0)} a ${num(faixa.max, 0)} GPa)` : ""}.
          </DescricaoCartao>
          <div className="mt-4 h-80" role="img" aria-label="Gráfico do módulo efetivo em função da porosidade">
            <ResponsiveContainer>
              <ComposedChart data={curva} margin={{ left: 8, right: 24, top: 8, bottom: 16 }}>
                <CartesianGrid vertical={false} />
                <XAxis dataKey="p" type="number" domain={[0, 90]} tickFormatter={(v: number) => `${v} %`} stroke="rgb(var(--linha))" />
                <YAxis
                  domain={[0, eixoY.max]}
                  ticks={eixoY.marcas}
                  stroke="rgb(var(--linha))"
                  tickFormatter={(v: number) => num(v, 0)}
                  label={{ value: "Módulo efetivo (GPa)", angle: -90, position: "insideLeft", offset: 0, style: { textAnchor: "middle", fill: "rgb(var(--texto-2))", fontSize: 12 } }}
                  width={64}
                />
                <Tooltip
                  formatter={(v: number) => [`${num(v, 1)} GPa`, "E"]}
                  labelFormatter={(l: number) => `p = ${l} %`}
                  contentStyle={{ color: "rgb(var(--texto))" }}
                />
                {faixa && <ReferenceArea y1={faixa.min} y2={faixa.max} fill="#E69F00" fillOpacity={0.18} strokeOpacity={0} />}
                {alvo !== null && <ReferenceLine y={alvo} stroke="rgb(var(--texto-2))" strokeDasharray="4 4" />}
                <Area dataKey="E" stroke="none" fill="rgb(var(--acento))" fillOpacity={0.08} isAnimationActive={false} />
                <Line dataKey="E" stroke="rgb(var(--acento))" strokeWidth={2.5} dot={false} isAnimationActive={false} />
                <ReferenceDot x={Math.round(porosidade * 100)} y={e} r={7} fill="rgb(var(--acento))" stroke="rgb(var(--superficie))" strokeWidth={2} />
              </ComposedChart>
            </ResponsiveContainer>
          </div>
          <div className="mt-4">
            <div className="flex items-baseline justify-between text-sm">
              <span className="font-medium">Porosidade p</span>
              <span className="numero text-lg font-bold text-acento-texto">{num(porosidade * 100, 0)} %</span>
            </div>
            <Cursor
              aria-label="Porosidade"
              min={0}
              max={0.9}
              step={0.01}
              value={[porosidade]}
              onValueChange={([v]) => setPorosidade(v)}
            />
          </div>
          <div className="mt-4 grid gap-3 sm:grid-cols-3">
            <Numero titulo="E maciço" valor={`${num(eMacico, 1)} GPa`} />
            <Numero titulo="E com esta porosidade" valor={`${num(e, 1)} GPa`} destaque />
            <Numero titulo="Porosidade para o alvo" valor={pAlvo !== null ? `${num(pAlvo * 100, 0)} %` : "n.d."} />
          </div>
          <p className="mt-3 text-sm">
            {dentroOsso ? (
              <Etiqueta tom="sucesso">Dentro da faixa do osso cortical</Etiqueta>
            ) : (
              <Etiqueta tom="aviso">{faixa && e > faixa.max ? "Mais rígido do que o osso cortical" : "Menos rígido do que o osso cortical"}</Etiqueta>
            )}
          </p>
        </Cartao>

        <div className="space-y-4">
          <Cartao>
            <TituloCartao>Material maciço</TituloCartao>
            <ul className="mt-3 space-y-1.5">
              {p.alternativas.map((a, i) => (
                <li key={a}>
                  <button
                    type="button"
                    onClick={() => setMaterial(a)}
                    aria-pressed={a === material}
                    className={`flex w-full items-center justify-between gap-2 rounded-md border px-3 py-2 text-left text-sm ${
                      a === material ? "border-acento bg-acento/10" : "border-linha hover:bg-superficie2"
                    }`}
                  >
                    <NomeMaterial material={a} />
                    <span className="numero text-xs text-texto2">{num(p.x_tipico[i][j], 1)} GPa</span>
                  </button>
                </li>
              ))}
            </ul>
          </Cartao>
          <Cartao>
            <TituloCartao>Estrutura porosa</TituloCartao>
            <Visualizador3D modelo="scaffold" porosidade={porosidade} className="mt-3 h-64" rotulo={`Rede porosa de ${nomeSimples(material)}`} />
          </Cartao>
          {cortical && <Fonte referencia={cortical.fonte} className="block" />}
          <p className="text-xs leading-relaxed text-texto2">
            Aproximação de primeira ordem (constante igual a 1, expoente 2, espuma de células abertas); a forma real dos
            poros, a anisotropia e o fabrico mudam o valor. A haste porosa da FEA usa um valor de desenho.
          </p>
        </div>
      </div>
    </div>
  );
}

function Numero({ titulo, valor, destaque = false }: { titulo: string; valor: string; destaque?: boolean }) {
  return (
    <div className="rounded-md bg-superficie2 p-3">
      <div className="text-xs text-texto2">{titulo}</div>
      <div className={`numero mt-1 font-bold ${destaque ? "text-xl text-acento-texto" : "text-lg"}`}>{valor}</div>
    </div>
  );
}
