# 8. Extensões exploratórias

Este capítulo junta cinco extensões feitas depois da análise principal. Nenhuma muda os rankings dos capítulos 4 a 7; servem para mostrar a escala da triagem, ajustar a decisão ao doente e ver, com mecânica e com fluidos, o que os critérios mais pesados querem dizer para o corpo. Todas são exploratórias: modelos simplificados, com as hipóteses escritas, verificadas contra soluções conhecidas e, nas simulações, entre ferramentas (verificação numérica cruzada); nenhuma foi validada experimentalmente. Cada secção abre com uma caixa curta: contexto de uso, verificação feita e o que não demonstra.

## 8.1 Triagem em larga escala

> **Contexto de uso:** mostrar a escala da triagem e de onde vêm os candidatos; os dados calculados servem para filtrar, nunca para decidir.
>
> **Verificação feita:** as contagens do funil são geradas por um script a partir dos dados abertos do Materials Project (versão de 28 de setembro de 2026).
>
> **O que não demonstra:** que os 6 479 compostos sejam biomateriais viáveis: as propriedades são calculadas, sem processamento, forma do dispositivo nem evidência clínica.

A base verificada (31 entradas no total, de 5 a 8 por componente; no par articular, as 5 entradas são combinações de dois materiais, cabeça e acetábulo, e não materiais únicos) é o fim de um funil, não o ponto de partida. A triagem começou nos dados abertos do Materials Project (Jain et al. 2013; versão de 28 de setembro de 2026, licença CC BY 4.0), com 271 325 compostos. As propriedades do Materials Project são calculadas (teoria do funcional da densidade) e serviram só para filtrar, nunca para decidir.

Os filtros foram aplicados por esta ordem:

- elementos: dos 118 elementos, saíram os radioativos, os da classe 1 da ICH Q3D(R2) (As, Cd, Hg e Pb; ICH 2022) e o berílio; o níquel e o crómio ficaram, porque só alguns dos seus compostos (compostos de níquel, crómio(VI)) são do grupo 1 (IARC 1990) e a sua avaliação faz-se na liga; ficaram 212 176 compostos;
- estabilidade termodinâmica: 124 394;
- densidade dentro do limite de desenho: 123 427;
- com dados elásticos calculados: 6 800;
- módulo de Young dentro do intervalo de interesse: 6 479.

Em paralelo, as 73 normas ASTM de materiais para implantes deram as ligas e os polímeros com uso clínico. A passagem dos 6 479 compostos para os 31 materiais da base verificada não é automática: exige processamento, forma do dispositivo e evidência clínica, que não existem nos dados calculados. É também por isso que a base é pequena: cada valor tem fonte e estado.

<!-- figura: funil -->

## 8.2 Perfis de doente e filtros de requisito

> **Contexto de uso:** ver como as prioridades de um doente mudam a ordem, como análise de sensibilidade.
>
> **Verificação feita:** cada regra tem condição, efeito, mecanismo, fonte e estado; os efeitos no ranking são testados automaticamente.
>
> **O que não demonstra:** uma recomendação para doentes reais: 26 das 44 regras são regras do trabalho e os fatores (×2) são valores de desenho. Este trabalho não é uma ferramenta clínica nem uma recomendação terapêutica.

A decisão dos capítulos 4 a 7 é para um doente "médio". Para a ajustar, a base de regras de perfis de doente (anexo digital) tem 44 regras, cada uma com a condição, o efeito, o mecanismo, a fonte e o estado (16 verificadas na fonte, 26 regras do trabalho e 2 por verificar). Os efeitos são de cinco tipos: peso multiplicado e renormalizado (29 regras), nota sem efeito no ranking (9), exclusão (3), mudança da leitura do problema (2) e um critério acrescentado (o teor de níquel no stent). As condições incluem idade, nível de atividade, osteoporose, índice de massa corporal, diabetes, tabagismo, alergias ao níquel, ao cobalto e ao titânio, doença periodontal, bruxismo e o tipo de defeito ósseo. As exclusões por alergia exigem alergia confirmada por teste; a suspeita dá só uma nota a recomendar o teste.

