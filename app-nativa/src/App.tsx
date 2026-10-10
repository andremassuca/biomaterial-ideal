// Estrutura da aplicação: barra lateral com os ecrãs, barra superior com o botão sol/lua e o conteúdo.
import { useState, type ComponentType } from "react";
import { AnimatePresence, motion } from "framer-motion";
import {
  Bone,
  BookOpenText,
  Database,
  Filter,
  FlaskConical,
  HeartPulse,
  Home,
  Info,
  Layers,
  Moon,
  Settings,
  Sun,
  UserRound,
  Waves,
} from "lucide-react";
import { ProvedorDicas } from "@/componentes/ui/controlos";
import { useDefinicoes } from "@/lib/definicoes";
import { modoNucleo } from "@/lib/nucleo";
import { cn } from "@/lib/utils";
import { BaseTriagem } from "@/ecras/BaseTriagem";
import { Caso } from "@/ecras/Caso";
import { Definicoes } from "@/ecras/Definicoes";
import { Doente } from "@/ecras/Doente";
import { Fichas } from "@/ecras/Fichas";
import { Filtros } from "@/ecras/Filtros";
import { GibsonAshby } from "@/ecras/GibsonAshby";
import { Inicio } from "@/ecras/Inicio";
import { Porque } from "@/ecras/Porque";
import { Sobre } from "@/ecras/Sobre";

export type Ecra =
  | "inicio"
  | "haste"
  | "stent"
  | "scaffold"
  | "gibson"
  | "fichas"
  | "triagem"
  | "doente"
  | "filtros"
  | "porque"
  | "definicoes"
  | "sobre";

const MENU: { ecra: Ecra; texto: string; Icone: ComponentType<{ className?: string }>; grupo?: string }[] = [
  { ecra: "inicio", texto: "Início", Icone: Home },
  { ecra: "haste", texto: "Haste femoral", Icone: Bone, grupo: "Casos" },
  { ecra: "stent", texto: "Stent", Icone: HeartPulse, grupo: "Casos" },
  { ecra: "scaffold", texto: "Scaffold ósseo", Icone: Layers, grupo: "Casos" },
  { ecra: "gibson", texto: "Gibson e Ashby", Icone: Waves, grupo: "Explorar" },
  { ecra: "fichas", texto: "Fichas dos materiais", Icone: FlaskConical, grupo: "Explorar" },
  { ecra: "triagem", texto: "Base de triagem", Icone: Database, grupo: "Explorar" },
  { ecra: "doente", texto: "Doente", Icone: UserRound, grupo: "Explorar" },
  { ecra: "filtros", texto: "Filtros", Icone: Filter, grupo: "Explorar" },
  { ecra: "porque", texto: "Porquê", Icone: BookOpenText, grupo: "Explorar" },
  { ecra: "definicoes", texto: "Definições", Icone: Settings, grupo: "Aplicação" },
  { ecra: "sobre", texto: "Sobre", Icone: Info, grupo: "Aplicação" },
];

export default function App() {
  const [ecra, setEcra] = useState<Ecra>("inicio");
  const { escuro, apresentacao, definir } = useDefinicoes();
  const compacta = apresentacao;

  return (
    <ProvedorDicas>
      <div className="flex h-screen overflow-hidden bg-fundo text-texto">
        <nav
          aria-label="Ecrãs"
          // no telemóvel (abaixo de md) a barra fica só com os ícones, para o conteúdo caber nos 390 px
          className={cn("flex shrink-0 flex-col border-r border-linha bg-superficie", compacta ? "w-[72px]" : "w-14 md:w-60")}
        >
          <div className={cn("flex items-center gap-2 py-5", compacta ? "justify-center px-0" : "justify-center px-0 md:justify-start md:px-4")}>
            <span aria-hidden className="h-7 w-7 shrink-0 rounded-md bg-acento" />
            {!compacta && <span className="hidden text-lg font-bold leading-tight text-acento md:inline">Biomaterial Ideal</span>}
          </div>
          <ul className="flex-1 space-y-0.5 overflow-y-auto px-1.5 pb-4 md:px-2">
            {MENU.map((m, k) => (
              <li key={m.ecra}>
                {!compacta && m.grupo && m.grupo !== MENU[k - 1]?.grupo && (
                  <div className="hidden px-3 pb-1 pt-4 text-[0.7rem] font-bold uppercase tracking-wider text-texto2 md:block">{m.grupo}</div>
                )}
                <button
                  type="button"
                  onClick={() => setEcra(m.ecra)}
                  aria-current={ecra === m.ecra ? "page" : undefined}
                  aria-label={m.texto}
                  title={m.texto}
                  className={cn(
                    "flex w-full items-center gap-3 rounded-md py-2 text-sm",
                    compacta ? "justify-center px-0" : "justify-center px-0 md:justify-start md:px-3",
                    ecra === m.ecra ? "bg-acento/10 font-bold text-acento-texto" : "text-texto2 hover:bg-superficie2 hover:text-texto",
                  )}
                >
                  <m.Icone className="h-[18px] w-[18px] shrink-0" />
                  {!compacta && <span className="hidden md:inline">{m.texto}</span>}
                </button>
              </li>
            ))}
          </ul>
        </nav>

        <div className="flex min-w-0 flex-1 flex-col">
          <header className="flex h-14 shrink-0 items-center justify-end gap-3 border-b border-linha bg-superficie px-4 md:px-6">
            {modoNucleo() === "topsis" && (
              <span className="rounded-sm bg-aviso/15 px-2 py-0.5 text-xs font-medium text-aviso">Modo navegador: só o TOPSIS</span>
            )}
            <button
              type="button"
              onClick={() => definir({ tema: escuro ? "claro" : "escuro" })}
              className="flex h-9 w-9 items-center justify-center rounded-md text-texto2 hover:bg-superficie2 hover:text-texto"
              aria-label={escuro ? "Mudar para o tema claro" : "Mudar para o tema escuro"}
              title={escuro ? "Tema claro" : "Tema escuro"}
            >
              {escuro ? <Sun className="h-5 w-5" /> : <Moon className="h-5 w-5" />}
            </button>
          </header>

          <main className="min-h-0 flex-1 overflow-y-auto">
            <AnimatePresence mode="wait">
              <motion.div
                key={ecra}
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -8 }}
                transition={{ duration: 0.22 }}
                className="mx-auto max-w-[1400px] px-4 py-6 md:px-6 lg:px-8"
              >
                {ecra === "inicio" && <Inicio irPara={setEcra} />}
                {ecra === "haste" && <Caso key="Haste" id="Haste" />}
                {ecra === "stent" && <Caso key="Stent" id="Stent" />}
                {ecra === "scaffold" && <Caso key="Scaffold" id="Scaffold" />}
                {ecra === "gibson" && <GibsonAshby />}
                {ecra === "fichas" && <Fichas />}
                {ecra === "triagem" && <BaseTriagem />}
                {ecra === "doente" && <Doente />}
                {ecra === "filtros" && <Filtros />}
                {ecra === "porque" && <Porque />}
                {ecra === "definicoes" && <Definicoes />}
                {ecra === "sobre" && <Sobre />}
              </motion.div>
            </AnimatePresence>
          </main>
        </div>
      </div>
    </ProvedorDicas>
  );
}
