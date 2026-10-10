// "Porquê": explicações em linguagem simples, com um exemplo calculado com os dados reais em cada tema.
import { useEffect, useMemo, useState, type ReactNode } from "react";
import { CabecalhoEcra, Informacao, NomeMaterial } from "@/componentes/comuns";
import { Markdown } from "@/componentes/Markdown";
import { Cartao, TituloCartao } from "@/componentes/ui/cartao";
import { ConteudoSeparador, ListaSeparadores, Opcoes, Separador, Separadores } from "@/componentes/ui/controlos";
import { APP, CASOS, CFD, QUANTITATIVOS, TITULO_CASO, nomeSimples, resolverMaterial, type IdCaso } from "@/lib/dados";
import { num, pct, valor } from "@/lib/formato";
import { avaliarCaso, mensagemErro, modoNucleo } from "@/lib/nucleo";
import { normalizarColuna, topsisPassos } from "@/lib/topsis";
import type { RespostaCaso } from "@/lib/tipos";

const TEMAS = [
  ["vencedor", "Porquê este vencedor"],
  ["criterios", "Os critérios e os critérios-alvo"],
  ["topsis", "TOPSIS"],
  ["waspas", "WASPAS"],
  ["vikor", "VIKOR"],
  ["borda", "Borda"],
  ["mc", "Monte Carlo"],
  ["fea", "FEA da haste"],
  ["cfd", "CFD do stent"],
  ["massa", "Massa e iões"],
] as const;

/** Ranking do caso de base (núcleo Rust); null no navegador. */
function useRankingBase(caso: IdCaso, cenario: string) {
  const [r, setR] = useState<RespostaCaso | null>(null);
  const [erro, setErro] = useState<string | null>(null);
  useEffect(() => {
    let ativo = true;
    avaliarCaso({ caso, cenario })
      .then((x) => ativo && setR(x))
      .catch((e) => ativo && setErro(mensagemErro(e)));
    return () => {
      ativo = false;
    };
  }, [caso, cenario]);
  return { r, erro };
}

export function Porque() {
  return (
    <div className="space-y-6">
      <CabecalhoEcra
        titulo="Porquê"
        subtitulo="Cada ferramenta explicada em linguagem simples, com um exemplo feito com os dados do trabalho."
      />
      <Separadores defaultValue="vencedor" orientation="vertical" className="grid gap-6 lg:grid-cols-[240px_1fr]">
        <ListaSeparadores className="h-fit flex-col items-stretch">
          {TEMAS.map(([v, t]) => (
            <Separador key={v} value={v} className="text-left">
              {t}
            </Separador>
          ))}
        </ListaSeparadores>
        <div>
          <ConteudoSeparador value="vencedor">
            <Vencedor />
          </ConteudoSeparador>
          <ConteudoSeparador value="criterios">
            <Criterios />
          </ConteudoSeparador>
          <ConteudoSeparador value="topsis">
            <Topsis />
          </ConteudoSeparador>
          <ConteudoSeparador value="waspas">
            <Waspas />
          </ConteudoSeparador>
          <ConteudoSeparador value="vikor">
            <Vikor />
          </ConteudoSeparador>
          <ConteudoSeparador value="borda">
            <Borda />
          </ConteudoSeparador>
          <ConteudoSeparador value="mc">
            <MonteCarlo />
          </ConteudoSeparador>
          <ConteudoSeparador value="fea">
            <FeaHaste />
          </ConteudoSeparador>
          <ConteudoSeparador value="cfd">
            <CfdStent />
          </ConteudoSeparador>
          <ConteudoSeparador value="massa">
            <MassaIoes />
          </ConteudoSeparador>
        </div>
      </Separadores>
    </div>
  );
}

function Tema({ titulo, simples, children }: { titulo: string; simples: ReactNode; children?: ReactNode }) {
  return (
    <Cartao className="space-y-4">
      <TituloCartao className="text-xl">{titulo}</TituloCartao>
      <div className="space-y-2 text-sm leading-relaxed">{simples}</div>
      {children && (
        <div className="rounded-md border border-linha p-4">
          <div className="mb-2 text-xs font-bold uppercase tracking-wide text-acento-texto">Exemplo com os dados</div>
          {children}
        </div>
      )}
    </Cartao>
  );
}

