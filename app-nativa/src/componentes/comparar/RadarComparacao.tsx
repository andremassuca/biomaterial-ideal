// Radar opcional da comparação: uma pontuação de 0 a 1 por critério (1 = melhor entre os materiais do cenário).
import { Legend, PolarAngleAxis, PolarGrid, PolarRadiusAxis, Radar, RadarChart, ResponsiveContainer } from "recharts";
import { nomeSimples } from "@/lib/dados";
import { pontuacaoRadar } from "@/lib/comparar";
import type { Problema } from "@/lib/tipos";

/** Etiqueta curta de um critério: tira o que vem entre parênteses ("Fabricabilidade (ordinal 1-5)" -> "Fabricabilidade"). */
export function rotuloCurto(criterio: string): string {
  return criterio.replace(/\s*\(.*$/, "").trim() || criterio;
}

/** Dados do radar: uma linha por critério com a pontuação de cada um dos dois materiais (null se faltar o valor). */
export function dadosRadar(p: Problema, a: string, b: string): Record<string, string | number | null>[] {
  const ia = p.alternativas.indexOf(a);
  const ib = p.alternativas.indexOf(b);
  return p.criterios.map((c, j) => {
    const coluna = p.x_tipico.map((linha) => linha[j]);
    return {
      criterio: rotuloCurto(c),
      a: ia < 0 ? null : pontuacaoRadar(p.tipos[j], p.x_tipico[ia][j], coluna, p.alvos[j] ?? null),
      b: ib < 0 ? null : pontuacaoRadar(p.tipos[j], p.x_tipico[ib][j], coluna, p.alvos[j] ?? null),
    };
  });
}

export function RadarComparacao({ problema, a, b }: { problema: Problema; a: string; b: string }) {
  const dados = dadosRadar(problema, a, b);
  const nomeA = nomeSimples(a);
  const nomeB = a === b ? `${nomeSimples(b)} (2)` : nomeSimples(b);
  // os critérios sem valor num dos materiais ficam a 0 no desenho (a tabela diz "Sem valor na base")
  const desenho = dados.map((d) => ({ criterio: d.criterio, [nomeA]: d.a ?? 0, [nomeB]: d.b ?? 0 }));
  return (
    <div className="h-80 w-full" role="img" aria-label={`Radar de ${nomeA} e ${nomeB}: pontuação de 0 a 1 por critério, 1 é o melhor`}>
      <ResponsiveContainer>
        <RadarChart data={desenho} outerRadius="70%">
          <PolarGrid stroke="rgb(var(--linha))" />
          <PolarAngleAxis dataKey="criterio" tick={{ fontSize: 11, fill: "rgb(var(--texto-2))" }} />
          <PolarRadiusAxis domain={[0, 1]} tick={false} axisLine={false} />
          <Radar name={nomeA} dataKey={nomeA} stroke="var(--cor-borda)" fill="var(--cor-borda)" fillOpacity={0.25} />
          <Radar name={nomeB} dataKey={nomeB} stroke="rgb(var(--aviso))" fill="rgb(var(--aviso))" fillOpacity={0.2} />
          <Legend />
        </RadarChart>
      </ResponsiveContainer>
    </div>
  );
}