Dois exemplos mostram o efeito:

- num doente jovem e muito ativo, como sensibilidade ao fator do perfil e não como recomendação: o peso da resistência à fadiga sobe e o Co-Cr-Mo passa a 1.º com o TOPSIS, embora o Ti-6Al-4V ELI continue em 1.º com o WASPAS e o VIKOR; este resultado não corresponde à prática (no jovem ativo usa-se haste não cimentada de titânio) e mostra a sensibilidade ao fator 2, que é um valor de desenho;
- num doente com alergia ao níquel, o teor de níquel entra como critério de custo e o Pt-Cr, a liga com menos níquel (cerca de 9 %, contra 9-11 % no L605 e 33-37 % no MP35N), fica em 1.º com os três métodos (no caso de base, o WASPAS preferia o L605), por uma diferença sem significado clínico conhecido. Nenhuma liga permanente candidata é isenta de níquel; em alergia confirmada, a decisão é clínica, e a relevância da alergia em stents é debatida (secção 5.5, questão 3).

As regras da haste têm também notas sem efeito no ranking. No idoso com osteoporose, a decisão principal na prática é o modo de fixação (cimentada ou não cimentada), antes do material: o modelo compara materiais de hastes não cimentadas, e numa haste cimentada polida o material é aço ou Co-Cr e o critério do módulo deixa de ser o determinante. Os fatores de 2 aplicados aos pesos são valores de desenho, não medidos.

Três requisitos entram como filtros e não como critérios com peso, para não mudar os rankings do relatório: compatibilidade com a ressonância magnética (não ferromagnético, ASTM F2503), avaliação biológica segundo a ISO 10993-1 e compatibilidade com o método de esterilização (ISO 11135, ISO 11137 e ISO 17665). Nenhum material da base foi classificado como ferromagnético neste filtro, e a ISO 10993-1 não exclui nenhum (assinala os que ainda são de investigação). A esterilização é o filtro que mais pesa: impor vapor retira os polímeros sensíveis ao calor. No stent (cenário B), saem o Mg WE43 e o PLLA e o vencedor passa do L605 ao Pt-Cr com o TOPSIS e o VIKOR, uma inversão de ranking ao sair materiais que não ganhavam (é um teste da normalização, sem significado clínico, porque os stents com eluição de fármaco não se esterilizam por vapor); no scaffold, saem os polímeros (PCL e o compósito PCL/β-TCP; no cenário B também o PLLA e o PLGA) e passam a ganhar o β-TCP poroso e o vidro bioativo 45S5. O óxido de etileno e a radiação gama não mudam nenhum vencedor.

## 8.3 Simulação da haste por elementos finitos

> **Contexto de uso:** interpretar o critério-alvo do módulo, comparando materiais pela energia de deformação no osso, um indicador mecânico de redistribuição de carga.
>
> **Verificação feita:** solução analítica, equilíbrio, convergência da malha e verificação numérica cruzada com o SOLIDWORKS Simulation e o Ansys Mechanical APDL.
>
> **O que não demonstra:** perda óssea, descolamento nem micromovimento (interface colada, um só instante da marcha, osso isotrópico, sem remodelação); não houve validação experimental.

Um dos critérios com mais peso na haste é o módulo de Young com alvo no osso cortical (0,20, a seguir à resistência à fadiga, com 0,25; secção 4.2). Para ver o efeito desse critério no osso, simulou-se a haste dentro de um fémur e mediu-se a energia de deformação no osso proximal, nas zonas de Gruen 1 e 7 (Gruen et al. 1979), em relação ao fémur intacto. A razão é um indicador mecânico de redistribuição de carga: uma razão baixa quer dizer que o osso recebe menos estímulo mecânico (*stress shielding*); não é uma previsão de perda óssea nem de descolamento, porque a simulação não modela a remodelação. As zonas de Gruen, definidas na radiografia, foram traduzidas para 3D pelo plano da haste e por terços do comprimento implantado; a zona 1 contém a inserção dos abdutores, por isso a zona 7 (calcar) é o indicador mais informativo.

