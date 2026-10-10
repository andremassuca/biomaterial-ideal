// Ponte para o núcleo Rust. Na aplicação nativa usa os comandos Tauri; na versão web usa o mesmo núcleo compilado
// para WebAssembly (crates/mcdm-wasm, gerado em src/wasm por `npm run wasm`). Sem o WebAssembly (por exemplo,
// `npm run dev` antes de o gerar) só o TOPSIS funciona, com o port em topsis.ts; o resto devolve um erro claro.
import { invoke, isTauri } from "@tauri-apps/api/core";
import { listen } from "@tauri-apps/api/event";
import { CASOS, type IdCaso } from "./dados";
import { excluirMateriais, posicoes, renormalizar, topsisPassos } from "./topsis";
import type { Perfil, RespostaCaso, RespostaDoente, ResumoMonteCarlo } from "./tipos";

/** Verdadeiro dentro da aplicação nativa. */
export function emTauri(): boolean {
  try {
    return isTauri();
  } catch {
    return false;
  }
}

interface ModuloWasm {
  avaliar_caso(pedido: string): string;
  avaliar_doente(pedido: string): string;
  monte_carlo_web(pedido: string): string;
}

// O módulo só existe depois de `npm run wasm`; import.meta.glob não falha se o ficheiro não existir.
const carregadores = import.meta.glob("../wasm/mcdm_wasm.js") as Record<string, () => Promise<{ default: () => Promise<unknown> } & ModuloWasm>>;
let wasm: ModuloWasm | null = null;
const wasmPronto: Promise<ModuloWasm | null> = (async () => {
  if (emTauri()) return null;
  const carregar = Object.values(carregadores)[0];
  if (!carregar) return null;
  try {
    const m = await carregar();
    await m.default();
    wasm = m;
    return m;
  } catch {
    return null;
  }
})();

/** "nativo" (Tauri), "web" (núcleo em WebAssembly) ou "topsis" (só o port TypeScript do TOPSIS). */
export function modoNucleo(): "nativo" | "web" | "topsis" {
  if (emTauri()) return "nativo";
  return wasm ? "web" : "topsis";
}

/** Espera pelo carregamento do WebAssembly (a interface chama-a uma vez ao arrancar). */
export async function prepararNucleo(): Promise<void> {
  await wasmPronto;
}

export class SemNucleo extends Error {
  constructor(o_que: string) {
    super(`${o_que} precisa do núcleo de cálculo (aplicação nativa ou versão web com WebAssembly). Aqui só o TOPSIS está disponível.`);
    this.name = "SemNucleo";
  }
}

export interface PedidoCaso {
  caso: IdCaso;
  cenario: string;
  pesos?: number[];
  eta?: number;
  excluir?: string[];
}

/** Ranking de um caso com os três métodos e o consenso de Borda. */
export async function avaliarCaso(pedido: PedidoCaso): Promise<RespostaCaso> {
  if (emTauri()) {
    return invoke<RespostaCaso>("avaliar_caso", {
      pedido: { ...pedido, excluir: pedido.excluir ?? [], pesos: pedido.pesos ?? null, eta: pedido.eta ?? null },
    });
  }
  const w = await wasmPronto;
  if (w) {
    return JSON.parse(
      w.avaliar_caso(JSON.stringify({ ...pedido, excluir: pedido.excluir ?? [], pesos: pedido.pesos ?? null, eta: pedido.eta ?? null })),
    ) as RespostaCaso;
  }
  if (pedido.eta !== undefined && pedido.eta < 1) throw new SemNucleo("O nível de confiança η");
  return topsisNoNavegador(pedido);
}

/** Modo navegador: só o TOPSIS (as outras listas ficam vazias e a interface explica porquê). */
function topsisNoNavegador(pedido: PedidoCaso): RespostaCaso {
  const base = CASOS[pedido.caso].cenarios[pedido.cenario];
  if (!base) throw new Error(`cenário desconhecido: ${pedido.cenario}`);
  let problema = { ...base, pesos: pedido.pesos ? renormalizar(pedido.pesos) : base.pesos };
  let excluidos: string[] = [];
  if (pedido.excluir && pedido.excluir.length > 0) {
    const r = excluirMateriais(problema, pedido.excluir);
    problema = r.problema;
    excluidos = r.saem;
  }
  const { c } = topsisPassos(problema.x_tipico, problema.pesos, problema.tipos, problema.alvos);
  return {
    problema,
    excluidos,
    apenasTopsis: true,
    ranking: {
      alternativas: problema.alternativas,
      c_topsis: c,
      pos_topsis: posicoes(c, true),
      q_waspas: [],
      s_vikor: [],
      r_vikor: [],
      p_vikor: [],
      pos_waspas: [],
      pos_vikor: [],
      pontos_borda: [],
      pos_borda: [],
    },
  };
}

/** Caso de base e resultado com os dados do doente (regras de data/perfis_doente.csv). */
export async function avaliarDoente(caso: IdCaso, cenario: string, perfil: Perfil): Promise<RespostaDoente> {
  if (!emTauri()) {
    const w = await wasmPronto;
    if (!w) throw new SemNucleo("O perfil de doente");
    return JSON.parse(w.avaliar_doente(JSON.stringify({ caso, cenario, perfil }))) as RespostaDoente;
  }
  return invoke<RespostaDoente>("avaliar_doente", { pedido: { caso, cenario, perfil } });
}

export interface PedidoMonteCarlo extends PedidoCaso {
  nIter: number;
  variar: "propriedades" | "pesos";
  spread?: number;
}

/** Monte Carlo com progresso; `aoProgredir(feitas, total)` é chamado cerca de 100 vezes. */
export async function monteCarlo(
  pedido: PedidoMonteCarlo,
  aoProgredir: (feitas: number, total: number) => void,
): Promise<ResumoMonteCarlo> {
  if (!emTauri()) {
    const w = await wasmPronto;
    if (!w) throw new SemNucleo("O Monte Carlo");
    // no navegador corre de uma vez (sem progresso intermédio nem paragem)
    aoProgredir(0, pedido.nIter);
    const r = JSON.parse(
      w.monte_carlo_web(
        JSON.stringify({
          caso: pedido.caso,
          cenario: pedido.cenario,
          pesos: pedido.pesos ?? null,
          eta: pedido.eta ?? null,
          excluir: pedido.excluir ?? [],
          n_iter: pedido.nIter,
          variar: pedido.variar,
          spread: pedido.spread ?? null,
        }),
      ),
    ) as ResumoMonteCarlo;
    aoProgredir(r.feitas, r.pedidas);
    return r;
  }
  const deixar = await listen<{ feitas: number; total: number }>("mc-progresso", (e) =>
    aoProgredir(e.payload.feitas, e.payload.total),
  );
  try {
    return await invoke<ResumoMonteCarlo>("monte_carlo", {
      pedido: {
        caso: pedido.caso,
        cenario: pedido.cenario,
        pesos: pedido.pesos ?? null,
        eta: pedido.eta ?? null,
        excluir: pedido.excluir ?? [],
        n_iter: pedido.nIter,
        variar: pedido.variar,
        spread: pedido.spread ?? null,
      },
    });
  } finally {
    deixar();
  }
}

/** Pede ao núcleo para parar o Monte Carlo em curso. */
export async function pararMonteCarlo(): Promise<void> {
  if (emTauri()) await invoke("parar_monte_carlo");
}

/** Mensagem de erro legível (os comandos Rust devolvem texto). */
export function mensagemErro(e: unknown): string {
  if (typeof e === "string") return e;
  if (e instanceof Error) return e.message;
  return "erro desconhecido";
}
