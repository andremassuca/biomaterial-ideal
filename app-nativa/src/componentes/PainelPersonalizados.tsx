// Cartão "Materiais personalizados": o utilizador cria um material com as suas propriedades, que entra só na sua
// análise (ranking local) e fica marcado "Definido pelo utilizador". A base de dados nunca é alterada.
import { useState } from "react";
import { Plus, Trash2 } from "lucide-react";
import { Informacao } from "@/componentes/comuns";
import { Botao } from "@/componentes/ui/botao";
import { Cartao, DescricaoCartao, Etiqueta, TituloCartao } from "@/componentes/ui/cartao";
import { APP, type IdCaso } from "@/lib/dados";
import {
  nomeMarcado,
  guardarPersonalizado,
  removerPersonalizado,
  validarFormulario,
  type MaterialPersonalizado,
  type RascunhoValor,
} from "@/lib/personalizados";
import type { Problema } from "@/lib/tipos";

/** Unidade de um critério, lida da base (primeira ficha com esse nome de propriedade); vazio se não houver. */
export function unidadeCriterio(criterio: string): string {
  return APP.fichas.materiais.find((l) => l.propriedade === criterio && l.unidade)?.unidade ?? "";
}

const CAMPO =
  "h-8 w-full rounded-md border border-linha bg-fundo px-2 text-sm text-texto placeholder:text-texto2 focus-visible:outline focus-visible:outline-2 focus-visible:outline-acento";

export function PainelPersonalizados({
  caso,
  problema,
  lista,
  deFora,
}: {
  caso: IdCaso;
  /** Problema do cenário atual (define os critérios a preencher). */
  problema: Problema;
  lista: MaterialPersonalizado[];
  /** Materiais personalizados que não entram neste cenário e os critérios que lhes faltam. */
  deFora: { nome: string; falta: string[] }[];
}) {
  const [aberto, setAberto] = useState(false);
  const [nome, setNome] = useState("");
  const [rascunho, setRascunho] = useState<Record<string, RascunhoValor>>({});
  const [erros, setErros] = useState<string[]>([]);

  const mudar = (c: string, campo: keyof RascunhoValor, v: string) =>
    setRascunho((r) => ({ ...r, [c]: { ...(r[c] ?? { tipico: "", min: "", max: "" }), [campo]: v } }));

  const criar = () => {
    const existentes = [...problema.alternativas, ...lista.map((m) => m.nome)];
    const r = validarFormulario(problema, nome, rascunho, existentes);
    setErros(r.erros);
    if (!r.valores) return;
    guardarPersonalizado({
      id: `${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 6)}`,
      caso,
      nome: nome.trim(),
      valores: r.valores,
    });
    setNome("");
    setRascunho({});
    setAberto(false);
  };

  return (
    <Cartao data-personalizados>
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <TituloCartao>Materiais personalizados</TituloCartao>
          <DescricaoCartao>
            Crie um material com as suas propriedades para o ver no ranking. Fica só neste computador, só na sua análise, e
            não altera a base de dados.
          </DescricaoCartao>
        </div>
        <Botao variante="contorno" tamanho="pequeno" onClick={() => setAberto((a) => !a)} aria-expanded={aberto}>
          <Plus className="h-3.5 w-3.5" /> {aberto ? "Fechar o formulário" : "Novo material"}
        </Botao>
      </div>

      {lista.length > 0 && (
        <ul className="mt-4 space-y-2">
          {lista.map((m) => (
            <li key={m.id} className="flex items-center justify-between gap-3 rounded-md border border-linha px-3 py-2 text-sm">
              <span className="flex flex-wrap items-center gap-2">
                <strong>{nomeMarcado(m.nome)}</strong>
                <Etiqueta tom="aviso">Definido pelo utilizador</Etiqueta>
              </span>
              <Botao variante="fantasma" tamanho="pequeno" aria-label={`Apagar ${m.nome}`} onClick={() => removerPersonalizado(m.id)}>
                <Trash2 className="h-3.5 w-3.5" />
              </Botao>
            </li>
          ))}
        </ul>
      )}
      {deFora.length > 0 && (
        <Informacao>
          Neste cenário não entram: {deFora.map((d) => `${d.nome} (falta ${d.falta.join(", ")})`).join("; ")}.
        </Informacao>
      )}

      {aberto && (
        <form
          className="mt-4 space-y-3"
          onSubmit={(e) => {
            e.preventDefault();
            criar();
          }}
        >
          <label className="block text-sm font-medium">
            Nome do material
            <input className={`${CAMPO} mt-1`} value={nome} onChange={(e) => setNome(e.target.value)} maxLength={60} />
          </label>
          <p className="text-xs text-texto2">
            Valor típico obrigatório em todos os critérios do cenário atual; mínimo e máximo são opcionais (ficam iguais ao
            típico). Critérios ordinais: números inteiros de 1 a 5. Use ponto ou vírgula nos decimais.
          </p>
          <div className="space-y-2">
            {problema.criterios.map((c, j) => {
              const u = unidadeCriterio(c);
              return (
                <fieldset key={c} className="grid items-end gap-2 sm:grid-cols-[1fr_repeat(3,110px)]">
                  <legend className="sr-only">{c}</legend>
                  <span className="text-sm">
                    {c}
                    {u ? <span className="text-texto2"> ({u})</span> : null}
                    {problema.ordinal[j] ? <span className="text-texto2"> (ordinal 1 a 5)</span> : null}
                  </span>
                  {(["tipico", "min", "max"] as const).map((campo) => (
                    <input
                      key={campo}
                      className={CAMPO}
                      inputMode="decimal"
                      placeholder={campo === "tipico" ? "típico" : campo === "min" ? "mínimo" : "máximo"}
                      aria-label={`${c}: ${campo === "tipico" ? "valor típico" : campo === "min" ? "mínimo" : "máximo"}`}
                      value={rascunho[c]?.[campo] ?? ""}
                      onChange={(e) => mudar(c, campo, e.target.value)}
                    />
                  ))}
                </fieldset>
              );
            })}
          </div>
          {erros.length > 0 && (
            <ul role="alert" className="list-disc space-y-0.5 pl-5 text-sm text-perigo">
              {erros.map((e) => (
                <li key={e}>{e}</li>
              ))}
            </ul>
          )}
          <Botao type="submit">Acrescentar ao ranking</Botao>
        </form>
      )}
    </Cartao>
  );
}
