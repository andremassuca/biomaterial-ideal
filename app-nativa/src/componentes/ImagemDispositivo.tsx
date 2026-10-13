// Imagem grande de um dispositivo (cartões do Início): usa src/imagens/inicio/<id>.webp ou .png se existir; senão, a ilustração SVG.
import { useDefinicoes } from "@/lib/definicoes";
import { cn } from "@/lib/utils";
import { Ilustracao } from "./comuns";

// As imagens entram no pacote da aplicação (com o endereço final já calculado), por isso nunca há pedidos a ficheiros que não existem.
const IMAGENS = import.meta.glob("../imagens/inicio/*.{webp,png}", { eager: true, query: "?url", import: "default" }) as Record<string, string>;

/** Extensões aceites, por ordem: primeiro webp (mais leve), depois png. */
export const EXTENSOES_IMAGEM = ["webp", "png"] as const;

/**
 * Endereço da imagem de um dispositivo, ou null se não existir.
 * Em linguagem simples: procura primeiro a imagem do tema (haste_escura ou haste_clara), depois haste, em webp e depois
 * em png, na lista de imagens do pacote (`imagens` serve para testar). `escuro` diz qual dos temas está ativo.
 */
export function urlImagem(id: string, imagens: Record<string, string> = IMAGENS, escuro = true): string | null {
  for (const nome of [`${id}_${escuro ? "escura" : "clara"}`, id]) {
    for (const ext of EXTENSOES_IMAGEM) {
      const chave = Object.keys(imagens).find((k) => k.endsWith(`/${nome}.${ext}`));
      if (chave) return imagens[chave];
    }
  }
  return null;
}

/**
 * Mostra a imagem do dispositivo; sem imagem, mostra a ilustração SVG de `ilustracao`.
 * Em linguagem simples: usa o render quando já lá estiver, e a ilustração antiga até lá.
 */
export function ImagemDispositivo({
  id,
  ilustracao,
  alt = "",
  className,
  imagens,
}: {
  id: string;
  ilustracao: string;
  alt?: string;
  className?: string;
  imagens?: Record<string, string>;
}) {
  const { escuro } = useDefinicoes();
  const url = urlImagem(id, imagens, escuro);
  return (
    <div className={cn("relative flex items-center justify-center overflow-hidden bg-superficie2", className)} data-imagem-dispositivo={id}>
      {url ? (
        <img src={url} alt={alt} loading="lazy" className="h-full w-full object-cover" />
      ) : (
        <Ilustracao nome={ilustracao} className="h-2/3 w-2/3 text-acento" />
      )}
    </div>
  );
}
