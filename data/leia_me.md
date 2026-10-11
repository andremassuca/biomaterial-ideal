# LEIA-ME da base de dados

Fonte de verdade: os ficheiros CSV em data/ (materiais, criterios, tecido, cenarios, parametros,
problemas_criticos)
e este ficheiro (texto da folha LEIA-ME). O base_dados_biomateriais.xlsx é gerado por
scripts/exportar_xlsx.py e não se edita à mão.

## Estado dos valores
- Os valores começaram como pontos de partida de manuais e revisões, marcados "A verificar"; cada valor confirmado na fonte passou a um dos estados "Verificado" (ver a Legenda). O número atual de valores verificados conta-se na coluna estado de materiais.csv (estados que começam por "Verificado").
- Antes de usar um valor no relatório ou no poster: abre a fonte, confirma o número, preenche a coluna doi_url e muda o estado para "Verificado".
- Se a fonte der outro valor, usa o da fonte e regista a página ou tabela na coluna notas.

## Alterações v0.3 (após revisão crítica)
Densidade deixa de ser proxy de radiopacidade (nova escala de radiopacidade) · σy/E renomeado "proxy material" · Nitinol fora do ranking · K_IC retirado do par articular · "Resistência" retirada da matriz dentária (tração ≠ flexão) · alvos do scaffold passam a cenários · nova folha Cenarios

Par articular e implante dentário ficam SEMIQUANTITATIVOS (ordinais > 50 % do peso): MCDM quantitativo só para haste, stent (balão) e scaffold.

## Alterações v0.4 (28 set 2026)
- Os CSV passam a ser a fonte de verdade; o .xlsx é gerado só com valores (sem fórmulas).
- Novas colunas em materiais.csv: doi_url (a preencher) e valor_texto (propriedades categóricas).
- Nova propriedade "Tipo de expansão" do stent (balão ou autoexpansível), usada na triagem.
- Índices derivados calculados em src/biomat_mcdm/indices.py (σy/E do stent; E_implante/E_osso da haste).
- Cenários em cenarios.csv; η em parametros.csv.