O caso principal foi resolvido com ferramentas gratuitas em Python (gmsh, scikit-fem e pyamg), num fémur anatómico (BodyParts3D) com osso cortical (17,5 GPa) e trabecular (0,39 GPa; Li et al. 2014) e uma haste Corail de tamanho 8, colocada por planeamento. A carga é o pico da marcha: força na anca de 238 % do peso corporal (Bergmann et al. 2001), com a direção e os abdutores do caso de carga de Heller et al. 2005, com as componentes lidas numa reprodução da tabela original (Baharuddin et al. 2014, Tabela 3), para um peso de desenho de 75 kg. A interface é colada (não modela micromovimento) e a diáfise fica fixa. Como o modelo é linear, o peso de 75 kg não muda as razões, só os valores absolutos. A interface colada favorece a transferência de carga para o osso proximal; um só instante da marcha, sem subir escadas, e o osso isotrópico com espessura cortical de desenho limitam o resultado a uma comparação entre materiais. Compararam-se quatro hastes: aço 316L, Co-Cr-Mo, Ti-6Al-4V ELI e Ti-6Al-4V poroso com 17 GPa (valor de desenho, igual ao alvo do módulo).

Verificações:

- solução analítica: uma barra de Ti-6Al-4V à compressão e à flexão bate com a teoria das vigas com erro abaixo de 2 %;
- equilíbrio: as reações igualam as cargas (erro abaixo de 10⁻⁶ %);
- convergência: quatro malhas de 2,0 a 0,75 mm; a razão em Gruen 1 e 7 varia no máximo 1,9 % entre as duas mais finas;
- verificação numérica cruzada com uma segunda ferramenta: o mesmo problema no SOLIDWORKS Simulation, num fémur simplificado em que a haste não toca na cortical, dá a mesma ordem dos materiais nas duas zonas; os valores absolutos em Gruen 7 são cerca do dobro (por exemplo 0,25 contra 0,12 no Co-Cr-Mo), o que mostra que o valor da razão depende da geometria e do apoio cortical, e que só a ordem é um resultado robusto;
- ordem de grandeza: as deformações na cortical são cerca de duas vezes os picos calculados por elementos finitos com o conjunto completo de músculos por Edwards et al. 2016, o que se explica por o fémur estar preso só na diáfise e só com os abdutores; Speirs et al. 2007 descrevem o mesmo efeito com estas condições de fronteira, que é igual para todas as hastes.

Resultados (energia no osso face ao fémur intacto, Gruen 1 e Gruen 7; Python e SOLIDWORKS): Co-Cr-Mo 0,53 e 0,12 (0,53 e 0,25); aço 316L 0,54 e 0,13 (0,53 e 0,27); Ti-6Al-4V ELI 0,61 e 0,22 (0,63 e 0,44); Ti-6Al-4V poroso 0,96 e 1,01 (1,31 e 1,41). Junto ao colo (Gruen 7), as hastes de Co-Cr-Mo e de aço deixam ao osso cerca de um oitavo da energia do fémur intacto, a de Ti-6Al-4V cerca de um quinto e a porosa praticamente toda. Com o trabecular a 2,44 GPa (sensibilidade), a ordem não muda; a razão da haste porosa em Gruen 7 sobe para 1,4, como no SOLIDWORKS: uma haste de rigidez igual à do osso, colada, pode pôr no calcar mais carga do que o fémur intacto. Uma razão acima de 1 é efeito do modelo (interface colada), não um ganho.

