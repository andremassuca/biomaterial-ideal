// Imagem que se amplia ao clicar (janela simples sobre o ecrã, fecha com Esc, com o botão ou ao clicar fora).
import { useEffect, useState } from "react";
import { X } from "lucide-react";
import { cn } from "@/lib/utils";

/**
 * Imagem com legenda que se vê em grande ao clicar.
 * Em linguagem simples: mostra a imagem pequena dentro de um botão; ao clicar, abre uma janela escura com a imagem
 * inteira e a mesma legenda; Esc, o botão "Fechar" ou um clique fora fecham-na.
 */
export function Ampliavel({
  src,
  alt,
  legenda,
  className,
}: {
  src: string;
  alt: string;
  legenda?: string;
  className?: string;
}) {
  const [aberta, setAberta] = useState(false);

  useEffect(() => {
    if (!aberta) return;
    const aoTecla = (e: KeyboardEvent) => {
      if (e.key === "Escape") setAberta(false);
    };
    window.addEventListener("keydown", aoTecla);
    return () => window.removeEventListener("keydown", aoTecla);
  }, [aberta]);

  return (
    <>
      <button
        type="button"
        onClick={() => setAberta(true)}
        aria-label={`Ampliar: ${alt}`}
        className="block w-full cursor-zoom-in overflow-hidden rounded-md border border-linha bg-white focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-acento"
      >
        <img src={src} alt={alt} loading="lazy" className={cn("mx-auto block h-auto max-h-[28rem] w-auto max-w-full", className)} />
      </button>
      {aberta && (
        <div
          role="dialog"
          aria-modal="true"
          aria-label={alt}
          className="fixed inset-0 z-50 flex flex-col items-center justify-center gap-3 bg-black/80 p-4"
          onClick={() => setAberta(false)}
        >
          <button
            type="button"
            onClick={() => setAberta(false)}
            className="absolute right-4 top-4 inline-flex items-center gap-1 rounded-md bg-superficie px-3 py-1.5 text-sm font-medium text-texto"
          >
            <X aria-hidden className="h-4 w-4" /> Fechar
          </button>
          <img
            src={src}
            alt={alt}
            onClick={(e) => e.stopPropagation()}
            className="max-h-[80vh] max-w-full rounded-md bg-white object-contain"
          />
          {legenda && <p className="max-w-3xl text-center text-sm text-white">{legenda}</p>}
        </div>
      )}
    </>
  );
}
