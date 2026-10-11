// Filtros de requisito: RM (ASTM F2503), ISO 10993-1 e esterilização imposta (cenário de sensibilidade).
// Os filtros tiram materiais antes do ranking; não entram como critérios com peso (decisão de 8 out).
import { useEffect, useMemo, useState } from "react";
import { ChevronDown } from "lucide-react";
import { Aviso, CabecalhoEcra, Fonte, Informacao, NomeMaterial } from "@/componentes/comuns";
import { RankingAnimado } from "@/componentes/RankingAnimado";
import { Cartao, DescricaoCartao, Etiqueta, TituloCartao } from "@/componentes/ui/cartao";
import { Interruptor, Opcoes } from "@/componentes/ui/controlos";
import { APP, CASOS, TITULO_CASO, cenarios, descricaoCenario, nomeSimples, type IdCaso } from "@/lib/dados";
import { avaliarCaso, mensagemErro } from "@/lib/nucleo";
import { textoPublico } from "@/lib/publico";
import type { FiltroMaterial, RespostaCaso } from "@/lib/tipos";
import { cn } from "@/lib/utils";

type Metodo = "nenhum" | "vapor" | "oxido_etileno" | "radiacao_gama";
const LISTA_CASOS: IdCaso[] = ["Haste", "Stent", "Scaffold", "Par articular", "Implante dentário"];

function filtroDe(material: string): FiltroMaterial | undefined {
  return APP.filtros.materiais.find((f) => f.material === material);
}

/** Materiais que saem com os filtros escolhidos, e porquê. */
export function exclusoes(materiais: string[], rm: boolean, iso: boolean, metodo: Metodo): Map<string, string[]> {
  const out = new Map<string, string[]>();
  for (const m of materiais) {
    const f = filtroDe(m);
    if (!f) continue;
    const motivos: string[] = [];
    if (rm && f.rm === "exclui") motivos.push("ferromagnético (RM)");
    if (iso && f.iso10993 === "por demonstrar no dispositivo final") motivos.push("ISO 10993-1 por demonstrar");
    if (metodo !== "nenhum" && (f[metodo] ?? "").trim().toLowerCase() === "incompatível") {
      motivos.push(`incompatível com ${APP.filtros.metodos[metodo]}`);
    }
    if (motivos.length) out.set(m, motivos);
  }
  return out;
}

function tomCompat(v: string): "sucesso" | "aviso" | "perigo" | "neutro" {
  const t = v.trim().toLowerCase();
  if (t === "compatível" || t === "passa" || t === "não") return "sucesso";
  if (t === "incompatível" || t === "exclui" || t === "sim") return "perigo";
  if (t.startsWith("a verificar") || t.startsWith("com restrições")) return "aviso";
  return "neutro";
}