A razão mede o estímulo mecânico inicial, não a perda óssea nem o descolamento: não se simulou a remodelação. Com a interface colada, o modelo também não mostra o custo de uma haste flexível, que aumenta as tensões e o micromovimento na interface proximal (Huiskes et al. 1992); por isso a haste porosa de 17 GPa é um limite teórico, não uma recomendação. A resistência da haste porosa também não foi avaliada aqui (secção 9.8).

<!-- figura: fea/sed_corte_coronal -->

## 8.4 Simulação do escoamento no stent

> **Contexto de uso:** interpretar o critério da espessura do strut; o resultado é da espessura, não da liga.
>
> **Verificação feita:** escoamento de Poiseuille analítico, convergência da malha, passo de tempo, repetição entre ciclos e verificação numérica cruzada com o Ansys Fluent (escoamento estacionário).
>
> **O que não demonstra:** reestenose nem trombose: geometria idealizada, sem lesão, parede rígida e sangue newtoniano; 0,4 Pa é um limiar operacional deste estudo; não houve validação experimental.

O critério com mais peso no stent é a espessura dos struts (secção 5.2). Para ver o seu efeito no escoamento, simulou-se o sangue a passar numa artéria coronária com o stent, com struts de 79 µm (DES atual, valor típico do Pt-Cr na base) e de 135 µm (1.ª geração, valor típico do 316L). O resultado é da espessura e não da liga: a decisão do stent é entre o Pt-Cr e o L605, e a simulação compara um strut atual com um de 1.ª geração. A grandeza é a tensão de corte na parede: tensões de corte baixas favorecem um fenótipo aterogénico do endotélio (Malek et al. 1999), e as zonas de corte baixo entre os struts associam-se à hiperplasia da neoíntima (LaDisa et al. 2005). Estudos de CFD e experimentais mostram mais recirculação com struts mais espessos (Jiménez e Davies 2009; Kolandaivelu et al. 2011).

O modelo foi resolvido com o OpenFOAM (gratuito). É um setor de 22,5° de um segmento reto e idealizado de artéria coronária com 3,0 mm, sem lesão, com planos de simetria nos lados, e o stent em losangos (oito células à volta, struts a 45° do eixo, 90 µm de largura nos dois). O sangue é newtoniano, com 1060 kg/m³ e 3,5 mPa·s (Boldock et al. 2022). A hipótese é válida acima de cerca de 100 a 200 s⁻¹ (Thondapu et al. 2022); as zonas de corte baixo entre os struts ficam abaixo desta gama (0,4 Pa com 3,5 mPa·s corresponde a cerca de 114 s⁻¹), e um modelo não newtoniano daria tensões mais altas nessas zonas e uma área de corte baixo menor (Thondapu et al. 2022). A comparação entre as duas espessuras é mais fiável do que os valores absolutos. O caudal pulsa como no doente 1 de Chodzyński et al. 2015 (descendente anterior proximal: velocidade média no eixo de 18,6 cm/s, entre 3,7 e 32,9 cm/s, ciclo de 1,06 s), com o pico na diástole (Davies et al. 2006). A parede é rígida, o stent está totalmente encostado e o padrão é periódico; os planos de simetria laterais não representam as pontes de um stent real; a espessura do strut é do dispositivo, não do material.

Verificações:

- solução analítica: num tubo sem stent, com a mesma malha, o escoamento de Poiseuille bate com a teoria (perfil de velocidade com erro máximo de 1,5 %, tensão de corte na parede com 0,24 % e queda de pressão com 0,44 %);
- convergência da malha: com o caudal médio, três malhas (células de 28, 20 e 14 µm junto à parede); a área com corte baixo varia no máximo 1,5 % entre a malha média e a fina; as diferenças não diminuem com a malha (os cantos dos struts são vivos), mas são muito menores do que a diferença entre as duas espessuras (35 pontos percentuais);
- passo de tempo: com o dobro dos passos por ciclo, a área com corte baixo muda @@CFD_PASSO@@ pontos percentuais;
- repetição entre ciclos: o segundo ciclo repete o primeiro com diferença máxima de 0,0 %, porque o escoamento fica periódico logo no primeiro ciclo (o domínio é curto e a entrada é imposta); as médias são do segundo ciclo.

