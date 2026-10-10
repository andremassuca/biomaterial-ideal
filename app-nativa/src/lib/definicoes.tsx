// Definições da aplicação (tema, letra, movimento, modo apresentação), guardadas no localStorage.
import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
import { MotionConfig } from "framer-motion";
import { gravar, ler } from "./utils";

export type Tema = "sistema" | "claro" | "escuro";
export type Letra = "normal" | "grande" | "muito-grande";
export type Movimento = "sistema" | "completo" | "reduzido";

interface Definicoes {
  tema: Tema;
  letra: Letra;
  movimento: Movimento;
  apresentacao: boolean;
  /** Tema efetivo depois de resolver "sistema". */
  escuro: boolean;
  /** Movimento efetivo depois de resolver "sistema". */
  reduzido: boolean;
  definir: (d: Partial<Pick<Definicoes, "tema" | "letra" | "movimento" | "apresentacao">>) => void;
}

const Contexto = createContext<Definicoes | null>(null);

function preferencia(consulta: string): boolean {
  try {
    return matchMedia(consulta).matches;
  } catch {
    return false;
  }
}

/** Acompanha uma media query do sistema (tema escuro, movimento reduzido). */
function useMediaQuery(consulta: string): boolean {
  const [v, setV] = useState(() => preferencia(consulta));
  useEffect(() => {
    let mq: MediaQueryList;
    try {
      mq = matchMedia(consulta);
    } catch {
      return;
    }
    const f = () => setV(mq.matches);
    mq.addEventListener("change", f);
    return () => mq.removeEventListener("change", f);
  }, [consulta]);
  return v;
}

function valido<T extends string>(v: string | null, opcoes: readonly T[], omissao: T): T {
  return v !== null && (opcoes as readonly string[]).includes(v) ? (v as T) : omissao;
}

export function ProvedorDefinicoes({ children }: { children: ReactNode }) {
  const [tema, setTema] = useState<Tema>(() => valido(ler("biomat.tema"), ["sistema", "claro", "escuro"], "sistema"));
  const [letra, setLetra] = useState<Letra>(() => valido(ler("biomat.letra"), ["normal", "grande", "muito-grande"], "normal"));
  const [movimento, setMovimento] = useState<Movimento>(() =>
    valido(ler("biomat.movimento"), ["sistema", "completo", "reduzido"], "sistema"),
  );
  const [apresentacao, setApresentacao] = useState<boolean>(() => ler("biomat.apresentacao") === "sim");
  const sistemaEscuro = useMediaQuery("(prefers-color-scheme: dark)");
  const sistemaReduzido = useMediaQuery("(prefers-reduced-motion: reduce)");

  const escuro = tema === "escuro" || (tema === "sistema" && sistemaEscuro);
  const reduzido = movimento === "reduzido" || (movimento === "sistema" && sistemaReduzido);

  // Aplica ao documento: tema, tamanho da letra, movimento e modo apresentação.
  useEffect(() => {
    const raiz = document.documentElement;
    raiz.dataset.tema = escuro ? "escuro" : "claro";
    raiz.dataset.letra = apresentacao ? "muito-grande" : letra;
    raiz.dataset.movimento = reduzido ? "reduzido" : "completo";
    raiz.dataset.apresentacao = apresentacao ? "sim" : "nao";
  }, [escuro, letra, reduzido, apresentacao]);

  const valor = useMemo<Definicoes>(
    () => ({
      tema,
      letra,
      movimento,
      apresentacao,
      escuro,
      reduzido,
      definir: (d) => {
        if (d.tema) {
          setTema(d.tema);
          gravar("biomat.tema", d.tema);
        }
        if (d.letra) {
          setLetra(d.letra);
          gravar("biomat.letra", d.letra);
        }
        if (d.movimento) {
          setMovimento(d.movimento);
          gravar("biomat.movimento", d.movimento);
        }
        if (d.apresentacao !== undefined) {
          setApresentacao(d.apresentacao);
          gravar("biomat.apresentacao", d.apresentacao ? "sim" : "nao");
        }
      },
    }),
    [tema, letra, movimento, apresentacao, escuro, reduzido],
  );

  return (
    <Contexto.Provider value={valor}>
      <MotionConfig reducedMotion={reduzido ? "always" : "never"}>{children}</MotionConfig>
    </Contexto.Provider>
  );
}

export function useDefinicoes(): Definicoes {
  const d = useContext(Contexto);
  if (!d) throw new Error("useDefinicoes fora do ProvedorDefinicoes");
  return d;
}
