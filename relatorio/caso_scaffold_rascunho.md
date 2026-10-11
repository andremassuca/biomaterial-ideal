# Caso 4: Scaffold para regeneração óssea

## Problema crítico e resposta

**Problema indicado pelo docente: suporte celular e degradação controlada.**

Os critérios que respondem diretamente ao problema são a porosidade e a bioatividade (suporte celular) e o tempo de degradação (degradação controlada), com 45 % do peso no total. A imprimibilidade e as propriedades mecânicas contribuem de forma indireta.

O resultado depende da leitura do problema e de o defeito suportar ou não carga. Com a leitura literal (só porosidade, bioatividade e degradação, com o peso duplicado), o β-TCP poroso passa a 1.º com o TOPSIS e o VIKOR: é mais bioativo (nota 4, contra 3 do compósito) e reabsorve-se em cerca de 13 meses (Hirata et al. 2006), mais perto do cenário de referência de 9 meses do que o compósito, que se degrada em cerca de 26 meses (Zhong et al. 2026). Com a leitura ampla, que inclui o suporte mecânico enquanto o osso se forma, o compósito PCL/β-TCP impresso fica em 1.º no ranking direto em 5 das 6 combinações de método e cenário; só o TOPSIS do cenário A dá o β-TCP poroso, por uma margem pequena (ΔC = 0,019). A resposta deste caso é a seguinte. Depende da carga: compósito PCL/β-TCP impresso quando o defeito suporta carga (1.º no ranking direto em 5 das 6 combinações); β-TCP poroso quando não suporta (mais vezes 1.º na incerteza dos dados). Propõe-se o compósito como estrutura de contenção do enxerto em defeitos que precisam de algum suporte mecânico enquanto o osso se forma, sempre com fixação interna (Lodewijks et al. 2025). Nenhum scaffold suporta sozinho a carga de um defeito segmentar: a carga passa pela fixação.

## Candidatos e critérios

<!-- incluir: tabelas/scaffold_criterios.md -->

## Resultados

<!-- incluir: tabelas/scaffold_resultados.md -->

## Robustez

<!-- incluir: tabelas/scaffold_robustez.md -->

**Análises complementares (cenário A).** Retirar o vidro 45S5 passa o 1.º do TOPSIS para o compósito; retirar o PCL ou a HA passa o 1.º do VIKOR para o β-TCP poroso. Com pesos iguais dentro das dimensões, os vencedores mantêm-se, mas nas repartições ao acaso mantêm o 1.º só em 31 a 48 % (no TOPSIS, o compósito fica mais vezes em 1.º, 39,9 %). Os valores mais sensíveis são as porosidades (variações de 4 a 8 %) e a resistência à compressão (cerca de 10 %). Confirma que a escolha entre o compósito e o β-TCP depende das prioridades e dos dados.

*Retirar uma alternativa de cada vez.*

<!-- incluir: tabelas/scaffold_retirar.md -->

*Dupla contagem: peso total de cada dimensão fixo e redistribuído dentro dela.*

<!-- incluir: tabelas/scaffold_dimensoes.md -->

*Menor ajuste de um só peso ou de um só valor típico que troca o vencedor.*

<!-- incluir: tabelas/scaffold_ajuste_minimo.md -->

<!-- figura: fig_b_posicoes -->
<!-- figura: fig_c_monte_carlo -->
<!-- figura: fig_d_vencedor_eta -->

## Resposta às questões do enunciado

### 1. Função do dispositivo

Um scaffold ósseo preenche um defeito ósseo demasiado grande para cicatrizar sozinho (defeito de tamanho crítico), por exemplo depois de um trauma, da remoção de um tumor ou de uma infeção. Funciona como uma estrutura temporária: dá suporte às células, permite a entrada de vasos sanguíneos e guia a formação de osso novo. Idealmente, degrada-se à medida que o osso novo o substitui, sem deixar material permanente.

### 2. Propriedades mecânicas necessárias