export function Filtros() {
  const [id, setId] = useState<IdCaso>("Stent");
  const caso = CASOS[id];
  const [cenario, setCenario] = useState("B");
  const problema = caso.cenarios[cenario] ?? caso.cenarios[cenarios(caso)[0]];
  const cen = caso.cenarios[cenario] ? cenario : cenarios(caso)[0];
  const [rm, setRm] = useState(true);
  const [iso, setIso] = useState(false);
  const [metodo, setMetodo] = useState<Metodo>("nenhum");
  const saem = useMemo(() => exclusoes(problema.alternativas, rm, iso, metodo), [problema, rm, iso, metodo]);
  const ficam = problema.alternativas.length - saem.size;

  const [base, setBase] = useState<RespostaCaso | null>(null);
  const [filtrado, setFiltrado] = useState<RespostaCaso | null>(null);
  const [erro, setErro] = useState<string | null>(null);

  useEffect(() => {
    let ativo = true;
    setErro(null);
    const excluir = [...saem.keys()];
    Promise.all([
      avaliarCaso({ caso: id, cenario: cen }),
      ficam >= 2 ? avaliarCaso({ caso: id, cenario: cen, excluir }) : Promise.resolve(null),
    ])
      .then(([b, f]) => {
        if (!ativo) return;
        setBase(b);
        setFiltrado(f);
      })
      .catch((e) => ativo && setErro(mensagemErro(e)));
    return () => {
      ativo = false;
    };
  }, [id, cen, saem, ficam]);

  const vencedor = (r: RespostaCaso | null, chave: "pos_topsis" | "pos_waspas" | "pos_vikor") => {
    if (!r || !r.ranking[chave].length) return null;
    return r.ranking.alternativas[r.ranking[chave].indexOf(1)];
  };

  return (
    <div className="space-y-6">
      <CabecalhoEcra
        titulo="Filtros de requisito"
        subtitulo="Requisitos que um material tem de cumprir antes de entrar na comparação. Nos rankings do relatório não entram como critérios com peso; aqui pode ver o efeito de cada um."
      />
      <div className="grid gap-6 [&>*]:min-w-0 xl:grid-cols-[360px_1fr]">
        <div className="space-y-4">
          <Cartao>
            <TituloCartao>Caso</TituloCartao>
            <div className="mt-3 flex flex-wrap gap-2">
              <Opcoes rotulo="Caso" valor={id} aoMudar={setId} opcoes={LISTA_CASOS.map((c) => ({ valor: c, texto: TITULO_CASO[c] }))} />
              <Opcoes rotulo="Cenário" valor={cen} aoMudar={setCenario} opcoes={cenarios(caso).map((c) => ({ valor: c, texto: `Cenário ${c}` }))} />
            </div>
            <p className="mt-2 text-xs text-texto2">{descricaoCenario(cen)}</p>
          </Cartao>
          <Cartao className="space-y-4">
            <Linha
              titulo="Ressonância magnética (ASTM F2503)"
              texto="Um material ferromagnético é “MR Unsafe” e sai. Sem fonte direta, fica assinalado “A verificar”, sem sair."
              ativo={rm}
              mudar={setRm}
            />
            <Linha
              titulo="ISO 10993-1 (exploração)"
              texto="A avaliação biológica é do dispositivo final, por isso no relatório este filtro não exclui ninguém, só assinala. Ligue para ver o efeito de tirar os materiais com a avaliação ainda por demonstrar."
              ativo={iso}
              mudar={setIso}
            />
            <div>
              <div className="text-sm font-bold">Esterilização imposta (sensibilidade)</div>
              <p className="mb-2 mt-1 text-xs text-texto2">
                Saem os materiais incompatíveis com o método; “com restrições” e “A verificar” ficam.
              </p>
              <Opcoes
                rotulo="Método de esterilização"
                valor={metodo}
                aoMudar={setMetodo}
                opcoes={[{ valor: "nenhum" as Metodo, texto: "Nenhum" }, ...Object.entries(APP.filtros.metodos).map(([k, v]) => ({ valor: k as Metodo, texto: v }))]}
              />
            </div>
          </Cartao>
        </div>

        <div className="space-y-6">
          <Cartao>
            <TituloCartao>Ranking com os filtros</TituloCartao>
            <DescricaoCartao>
              {saem.size === 0
                ? "Nenhum material sai com estes filtros."
                : `Saem ${saem.size} de ${problema.alternativas.length}: ${[...saem.keys()].map(nomeSimples).join(", ")}.`}
            </DescricaoCartao>
            {erro && <p className="mt-2 text-sm text-perigo">{erro}</p>}
            <div className="mt-4">
              {ficam < 2 ? (
                <Informacao>Menos de dois candidatos compatíveis: não há ranking.</Informacao>
              ) : filtrado ? (
                <RankingAnimado caso={id} ranking={filtrado.ranking} apenasTopsis={filtrado.apenasTopsis} />
              ) : (
                <div className="h-40 animate-pulse rounded-md bg-superficie2" />
              )}
            </div>
            {base && filtrado && saem.size > 0 && (
              <div className="mt-4 grid gap-2 sm:grid-cols-3">
                {(["pos_topsis", "pos_waspas", "pos_vikor"] as const).map((k) => {
                  const antes = vencedor(base, k);
                  const depois = vencedor(filtrado, k);
                  if (!antes || !depois) return null;
                  return (
                    <div key={k} className="rounded-md bg-superficie2 p-3 text-sm">
                      <div className="text-xs font-bold text-texto2">{k.replace("pos_", "").toUpperCase()}</div>
                      <div>
                        {nomeSimples(antes)} → <strong>{nomeSimples(depois)}</strong>
                      </div>
                      {antes !== depois && <Etiqueta tom="aviso">o vencedor muda</Etiqueta>}
                    </div>
                  );
                })}
              </div>
            )}
          </Cartao>

          <Cartao>
            <TituloCartao>Situação de cada material</TituloCartao>
            <ul className="mt-3 divide-y divide-linha">
              {problema.alternativas.map((m) => (
                <LinhaMaterial key={m} material={m} motivos={saem.get(m)} />
              ))}
            </ul>
          </Cartao>

          <Cartao>
            <TituloCartao>Cenário da esterilização em todos os casos</TituloCartao>
            <DescricaoCartao>Combinações em que algum material sai (results/filtros.md). Vencedores por TOPSIS / WASPAS / VIKOR.</DescricaoCartao>
            <div className="mt-3 overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead className="text-xs text-texto2">
                  <tr>
                    <th className="py-1 font-medium">Caso</th>
                    <th className="py-1 font-medium">Cenário</th>
                    <th className="py-1 font-medium">Método</th>
                    <th className="py-1 font-medium">Saem</th>
                    <th className="py-1 font-medium">Antes</th>
                    <th className="py-1 font-medium">Depois</th>
                  </tr>
                </thead>
                <tbody>
                  {APP.filtros.esterilizacao
                    .filter((l) => l.saem)
                    .map((l, k) => (
                      <tr key={k} className="border-t border-linha align-top">
                        <td className="py-1.5 pr-2">{l.caso}</td>
                        <td className="py-1.5 pr-2">{l.cenario}</td>
                        <td className="py-1.5 pr-2">{l.metodo}</td>
                        <td className="py-1.5 pr-2">{String(l.saem).split("; ").map(nomeSimples).join(", ")}</td>
                        <td className="py-1.5 pr-2">{(["TOPSIS", "WASPAS", "VIKOR"] as const).map((m) => nomeSimples(String(l[`antes_${m}`]))).join(" / ")}</td>
                        <td className="py-1.5">
                          {(["TOPSIS", "WASPAS", "VIKOR"] as const).map((m) => nomeSimples(String(l[`depois_${m}`]))).join(" / ")}
                        </td>
                      </tr>
                    ))}
                </tbody>
              </table>
            </div>
          </Cartao>
          <Aviso />
        </div>
      </div>
    </div>
  );
}