Resultados (Tabela [n]), com o limiar de 0,4 Pa (limiar operacional deste estudo; o efeito de o mudar vem a seguir): com os struts de 79 µm, 47 % da parede entre os struts fica com a tensão de corte média no ciclo (TAWSS) abaixo de 0,4 Pa; com os de 135 µm, 82 %. A TAWSS média na parede é de 0,41 Pa com o strut de 79 µm e 0,23 Pa com o de 135 µm (num tubo sem stent seria cerca de 0,87 Pa, a solução de Poiseuille com o caudal médio). O índice de corte oscilatório (OSI) médio é de 0,001 com o strut de 79 µm e 0,009 com o de 135 µm; com uma onda de um só harmónico, sem inversão do caudal, o OSI fica quase nulo por construção, e a TAWSS no ciclo é praticamente igual à do escoamento estacionário com o caudal médio (0,408 contra 0,410 Pa com o strut de 79 µm). As zonas de corte baixo ficam dos dois lados de cada strut, sobretudo a jusante, onde o escoamento descola e recircula, e nos cantos das células, e crescem com a altura do strut.

| Strut | Espessura do strut (µm) | TAWSS média (Pa) | Parede abaixo de 0,4 Pa | OSI médio |
|---|---|---|---|---|
| DES atual (típico do Pt-Cr) | 79 | 0,41 | 47 % | 0,001 |
| 1.ª geração (típico do 316L) | 135 | 0,23 | 82 % | 0,009 |

Table: Resultados da simulação do escoamento no stent (fluxo pulsátil, médias no segundo ciclo, parede da artéria entre os struts): efeito da espessura do strut.

A fração depende do limiar: com 0,3 Pa seria 35 % contra 67 %, com 0,5 Pa 59 % contra 94 % e com 0,6 Pa 73 % contra 97 %; a partir de cerca de 0,8 Pa, quase toda a parede entre os struts fica abaixo do limiar nas duas espessuras (98 % e 99 %), porque a parede sem stent está a 0,87 Pa. A medida menos dependente do limiar é a TAWSS média relativa à do tubo sem stent: 0,47 com o strut de 79 µm e 0,27 com o de 135 µm. A espessura atua também pela lesão da parede e pelo tempo de cobertura endotelial, que o modelo não representa; a evidência clínica do efeito da espessura é o ensaio ISAR-STEREO (Kastrati et al. 2001).

<!-- figura: cfd/tawss_mapas -->

## 8.5 Massa da haste e iões metálicos

> **Contexto de uso:** ver se a massa da haste importa para o corpo e enquadrar os iões metálicos de forma qualitativa.
>
> **Verificação feita:** massa a partir do volume do modelo e das densidades da base; ordem de grandeza comparada com o movimento do centro de massa na marcha (Orendurff et al. 2004).
>
> **O que não demonstra:** a libertação de iões pela haste nem os seus efeitos biológicos: não há modelo de corrosão.

A massa da haste (Tabela [n+1]) foi calculada a partir do volume do modelo (23,8 cm³, Corail tamanho 8) e das densidades da base. A forma é a mesma em todas as ligas, por isso o centro de massa da haste também é o mesmo; muda só a massa.

| Material da haste | Densidade (g/cm³) | Massa (g) |
|---|---|---|
| Co-Cr-Mo forjado | 8,28 | 197 |
| Aço inox 316L | 8,00 | 190 |
| Ti-35Nb-7Zr-5Ta (TNZT) | 5,70 | 136 |
| Ti-13Nb-13Zr | 5,00 | 119 |
| Ti cp grau 4 | 4,51 | 107 |
| Ti-6Al-4V ELI | 4,43 | 105 |

