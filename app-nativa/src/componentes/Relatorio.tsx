// Relatório de uma análise, em folha branca pronta a imprimir ou guardar em PDF (caixa de impressão do sistema).
// Mostra o caso, o perfil, os pesos, os rankings dos três métodos, o Monte Carlo, as fontes e as limitações.
import { useEffect } from "react";
import { createPortal } from "react-dom";
import { Printer, X } from "lucide-react";
import { TEXTO_AVISO } from "@/componentes/comuns";
import { Botao } from "@/componentes/ui/botao";
import type { Analise } from "@/lib/analise";
import { TITULO_CASO, descricaoCenario, rotuloMaterial } from "@/lib/dados";
import { num, pct, valor, decimalPt } from "@/lib/formato";
import { ehPersonalizado } from "@/lib/personalizados";
import { textoPublico } from "@/lib/publico";
import { contagemEstados, fecharRelatorio, useRelatorio } from "@/lib/relatorio";

/** Data e hora legíveis (hora de Lisboa) a partir do texto ISO. */
export function dataLegivel(iso: string): string {
  const d = new Date(iso);
  return Number.isNaN(d.getTime())
    ? iso
    : d.toLocaleString("pt-PT", { dateStyle: "long", timeStyle: "short", timeZone: "Europe/Lisbon" });
}

const TIPO: Record<string, string> = { benefit: "benefício", cost: "custo", target: "alvo" };

/** Limitações que valem para toda a análise (texto fixo; o que depende da análise acrescenta-se à parte). */
export const LIMITACOES = [
  "Ferramenta educativa de exploração de critérios, não clínica: o ranking compara materiais, não escolhe um implante para um doente.",
  "Os valores das propriedades vêm de intervalos da literatura e de fichas de fornecedor; cada valor tem estado e fonte nas fichas dos materiais, e os que estão 'A verificar' pesam menos na confiança do resultado.",
  "Os pesos dos critérios e os fatores das regras do perfil são valores de desenho do trabalho, não medições; o Monte Carlo mostra o quanto o resultado muda quando os dados ou os pesos variam.",
  "As regras do perfil só alteram pesos, candidatos e critérios; não representam decisão clínica e algumas assentam em evidência fraca ou contraditória (ver o estado de cada regra).",
  "Os rankings dos três métodos (TOPSIS, WASPAS e VIKOR) podem discordar; o consenso de Borda resume-os, mas não elimina a diferença.",
];

function Tabela({ cabecalho, linhas }: { cabecalho: string[]; linhas: (string | number)[][] }) {
  return (
    <table className="w-full border-collapse text-left text-[11px]">
      <thead>
        <tr>
          {cabecalho.map((c, k) => (
            <th key={`${c}-${k}`} className="border-b border-neutral-400 py-1 pr-2 font-semibold">
              {c}
            </th>
          ))}
        </tr>
      </thead>
      <tbody>
        {linhas.map((l, i) => (
          <tr key={i} className="break-inside-avoid">
            {l.map((c, k) => (
              <td key={k} className="border-b border-neutral-200 py-1 pr-2 align-top">
                {c}
              </td>
            ))}
          </tr>
        ))}
      </tbody>
    </table>
  );
}

function Seccao({ titulo, children }: { titulo: string; children: React.ReactNode }) {
  return (
    <section className="mt-5 break-inside-avoid-page">
      <h2 className="mb-2 border-b border-neutral-300 pb-1 text-sm font-bold uppercase tracking-wide">{titulo}</h2>
      {children}
    </section>
  );
}

