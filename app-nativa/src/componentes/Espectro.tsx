// Espectro de confiança: ΔC do TOPSIS (1.º menos 2.º, cenário A) de cada caso, do mais claro ao mais renhido.
// Números de app.json (results/pontuacoes.csv, monte_carlo.csv e semiquantitativos.csv).
import { motion } from "framer-motion";
import { APP, RECOMENDACAO_CURTA, TITULO_CASO, type IdCaso, nomeSimples, semPrefixo } from "@/lib/dados";
import { num, pct } from "@/lib/formato";
import type { EntradaEspectro } from "@/lib/tipos";

/**
 * Material que o TOPSIS põe mais vezes em 1.º no Monte Carlo das propriedades (results/monte_carlo.csv), quando não é
 * o vencedor do caso. Em linguagem simples: se o material que ganha na leitura principal não for o que o TOPSIS põe
 * mais vezes em 1.º com os dados a variar, a frase do espectro tem de o dizer. Devolve null quando o mais frequente é o
 * vencedor.
 */
export function outroMaisFrequenteTopsis(caso: string, vencedor: string): { material: string; pct: number } | null {
  const linhas = APP.monte_carlo_referencia.filter((l) => l.caso === caso && l.analise === "MC propriedades" && l.metodo === "TOPSIS");
  if (!linhas.length) return null;
  const topo = linhas.reduce((a, b) => (b.pct_primeiro > a.pct_primeiro ? b : a));
  return topo.material === vencedor ? null : { material: topo.material, pct: topo.pct_primeiro };
}

/**
 * Posição x (no SVG) do rótulo de cada ponto. Em linguagem simples: os pontos ficam onde os dados mandam, mas os
 * rótulos do mesmo lado (em cima ou em baixo) afastam-se pelo menos `distancia` uns dos outros e não saem das margens,
 * para não se taparem quando dois casos têm um ΔC parecido (scaffold 0,019 e stent 0,022).
 */
export function posicoesRotulos(xs: number[], lado: boolean[], distancia: number, min: number, max: number): number[] {
  const saida = [...xs];
  for (const cima of [true, false]) {
    const idx = xs.map((_, i) => i).filter((i) => lado[i] === cima).sort((a, b) => xs[a] - xs[b]);
    for (let k = 1; k < idx.length; k++) {
      saida[idx[k]] = Math.max(saida[idx[k]], saida[idx[k - 1]] + distancia);
    }
    for (let k = idx.length - 1; k >= 0; k--) {
      const limite = k === idx.length - 1 ? max : saida[idx[k + 1]] - distancia;
      saida[idx[k]] = Math.max(min, Math.min(saida[idx[k]], limite));
    }
  }
  return saida;
}

/** Frase de cada caso, por baixo do espectro. */
export function fraseEspectro(c: EntradaEspectro): string {
  if (c.semiquantitativo) {
    return `${nomeSimples(c.vencedor)} fica em 1.º em ${c.versoes_mantem} de ${c.versoes_total} versões da análise (semiquantitativo).`;
  }
  const base = `${nomeSimples(c.vencedor)} fica em 1.º em ${pct(c.pct_primeiro_min)} a ${pct(c.pct_primeiro_max)} das ${num(
    c.n_iter ?? 0,
    0,
  )} repetições do Monte Carlo das propriedades`;
  const outro = outroMaisFrequenteTopsis(c.caso, c.vencedor);
  return outro ? `${base}; com o TOPSIS, ${nomeSimples(outro.material)} fica em 1.º mais vezes (${pct(outro.pct)}).` : `${base}.`;
}