O scaffold deve aproximar-se do osso trabecular que vai substituir:
- resistência à compressão de cerca de 2 a 12 MPa;
- módulo de compressão de cerca de 50 a 500 MPa.

Estes valores do osso trabecular dependem do local anatómico e da direção de ensaio. No trabalho, estes intervalos foram usados como critérios-alvo (7 MPa e 250 MPa), testados em cenários de sensibilidade com os extremos do intervalo.

Há um compromisso central: a porosidade é necessária para a regeneração, mas quanto mais poroso, mais fraco. Por isso as propriedades mecânicas só se comparam à porosidade típica de cada material (regra da porosidade). Em defeitos que suportam carga, o scaffold não trabalha sozinho e é protegido por fixação metálica.

### 3. Propriedades químicas e físicas relevantes

- **Porosidade e tamanho de poro:** poros interligados, com porosidade elevada, permitem a entrada de células e vasos: considera-se que o tamanho mínimo de poro ronda os 100 µm e recomendam-se poros acima de 300 µm, que favorecem a formação de osso novo e de capilares, embora mais porosidade reduza a resistência mecânica (Karageorgiou e Kaplan 2005). O alvo usado foi 70 %. Além da porosidade total, contam a interligação, a distribuição do tamanho dos poros e a permeabilidade.
- **Velocidade de degradação:** deve acompanhar a formação de osso novo; o alvo usado corresponde a um cenário de referência de 9 meses. Um scaffold que se degrada depressa demais perde o suporte antes do tempo; um que dura demasiado ocupa o espaço do osso novo.
- **Produtos de degradação:** os poliésteres (PLLA, PLGA) libertam produtos ácidos; os fosfatos de cálcio libertam iões de cálcio e fosfato, que o organismo usa; o vidro 45S5 liberta iões de silício, cálcio e sódio e eleva o pH local.
- **Molhabilidade da superfície**, que condiciona a adesão das células.
- **Compatibilidade com a esterilização:** os polímeros de baixo ponto de fusão (PCL, cerca de 60 °C) não suportam autoclave, e a radiação degrada parte das cadeias poliméricas.

### 4. Biocompatibilidade

Além dos ensaios gerais da série ISO 10993, interessa a biocompatibilidade dos produtos de degradação, porque o scaffold vai sendo libertado no tecido ao longo de meses. Os produtos de degradação do PLGA (ácido láctico e ácido glicólico) baixam o pH local, o que pode desencadear uma reação inflamatória; a acidificação pode, por sua vez, acelerar a degradação (Liu et al. 2006). Os fosfatos de cálcio e os vidros bioativos têm composição próxima da fase mineral do osso.

### 5. Bioinerte, bioativo ou biodegradável

O scaffold ideal é **bioativo e biodegradável**. Distinguem-se dois níveis de bioatividade:
- **Classe A, osteoprodutiva:** estimula a formação de osso novo (vidro 45S5).
- **Classe B, osteocondutora com ligação ao osso:** serve de guia ao crescimento do osso (hidroxiapatite, β-TCP).

Os polímeros sintéticos (PCL, PLLA, PLGA) são biodegradáveis mas pouco bioativos. Os compósitos polímero-cerâmico combinam as duas características.

### 6. Riscos de corrosão, desgaste ou degradação

- **Fratura frágil** dos scaffolds cerâmicos porosos, que têm resistência baixa e pouca tenacidade.
- **Perda prematura de suporte**, se a degradação for rápida (PLGA, cerca de 1 a 3 meses).
- **Persistência a longo prazo**, se a degradação for lenta: a hidroxiapatite não foi reabsorvida de forma mensurável em 3,5 anos (Hoogendoorn et al. 1984), e o PLLA maciço persiste vários anos.
- **Inflamação** pelos produtos ácidos de degradação dos poliésteres.
- **Má vascularização no centro** de scaffolds grandes ou pouco interligados.
- **Alteração das propriedades pela esterilização:** no PCL/β-TCP, a radiação por feixe de eletrões tornou a degradação mais rápida (Bruyas et al. 2019).

### 7. Resposta do organismo