/** Conteúdo do relatório (a folha). */
export function Relatorio({ analise: a }: { analise: Analise }) {
  const r = a.ranking;
  const ordem = r.alternativas.map((_, i) => i).sort((i, j) => (r.pos_borda[i] ?? i + 1) - (r.pos_borda[j] ?? j + 1));
  const ordenado = a.apenasTopsis ? r.alternativas.map((_, i) => i).sort((i, j) => r.pos_topsis[i] - r.pos_topsis[j]) : ordem;
  const perfil = a.perfil ? Object.entries(a.perfil) : [];
  const estados = contagemEstados(a.caso, r.alternativas);
  const fontesRegras = Array.from(new Set(a.regras.map((x) => x.fonte).filter((x): x is string => !!x)));

  return (
    <article className="mx-auto max-w-[190mm] bg-white p-8 text-[12px] leading-snug text-neutral-900" data-relatorio>
      <header className="border-b-2 border-neutral-800 pb-3">
        <p className="text-[10px] font-semibold uppercase tracking-widest text-neutral-600">Biomaterial Ideal: relatório de análise</p>
        <h1 className="mt-1 text-xl font-bold">{TITULO_CASO[a.caso]}</h1>
        <p className="mt-1 text-[11px] text-neutral-700">
          {descricaoCenario(a.cenario)}. Gerado em {dataLegivel(a.criadaEm)}. Versão da aplicação {a.versaoApp}; versão dos dados{" "}
          {a.versaoDados}.
        </p>
        <p className="mt-2 rounded border border-neutral-400 px-2 py-1 text-[11px]">{TEXTO_AVISO}</p>
      </header>

      <Seccao titulo="Perfil do doente">
        {perfil.length === 0 ? (
          <p>Sem perfil: caso de base, com os pesos e os candidatos do cenário.</p>
        ) : (
          <Tabela cabecalho={["Dado", "Valor"]} linhas={perfil.map(([k, v]) => [k.replace(/_/g, " "), String(v)])} />
        )}
        {a.regras.length > 0 && (
          <div className="mt-3">
            <p className="mb-1 font-semibold">Regras ativadas</p>
            <Tabela
              cabecalho={["Regra", "Condição", "Efeito", "Justificação", "Estado"]}
              linhas={a.regras.map((x) => [
                x.id,
                textoPublico(x.condicao ?? ""),
                `${x.efeito}: ${x.alvo}${x.valor ? ` (${decimalPt(x.valor)})` : ""}`,
                textoPublico(x.justificacao ?? ""),
                x.estado ?? "",
              ])}
            />
          </div>
        )}
        {a.excluidos.length > 0 && (
          <p className="mt-2">
            <strong>Materiais excluídos pelo perfil: </strong>
            {a.excluidos.map(rotuloMaterial).join(", ")}.
          </p>
        )}
        {a.notas.length > 0 && (
          <ul className="mt-2 list-disc pl-5">
            {a.notas.map((n) => (
              <li key={n}>{textoPublico(n)}</li>
            ))}
          </ul>
        )}
      </Seccao>

      <Seccao titulo="Pesos dos critérios">
        <Tabela
          cabecalho={["Critério", "Tipo", "Peso de base", "Peso usado"]}
          linhas={a.criterios.map((c) => [
            c.nome + (c.novo ? " (acrescentado)" : ""),
            c.tipo === "target" ? `${TIPO[c.tipo]}: ${valor(c.alvo)}` : TIPO[c.tipo],
            c.pesoBase === null ? "n.a." : pct(100 * c.pesoBase),
            pct(100 * c.peso),
          ])}
        />
        {a.eta !== null && <p className="mt-1">Nível de confiança η = {num(a.eta, 1)}.</p>}
      </Seccao>

      <Seccao titulo="Rankings">
        {a.apenasTopsis ? (
          <p className="mb-1">Só o TOPSIS foi calculado (modo navegador sem o núcleo completo).</p>
        ) : null}
        <Tabela
          cabecalho={
            a.apenasTopsis
              ? ["Material", "TOPSIS (C)", "Pos."]
              : ["Material", "TOPSIS (C)", "Pos.", "WASPAS (Q)", "Pos.", "VIKOR (P, menor é melhor)", "Pos.", "Borda (pontos)", "Pos."]
          }
          linhas={ordenado.map((i) =>
            a.apenasTopsis
              ? [rotuloMaterial(r.alternativas[i]), num(r.c_topsis[i], 3), r.pos_topsis[i]]
              : [
                  rotuloMaterial(r.alternativas[i]),
                  num(r.c_topsis[i], 3),
                  r.pos_topsis[i],
                  num(r.q_waspas[i], 3),
                  r.pos_waspas[i],
                  num(r.p_vikor[i], 3),
                  r.pos_vikor[i],
                  num(r.pontos_borda[i], 0),
                  r.pos_borda[i],
                ],
          )}
        />
      </Seccao>

      <Seccao titulo="Robustez: Monte Carlo">
        {a.monteCarlo ? (
          <>
            <p className="mb-1">
              {num(a.monteCarlo.feitas, 0)} repetições{a.monteCarlo.parado ? " (parado a pedido)" : ""}; variaram{" "}
              {a.monteCarloVariou === "pesos" ? "os pesos" : "as propriedades"}. Percentagem de repetições em 1.º lugar:
            </p>
            <Tabela
              cabecalho={["Material", ...a.monteCarlo.metodos.map((m) => m.metodo)]}
              linhas={a.monteCarlo.alternativas.map((m, i) => [
                rotuloMaterial(m),
                ...a.monteCarlo!.metodos.map((x) => pct(x.pct_primeiro[i])),
              ])}
            />
          </>
        ) : (
          <p>O Monte Carlo não foi corrido nesta análise.</p>
        )}
      </Seccao>

      <Seccao titulo="Fontes e estado dos dados">
        <ul className="list-disc pl-5">
          <li>Método: TOPSIS, WASPAS e VIKOR com critérios-alvo, Petković et al., Appl. Sci. 2025, 15(16), 9198, doi:10.3390/app15169198.</li>
          <li>Valores das propriedades: base de dados do trabalho (versão dos dados {a.versaoDados}); fonte e estado de cada valor nas fichas dos materiais.</li>
          {fontesRegras.map((f) => (
            <li key={f}>Regras do perfil: {textoPublico(f)}</li>
          ))}
        </ul>
        <div className="mt-2">
          <Tabela
            cabecalho={["Material", "Valores na base", "Por estado"]}
            linhas={estados.map((e) => [
              rotuloMaterial(e.material),
              e.total,
              ehPersonalizado(e.material)
                ? "Definido pelo utilizador (fora da base)"
                : Object.entries(e.porEstado)
                    .map(([k, v]) => `${k}: ${v}`)
                    .join("; "),
            ])}
          />
        </div>
      </Seccao>

      <Seccao titulo="Limitações">
        <ul className="list-disc pl-5">
          {LIMITACOES.map((l) => (
            <li key={l}>{l}</li>
          ))}
        </ul>
      </Seccao>
    </article>
  );
}

