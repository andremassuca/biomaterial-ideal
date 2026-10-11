// Componentes pequenos usados em vários ecrãs.
import type { ReactNode } from "react";
import { AlertTriangle, BookOpen, Info } from "lucide-react";
import { codigo, nomeSimples } from "@/lib/dados";
import { textoPublico } from "@/lib/publico";
import { cn } from "@/lib/utils";
import { Etiqueta } from "./ui/cartao";

import haste from "@/ilustracoes/haste.svg?raw";
import stent from "@/ilustracoes/stent.svg?raw";
import scaffold from "@/ilustracoes/scaffold.svg?raw";
import par from "@/ilustracoes/par.svg?raw";
import dentario from "@/ilustracoes/dentario.svg?raw";

/** Texto fixo do aviso (especificação da aplicação). */
export const TEXTO_AVISO =
  "Ferramenta educativa de exploração de critérios. Não é ferramenta clínica nem recomendação terapêutica: não é um dispositivo médico e não substitui a decisão clínica.";

/** Aviso fixo, visível nos resultados e no Sobre. */
export function Aviso({ className }: { className?: string }) {
  return (
    <p
      role="note"
      className={cn(
        "flex items-start gap-2 rounded-md border border-aviso/40 bg-aviso/10 px-3 py-2 text-xs leading-relaxed text-texto",
        className,
      )}
    >
      <AlertTriangle aria-hidden className="mt-0.5 h-4 w-4 shrink-0 text-aviso" />
      <span>{TEXTO_AVISO}</span>
    </p>
  );
}

/** Nome simples do material, com o código técnico em letra pequena. */
export function NomeMaterial({ material, className, linha = false }: { material: string; className?: string; linha?: boolean }) {
  const c = codigo(material);
  return (
    <span className={cn(linha ? "inline-flex items-baseline gap-1.5" : "inline-flex flex-col", className)}>
      <span className="font-medium leading-tight text-texto">{nomeSimples(material)}</span>
      {c && <span className="text-xs leading-tight text-texto2">{c}</span>}
    </span>
  );
}

/** Cabeçalho de um ecrã. */
export function CabecalhoEcra({ titulo, subtitulo, acoes }: { titulo: string; subtitulo?: ReactNode; acoes?: ReactNode }) {
  return (
    <header className="mb-6 flex flex-wrap items-end justify-between gap-4">
      <div>
        <h1 className="text-[1.75rem] font-bold leading-tight text-acento">{titulo}</h1>
        {subtitulo && <p className="mt-1 max-w-3xl text-sm text-texto2">{subtitulo}</p>}
      </div>
      {acoes}
    </header>
  );
}

/** Fonte de um valor ou de uma regra (referência, DOI ou ligação), em texto selecionável. */
export function Fonte({ referencia: bruta, doi, className }: { referencia?: string | null; doi?: string | null; className?: string }) {
  const referencia = textoPublico(bruta);
  if (!referencia && !doi) return <span className={cn("text-xs text-texto2", className)}>Sem fonte indicada</span>;
  return (
    <span className={cn("inline-flex items-start gap-1.5 text-xs leading-relaxed text-texto2", className)}>
      <BookOpen aria-hidden className="mt-0.5 h-3.5 w-3.5 shrink-0" />
      <span className="select-text">
        {referencia}
        {doi && (
          <>
            {referencia ? "; " : ""}
            <span className="break-all text-acento-texto">{doi}</span>
          </>
        )}
      </span>
    </span>
  );
}

/** Estado de um valor da base ("Verificado", "A verificar", "Regra do trabalho"). */
export function EstadoValor({ estado }: { estado: string | null | undefined }) {
  if (!estado) return <Etiqueta>sem estado</Etiqueta>;
  const tom = estado.startsWith("Verificado") ? "sucesso" : estado.startsWith("A verificar") ? "aviso" : "neutro";
  return <Etiqueta tom={tom}>{estado}</Etiqueta>;
}

/** Caixa de informação (modo navegador, resultados por chegar). */
export function Informacao({ children, className }: { children: ReactNode; className?: string }) {
  return (
    <div className={cn("flex items-start gap-2 rounded-md border border-linha bg-superficie2 px-3 py-2 text-sm text-texto2", className)}>
      <Info aria-hidden className="mt-0.5 h-4 w-4 shrink-0 text-acento-texto" />
      <div>{children}</div>
    </div>
  );
}

const ILUSTRACOES: Record<string, string> = { haste, stent, scaffold, par, dentario };

/** Ilustração SVG do dispositivo, desenhada com currentColor (segue o tema). */
export function Ilustracao({ nome, className }: { nome: string; className?: string }) {
  const svg = ILUSTRACOES[nome];
  if (!svg) return null;
  return <span aria-hidden className={cn("inline-block [&>svg]:h-full [&>svg]:w-full", className)} dangerouslySetInnerHTML={{ __html: svg }} />;
}