Table: Massa da haste Corail de tamanho 8 com cada liga (volume do modelo e densidades típicas da base).

A diferença entre a haste mais pesada e a mais leve é de 92 g. Num corpo de 75 kg, e com a haste a menos de 0,5 m do centro de massa do corpo, trocar uma pela outra desloca o centro de massa no máximo 0,6 mm. É desprezável: na marcha, o próprio centro de massa sobe e desce 2,7 a 4,8 cm e oscila 3,9 a 7,0 cm para os lados a cada passo (Orendurff et al. 2004). Além disso, a haste substitui osso retirado; numa prótese total não cimentada, o ganho de massa mediano medido foi de 145 g (Marmor et al. 2023). O material importa pela rigidez (secção 8.3), não pela massa.

Os iões metálicos contam mais do que a massa:

- cobalto: a toxicidade sistémica (miocardiopatia, hipotiroidismo, perda de audição e de visão) é rara e surge com concentrações muito altas no sangue, sobretudo depois de revisões de cerâmicas partidas com componentes de cobalto e no desgaste de pares metal-metal (Bradberry et al. 2014); no Reino Unido, cobalto ou crómio a partir de 7 µg/L no sangue pede seguimento apertado, sem um limiar que obrigue à revisão (MHRA 2017), e um consenso europeu põe o limiar de preocupação entre 2 e 7 µg/L (Hannemann et al. 2013); o cobalto metálico é provavelmente carcinogénico (grupo 2A; Karagas et al. 2022);
- crómio: o crómio(VI) é carcinogénico (grupo 1) e o crómio(III) não é classificável (IARC 1990);
- níquel: todas as ligas permanentes do stent têm níquel (9 % no Pt-Cr a 35 % no MP35N); a alergia ao níquel afeta cerca de 8 a 19 % dos adultos na Europa (Ahlström et al. 2019), e em doentes com stents de 316L a alergia ao níquel e ao molibdénio foi associada à reestenose (Köster et al. 2000), mas outros estudos não encontram relação (Norgaz et al. 2005), pelo que o perfil de doente da secção 8.2 é exploratório.

Com pares metal-polietileno, os níveis de cobalto e crómio são mais baixos do que com metal-metal (Engh et al. 2014); na haste, o que conta é a corrosão nas junções.

## 8.6 Síntese

Como verificação numérica cruzada, e não como validação experimental, a análise estrutural da haste foi repetida no Ansys Mechanical APDL com a geometria do SOLIDWORKS, os mesmos materiais e as mesmas cargas: as razões de energia nas zonas de Gruen 1 e 7 e o deslocamento máximo ficaram a 2,3 % ou menos dos do SOLIDWORKS. O escoamento no stent (escoamento estacionário) foi repetido no Ansys Fluent com a mesma malha e condições: a área da parede abaixo de 0,4 Pa ficou a 1,1 pontos percentuais ou menos da do OpenFOAM (Pt-Cr 45,8 % contra 46,2 %; 316L 79,8 % contra 80,9 %). Em ambos os casos, a ordem dos materiais não muda.

As duas simulações ilustram, com modelos físicos simplificados, o mecanismo por trás dos dois critérios mais pesados; não são uma confirmação independente, porque, com tudo o resto igual, um strut mais alto dá necessariamente mais recirculação e uma haste mais rígida deixa menos carga no osso. Na haste, quanto mais rígida a liga, menos carga chega ao osso junto ao colo, e só a rigidez próxima da do osso (titânio poroso) mantém o osso a trabalhar; é o que o critério-alvo do módulo traduz. No stent, struts mais grossos deixam mais parede com o sangue a passar devagar; é o que o critério de custo da espessura traduz. A massa da haste é desprezável para o corpo, e os iões ficam como argumento qualitativo (cobalto e crómio no par articular, níquel no stent). Nenhuma das extensões substitui os ensaios pré-clínicos indicados na questão 10 de cada caso.
