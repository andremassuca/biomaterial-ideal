// Bloco "Vídeo da simulação": só aparece se o ficheiro MP4 existir em public/simulacao/videos (nada a mostrar sem ele).
import { Cartao, TituloCartao } from "@/componentes/ui/cartao";
import { NOTA_VERIFICACAO, urlVideo, videosDisponiveis, type VideoSimulacao } from "@/lib/simulacao";

/** Um vídeo com controlos, sem som, em ciclo, que só carrega os metadados até se carregar em reproduzir. */
export function CartaoVideo({ video }: { video: VideoSimulacao }) {
  return (
    <Cartao data-video={video.ficheiro}>
      <TituloCartao>{video.titulo}</TituloCartao>
      <figure className="mt-3">
        <video
          src={urlVideo(video.ficheiro)}
          controls
          muted
          loop
          playsInline
          preload="metadata"
          aria-label={video.titulo}
          className="w-full rounded-md bg-black"
        />
        <figcaption className="mt-2 text-xs leading-relaxed text-texto2">{video.legenda}</figcaption>
      </figure>
      <p role="note" className="mt-2 rounded-md border border-aviso/40 bg-aviso/10 px-3 py-2 text-xs font-medium text-texto">
        {NOTA_VERIFICACAO} Verificação numérica cruzada, não validação clínica nem experimental.
      </p>
    </Cartao>
  );
}

/** Vídeos disponíveis de um separador; não desenha nada se não houver nenhum ficheiro. */
export function BlocoVideo({ separador, existentes }: { separador: "cfd" | "fea"; existentes?: readonly string[] }) {
  const videos = existentes ? videosDisponiveis(separador, existentes) : videosDisponiveis(separador);
  if (videos.length === 0) return null;
  return (
    <>
      {videos.map((v) => (
        <CartaoVideo key={v.ficheiro} video={v} />
      ))}
    </>
  );
}
