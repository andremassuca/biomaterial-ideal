// Fichas dos materiais: cada propriedade com o valor, o intervalo, a fonte, o estado e a nota da base de dados.
import { useMemo, useState } from "react";
import { ChevronDown, Search } from "lucide-react";
import { CabecalhoEcra, EstadoValor, Fonte, NomeMaterial } from "@/componentes/comuns";
import { Cartao, DescricaoCartao, Etiqueta, TituloCartao } from "@/componentes/ui/cartao";
import { APP, codigo, fichaMaterial, nomeSimples } from "@/lib/dados";
import { intervalo, valor } from "@/lib/formato";
import { textoPublico } from "@/lib/publico";
import { cn } from "@/lib/utils";

export function Fichas() {
  // Materiais agrupados por dispositivo (caso e componente), pela ordem da base.
  const grupos = useMemo(() => {
    const g = new Map<string, string[]>();
    for (const l of APP.fichas.materiais) {
      const chave = l.componente && l.componente !== l.caso ? `${l.caso} | ${l.componente}` : l.caso;
      const lista = g.get(chave) ?? [];
      if (!lista.includes(l.material)) lista.push(l.material);
      g.set(chave, lista);
    }
    return [...g.entries()];
  }, []);
  const [busca, setBusca] = useState("");
  const [material, setMaterial] = useState(grupos[0]?.[1][0] ?? "");
  const termo = busca.trim().toLowerCase();
  const corresponde = (m: string) =>
    !termo || m.toLowerCase().includes(termo) || nomeSimples(m).toLowerCase().includes(termo) || codigo(m).toLowerCase().includes(termo);

  const linhas = fichaMaterial(material);
  const primeira = linhas[0];
  const contagem = linhas.reduce<Record<string, number>>((acc, l) => {
    const e = l.estado ?? "sem estado";
    acc[e] = (acc[e] ?? 0) + 1;
    return acc;
  }, {});

  return (
    <div className="space-y-6">
      <CabecalhoEcra
        titulo="Fichas dos materiais"
        subtitulo="Os valores da base de dados (data/materiais.csv), cada um com a fonte e o estado. Os valores sem fonte confirmada ficam “A verificar”."
      />
      <div className="grid gap-6 [&>*]:min-w-0 lg:grid-cols-[300px_1fr]">
        <Cartao className="h-fit p-3">
          <label className="flex items-center gap-2 rounded-md border border-linha bg-superficie2 px-2 py-1.5 focus-within:border-acento focus-within:ring-2 focus-within:ring-acento">
            <Search aria-hidden className="h-4 w-4 text-texto2" />
            <input
              value={busca}
              onChange={(e) => setBusca(e.target.value)}
              placeholder="Procurar material"
              aria-label="Procurar material"
              className="w-full bg-transparent text-sm outline-none placeholder:text-texto2"
            />
          </label>
          <nav className="mt-3 max-h-[60vh] space-y-4 overflow-y-auto pr-1">
            {grupos.map(([grupo, materiais]) => {
              const visiveis = materiais.filter(corresponde);
              if (!visiveis.length) return null;
              return (
                <div key={grupo}>
                  <h3 className="mb-1 text-xs font-bold uppercase tracking-wide text-texto2">{grupo}</h3>
                  <ul className="space-y-1">
                    {visiveis.map((m) => (
                      <li key={`${grupo}-${m}`}>
                        <button
                          type="button"
                          onClick={() => setMaterial(m)}
                          aria-pressed={m === material}
                          className={cn(
                            "w-full rounded-md px-2 py-1.5 text-left text-sm",
                            m === material ? "bg-acento/10 ring-1 ring-acento/50" : "hover:bg-superficie2",
                          )}
                        >
                          <NomeMaterial material={m} />
                        </button>
                      </li>
                    ))}
                  </ul>
                </div>
              );
            })}
          </nav>
        </Cartao>

        <Cartao>
          {primeira ? (
            <>
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <TituloCartao className="text-xl">{nomeSimples(material)}</TituloCartao>
                  <DescricaoCartao>
                    {material}
                    {primeira.norma && primeira.norma !== "-" ? ` · ${primeira.norma}` : ""}
                    {primeira.classe ? ` · ${primeira.classe}` : ""}
                    {primeira.estatuto ? ` · ${textoPublico(primeira.estatuto)}` : ""}
                  </DescricaoCartao>
                </div>
                <div className="flex flex-wrap gap-1">
                  {Object.entries(contagem).map(([e, n]) => (
                    <Etiqueta key={e}>
                      {n} {e}
                    </Etiqueta>
                  ))}
                </div>
              </div>
              <ul className="mt-4 divide-y divide-linha">
                {linhas.map((l, k) => (
                  <Propriedade key={`${l.caso}-${l.componente}-${l.propriedade}-${k}`} linha={l} />
                ))}
              </ul>
            </>
          ) : (
            <p className="text-sm text-texto2">Escolha um material.</p>
          )}
        </Cartao>
      </div>
    </div>
  );
}

function Propriedade({ linha: l }: { linha: (typeof APP.fichas.materiais)[number] }) {
  const [aberta, setAberta] = useState(false);
  const temNumero = l.tipico !== null || l.min !== null || l.max !== null;
  return (
    <li className="py-3">
      <button type="button" className="flex w-full items-start gap-3 text-left" onClick={() => setAberta((a) => !a)} aria-expanded={aberta}>
        <div className="min-w-0 flex-1">
          <div className="text-sm font-medium">{l.propriedade}</div>
          <div className="text-xs text-texto2">
            {l.caso}
            {l.componente && l.componente !== l.caso ? ` · ${l.componente}` : ""}
          </div>
        </div>
        <div className="text-right">
          <div className="numero text-sm font-bold">
            {temNumero ? `${valor(l.tipico ?? l.min)} ${l.unidade && l.unidade !== "-" ? l.unidade : ""}` : (l.valor_texto ?? "n.d.")}
          </div>
          {temNumero && l.min !== null && l.max !== null && l.min !== l.max && (
            <div className="numero text-xs text-texto2">intervalo {intervalo(l.min, l.max, 2)}</div>
          )}
        </div>
        <EstadoValor estado={l.estado} />
        <ChevronDown aria-hidden className={cn("mt-0.5 h-4 w-4 shrink-0 text-texto2 transition-transform", aberta && "rotate-180")} />
      </button>
      {aberta && (
        <div className="mt-2 space-y-2 rounded-md bg-superficie2 p-3">
          <Fonte referencia={l.referencia} doi={l.doi_url} className="flex" />
          {textoPublico(l.notas) && <p className="text-xs leading-relaxed text-texto2">{textoPublico(l.notas)}</p>}
        </div>
      )}
    </li>
  );
}
