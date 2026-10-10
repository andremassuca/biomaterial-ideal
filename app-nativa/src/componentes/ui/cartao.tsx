import type { HTMLAttributes, ReactNode } from "react";
import { cn } from "@/lib/utils";

// Cartão (superfície com linha fina), título e descrição.
export function Cartao({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return <div className={cn("rounded-lg border border-linha bg-superficie p-5 shadow-sm", className)} {...props} />;
}

export function TituloCartao({ children, className }: { children: ReactNode; className?: string }) {
  return <h3 className={cn("text-base font-bold leading-tight text-texto", className)}>{children}</h3>;
}

export function DescricaoCartao({ children, className }: { children: ReactNode; className?: string }) {
  return <p className={cn("mt-1 text-sm text-texto2", className)}>{children}</p>;
}

/** Etiqueta pequena (estado de um valor, efeito de uma regra). */
export function Etiqueta({
  children,
  tom = "neutro",
  className,
}: {
  children: ReactNode;
  tom?: "neutro" | "acento" | "aviso" | "perigo" | "sucesso";
  className?: string;
}) {
  const cores = {
    neutro: "bg-superficie2 text-texto2",
    acento: "bg-acento/15 text-acento-texto",
    aviso: "bg-aviso/15 text-aviso",
    perigo: "bg-perigo/15 text-perigo",
    sucesso: "bg-sucesso/15 text-sucesso",
  } as const;
  return (
    <span className={cn("inline-flex items-center rounded-sm px-2 py-0.5 text-xs font-medium", cores[tom], className)}>
      {children}
    </span>
  );
}