function Linha({ titulo, texto, ativo, mudar }: { titulo: string; texto: string; ativo: boolean; mudar: (v: boolean) => void }) {
  return (
    <label className="flex items-start justify-between gap-3">
      <span>
        <span className="block text-sm font-bold">{titulo}</span>
        <span className="mt-1 block text-xs text-texto2">{texto}</span>
      </span>
      <Interruptor checked={ativo} onCheckedChange={mudar} aria-label={titulo} />
    </label>
  );
}

function LinhaMaterial({ material, motivos }: { material: string; motivos?: string[] }) {
  const [aberta, setAberta] = useState(false);
  const f = filtroDe(material);
  return (
    <li className={cn("py-2", motivos && "opacity-80")}>
      <button type="button" onClick={() => setAberta((a) => !a)} aria-expanded={aberta} className="flex w-full flex-wrap items-center gap-2 text-left">
        <NomeMaterial material={material} className="min-w-[180px] flex-1" />
        {f ? (
          <>
            <Etiqueta tom={tomCompat(f.rm)}>RM: {f.rm}</Etiqueta>
            <Etiqueta tom={f.iso10993.startsWith("por demonstrar") ? "aviso" : "neutro"}>ISO: {f.iso10993}</Etiqueta>
            {(["vapor", "oxido_etileno", "radiacao_gama"] as const).map((k) => (
              <Etiqueta key={k} tom={tomCompat(f[k])}>
                {APP.filtros.metodos[k]}: {f[k]}
              </Etiqueta>
            ))}
          </>
        ) : (
          <Etiqueta>sem dados de filtros</Etiqueta>
        )}
        {motivos && <Etiqueta tom="perigo">sai: {motivos.join("; ")}</Etiqueta>}
        <ChevronDown aria-hidden className={cn("h-4 w-4 text-texto2 transition-transform", aberta && "rotate-180")} />
      </button>
      {aberta && f && (
        <div className="mt-2 space-y-2 rounded-md bg-superficie2 p-3">
          <Fonte referencia={`RM: ${f.fonte_rm || "sem fonte"}`} className="flex" />
          <Fonte referencia={`Esterilização: ${f.fonte_esterilizacao || "sem fonte"}`} className="flex" />
          {f.notas && <p className="text-xs leading-relaxed text-texto2">{textoPublico(f.notas)}</p>}
          <p className="text-xs text-texto2">Estado: {f.estado}</p>
        </div>
      )}
    </li>
  );
}
