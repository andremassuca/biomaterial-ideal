// Gráfico do Monte Carlo: % de repetições em 1.º lugar por material e método (Recharts).
import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { codigo, nomeSimples } from "@/lib/dados";
import { COR_METODO } from "@/lib/cores";
import { pct } from "@/lib/formato";
import type { ResumoMonteCarlo } from "@/lib/tipos";

/**
 * Rótulo de cada material no eixo: o nome simples, ou o nome simples com o código quando dois materiais da mesma
 * lista têm o mesmo nome simples (por exemplo, três "Polímero" no scaffold, cenário B). O eixo agrupa por rótulo,
 * por isso rótulos repetidos juntavam materiais diferentes numa só linha.
 */
export function rotulosEixo(materiais: string[]): string[] {
  const nomes = materiais.map(nomeSimples);
  return materiais.map((m, i) => {
    if (nomes.filter((n) => n === nomes[i]).length === 1) return nomes[i];
    const c = codigo(m);
    return c && c !== nomes[i] ? `${nomes[i]} (${c})` : m;
  });
}

/** Largura do eixo dos nomes: mais estreita em ecrãs pequenos (telemóvel), para sobrar espaço às barras. */
export function larguraEixo(janela: number = typeof window === "undefined" ? 1280 : window.innerWidth): number {
  return janela < 520 ? 110 : 170;
}

export function GraficoMC({ resumo }: { resumo: ResumoMonteCarlo }) {
  const rotulos = rotulosEixo(resumo.alternativas);
  const larg = larguraEixo();
  const dados = resumo.alternativas.map((_, i) => {
    const linha: Record<string, string | number> = { material: rotulos[i] };
    for (const m of resumo.metodos) linha[m.metodo] = m.pct_primeiro[i];
    return linha;
  });
  return (
    <div className="h-72 w-full" role="img" aria-label="Percentagem de repetições em primeiro lugar por material e método">
      <ResponsiveContainer>
        <BarChart data={dados} layout="vertical" margin={{ left: 8, right: 24, top: 8, bottom: 8 }}>
          <CartesianGrid horizontal={false} strokeDasharray="3 3" />
          <XAxis type="number" domain={[0, 100]} tickFormatter={(v: number) => `${v} %`} stroke="rgb(var(--linha))" tickLine={false} />
          <YAxis type="category" dataKey="material" width={larg} stroke="rgb(var(--linha))" tick={{ fontSize: 12 }} tickLine={false} axisLine={false} />
          <Tooltip
            formatter={(v: number) => pct(v)}
            contentStyle={{ color: "rgb(var(--texto))" }}
            cursor={{ fill: "rgb(var(--superficie-2))" }}
          />
          <Legend iconType="circle" iconSize={9} wrapperStyle={{ fontSize: 12, color: "rgb(var(--texto-2))", paddingTop: 4 }} />
          {resumo.metodos.map((m) => (
            <Bar key={m.metodo} dataKey={m.metodo} fill={COR_METODO[m.metodo]} radius={[0, 3, 3, 0]} isAnimationActive barSize={10} />
          ))}
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