## Alterações v0.5 (1 out 2026): 2.ª ronda do stent
- Valores de fichas de fornecedor no 316L (alongamento), no L605 (cedência, módulo, tração) e no MP35N (tração), com o valor anterior na nota.
- L605: o típico é o da chapa (Haynes), por não haver ficha de tubo com valores; a fita (Matthey) dá o intervalo.
- Pt-Cr: cedência (480 MPa), módulo, tração e alongamento ficam "A verificar" (a cedência só foi lida no resumo de O'Brien 2010; estado mudado a 11 out 2026), com fontes secundárias na nota. Precisa de acesso: O'Brien BJ, Stinson JS, Larsen SR, Eppihimer MJ, Carroll WM. A platinum-chromium steel for cardiovascular stents. Biomaterials 2010;31:3755-3761 (doi:10.1016/j.biomaterials.2010.01.146), Tabelas 4 e 6; sem acesso aberto legítimo a 11 out 2026 (Unpaywall, Europe PMC, Semantic Scholar).
- Radiopacidade: rubrica escrita (ver "Rubricas ordinais"), fontes nas 7 linhas e estado "Verificado"; as notas não mudam.
- Densidades do 316L, L605, MP35N e Pt-Cr com fonte. A densidade não é critério do stent.

## Alterações v0.6 (1 out 2026): 1.ª ronda do scaffold
- Rubrica da bioatividade reescrita segundo a classificação de Hench (classes A e B); as notas dos materiais não mudam.
- Regra da porosidade para as propriedades mecânicas dos scaffolds (ver "Cuidados").
- 11 linhas do scaffold com fonte primária: porosidade do quitosano/HA, do PLLA e do β-TCP; resistência à compressão da HA; e sete notas ordinais (imprimibilidade, esterilização e bioatividade).
- A esterilização da HA continua "A verificar".

## Alterações v0.7 (1 out 2026): 2.ª ronda do scaffold
- Regra do típico: típico = mediana das fontes dentro da janela de porosidade (porosidade típica do material ±10 pontos percentuais); o intervalo vai do mínimo ao máximo dessas fontes.
- β-TCP: resistência 0,35-7,72 MPa, típico 2. PCL/β-TCP: porosidade típica 70 % (especificação dos scaffolds por FDM).
- HA: tempo de degradação tratado como não reabsorvível (mínimo 42 meses; máximo e típico = pior valor observado nos outros materiais, como a opção O2 do stent).
- PLLA definido como scaffold impresso; degradação 24-60 meses, com dados de PLLA maciço.
- Vidro 45S5: resistência 0,2-1,1 MPa e degradação 6-24 meses (dados de partículas). O módulo fica sem fonte primária.
- Quitosano/HA: módulo e resistência cerca de dez vezes abaixo dos valores anteriores.
- Porosidades do PCL, do PLGA e da HA com fonte.

## Alterações v0.8 (2 out 2026): regra da forma revista (stent)
- Regra da forma: nas propriedades dependentes da forma do produto, min, max e tipico cobrem só a forma usada no dispositivo (no stent: tubo ou fita); os valores de outras formas (fio, barra, chapa) ficam só na coluna notas. Se a forma do dispositivo tiver um único valor, min = max e o Monte Carlo aplica ±10 % (incerteza_valor_unico em parametros.csv).
- Linhas revistas: L605 módulo 225 (antes 225-243), tração 900-1000 (antes 900-1138), alongamento 40 (antes 40-50); MP35N tração 965 (antes 931-965), alongamento 40 (antes 40-70). Sem alteração: 316L alongamento 40-50 e L605 cedência 380-700. Os típicos não mudaram.
- Exceção mantida no L605: o típico da cedência e da tração é o da chapa (Haynes), por não haver ficha de tubo com valores; fica dentro do intervalo da fita (Matthey).

## Alterações v0.9 (3 out 2026): problemas críticos do professor
- Novo problemas_criticos.csv: para cada caso, os critérios que respondem ao problema crítico indicado pelo professor (2 out 2026), com ligação direta ou indireta e justificação. Folha Problemas_criticos no .xlsx.
- Novo parâmetro fator_foco_problema = 2 (valor de desenho) e novo cenário P-foco: peso dos critérios de ligação direta x2, restantes renormalizados; sensibilidade com direta + indireta; no par articular, só como sensibilidade semiquantitativa.
- Implante dentário: a corrosão passa a critério na v0.10.

## Alterações v0.10 (3 out 2026): implante dentário centrado na osteointegração e na corrosão
- Novo critério "Resistência à corrosão em meio oral (ordinal 1-5)", de benefício, peso 0,15 (problema crítico do docente); para lhe dar peso: estética 0,15 → 0,10, módulo 0,20 → 0,15 e a densidade deixa de ser critério do dentário (a propriedade fica na base).
- Corrosão: Ti grau 4 = 3, Ti-6Al-4V ELI = 3, Ti-Zr = 3 (4 como sensibilidade), Y-TZP = 4, PEEK = 5.
- Osteointegração com fontes e rubrica nova; Ti-6Al-4V ELI 4 → 2 (sem estudos clínicos dedicados no corpo do implante dentário).
- Estado "Verificado" com a nota "só resumo; nota segundo a rubrica do leia_me" (decisão do André).
- Peso ordinal do dentário: 0,70 (antes 0,60); o caso continua SEMIQUANTITATIVO: ranking e P-foco só como indicação (results/semiquantitativos.csv).

## Alterações v0.11 (10 out 2026): revisão por especialistas (frente DADOS)
- Implante dentário: módulo do Ti-6Al-4V ELI (101-110, típico 105,5 GPa) e do Ti cp grau 4 (104,1 GPa) iguais aos valores verificados da haste (Li et al. 2014, Tabela 4); antes 110-114 e 103-110 GPa, "A verificar".
- HA do scaffold: a porosidade passa a "A verificar" (o típico e o máximo não têm fonte) e o tempo de degradação ao novo estado "Valor de modelação". Os valores não mudam.
- PLLA do stent: cedência e densidade com "[fonte a indicar]" (a referência anterior não tem estes números). Os valores não mudam.
- Notas: densidade do Ti-Zr (a confirmar), densidade do L605 (porque o típico é o da fita), níveis intermédios das rubricas, natureza dos valores de alongamento do stent.

## Alterações v0.12 (11 out 2026): decisões do André sobre a revisão
- Haste: o critério "Limite de fadiga (10^7 ciclos)" passa a "Resistência à fadiga a 10⁷ ciclos (σmax, R = 0,1)" (materiais, critérios e perfis); os valores não mudam. Nota no Co-Cr-Mo: σmax acima de σ0,2 (tensão máxima a R = 0,1, não limite em amplitude). Ti-13Nb-13Zr e TNZT: modo de ensaio não registado (nota). Rótulo da norma do Co-Cr-Mo mantido, com a diferença anotada na cedência.
- Stent: cedência do 316L continua "A verificar" (nota com o mínimo de 190 MPa da Alleima, mínimo de especificação); L605 com a ressalva do Orsiro (60 e 80 µm) na espessura do strut, valor mantido (XIENCE); MP35N mantém o Resolute Integrity (nota).
- Perfis H-JOV e H-OST: notas sem efeito no ranking (fator 2 como valor de desenho; fixação no idoso com osteoporose).
- Critérios do implante dentário: "Problema crítico do docente (2 out 2026)" passa a "Problema crítico indicado".

## Alterações v0.13 (11 out 2026): verificação nas fontes primárias (stent e scaffold)
- Stent: cedência do Pt-Cr (480 MPa) passa de "Verificado" a "A verificar" (só lida no resumo; precisa de acesso ao O'Brien 2010, Tabelas 4 e 6). Os valores não mudam.
- Compósito PCL/β-TCP, resistência à compressão: 2,2 MPa (Kawai 2018, secção 3.4, cedência a 1 %, 59,5 %), "Verificado"; antes 2,2-6,38, típico 4,3 MPa. O 6,38 MPa (Wong 2025) sai: não é rastreável até uma fonte primária do compósito e não diz que grandeza é.
- Compósito PCL/β-TCP, tempo de degradação: 26 meses (Zhong 2026, Discussão e Figura 7E-F, estimativa por correlação in vitro / in vivo), "Verificado"; antes 12-24, típico 18 meses (Rezwan 2006).
- β-TCP poroso, tempo de degradação: 12,7 meses (5-26) (Hirata 2006, Resultados, 53 doentes), "Verificado"; antes 6-18, típico 12 meses.
- β-TCP poroso, módulo de compressão: 546 MPa (Montelongo 2021, 59,6 %), "Verificado"; antes 100-1000, típico 550 MPa.
- Efeito: no cenário A, o TOPSIS passa a pôr o β-TCP poroso em 1.º (o WASPAS e o VIKOR mantêm o compósito); no cenário B, os três métodos mantêm o compósito.

## Alterações v0.14 (11 out 2026): análises de robustez complementares
- Novo data/dimensoes_criterios.csv (caso, critério, dimensão, nota): mapa de cada critério dos casos quantitativos para uma dimensão (mecânica, biológica, clínica ou económica), usado só na análise de dupla contagem (scripts/robustez_extra.py). É uma escolha de desenho do trabalho, com a justificação na nota; os valores e os pesos da base não mudam.

## Legenda
- min e max alimentam o Monte Carlo (distribuição entre mín. e máx.); nas propriedades dependentes da forma, só com valores da forma do dispositivo (regra da forma, v0.8).
- tipico = valor usado nos métodos; por omissão o ponto médio; pode diferir quando a regra da forma ou outra regra o justifica, com nota.
- Estados da coluna estado:
  - "A verificar": valor de partida (manual, revisão ou fonte secundária) ainda não confirmado na fonte original.
  - "Verificado": valor confirmado na fonte indicada em doi_url (artigo ou norma).
  - "Verificado (fornecedor)": valor confirmado numa página de fornecedor que declara cumprir a norma, não no texto da norma.
  - "Verificado (composição química)": valor que resulta da composição química do material (ex.: 0 % de níquel num polímero sem metais).
  - "Verificado (derivado)": valor calculado a partir de dados da fonte (ex.: razão σFS/σUTS × σUTS), com o cálculo na nota.
  - "Valor de modelação" (10 out 2026): número escolhido por uma regra do trabalho (ex.: tempo de degradação da HA, não reabsorvível, igual ao pior valor observado nos outros materiais, como a opção O2 do stent); a fonte confirma o comportamento (não reabsorve), não o número. Não conta como verificado nem entra na lista "A verificar".
- Teor de níquel (stent): % em massa. No WE43 e no PLLA é 0 % pela composição nominal (decisão de 8 out 2026, ver "Funil de triagem"); o níquel da WE43 só aparece como impureza, até 0,005 %, e fica na nota.

## Tipos de critério (Petković et al., Appl Sci 2025;15:9198)
Estrito = triagem passa/falha · Benefício = maior é melhor · Custo = menor é melhor · Alvo = mais próximo do valor-alvo é melhor

## Rubricas ordinais (1-5): justificar cada nota no relatório com uma referência
- Corrosão: 5 = camada passiva estável sem libertação relevante; 3 = suscetível a picadas/fendas in vivo; 1 = corrosão clinicamente problemática
- Segurança iónica/ALTR: 5 = sem contacto metal-metal; 4 = risco na junção cabeça-cone; 1 = libertação de iões Co/Cr com ALTR documentada
- Osteointegração (implante dentário; revista a 3 out 2026, pelo tipo e duração da evidência clínica do corpo do implante): 5 = coortes com 10 anos ou mais e milhares de implantes, mais meta-análises a 10 anos; 4 = ensaios aleatorizados ou meta-análises com centenas de implantes e pelo menos um estudo a 10 anos; 3 = meta-análises a 1-5 anos ou coortes de 10 anos pequenas e heterogéneas; 2 = uso clínico sem estudos clínicos dedicados (só equivalência em estudos animais); 1 = só evidência pré-clínica. Fontes por material na coluna referencia e em NOTAS_METODOLOGICAS.md.
- Corrosão em meio oral (implante dentário, 3 out 2026): 5 = inerte em meio oral (sem corrosão eletroquímica nem degradação com efeito documentado); 4 = sem corrosão eletroquímica, mas com degradação lenta documentada em meio húmido ou oral (envelhecimento, absorção de água); 3 = metal passivo estável em saliva, atacado só em condições agressivas (fluoreto em meio ácido, tribocorrosão), com libertação de iões ou partículas documentada; 2 = metal atacado em condições orais comuns ou com acoplamento galvânico relevante; 1 = sem filme protetor estável.
- Estética: 5 = cor de dente; 3 = neutro; 2 = sombra cinzenta possível
- Bioatividade (classificação de Hench): 5 = classe A, osteoprodutivo (ex.: vidro 45S5); 4 = classe B, osteocondutor com ligação química ao osso (HA, β-TCP); 3 = osteocondutor sem ligação química, ou compósito com fase bioativa minoritária; 2 = pouca interação; 1 = bioinerte ou sem osteocondução. Fonte: Hench LL. Bioactive ceramics: theory and clinical applications. Bioceramics 1994;7:3-14 (original não lido); classes A e B lidas em Bramhill J, Ross S, Ross G. Int J Environ Res Public Health 2017;14:66, doi:10.3390/ijerph14010066 (revisão, texto completo).
- Imprimibilidade 3D: 5 = extrusão direta fácil; 3 = possível com limitações; 2 = requer técnicas especiais (robocasting, liofilização)
- Compatibilidade com RM: 5 = sem artefacto/aquecimento relevante; 4 = MR-condicional, artefacto pequeno (Ti); 3 = artefacto moderado (CoCr, Pt); 2 = artefacto marcado (aço inox)
- Esterilização: 5 = aceita métodos padrão sem degradação; 4 = requer método específico sem perda de propriedades; 3 = método restrito com risco de degradação; 2 = degradação documentada
- Custo relativo de material e fabrico (NÃO é preço clínico; critério de CUSTO): 1 = matéria-prima e processo maduros, menor complexidade; 2 = processo estabelecido com maior exigência de controlo; 3 = liga/material especializado ou cadeia de fabrico exigente; 4 = material caro, processo complexo, revestimento ou controlo rigoroso; 5 = material crítico, arquitetura complexa ou processo pouco escalável
- Fabricabilidade: 5 = processos industriais maduros (incl. fabrico aditivo); 3 = possível com limitações; 2 = escala laboratorial
- Galvânica cabeça-cone: 5 = sem par metálico; 3 = CoCr em cone de Ti (fretting documentado); 2 = múltiplas interfaces metal-metal
- Radiopacidade (stent): 5 = liga com fração elevada de elemento de Z alto (Pt-Cr); 4 = melhoria clara face ao 316L (L605, com W); 3 = referência dos metais de stent (316L, MP35N); 2 = pouco radiopaco (Nitinol); 1 = radiotransparente, precisa de marcadores (Mg WE43, PLLA). Critério: teor de elementos de Z alto (Pt, Z = 78; W, Z = 74). A densidade não é critério (desde a v0.3), serve só de evidência de apoio. Fontes: Allocco DJ et al. Trials 2010;11:1, doi:10.1186/1745-6215-11-1 (PMC2826324); PMC3692344 ("modest improvement" do CoCr face ao aço).

- Níveis intermédios (2 e 4, quando não estão descritos na rubrica): usam-se quando o material fica entre duas descrições; a justificação de cada nota está na coluna notas ou referencia da linha do material em materiais.csv.

NOTA: índices ordinais só devem pesar ≤ 50 % do total de cada caso: o resto deve vir de propriedades medidas.

## Cuidados
1. Propriedades de scaffolds dependem da porosidade. Regra da porosidade: as propriedades mecânicas de um scaffold usam-se à porosidade típica desse material (±10 pontos percentuais); valores medidos a porosidades muito diferentes ficam de fora ou só alargam o intervalo, com nota. Dentro da janela, típico = mediana das fontes dentro da janela de porosidade (porosidade típica do material ±10 pontos percentuais); o intervalo vai do mínimo ao máximo dessas fontes. Regista sempre a porosidade e o método de fabrico do estudo.
2. Cerâmicos: resistência à flexão ≠ resistência à tração. Assinala sempre qual é.
3. Stents: o Nitinol é autoexpansível (outra classe): eliminado na triagem pela regra "Tipo de expansão"; só na discussão.
4. Alongamento na rotura do stent: as fontes não dão todas o mesmo tipo de valor. No 316L, 40 % é típico (Alleima, coluna "typical"); no L605 e no MP35N, as fichas (Matthey, K-Tube) não dizem se 40 % é típico ou mínimo de especificação; no Pt-Cr, 45 % vem de uma fonte secundária. As diferenças entre ligas (40 contra 45 %) são da ordem da diferença entre mínimo e típico; o critério pesa 0,10 e o Monte Carlo aplica ±10 % aos valores únicos.
5. Cenários (cenarios.csv): A = só materiais clínicos; B = inclui investigação e bioabsorvíveis. No stent, A = só permanentes em uso clínico (316L, L605, MP35N, Pt-Cr); B = A + Mg WE43 e PLLA.

## Níveis de validação
(1) verificação de código = reproduzir Petković et al. 2025; (2) robustez interna = cenários; (3) validação clínica = NÃO demonstrada (trabalho futuro).

## Perfis de doente (perfis_doente.csv)
Uma linha por regra (aprovada a 5 out 2026). Colunas: id, dispositivo, condicao (texto), condicao_codigo (condições
separadas por "; ", todas têm de se verificar), efeito, alvo_do_efeito, valor, justificacao, fonte, doi_url, estado.
- Efeitos: "peso multiplicado" (o peso do critério é multiplicado pelo valor e os pesos voltam a somar 1);
  "critério acrescentado" (o critério entra com o peso do valor e os restantes ficam com 1 menos esse peso, na mesma
  proporção); "leitura do problema" (P-foco com a leitura indicada e fator_foco_problema); "exclusão" (os materiais
  listados, separados por "; ", saem do ranking); "nota" (não altera o ranking; mostra o texto do alvo_do_efeito).
- Várias regras que sobem o mesmo critério: usa-se o maior fator, não o produto.
- Estado: "Verificado" = a fonte liga a condição (ou uma definição próxima, indicada na justificação) ao mecanismo do
  critério; "Regra do trabalho" = a ligação ao critério é do trabalho, mesmo quando o fator de risco tem fonte. O
  valor do fator é sempre de desenho. "A verificar" = a fonte não foi encontrada ou não liga a condição ao
  critério; a regra fica visível mas deve ser lida como provisória.
- 8 out 2026: mais 25 regras (patologias: RM frequente, corticoterapia, insuficiência renal, artrite reumatoide,
  tabagismo, diabetes, radioterapia da cabeça e pescoço, osteoporose, idade avançada, hipertensão, alergia ao
  cobalto e ao titânio); 42 regras no total. Mecanismo e o que cada fonte diz: docs/PATOLOGIAS_NOTAS.md.
- Sem regra para o sexo: os dados demográficos só entram através de um mecanismo (docs/TP2_fisiopatologia_da_falha.md).

## Funil de triagem (data/funil/, 8 out 2026)
Três níveis, gerados por scripts/funil.py (results/funil.md e results/funil.csv):
1. Universo de partida: o resumo do Materials Project (dados abertos no AWS, versão 2026-09-28, licença CC BY 4.0;
   atribuição: Jain A et al. APL Materials 2013;1:011002, doi:10.1063/1.4812323), os 118 elementos
   (elementos.csv, com a classificação de toxicidade de fontes oficiais) e as normas ASTM de materiais para implantes
   (normas.csv, com a norma como fonte).
2. Filtros automáticos sobre o Materials Project (filtros.csv; os limites são valores de desenho): elementos
   excluídos (radioativos, classe 1 da ICH Q3D, grupo 1 da IARC como elemento), estabilidade, densidade e módulo de
   Young (calculado a partir de K e G, E = 9KG/(3K + G)).
3. A base verificada (materiais.csv), onde se faz o MCDM.
Cuidados: as propriedades do Materials Project são calculadas (DFT) e só servem para filtrar; nenhum valor do Materials
Project entra no MCDM. O Materials Project só tem fases cristalinas ordenadas (as ligas como o Ti-6Al-4V e os polímeros
não estão lá); por isso o nível 3 não sai automaticamente do nível 2: junta os materiais com norma ou uso clínico e
propriedades confirmadas em fontes. Não se copiam dados do MatWeb nem do ASM (termos de uso); podem ser citados como
fontes de consulta.
- Níquel (decisão de 8 out 2026): 0 % no PLLA e na liga de Mg WE43, pela composição nominal (o níquel da WE43 só
  aparece como impureza, até 0,005 %). Num critério de custo com mínimo 0, o WASPAS usa a eq. 11 de Petković et al.
  com o alvo T = 0 (r = 1 - x / máx), porque a eq. 10 (mín / x) fica indefinida; o perfil de alergia ao níquel passa
  a funcionar no cenário B. Nenhum critério dos casos de base tem mínimo 0, por isso os rankings do relatório não
  mudam (confirmado: results/pontuacoes.csv igual).
- H1 (jovem ativo) e H3 (IMC 38) dão o mesmo ranking: as duas regras sobem só a resistência à fadiga com fator 2, porque
  ambas significam mais carga cíclica (decisão de 8 out 2026: fica assim; a aplicação explica-o).

## Filtros de requisito (filtros_material.csv, 8 out 2026)
Uma linha por material: ferromagnetico (sim, não ou A verificar; fonte_rm), vapor, oxido_etileno e radiacao_gama
(compatível, com restrições, incompatível ou A verificar; fonte_esterilizacao), notas e estado (Verificado quando os
quatro campos têm fonte, Parcial quando só alguns têm, A verificar quando nenhum tem). Decisão de 8 out 2026: a
ISO 10993-1, a RM (ASTM F2503) e a esterilização entram como filtros e no texto, não como critérios com peso, para não
mudar os rankings do relatório; a esterilização tem também um cenário de sensibilidade (método imposto; saem os
incompatíveis). Resultado em results/filtros.md (src/biomat_mcdm/filtros.py, chamado pelo run_all.py). Cuidados: a
compatibilidade dos metais com vapor e gama assenta numa frase genérica (Yu et al. 2026) e nenhuma liga foi testada em
particular; o óxido de etileno ficou A verificar nos metais; o "incompatível" da WE43 com vapor vem de um só provete
(Becerra 2021); o 316L encruado pode ter magnetização fraca [confirmar].
