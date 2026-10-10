import { forwardRef, type ButtonHTMLAttributes } from "react";
import { Slot } from "@radix-ui/react-slot";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

// Botão no padrão do shadcn/ui, com as cores do tema.
const variantes = cva(
  "inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-md text-sm font-medium transition-colors disabled:pointer-events-none disabled:opacity-50",
  {
    variants: {
      variante: {
        principal: "bg-acento-texto text-white hover:bg-acento-texto/90 dark:text-fundo",
        secundario: "bg-superficie2 text-texto hover:bg-linha",
        contorno: "border border-linha bg-transparent text-texto hover:bg-superficie2",
        fantasma: "bg-transparent text-texto hover:bg-superficie2",
        perigo: "bg-perigo text-white hover:bg-perigo/90",
      },
      tamanho: {
        normal: "h-9 px-4",
        pequeno: "h-8 px-3 text-xs",
        grande: "h-11 px-6 text-base",
        icone: "h-9 w-9",
      },
    },
    defaultVariants: { variante: "principal", tamanho: "normal" },
  },
);

export interface PropsBotao extends ButtonHTMLAttributes<HTMLButtonElement>, VariantProps<typeof variantes> {
  asChild?: boolean;
}

export const Botao = forwardRef<HTMLButtonElement, PropsBotao>(function Botao(
  { className, variante, tamanho, asChild = false, ...props },
  ref,
) {
  const Comp = asChild ? Slot : "button";
  return <Comp ref={ref} className={cn(variantes({ variante, tamanho }), className)} {...props} />;
});
