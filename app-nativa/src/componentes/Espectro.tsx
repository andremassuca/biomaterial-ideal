// Espectro de confiança: ΔC do TOPSIS (1.º menos 2.º, cenário A) de cada caso, do mais claro ao mais renhido.
// Números de app.json (results/pontuacoes.csv, monte_carlo.csv e semiquantitativos.csv).
import { motion } from "framer-motion";
import { APP, TITULO_CASO, type IdCaso, nomeSimples } from "@/lib/dados";
import { num, pct } from "@/lib/formato";

export function Espectro() {
  const casos = APP.espectro;
  const max = Math.max(...casos.map((c) => c.delta_c));
  const L = 1000;
  const margem = 110;
  const x = (dc: number) => margem + ((max - dc) / max) * (L - 2 * margem);
  const limiar = APP.limiar_empate;

  return (
    <figure className="w-full">
      <svg viewBox={`0 0 ${L} 150`} className="w-full" role="img" aria-label="Espectro de confiança dos cinco casos">
        <defs>
          <linearGradient id="grad-espectro" x1="0" x2="1">
            <stop offset="0" stopColor="rgb(var(--acento))" stopOpacity="0.9" />
            <stop offset="1" stopColor="rgb(var(--aviso))" stopOpacity="0.9" />
          </linearGradient>
        </defs>
        <rect x={margem} y={70} width={L - 2 * margem} height={8} rx={4} fill="url(#grad-espectro)" opacity={0.35} />
        {/* zona de empate (ΔC abaixo do limiar do relatório) */}
        <rect x={x(limiar)} y={62} width={L - margem - x(limiar)} height={24} rx={4} fill="rgb(var(--aviso))" opacity={0.18} />
        <text x={L - margem} y={104} textAnchor="end" fontSize={13} fill="rgb(var(--texto-2))">
          empate (ΔC abaixo de {num(limiar, 2)})
        </text>
        <text x={margem} y={104} fontSize={13} fill="rgb(var(--texto-2))">
          vencedor claro
        </text>
        {casos.map((c, i) => {
          const cx = x(c.delta_c);
          const cima = i % 2 === 0;
          return (
            <motion.g
              key={c.caso}
              initial={{ opacity: 0, y: cima ? -8 : 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.08 * i, duration: 0.3 }}
            >
              <line x1={cx} x2={cx} y1={cima ? 40 : 82} y2={cima ? 70 : 118} stroke="rgb(var(--linha))" />
              <circle cx={cx} cy={74} r={9} fill="rgb(var(--acento))" stroke="rgb(var(--superficie))" strokeWidth={3} />
              <text x={cx} y={cima ? 20 : 134} textAnchor="middle" fontSize={15} fontWeight={700} fill="rgb(var(--texto))">
                {TITULO_CASO[c.caso as IdCaso] ?? c.caso}
              </text>
              <text x={cx} y={cima ? 37 : 149} textAnchor="middle" fontSize={13} fill="rgb(var(--texto-2))">
                {nomeSimples(c.vencedor)} · ΔC {num(c.delta_c, 3)}
              </text>
            </motion.g>
          );
        })}
      </svg>
      <figcaption className="mt-3 grid gap-2 text-xs text-texto2 sm:grid-cols-2 lg:grid-cols-3">
        {casos.map((c) => (
          <span key={c.caso}>
            <strong className="text-texto">{TITULO_CASO[c.caso as IdCaso] ?? c.caso}:</strong>{" "}
            {c.semiquantitativo
              ? `${nomeSimples(c.vencedor)} fica em 1.º em ${c.versoes_mantem} de ${c.versoes_total} versões da análise (semiquantitativo).`
              : `${nomeSimples(c.vencedor)} fica em 1.º em ${pct(c.pct_primeiro_min)} a ${pct(c.pct_primeiro_max)} das ${num(
                  c.n_iter ?? 0,
                  0,
                )} repetições do Monte Carlo das propriedades.`}
          </span>
        ))}
      </figcaption>
    </figure>
  );
}