function Tabela({ cabecalho, linhas }: { cabecalho: ReactNode[]; linhas: ReactNode[][] }) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-left text-sm">
        <thead className="text-xs text-texto2">
          <tr>
            {cabecalho.map((c, k) => (
              <th key={k} className="py-1 pr-3 font-medium">
                {c}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {linhas.map((l, i) => (
            <tr key={i} className="border-t border-linha">
              {l.map((c, k) => (
                <td key={k} className="numero py-1.5 pr-3">
                  {c}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function SoNativo({ erro }: { erro: string | null }) {
  if (erro) return <p className="text-sm text-perigo">{erro}</p>;
  // com o núcleo (nativo ou WebAssembly) o exemplo está a ser calculado; só sem núcleo se pede a aplicação nativa
  return modoNucleo() !== "topsis" ? <div className="h-24 animate-pulse rounded-md bg-superficie2" /> : <Informacao>Este exemplo é calculado pelo núcleo Rust: abra a aplicação nativa.</Informacao>;
}

// ------------------------------------------------------------------ porquê este vencedor

function Vencedor() {
  const [id, setId] = useState<IdCaso>("Haste");
  const p = CASOS[id].cenarios.A;
  const passos = useMemo(() => topsisPassos(p.x_tipico, p.pesos, p.tipos, p.alvos), [p]);
  const ordem = passos.c.map((c, i) => [c, i] as const).sort((a, b) => b[0] - a[0]);
  const [v, s] = [ordem[0][1], ordem[1][1]];
  // Contribuição de cada critério: peso × diferença das pontuações normalizadas entre o 1.º e o 2.º.
  const contrib = p.criterios
    .map((c, j) => ({ c, d: p.pesos[j] * (passos.normalizada[v][j] - passos.normalizada[s][j]) }))
    .sort((a, b) => b.d - a.d);
  return (
    <Tema
      titulo="Porquê este vencedor"
      simples={
        <>
          <p>
            Um material ganha porque, somando todos os critérios com os seus pesos, fica mais perto do ideal do que os
            outros. Não precisa de ser o melhor em tudo: pode perder num critério e ganhar com folga noutros que pesam mais.
          </p>
          <p>
            Abaixo, para o cenário A, os critérios em que o 1.º do TOPSIS ganha ou perde face ao 2.º, medidos pelo peso
            vezes a diferença das pontuações normalizadas (de 0 a 1).
          </p>
        </>
      }
    >
      <Opcoes rotulo="Caso" valor={id} aoMudar={setId} opcoes={QUANTITATIVOS.map((c) => ({ valor: c, texto: TITULO_CASO[c] }))} className="mb-3" />
      <p className="mb-2 text-sm">
        <NomeMaterial material={p.alternativas[v]} linha /> (C = {num(passos.c[v], 3)}) contra <NomeMaterial material={p.alternativas[s]} linha /> (C ={" "}
        {num(passos.c[s], 3)}).
      </p>
      <ul className="space-y-1.5">
        {contrib.map(({ c, d }) => {
          const larg = Math.min(100, (Math.abs(d) / Math.max(...contrib.map((x) => Math.abs(x.d)), 1e-12)) * 100);
          return (
            <li key={c} className="grid grid-cols-[1fr_120px_64px] items-center gap-3 text-sm">
              <span>{c}</span>
              <span className="relative h-2 rounded-full bg-superficie2">
                <span className={`absolute h-2 rounded-full ${d >= 0 ? "bg-acento" : "bg-aviso"}`} style={{ width: `${larg}%` }} />
              </span>
              <span className={`numero text-right text-xs ${d >= 0 ? "text-acento-texto" : "text-aviso"}`}>
                {d >= 0 ? "+" : ""}
                {num(d, 3)}
              </span>
            </li>
          );
        })}
      </ul>
    </Tema>
  );
}

// ------------------------------------------------------------------ critérios

function Criterios() {
  const p = CASOS.Haste.cenarios.A;
  const j = p.tipos.indexOf("target");
  const col = p.x_tipico.map((l) => l[j]);
  const r = normalizarColuna(col, p.tipos[j], p.alvos[j]);
  return (
    <Tema
      titulo="Os critérios e os critérios-alvo"
      simples={
        <>
          <p>
            Cada critério é uma propriedade que interessa ao dispositivo. Num critério de <strong>benefício</strong>, mais é
            melhor (por exemplo, a resistência à fadiga). Num de <strong>custo</strong>, menos é melhor (por exemplo, a
            densidade). Num <strong>critério-alvo</strong>, o melhor é ficar perto de um valor ideal: uma haste demasiado
            rígida tira carga ao osso, que enfraquece (stress shielding).
          </p>
          <p>
            Para comparar unidades diferentes, cada coluna passa para uma escala de 0 a 1, em que 1 é o melhor possível
            (Petković et al. 2025, eq. 2). Os pesos dizem quanto cada critério conta e somam 100 %.
          </p>
        </>
      }
    >
      <p className="mb-2 text-sm">
        Haste, “{p.criterios[j]}”, alvo {valor(p.alvos[j])} GPa: quanto mais perto do alvo, mais perto de 1.
      </p>
      <Tabela
        cabecalho={["Material", "E (GPa)", "Pontuação normalizada"]}
        linhas={p.alternativas.map((a, i) => [<NomeMaterial key={a} material={a} />, valor(col[i]), num(r[i], 3)])}
      />
    </Tema>
  );
}

// ------------------------------------------------------------------ TOPSIS

function Topsis() {
  const p = CASOS.Haste.cenarios.A;
  const t = useMemo(() => topsisPassos(p.x_tipico, p.pesos, p.tipos, p.alvos), [p]);
  return (
    <Tema
      titulo="TOPSIS"
      simples={
        <>
          <p>
            Imagine um material ideal, com o melhor valor de cada critério, e um anti-ideal, com o pior. O TOPSIS mede a
            distância de cada material a cada um deles (D+ ao ideal, D− ao anti-ideal) e calcula C = D− / (D+ + D−).
          </p>
          <p>C vai de 0 a 1: perto de 1 quer dizer quase ideal. Ganha o maior C.</p>
        </>
      }
    >
      <p className="mb-2 text-sm">Haste, cenário A, pesos do relatório (calculado aqui, passo a passo):</p>
      <Tabela
        cabecalho={["Material", "D+ (ao ideal)", "D− (ao anti-ideal)", "C"]}
        linhas={p.alternativas
          .map((a, i) => ({ a, i }))
          .sort((x, y) => t.c[y.i] - t.c[x.i])
          .map(({ a, i }) => [<NomeMaterial key={a} material={a} />, num(t.dMais[i], 4), num(t.dMenos[i], 4), <strong key="c">{num(t.c[i], 3)}</strong>])}
      />
    </Tema>
  );
}

// ------------------------------------------------------------------ WASPAS

function Waspas() {
  const { r, erro } = useRankingBase("Haste", "A");
  return (
    <Tema
      titulo="WASPAS"
      simples={
        <>
          <p>
            O WASPAS junta duas maneiras de somar: a soma pesada (as pontuações normalizadas multiplicadas pelos pesos e
            somadas) e o produto pesado (as pontuações elevadas aos pesos e multiplicadas). O produto castiga mais quem tem
            um critério muito fraco.
          </p>
          <p>Q = metade da soma + metade do produto. Ganha o maior Q.</p>
        </>
      }
    >
      {r && !r.apenasTopsis ? (
        <Tabela
          cabecalho={["Material", "Q", "Posição"]}
          linhas={r.ranking.alternativas
            .map((a, i) => ({ a, i }))
            .sort((x, y) => r.ranking.pos_waspas[x.i] - r.ranking.pos_waspas[y.i])
            .map(({ a, i }) => [<NomeMaterial key={a} material={a} />, num(r.ranking.q_waspas[i], 3), `${r.ranking.pos_waspas[i]}.º`])}
        />
      ) : (
        <SoNativo erro={erro} />
      )}
    </Tema>
  );
}

// ------------------------------------------------------------------ VIKOR

function Vikor() {
  const { r, erro } = useRankingBase("Haste", "A");
  return (
    <Tema
      titulo="VIKOR"
      simples={
        <>
          <p>
            O VIKOR procura um compromisso. Para cada material calcula S, o “desvio total” somado em todos os critérios, e
            R, o desvio no pior critério. P mistura os dois a meias.
          </p>
          <p>Aqui menor é melhor: um P de 0 quer dizer o melhor compromisso entre os materiais comparados.</p>
        </>
      }
    >
      {r && !r.apenasTopsis ? (
        <Tabela
          cabecalho={["Material", "S", "R", "P", "Posição"]}
          linhas={r.ranking.alternativas
            .map((a, i) => ({ a, i }))
            .sort((x, y) => r.ranking.pos_vikor[x.i] - r.ranking.pos_vikor[y.i])
            .map(({ a, i }) => [
              <NomeMaterial key={a} material={a} />,
              num(r.ranking.s_vikor[i], 3),
              num(r.ranking.r_vikor[i], 3),
              num(r.ranking.p_vikor[i], 3),
              `${r.ranking.pos_vikor[i]}.º`,
            ])}
        />
      ) : (
        <SoNativo erro={erro} />
      )}
    </Tema>
  );
}

// ------------------------------------------------------------------ Borda

function Borda() {
  const { r, erro } = useRankingBase("Stent", "A");
  return (
    <Tema
      titulo="Consenso de Borda"
      simples={
        <>
          <p>
            Os três métodos nem sempre concordam. O consenso de Borda é uma votação: com m materiais, cada método dá m − 1
            pontos ao seu 1.º, m − 2 ao 2.º e assim por diante, até 0 ao último. Ganha quem somar mais pontos; num empate,
            decide o TOPSIS.
          </p>
        </>
      }
    >
      {r && !r.apenasTopsis ? (
        <>
          <p className="mb-2 text-sm">Stent, cenário A (m = {r.ranking.alternativas.length}):</p>
          <Tabela
            cabecalho={["Material", "TOPSIS", "WASPAS", "VIKOR", "Pontos", "Consenso"]}
            linhas={r.ranking.alternativas
              .map((a, i) => ({ a, i }))
              .sort((x, y) => r.ranking.pos_borda[x.i] - r.ranking.pos_borda[y.i])
              .map(({ a, i }) => {
                const m = r.ranking.alternativas.length;
                const pts = (pos: number) => `${pos}.º (${m - pos})`;
                return [
                  <NomeMaterial key={a} material={a} />,
                  pts(r.ranking.pos_topsis[i]),
                  pts(r.ranking.pos_waspas[i]),
                  pts(r.ranking.pos_vikor[i]),
                  <strong key="p">{r.ranking.pontos_borda[i]}</strong>,
                  `${r.ranking.pos_borda[i]}.º`,
                ];
              })}
          />
        </>
      ) : (
        <SoNativo erro={erro} />
      )}
    </Tema>
  );
}

// ------------------------------------------------------------------ Monte Carlo

function MonteCarlo() {
  const [id, setId] = useState<IdCaso>("Stent");
  const linhas = APP.monte_carlo_referencia.filter((l) => l.caso === id && l.analise === "MC propriedades");
  const materiais = [...new Set(linhas.map((l) => l.material))];
  const metodos = [...new Set(linhas.map((l) => l.metodo))];
  const n = linhas[0]?.n_iter;
  const inc = linhas[0]?.incerteza_valor_unico;
  return (
    <Tema
      titulo="Monte Carlo"
      simples={
        <>
          <p>
            Os valores da base não são exatos: cada propriedade tem um intervalo (mínimo a máximo). O Monte Carlo repete o
            ranking muitas vezes, sorteando em cada repetição um valor dentro de cada intervalo, e conta quantas vezes cada
            material fica em 1.º.
          </p>
          <p>
            Se um material ganha em quase todas as repetições, a escolha não depende da incerteza dos dados. Atenção: esta
            frequência não é uma probabilidade clínica; mede só a robustez da decisão aos dados. Os critérios ordinais (1 a
            5) não variam; um valor que vem de um só estudo varia{inc !== undefined ? ` ±${num(inc * 100, 0)} %` : ""} à volta do
            típico.
          </p>
        </>
      }
    >
      <Opcoes rotulo="Caso" valor={id} aoMudar={setId} opcoes={QUANTITATIVOS.map((c) => ({ valor: c, texto: TITULO_CASO[c] }))} className="mb-3" />
      <p className="mb-2 text-sm">
        % das {n !== undefined ? num(n, 0) : ""} repetições em 1.º lugar (cenário A, results/monte_carlo.csv):
      </p>
      <Tabela
        cabecalho={["Material", ...metodos]}
        linhas={materiais.map((m) => [
          <NomeMaterial key={m} material={m} />,
          ...metodos.map((me) => pct(linhas.find((l) => l.material === m && l.metodo === me)?.pct_primeiro)),
        ])}
      />
    </Tema>
  );
}

// ------------------------------------------------------------------ FEA

function FeaHaste() {
  const fea = APP.fea;
  if (!fea) {
    return <Tema titulo="FEA da haste" simples={<Informacao>Os resultados da FEA ainda não foram exportados.</Informacao>} />;
  }
  const materiais = [...new Set(fea.zonas.map((z) => z.material))].filter((m) => m !== "Fémur intacto");
  const zona = (m: string, z: number) => fea.zonas.find((x) => x.material === m && x.zona === z);
  const nome = (m: string) => {
    const base = fea.zonas.find((z) => z.material === m)?.material_base;
    return base && base !== m ? nomeSimples(base) : m;
  };
  return (
    <Tema
      titulo="FEA da haste: impacto no osso"
      simples={
        <>
          <p>
            A análise por elementos finitos (FEA) divide o fémur e a haste em milhares de pequenos blocos e calcula como
            cada um se deforma com a carga da marcha. Uma haste muito rígida carrega o peso sozinha e o osso à volta,
            junto ao colo, quase não trabalha: é o stress shielding, que leva à perda de osso.
          </p>
          <p>
            Mede-se a energia de deformação no osso nas zonas de Gruen 1 e 7 (perto do colo), com a haste, e divide-se pela
            do fémur intacto. Uma razão de 1 é como o osso natural; stress shielding = 1 − razão. Hipóteses: modelo linear e
            estático, osso isotrópico, interface colada. É uma extensão exploratória: interessa a ordem dos materiais.
          </p>
        </>
      }
    >
      <p className="mb-2 text-sm">Malha mais fina: {num(fea.malha_mm, 2)} mm (results/fea_haste.csv).</p>
      <Tabela
        cabecalho={["Material", "E (GPa)", "Razão Gruen 1", "Razão Gruen 7", "Stress shielding G1", "Stress shielding G7"]}
        linhas={materiais.map((m) => {
          const z1 = zona(m, 1);
          const z7 = zona(m, 7);
          return [
            <span key={m} className="inline-flex flex-col">
              <span className="font-medium">{nome(m)}</span>
              <span className="text-[0.7rem] text-texto2">{m}</span>
            </span>,
            valor(z1?.E_haste_GPa),
            num(z1?.razao, 2),
            num(z7?.razao, 2),
            pct((z1?.stress_shielding ?? NaN) * 100),
            pct((z7?.stress_shielding ?? NaN) * 100),
          ];
        })}
      />
      {fea.comparacao && (
        <>
          <p className="mb-2 mt-4 text-sm">Confirmação com outra ferramenta (fémur simplificado): a ordem dos materiais é a mesma.</p>
          <Tabela
            cabecalho={["Material", "G1 Python", "G1 SOLIDWORKS", "G7 Python", "G7 SOLIDWORKS"]}
            linhas={fea.comparacao.map((c) => [
              <span key={c.material}>{nomeSimples(c.material)}</span>,
              num(c.G1_python, 2),
              num(c.G1_solidworks, 2),
              num(c.G7_python, 2),
              num(c.G7_solidworks, 2),
            ])}
          />
        </>
      )}
    </Tema>
  );
}

// ------------------------------------------------------------------ CFD

function CfdStent() {
  return (
    <Tema
      titulo="CFD do stent: o sangue junto à parede"
      simples={
        <>
          <p>
            A dinâmica de fluidos computacional (CFD) simula o sangue a passar num segmento de artéria com o stent. Os
            struts (as barras do stent) salientes travam o sangue junto à parede. Onde o “atrito” do sangue na parede (a
            tensão de corte, WSS) é baixo, a parede tende a engrossar outra vez (reestenose).
          </p>
          <p>
            Compara-se um stent de struts finos com um de struts grossos, com o mesmo desenho, e mede-se a fração da parede
            com tensão de corte baixa ao longo do ciclo cardíaco.
          </p>
        </>
      }
    >
      {CFD ? (
        <Tabela
          cabecalho={["Material", "Strut (µm)", "TAWSS média (Pa)", "Área com TAWSS baixa", "OSI médio", "Área com OSI alto"]}
          linhas={Object.entries(CFD).map(([m, r]) => [
            <NomeMaterial key={m} material={resolverMaterial(m)} />,
            num(r.espessura_um, 0),
            num(r.tau_media, 3),
            pct(100 * r.fracao_baixa),
            num(r.osi_media, 3),
            pct(100 * r.fracao_osi),
          ])}
        />
      ) : (
        <div className="rounded-md border border-dashed border-aviso/60 bg-aviso/10 p-4 text-sm">
          <strong>Resultados da CFD ainda não disponíveis.</strong> A simulação está a correr. Os números aparecem aqui
          quando existir app-nativa/dados/cfd_stent.json, gerado por scripts/exportar_app_json.py a partir de
          results/cfd_pulsatil.json.
        </div>
      )}
    </Tema>
  );
}

// ------------------------------------------------------------------ massa e iões

function MassaIoes() {
  const m = APP.massa;
  return (
    <Tema
      titulo="Massa e iões"
      simples={
        <>
          <p>
            Uma haste de cobalto-crómio pesa mais do que uma de titânio, mas o corpo nota? Calcula-se a massa da mesma
            haste em cada material e quanto a troca deslocaria o centro de massa do corpo. Os iões metálicos libertados pelo
            desgaste e pela corrosão são outro efeito no doente, descrito abaixo com as fontes.
          </p>
        </>
      }
    >
      {m ? (
        <>
          <p className="mb-2 text-sm">
            Mesma haste ({num(m.volume_cm3, 1)} cm³) em cada material (results/massa_haste.csv):
          </p>
          <Tabela
            cabecalho={["Material", "Densidade (g/cm³)", "Massa (g)"]}
            linhas={m.materiais.map((x) => [<NomeMaterial key={x.material} material={x.material} />, num(x.densidade_g_cm3, 2), num(x.massa_g, 0)])}
          />
          <p className="mt-3 text-sm">
            Diferença entre a mais pesada e a mais leve: {num(m.diferenca_g, 0)} g. Com {num(m.massa_corpo_kg, 0)} kg de massa
            corporal e a haste a menos de {num(m.distancia_max_m, 1)} m do centro de massa do corpo (valores de desenho), o
            centro de massa desloca-se no máximo {num(m.desvio_max_mm, 2)} mm, contra {num(m.excursao_vertical_cm[0], 1)} a{" "}
            {num(m.excursao_vertical_cm[1], 1)} cm de subida e descida a cada passo na marcha normal. <strong>É desprezável</strong>:
            o que muda com o material é a rigidez (ver a FEA).
          </p>
        </>
      ) : (
        <Informacao>Os resultados da massa ainda não foram exportados.</Informacao>
      )}
      {APP.textos.ioes && (
        <div className="mt-4 border-t border-linha pt-4">
          <Markdown texto={APP.textos.ioes} />
        </div>
      )}
    </Tema>
  );
}
