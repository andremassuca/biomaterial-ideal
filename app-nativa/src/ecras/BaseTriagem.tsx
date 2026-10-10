// Base de triagem: todos os candidatos por caso, de bases abertas (Materials Project, JARVIS-DFT), das normas ASTM
// e da base verificada. Camada de triagem, não verificada: não entra no TOPSIS, no WASPAS nem no VIKOR.
import { useMemo, useState } from "react";
import { AlertTriangle, ArrowDownUp, Search } from "lucide-react";
import { CabecalhoEcra } from "@/componentes/comuns";
import { Cartao, DescricaoCartao, Etiqueta, TituloCartao } from "@/componentes/ui/cartao";
import { Opcoes, Progresso } from "@/componentes/ui/controlos";
import { TRIAGEM } from "@/lib/dados";
import { num, pct, valor } from "@/lib/formato";
import type { MaterialTriagem } from "@/lib/tipos";
import { cn } from "@/lib/utils";

type IdTriagem = "haste" | "stent" | "scaffold" | "par_articular" | "dentario";
const CASOS: { valor: IdTriagem; texto: string }[] = [
  { valor: "haste", texto: "Haste femoral" },
  { valor: "stent", texto: "Stent" },
  { valor: "scaffold", texto: "Scaffold ósseo" },
  { valor: "par_articular", texto: "Par articular" },
  { valor: "dentario", texto: "Implante dentário" },
];
type Classe = "todas" | "metálico" | "não metálico" | "polímero";
type Ordem = "nome" | "modulo" | "densidade";
const POR_PAGINA = 50;

