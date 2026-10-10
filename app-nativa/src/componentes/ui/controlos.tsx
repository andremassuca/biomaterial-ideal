// Controlos Radix no estilo do shadcn/ui: cursor, interruptor, separadores, barra de progresso, dica e grupo de opções.
import { forwardRef, type ComponentPropsWithoutRef, type ElementRef, type ReactNode } from "react";
import * as SliderPrimitivo from "@radix-ui/react-slider";
import * as SwitchPrimitivo from "@radix-ui/react-switch";
import * as TabsPrimitivo from "@radix-ui/react-tabs";
import * as ProgressPrimitivo from "@radix-ui/react-progress";
import * as TooltipPrimitivo from "@radix-ui/react-tooltip";
import * as ToggleGroupPrimitivo from "@radix-ui/react-toggle-group";
import { cn } from "@/lib/utils";

export const Cursor = forwardRef<
  ElementRef<typeof SliderPrimitivo.Root>,
  ComponentPropsWithoutRef<typeof SliderPrimitivo.Root>
>(function Cursor({ className, ...props }, ref) {
  return (
    <SliderPrimitivo.Root
      ref={ref}
      className={cn("relative flex w-full touch-none select-none items-center py-2", className)}
      {...props}
    >
      <SliderPrimitivo.Track className="relative h-1.5 w-full grow overflow-hidden rounded-full bg-linha">
        <SliderPrimitivo.Range className="absolute h-full bg-acento" />
      </SliderPrimitivo.Track>
      <SliderPrimitivo.Thumb
        className="block h-4 w-4 rounded-full border-2 border-acento bg-superficie shadow focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-acento"
        aria-label={props["aria-label"]}
      />
    </SliderPrimitivo.Root>
  );
});

export const Interruptor = forwardRef<
  ElementRef<typeof SwitchPrimitivo.Root>,
  ComponentPropsWithoutRef<typeof SwitchPrimitivo.Root>
>(function Interruptor({ className, ...props }, ref) {
  return (
    <SwitchPrimitivo.Root
      ref={ref}
      className={cn(
        "peer inline-flex h-6 w-11 shrink-0 cursor-pointer items-center rounded-full border-2 border-transparent bg-linha transition-colors data-[state=checked]:bg-acento disabled:cursor-not-allowed disabled:opacity-50",
        className,
      )}
      {...props}
    >
      <SwitchPrimitivo.Thumb className="pointer-events-none block h-5 w-5 rounded-full bg-white shadow-lg ring-0 transition-transform data-[state=checked]:translate-x-5 data-[state=unchecked]:translate-x-0" />
    </SwitchPrimitivo.Root>
  );
});

export const Separadores = TabsPrimitivo.Root;

export function ListaSeparadores({ className, ...props }: ComponentPropsWithoutRef<typeof TabsPrimitivo.List>) {
  return (
    <TabsPrimitivo.List
      className={cn("inline-flex flex-wrap items-center gap-1 rounded-md bg-superficie2 p-1", className)}
      {...props}
    />
  );
}

export function Separador({ className, ...props }: ComponentPropsWithoutRef<typeof TabsPrimitivo.Trigger>) {
  return (
    <TabsPrimitivo.Trigger
      className={cn(
        "rounded-sm px-3 py-1.5 text-sm font-medium text-texto2 transition-colors hover:text-texto data-[state=active]:bg-superficie data-[state=active]:text-texto data-[state=active]:shadow-sm",
        className,
      )}
      {...props}
    />
  );
}

export const ConteudoSeparador = TabsPrimitivo.Content;

export function Progresso({ valor, className, rotulo }: { valor: number; className?: string; rotulo: string }) {
  return (
    <ProgressPrimitivo.Root
      className={cn("relative h-2 w-full overflow-hidden rounded-full bg-linha", className)}
      value={valor}
      aria-label={rotulo}
    >
      <ProgressPrimitivo.Indicator
        className="h-full bg-acento transition-transform duration-150"
        style={{ transform: `translateX(-${100 - Math.max(0, Math.min(100, valor))}%)` }}
      />
    </ProgressPrimitivo.Root>
  );
}

export const ProvedorDicas = TooltipPrimitivo.Provider;

/** Dica que aparece ao passar o rato ou ao focar (explicações de TOPSIS, η e critério-alvo). */
export function Dica({ texto, children }: { texto: ReactNode; children: ReactNode }) {
  return (
    <TooltipPrimitivo.Root delayDuration={250}>
      <TooltipPrimitivo.Trigger asChild>{children}</TooltipPrimitivo.Trigger>
      <TooltipPrimitivo.Portal>
        <TooltipPrimitivo.Content
          sideOffset={6}
          className="z-50 max-w-xs rounded-md border border-linha bg-superficie px-3 py-2 text-xs leading-relaxed text-texto shadow-lg"
        >
          {texto}
        </TooltipPrimitivo.Content>
      </TooltipPrimitivo.Portal>
    </TooltipPrimitivo.Root>
  );
}

/** Grupo de opções exclusivas (botões segmentados). */
export function Opcoes<T extends string>({
  valor,
  aoMudar,
  opcoes,
  rotulo,
  className,
}: {
  valor: T;
  aoMudar: (v: T) => void;
  opcoes: { valor: T; texto: ReactNode }[];
  rotulo: string;
  className?: string;
}) {
  return (
    <ToggleGroupPrimitivo.Root
      type="single"
      value={valor}
      onValueChange={(v) => v && aoMudar(v as T)}
      aria-label={rotulo}
      className={cn("inline-flex flex-wrap gap-1 rounded-md bg-superficie2 p-1", className)}
    >
      {opcoes.map((o) => (
        <ToggleGroupPrimitivo.Item
          key={o.valor}
          value={o.valor}
          className="rounded-sm px-3 py-1.5 text-sm font-medium text-texto2 transition-colors hover:text-texto data-[state=on]:bg-superficie data-[state=on]:text-texto data-[state=on]:shadow-sm"
        >
          {o.texto}
        </ToggleGroupPrimitivo.Item>
      ))}
    </ToggleGroupPrimitivo.Root>
  );
}