Depois da implantação forma-se um hematoma e uma resposta inflamatória inicial, que recruta células mesenquimais. Estas migram para o interior dos poros e diferenciam-se em osteoblastos, que depositam osso novo ao longo das superfícies do scaffold (osteocondução). Os materiais osteoprodutivos, como o vidro 45S5, estimulam ainda essa diferenciação. Com o tempo, o osso novo é remodelado; o scaffold é reabsorvido por osteoclastos (fosfatos de cálcio) ou por hidrólise (polímeros), até ser substituído por osso.

### 8. Vantagem face aos materiais atuais

A referência clínica continua a ser o enxerto ósseo autólogo; os substitutos sintéticos usam-se para o completar ou substituir quando é insuficiente. Propõe-se um **scaffold compósito de PCL com β-TCP, fabricado por impressão 3D**, como estrutura de contenção do enxerto em defeitos que suportam carga, sempre com fixação interna; em defeitos sem carga, o β-TCP poroso. No ranking direto, o compósito ficou em 1.º com o WASPAS e o VIKOR no cenário A e com os três métodos no cenário B (ΔC = 0,016); o TOPSIS do cenário A dá o β-TCP poroso (ΔC = 0,019). Com pesos ±20 %, o compósito fica em 1.º em 98,7 % das iterações com o WASPAS e em 68,0 % com o VIKOR, e o β-TCP em 74,5 % com o TOPSIS. Na incerteza dos dados, o β-TCP fica em 1.º mais vezes com os três métodos (66,9 %, 46,1 % e 54,0 %, contra 7,2 %, 27,5 % e 16,7 % do compósito; TOPSIS, WASPAS e VIKOR). O ranking direto favorece o compósito pela imprimibilidade e pela porosidade e pelo módulo mais perto dos alvos. O Monte Carlo dos dados favorece o β-TCP porque a verificação das fontes primárias (11 out) baixou a resistência do compósito (de 4,3 para 2,2 MPa; Kawai et al. 2018) e alongou a sua degradação (de 18 para 26 meses; Zhong et al. 2026), e porque o intervalo largo da resistência do β-TCP (0,35 a 7,72 MPa) lhe dá muitas repetições com resistência acima da do compósito; as confirmações do β-TCP (reabsorção e módulo) quase não mudam o resultado. A verificação das fontes voltou, assim, a mudar o resultado deste caso.

O resultado já tinha mudado com a primeira verificação dos dados, e a mudança é instrutiva. Com os valores de partida, tirados de revisões, ganhava o β-TCP poroso. À porosidade relevante (cerca de 65 %), porém, a resistência à compressão do β-TCP é de apenas cerca de 2 MPa (mediana de três estudos), e não os 8 MPa de partida. O β-TCP puro tem bioatividade e degradação adequadas, mas é frágil. O PCL é tenaz e fácil de imprimir, mas pouco bioativo e de degradação lenta. O compósito junta as vantagens dos dois: a fase polimérica dá tenacidade e permite controlar a arquitetura dos poros por impressão, e a fase cerâmica dá bioatividade. Já foi usado em séries de casos clínicos em defeitos ósseos segmentares: três casos de defeitos traumáticos muito grandes da tíbia (Lodewijks et al. 2024) e dez doentes com defeitos segmentares pós-traumáticos do fémur ou da tíbia, tratados pela técnica da membrana induzida, com enxerto ósseo autólogo e seguimento de um a quatro anos (Lodewijks et al. 2025). Isto não equivale a uma aprovação regulamentar ampla para todas as formulações e indicações.

Os outros candidatos ficaram atrás por razões claras:
- o vidro 45S5 tem a melhor bioatividade, mas resistência muito baixa como scaffold poroso (cerca de 1 MPa);
- a hidroxiapatite praticamente não se reabsorve;
- o PLGA degrada-se depressa demais;
- o quitosano/HA tem resistência e módulo cerca de duas ordens de grandeza abaixo do osso trabecular.