export function BaseTriagem() {
  const [caso, setCaso] = useState<IdTriagem>("haste");
  const [classe, setClasse] = useState<Classe>("todas");
  const [ordem, setOrdem] = useState<Ordem>("nome");
  const [busca, setBusca] = useState("");
  const [mostrar, setMostrar] = useState(POR_PAGINA);

  const doCaso = useMemo(() => TRIAGEM?.materiais.filter((m) => m.caso === caso) ?? [], [caso]);
  const lista = useMemo(() => {
    const termo = busca.trim().toLowerCase();
    const l = doCaso.filter(
      (m) =>
        (classe === "todas" || m.classe === classe) &&
        (!termo || m.nome.toLowerCase().includes(termo) || m.chave.toLowerCase().includes(termo)),
    );
    if (ordem === "nome") return l;
    // valores em falta vão para o fim
    return [...l].sort((a, b) => (b[ordem] ?? -Infinity) - (a[ordem] ?? -Infinity));
  }, [doCaso, classe, ordem, busca]);

  if (!TRIAGEM) {
    return (
      <div className="space-y-6">
        <CabecalhoEcra titulo="Base de triagem" />
        <Cartao>
          <p className="text-sm text-texto2">A base de triagem ainda não foi gerada (scripts/base_triagem.py e scripts/exportar_app_json.py).</p>
        </Cartao>
      </div>
    );
  }

  const licencas = TRIAGEM.licencas;
  const contagens = TRIAGEM.contagens.filter((c) => c.caso === caso);
  const somar = (campo: "classe" | "fonte_base") =>
    Object.entries(
      contagens.reduce<Record<string, number>>((acc, c) => {
        acc[c[campo]] = (acc[c[campo]] ?? 0) + c.materiais;
        return acc;
      }, {}),
    ).sort((a, b) => b[1] - a[1]);
  const cobertura = TRIAGEM.cobertura.filter((c) => c.caso === caso && c.pct >= 1);

  return (
    <div className="space-y-6">
      <CabecalhoEcra
        titulo="Base de triagem"
        subtitulo="Todos os candidatos encontrados para cada caso em bases abertas e nas normas, com a fonte e o tipo de cada valor. Mostra a escala da procura; a decisão faz-se só na base verificada."
      />
      <p
        role="note"
        className="flex items-start gap-2 rounded-md border border-aviso/40 bg-aviso/10 px-3 py-2 text-sm leading-relaxed text-texto"
      >
        <AlertTriangle aria-hidden className="mt-0.5 h-4 w-4 shrink-0 text-aviso" />
        <span>
          <strong className="uppercase">{TRIAGEM.aviso}.</strong> Valores calculados (DFT) ou sem confirmação; não entram no TOPSIS, no
          WASPAS nem no VIKOR.
        </span>
      </p>

      <Opcoes
        rotulo="Caso"
        valor={caso}
        aoMudar={(v) => {
          setCaso(v);
          setMostrar(POR_PAGINA);
        }}
        opcoes={CASOS}
      />

      <div className="grid gap-6 lg:grid-cols-3">
        <Cartao>
          <DescricaoCartao>Materiais candidatos</DescricaoCartao>
          <div className="numero mt-1 text-4xl font-bold text-acento">{num(doCaso.length, 0)}</div>
          <ul className="mt-3 space-y-1 text-sm">
            {somar("classe").map(([k, n]) => (
              <li key={k} className="flex justify-between gap-2">
                <span className="text-texto2">{k}</span>
                <span className="numero">{num(n, 0)}</span>
              </li>
            ))}
          </ul>
        </Cartao>
        <Cartao>
          <TituloCartao>Por fonte</TituloCartao>
          <DescricaoCartao>Um composto que está em duas bases conta em cada uma.</DescricaoCartao>
          <ul className="mt-3 space-y-1 text-sm">
            {somar("fonte_base").map(([k, n]) => (
              <li key={k} className="flex justify-between gap-2">
                <span>
                  {k}
                  <span className="ml-1 text-xs text-texto2">({licencas[k]})</span>
                </span>
                <span className="numero">{num(n, 0)}</span>
              </li>
            ))}
          </ul>
        </Cartao>
        <Cartao>
          <TituloCartao>Propriedades preenchidas</TituloCartao>
          <ul className="mt-3 space-y-2">
            {cobertura.slice(0, 7).map((c) => (
              <li key={c.propriedade}>
                <div className="flex justify-between gap-2 text-sm">
                  <span>{c.propriedade}</span>
                  <span className="numero text-texto2">{pct(c.pct)}</span>
                </div>
                <Progresso valor={c.pct} rotulo={`${c.propriedade}: ${pct(c.pct)}`} className="mt-1" />
              </li>
            ))}
          </ul>
        </Cartao>
      </div>

      <Cartao>
        <div className="flex flex-wrap items-center gap-3">
          <label className="flex min-w-[220px] flex-1 items-center gap-2 rounded-md border border-linha bg-superficie2 px-2 py-1.5">
            <Search aria-hidden className="h-4 w-4 text-texto2" />
            <input
              value={busca}
              onChange={(e) => setBusca(e.target.value)}
              placeholder="Procurar fórmula, nome ou id"
              aria-label="Procurar material"
              className="w-full bg-transparent text-sm outline-none placeholder:text-texto2"
            />
          </label>
          <Opcoes
            rotulo="Classe"
            valor={classe}
            aoMudar={setClasse}
            opcoes={[
              { valor: "todas", texto: "Todas" },
              { valor: "metálico", texto: "Metálicos" },
              { valor: "não metálico", texto: "Não metálicos" },
              { valor: "polímero", texto: "Polímeros" },
            ]}
          />
          <Opcoes
            rotulo="Ordenar por"
            valor={ordem}
            aoMudar={setOrdem}
            opcoes={[
              { valor: "nome", texto: "Nome" },
              {
                valor: "modulo",
                texto: (
                  <span className="inline-flex items-center gap-1">
                    <ArrowDownUp aria-hidden className="h-3.5 w-3.5" /> Módulo
                  </span>
                ),
              },
              { valor: "densidade", texto: "Densidade" },
            ]}
          />
        </div>
        <p className="mt-3 text-xs text-texto2">
          {num(lista.length, 0)} materiais. Módulo e densidade do primeiro valor encontrado (base verificada, depois Materials
          Project, depois JARVIS-DFT).
        </p>
        <div className="mt-2 overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-linha text-left text-xs uppercase tracking-wide text-texto2">
                <th className="py-2 pr-3 font-bold">Material</th>
                <th className="py-2 pr-3 font-bold">Família</th>
                <th className="py-2 pr-3 text-right font-bold">Módulo (GPa)</th>
                <th className="py-2 pr-3 text-right font-bold">Densidade (g/cm³)</th>
                <th className="py-2 pr-3 font-bold">Fontes</th>
                <th className="py-2 font-bold">Tipo</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-linha">
              {lista.slice(0, mostrar).map((m) => (
                <Linha key={`${m.chave}-${m.caso}`} m={m} />
              ))}
            </tbody>
          </table>
        </div>
        {mostrar < lista.length && (
          <button
            type="button"
            onClick={() => setMostrar((n) => n + POR_PAGINA)}
            className="mt-3 rounded-md px-3 py-1.5 text-sm font-medium text-acento-texto hover:bg-superficie2"
          >
            Mostrar mais {num(Math.min(POR_PAGINA, lista.length - mostrar), 0)}
          </button>
        )}
      </Cartao>
    </div>
  );
}

function Linha({ m }: { m: MaterialTriagem }) {
  return (
    <tr>
      <td className="py-2 pr-3">
        <div className="font-medium">{m.nome}</div>
        <div className="text-xs text-texto2">{m.chave}</div>
      </td>
      <td className="py-2 pr-3 text-texto2">{m.familia}</td>
      <td className="numero py-2 pr-3 text-right">{valor(m.modulo)}</td>
      <td className="numero py-2 pr-3 text-right">{valor(m.densidade)}</td>
      <td className="py-2 pr-3 text-xs text-texto2">{m.fontes.join(", ")}</td>
      <td className="py-2">
        <div className="flex flex-wrap gap-1">
          {m.tipos.map((t) => (
            <Etiqueta key={t} tom={t === "verificado" ? "sucesso" : t === "calculado" ? "neutro" : "aviso"} className={cn("text-[0.7rem]")}>
              {t}
            </Etiqueta>
          ))}
        </div>
      </td>
    </tr>
  );
}
