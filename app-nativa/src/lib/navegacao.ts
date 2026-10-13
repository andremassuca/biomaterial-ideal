// Navegação entre ecrãs com o endereço: cada ecrã tem o seu "#/nome" (ex.: #/stent), o botão "Voltar" do navegador
// regressa ao ecrã anterior e um endereço pode abrir diretamente um caso (por exemplo a partir de um QR).
import { useCallback, useEffect, useState } from "react";

export const ECRAS = [
  "inicio",
  "como-funciona",
  "haste",
  "stent",
  "scaffold",
  "gibson",
  "fichas",
  "triagem",
  "doente",
  "comparar",
  "simulacao",
  "historico",
  "filtros",
  "porque",
  "definicoes",
  "sobre",
] as const;

export type Ecra = (typeof ECRAS)[number];

/** Ecrã que o endereço indica ("#/stent" dá "stent"); um endereço vazio ou desconhecido dá o Início. */
export function ecraDoHash(hash: string): Ecra {
  const nome = hash.replace(/^#\/?/, "").split(/[/?]/)[0].toLowerCase();
  return (ECRAS as readonly string[]).includes(nome) ? (nome as Ecra) : "inicio";
}

/** Endereço de um ecrã ("stent" dá "#/stent"). */
export function hashDoEcra(ecra: Ecra): string {
  return `#/${ecra}`;
}

/** Hook: ecrã atual guardado no endereço; mudar de ecrã acrescenta uma entrada ao histórico do navegador. */
export function useEcra(): [Ecra, (e: Ecra) => void] {
  const [ecra, setEcra] = useState<Ecra>(() => (typeof location === "undefined" ? "inicio" : ecraDoHash(location.hash)));

  useEffect(() => {
    const aoVoltar = () => setEcra(ecraDoHash(location.hash));
    window.addEventListener("popstate", aoVoltar);
    window.addEventListener("hashchange", aoVoltar);
    return () => {
      window.removeEventListener("popstate", aoVoltar);
      window.removeEventListener("hashchange", aoVoltar);
    };
  }, []);

  const ir = useCallback((e: Ecra) => {
    setEcra(e);
    try {
      if (location.hash !== hashDoEcra(e)) history.pushState(null, "", hashDoEcra(e));
    } catch {
      // sem histórico (ambiente de testes ou janela sem endereço): fica só o estado
    }
  }, []);

  return [ecra, ir];
}
