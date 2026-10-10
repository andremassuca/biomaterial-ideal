# Especificação da aplicação nativa "Biomaterial Ideal"

Documento de referência para as maquetes (Fase A), o protótipo (Fase B), a aplicação completa (Fase C) e o
acabamento (Fase D). A aplicação é só nativa (Tauri: Windows e Android); a aplicação Streamlit saiu do
repositório a 5 out 2026 e não há versão web. Sem números escritos à mão: os dados vêm de
scripts/exportar_app_json.py.

## Plataforma e prioridades
- Tauri 2 em app-nativa/: núcleo em Rust (crate mcdm: TOPSIS, WASPAS e VIKOR com critérios-alvo, Borda,
  pesos objetivos e η, Monte Carlo das propriedades e dos pesos, perfis de doente); interface React e TypeScript
  (Vite), shadcn/ui (Radix + Tailwind), gráficos com visx ou Recharts no estilo de design/biomat.mplstyle,
  Framer Motion e React Three Fiber com os modelos glTF de scripts/renders_blender.py; português.
- Prioridade: 1) Windows (.msi e .exe), 2) Android (.apk assinado para instalação direta). Sem versão web nem
  página de descarga web. Sem assinatura de código por agora.
- Distribuição: repositório público só de distribuição (biomaterial-ideal), sem código, com as releases do instalador e uma página simples; o código QR do poster aponta para ele (decisão de 5 out; ainda não criado). O repositório do código (biomat-mcdm) continua privado.

## Ecrãs
1. Início, com o espectro de confiança.
2. Doente (perfis de doente; ver abaixo).
3. Caso, com o ranking animado e os pesos ajustáveis.
4. Porquê este vencedor.
5. Robustez, com Monte Carlo em direto (barra de progresso e "parar").
6. Fichas dos materiais.
7. Gibson e Ashby.
8. Definições.
9. Sobre (versão 1.0.0, autor, Universidade Lusófona, Faculdade de Engenharia, UC; aviso fixo).

## Perfis de doente
- Fonte de verdade: data/perfis_doente.csv (uma linha por regra, com fonte, DOI e estado) e
  src/biomat_mcdm/perfis.py (com testes); casos de referência em results/perfis_referencia.csv
  (H1 jovem ativo, H2 idosa com osteoporose, H3 IMC 38, S1 alergia ao níquel, D1 gengiva fina, D2 bruxismo).
- Tabela aprovada a 5 out (17 regras): efeitos peso multiplicado e renormalizado, critério acrescentado (níquel no
  stent), leitura do problema (scaffold), exclusão (titânio só com alergia confirmada por teste) e nota (suspeita de
  alergia ao titânio sem teste: "recomenda-se teste de alergia"). Regras que sobem o mesmo critério: o maior fator.
  Sem regra para o sexo. Regras de aplicação em data/leia_me.md.
- Rust e TypeScript reimplementam o mesmo e são testados contra results/perfis_referencia.csv.
- Fluxo em passos: dispositivo; dados gerais (idade, sexo, IMC, atividade, tabagismo, diabetes, alergias);
  dados específicos do dispositivo; problema prioritário; resultado com os três métodos, o consenso, a lista
  "o que mudou face ao caso de base" (cada alteração com a fonte, que se abre ao tocar) e a comparação lado a
  lado com o caso de base. Perfis de exemplo num toque.
- Nada é guardado nem enviado; nenhum campo de identificação.
- Aviso fixo no resultado e no Sobre: "Ferramenta educativa de exploração de critérios. Não é um dispositivo
  médico e não substitui a decisão clínica."

## Tema
- Claro e escuro, desenhados com o mesmo cuidado; as maquetes mostram cada ecrã nas duas versões.
- Botão sol/lua sempre visível na barra superior; nas Definições, Sistema / Claro / Escuro, guardado entre
  sessões. Transição de 200 ms, sem piscar.
- Cores só por variáveis de tema: fundo, superfície, texto, texto secundário, linhas, acento.
- Azul da FE (regra de 5 out, igual no poster, na apresentação e na aplicação): #0477A8 em todo o texto azul
  pequeno (abaixo de 24 px; no poster, abaixo de 18 pt), com 5,0:1 em branco; #0595D1 nos títulos grandes, nos
  elementos gráficos e nos gráficos (3,4:1 em branco). No escuro, #4FB8EA para texto (7,8:1 sobre #0b1b2e).
- Gráficos: Okabe e Ito com variantes para fundo escuro (mesma cor de base por material nos dois temas,
  ajustada em luminância; ex.: o azul #0072B2 tem só 3,4:1 sobre #0b1b2e); eixos e grelhas com as cores do tema.
- Ilustrações SVG com currentColor; logótipo da Lusófona na versão branca no tema escuro.
- Teste automático de contraste AA nos dois temas.

## Definições
- Tema (Sistema / Claro / Escuro).
- Modo apresentação: letra e gráficos maiores, interface simplificada, para projetar.
- Tamanho da letra: normal, grande, muito grande.
- Movimento: completo ou reduzido; por omissão, o do sistema.
- Idioma: português. Inglês preparado na estrutura (textos em ficheiros de tradução), só ativado a pedido.

## Exportar
- Botão "Exportar" no resultado de um caso e de um perfil de doente: PNG e PDF com o ranking dos três métodos,
  o consenso, as alterações do perfil e o aviso "Ferramenta educativa; não é um dispositivo médico", sempre no
  tema claro (para imprimir).

## Qualidade (Fase D)
- Ícone em todas as resoluções (com ícone adaptativo Android) e ecrã de arranque.
- Transições de 200 a 300 ms, reordenação com mola, números a contar; respeita o movimento reduzido.
- Estados de passagem e de toque; valores visíveis nos cursores; "repor" só quando há alterações; dicas para
  TOPSIS, η e critério-alvo; três ecrãs de introdução que se podem saltar.
- Carregamento com esqueleto, erros claros.
- Contraste AA, teclado, leitores de ecrã, letra escalável.
- Arranque em menos de 1 s; 10 000 iterações de Monte Carlo em menos de 1 s (Rust); 60 fps.
- Testes Playwright sem erros na consola.

## Fases e paragens
- A: maquetes HTML. Arquivadas a 6 out (design/arquivo/maquetes/); não se usam.
- B: protótipo construído diretamente em Tauri 2: primeiro o caso do stent e o fluxo do doente, com o núcleo Rust
  validado (por exemplo, o scaffold em giroide com um deslizador de porosidade que muda o modelo e mostra o módulo
  de Gibson e Ashby). Paragem: a aplicação abre-se para o André testar.
- C: aplicação completa. D: acabamento.