/**
 * Janela do relatório por cima da aplicação, com os botões de imprimir e fechar.
 * Em linguagem simples: aparece quando se pede o PDF; "Imprimir ou guardar em PDF" abre a caixa de impressão do
 * sistema, onde se escolhe "Guardar como PDF". Na impressão só a folha sai (ver tema.css).
 */
export function ModalRelatorio() {
  const analise = useRelatorio();
  useEffect(() => {
    if (!analise) return;
    const aoTecla = (e: KeyboardEvent) => e.key === "Escape" && fecharRelatorio();
    window.addEventListener("keydown", aoTecla);
    return () => window.removeEventListener("keydown", aoTecla);
  }, [analise]);
  if (!analise || typeof document === "undefined") return null;
  return createPortal(
    <div id="relatorio-impressao" role="dialog" aria-modal="true" aria-label="Relatório da análise" className="fixed inset-0 z-50 overflow-y-auto bg-neutral-200">
      <div className="no-print sticky top-0 z-10 flex items-center justify-between gap-3 border-b border-neutral-400 bg-neutral-100 px-4 py-2 text-neutral-900">
        <span className="text-sm font-medium">Relatório da análise</span>
        <div className="flex gap-2">
          <Botao onClick={() => window.print()}>
            <Printer className="h-4 w-4" /> Imprimir ou guardar em PDF
          </Botao>
          <Botao variante="contorno" onClick={fecharRelatorio} aria-label="Fechar o relatório" className="text-neutral-900">
            <X className="h-4 w-4" /> Fechar
          </Botao>
        </div>
      </div>
      <div className="py-4">
        <Relatorio analise={analise} />
      </div>
    </div>,
    document.body,
  );
}