Uma limitação: o tempo de degradação do compósito, um dos critérios do próprio problema crítico, vem de uma só fonte (26 meses; Zhong et al. 2026), estimado por correlação entre ensaios in vitro e in vivo e válido para filamentos de cerca de 220 µm; o PCL puro degrada-se na base em 24 a 48 meses. Numa sensibilidade com esse intervalo no compósito, o WASPAS e o VIKOR mantêm o compósito em 1.º no cenário A até 36 meses e passam ao β-TCP poroso com 48 meses; o TOPSIS dá o β-TCP em todo o intervalo (ΔC de 0,014 a 0,038). No cenário B, os três métodos mantêm o compósito com 24 meses; com 36 e 48 meses, o TOPSIS passa ao β-TCP e o WASPAS ao PCL, e o VIKOR passa ao β-TCP só com 48 meses.

### 9. Fabrico

- **Compósito PCL/β-TCP:** mistura de PCL fundido com partículas de β-TCP (tipicamente 20 % em massa; Lodewijks et al. 2025), extrudida camada a camada por impressão 3D (deposição de material fundido), com uma arquitetura de filamentos cruzados que define poros interligados (por exemplo, filamentos de 300 µm separados por 1200 µm, com 70 % de porosidade; Sparks et al. 2023). Pode seguir-se um tratamento de superfície para aumentar a molhabilidade, por exemplo com hidróxido de sódio (Kawai et al. 2018).
- **Esterilização:** óxido de etileno ou radiação, sabendo que a radiação por feixe de eletrões acelera a degradação em cerca de 25 % (Bruyas et al. 2019).
- **Outros processos usados nos candidatos:** sinterização de espumas cerâmicas (β-TCP, HA); lixiviação de sal, separação de fases ou liofilização (polímeros e quitosano/HA).

### 10. Testes antes da utilização clínica

- **Biocompatibilidade:** série ISO 10993, incluindo a identificação e quantificação dos produtos de degradação de polímeros (ISO 10993-13:2010, escrita para polímeros não reabsorvíveis, com procedimentos adaptáveis aos reabsorvíveis) e de cerâmicos (ISO 10993-14:2001).
- **Caracterização do scaffold:** guias ASTM para a caracterização de scaffolds (ASTM F2150-19) e para a avaliação da microestrutura de scaffolds poliméricos, incluindo porosidade, tamanho e interligação dos poros (ASTM F2450-18).
- **Degradação in vitro:** ensaio de degradação in vitro de polímeros à base de polilactido, incluindo copolímeros com glicolido (ISO 13781:2017).
- **Ensaios mecânicos:** compressão à porosidade de projeto.
- **Ensaios in vivo:** modelos animais de defeito ósseo de tamanho crítico, como o defeito da calvária em rato, num local sem carga (Spicer et al. 2012), ou os defeitos segmentares da tíbia em animais de grande porte (Reichert et al. 2009).
- **Clínica:** ensaios clínicos com seguimento radiológico da formação de osso.

### 11. Propriedades que caracterizam cada material face à aplicação

<!-- incluir: tabelas/scaffold_propriedades.md -->

As técnicas de caracterização, com o princípio de cada uma, estão na secção 2.11. No compósito proposto, as propriedades a medir são as seguintes.

- **Microtomografia (micro-CT):** porosidade, tamanho e interligação dos poros.
- **Microscopia eletrónica (SEM):** morfologia dos poros e distribuição das partículas cerâmicas.
- **Ensaio de compressão:** resistência e módulo à porosidade de projeto.
- **GPC e DSC:** peso molecular e cristalinidade da fase polimérica.
- **Difração de raios X e FTIR:** fases cristalinas do β-TCP e composição.
- **Termogravimetria (TGA):** teor real de cerâmica no compósito.
- **Ângulo de contacto:** molhabilidade.
- **Degradação in vitro:** perda de massa, peso molecular e pH ao longo do tempo.
- **Ensaio em fluido corporal simulado:** formação de apatite (bioatividade).
- **Cultura de células:** adesão, proliferação e atividade da fosfatase alcalina.