export function Espectro() {
  const casos = APP.espectro;
  const max = Math.max(...casos.map((c) => c.delta_c));
  const L = 1000;
  const H = 186;
  const margem = 110;
  const x = (dc: number) => margem + ((max - dc) / max) * (L - 2 * margem);
  const limiar = APP.limiar_empate;
  const xs = casos.map((c) => x(c.delta_c));
  const lado = casos.map((_, i) => i % 2 === 0);
  // rótulos com cerca de 200 unidades de largura (título a 15): afastados entre si e dentro do SVG
  const xr = posicoesRotulos(xs, lado, 210, 100, L - 100);

  return (
    <figure className="w-full">
      {/* no telemóvel, o SVG ficava com letra de 5 a 6 px: abaixo de md, uma lista com barras */}
      <ol className="space-y-3 md:hidden" aria-label="Espectro de confiança dos cinco casos">
        {casos.map((c) => {
          const empate = c.delta_c < limiar;
          const curta = RECOMENDACAO_CURTA[c.caso as IdCaso];
          return (
            <li key={c.caso} className="text-sm">
              <div className="flex items-baseline justify-between gap-2">
                <span className="font-bold">{TITULO_CASO[c.caso as IdCaso] ?? c.caso}</span>
                <span className="numero shrink-0 text-texto2">ΔC {num(c.delta_c, 3)}</span>
              </div>
              <div className="text-texto2" data-recomendacao-curta={curta ? "" : undefined}>
                {curta ?? `${nomeSimples(c.vencedor)}${empate ? " (empate)" : ""}`}
              </div>
              <div className="mt-1 h-2 w-full overflow-hidden rounded-full bg-superficie2" aria-hidden>
                <div
                  className={empate ? "h-full rounded-full bg-aviso" : "h-full rounded-full bg-acento"}
                  style={{ width: `${Math.max(3, (100 * c.delta_c) / max)}%` }}
                />
              </div>
            </li>
          );
        })}
      </ol>
      <p className="mt-2 text-xs text-texto2 md:hidden">
        Barra maior: vencedor mais claro. ΔC abaixo de {num(limiar, 2)} conta como empate.
      </p>
      <svg viewBox={`0 0 ${L} ${H}`} className="hidden w-full md:block" role="img" aria-label="Espectro de confiança dos cinco casos">
        <defs>
          <linearGradient id="grad-espectro" x1="0" x2="1">
            <stop offset="0" stopColor="rgb(var(--acento))" stopOpacity="0.9" />
            <stop offset="1" stopColor="rgb(var(--aviso))" stopOpacity="0.9" />
          </linearGradient>
        </defs>
        <rect x={margem} y={70} width={L - 2 * margem} height={8} rx={4} fill="url(#grad-espectro)" opacity={0.35} />
        {/* zona de empate (ΔC abaixo do limiar do relatório) */}
        <rect x={x(limiar)} y={62} width={L - margem - x(limiar)} height={24} rx={4} fill="rgb(var(--aviso))" opacity={0.18} />
        {/* legendas das pontas numa linha própria, por baixo de todos os rótulos, para nenhum ponto as tapar */}
        <text x={L - margem} y={180} textAnchor="end" fontSize={13} fill="rgb(var(--texto-2))" data-rotulo-empate>
          empate (ΔC abaixo de {num(limiar, 2)})
        </text>
        <text x={margem} y={180} fontSize={13} fill="rgb(var(--texto-2))">
          vencedor claro
        </text>
        {casos.map((c, i) => {
          const cx = xs[i];
          const lx = xr[i];
          const cima = lado[i];
          const curta = RECOMENDACAO_CURTA[c.caso as IdCaso];
          return (
            <motion.g
              key={c.caso}
              initial={{ opacity: 0, y: cima ? -8 : 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.08 * i, duration: 0.3 }}
            >
              <polyline
                points={cima ? `${cx},66 ${cx},54 ${lx},44 ${lx},40` : `${cx},82 ${cx},94 ${lx},112 ${lx},118`}
                fill="none"
                stroke="rgb(var(--linha))"
              />
              <circle cx={cx} cy={74} r={6.5} fill="rgb(var(--acento))" stroke="rgb(var(--superficie))" strokeWidth={2} />
              <text x={lx} y={cima ? 20 : 134} textAnchor="middle" fontSize={15} fontWeight={700} fill="rgb(var(--texto))">
                {TITULO_CASO[c.caso as IdCaso] ?? c.caso}
              </text>
              <text x={lx} y={cima ? 37 : 151} textAnchor="middle" fontSize={13} fill="rgb(var(--texto-2))">
                {curta ? `ΔC ${num(c.delta_c, 3)}` : `${nomeSimples(c.vencedor)} · ΔC ${num(c.delta_c, 3)}`}
              </text>
            </motion.g>
          );
        })}
      </svg>
      <figcaption className="mt-3 grid gap-2 text-xs text-texto2 sm:grid-cols-2 lg:grid-cols-3">
        {casos.map((c) => {
          const curta = RECOMENDACAO_CURTA[c.caso as IdCaso];
          return (
            <span key={c.caso}>
              <strong className="text-texto">{TITULO_CASO[c.caso as IdCaso] ?? c.caso}:</strong>{" "}
              {curta && <span data-recomendacao-curta>{semPrefixo(curta)}. </span>}
              {fraseEspectro(c)}
            </span>
          );
        })}
      </figcaption>
    </figure>
  );
}
