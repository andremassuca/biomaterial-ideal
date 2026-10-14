# Aplicação nativa "Biomaterial Ideal"

Tauri 2 com interface em React e TypeScript (Vite), Tailwind com componentes Radix no estilo do shadcn/ui,
Recharts, Framer Motion e React Three Fiber. O cálculo é feito pelo núcleo Rust em `crates/mcdm` (TOPSIS,
WASPAS e VIKOR com critérios-alvo, Borda, pesos objetivos e η, Monte Carlo, perfis de doente), testado contra o
Python. Especificação em `docs/ESPECIFICACAO_APP.md`.

Ferramenta educativa de exploração de critérios. Não é um dispositivo médico e não substitui a decisão clínica.

## Estrutura

- `dados/`: JSON gerados por `scripts/exportar_app_json.py` (não se editam à mão).
  - `caso_*.json`: um por caso (problemas dos cenários, regras dos perfis, perfis de exemplo).
  - `app.json`: nomes simples aprovados, fichas dos materiais e do tecido (com fonte e estado), filtros (RM,
    ISO 10993-1, esterilização e o cenário de sensibilidade), espectro de confiança, Monte Carlo do relatório,
    FEA da haste, massa da haste, texto dos iões metálicos e o limiar de empate. Também traz as verificações
    adicionais do relatório v11.1: `cfd_carreau` (sangue de Carreau, de `results/cfd_pulsatil_carreau.json`, gerado por
    `scripts/resumo_cfd_carreau_pulsatil.py`) e `micromovimento` (de `results/micromovimento_haste.json`).
  - `cfd_stent.json`: só aparece quando existir `results/cfd_pulsatil.json`; até lá, o ecrã "Porquê" mostra um
    marcador "Resultados da CFD ainda não disponíveis".
  - `triagem.json`: só aparece quando existir `results/base_triagem.csv` (gerado por `scripts/base_triagem.py`);
    alimenta o ecrã "Base de triagem", com o aviso "triagem, não verificado" (não entra no MCDM).
- `crates/mcdm/`: núcleo de cálculo (com testes).
- `src-tauri/`: aplicação Tauri. `src/lib.rs` tem os comandos `avaliar_caso`, `avaliar_doente`,
  `monte_carlo` (com eventos `mc-progresso` e paragem) e `parar_monte_carlo`. Os JSON dos casos entram no
  executável na compilação (`include_str!`).
- `src/`: interface.
  - `lib/`: tipos, leitura dos dados, ponte para o Rust (`nucleo.ts`), port do TOPSIS para o modo navegador e
    para o exemplo passo a passo (`topsis.ts`), definições, cores (Okabe e Ito) e formatação em português.
  - `componentes/`: ranking animado, espectro de confiança, gráfico do Monte Carlo, visualizador 3D, leitor de
    markdown simples e controlos (`ui/`).
  - `ecras/`: Início, Como funciona (explicação para quem chega pelo QR do poster), Caso (haste, stent, scaffold), Gibson e Ashby, Fichas, Base de triagem, Doente, Filtros, Porquê,
    Definições e Sobre.
  - `estilos/tema.css`: variáveis do tema claro e escuro (só variáveis CSS) e a letra Inter.
- Letra Inter: lida de `design/fontes/` pelo `tema.css` (o Vite junta-a ao build, com caminhos relativos).
- `public/simulacao/videos/`: vídeos MP4 opcionais do ecrã Simulação (`cfd_stent_2ciclo_web.mp4`,
  `fea_haste_4materiais_web.mp4`). A lista é lida quando o Vite arranca (`vite.config.ts`); sem o ficheiro, o bloco
  "Vídeo da simulação" não aparece. Depois de copiar um MP4, reiniciar o `npm run dev` ou voltar a compilar.
- `public/modelos/`: modelos glTF opcionais (`haste.glb`, `stent.glb`, `par.glb`, `dentario.glb`), exportados
  do Blender sem compressão Draco. Sem ficheiro, o visualizador mostra uma forma simplificada com um aviso. A lista
  dos modelos é lida quando o Vite arranca (`vite.config.ts`): depois de acrescentar um `.glb`, reiniciar o
  `npm run dev` ou voltar a compilar. Sem WebGL no navegador, aparece uma nota em vez do modelo.

## Números

Nenhum número dos resultados está escrito à mão na interface: vêm de `dados/`. Depois de mudar `data/` ou
`results/`, correr:

    .venv\Scripts\python.exe scripts\exportar_app_json.py

## Modo navegador

`npm run dev` abre a interface num navegador em http://localhost:1420. Sem o núcleo Rust, só o TOPSIS é
calculado (port em `src/lib/topsis.ts`); WASPAS, VIKOR, Borda, η, Monte Carlo e perfis mostram uma mensagem.

## Compilar (quando houver máquina livre)

Requisitos: Rust estável, Node 20 ou mais recente e, no Windows, o WebView2 (já vem no Windows 11).

1. `npm install --no-audit --no-fund`
2. Ícones (uma vez): `npm run tauri icon caminho\para\icone.png` (PNG quadrado de 1024 px); cria
   `src-tauri/icons/`, que o `tauri.conf.json` espera.
3. Verificar os tipos: `npx tsc --noEmit`
4. Testes do Rust: `cargo test` em `crates/mcdm`, `crates/mcdm-wasm` e `src-tauri`.
5. Desenvolvimento: `npm run tauri dev`
6. Instaladores: `npm run tauri build` (gera `.msi` e `.exe` em `src-tauri/target/release/bundle/`).

Notas: os instaladores pedem `pt-PT` no WiX e `Portuguese` no NSIS; se a versão do Tauri não aceitar estes
idiomas, tirar a secção `bundle.windows` do `tauri.conf.json`. Sem assinatura de código por agora.

## Testes da interface

- `npm test` (vitest): `testes/numeros.test.ts` compara os números da aplicação (núcleo WebAssembly de `src/wasm` e
  JSON de `dados/`) com os CSV e JSON de `results/`; `testes/fumo.test.tsx` monta a aplicação no jsdom, abre todos
  os ecrãs e falha com qualquer erro ou aviso na consola.
- `npm run e2e` (Playwright, Chromium sem interface): depois de `npm run build:web`, serve `dist-web` em
  `http://127.0.0.1:4317/biomaterial-ideal/` (o mesmo subcaminho do GitHub Pages, só local) e testa em 390 × 844 e
  1440 × 900: ecrãs, consola, deslocamento horizontal no telemóvel e números contra `results/`. Na primeira vez:
  `npx playwright install chromium`.
- `npm run video`: grava a demonstração de 60 s (1920 × 1080) sobre a versão web servida localmente e converte-a
  para MP4 com o ffmpeg (`design/video/demo_app_60s.mp4`).
