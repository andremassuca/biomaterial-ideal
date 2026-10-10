# 8. Extensões exploratórias

Este capítulo junta cinco extensões feitas depois da análise principal. Nenhuma muda os rankings dos capítulos 4 a 7; servem para mostrar a escala da triagem, ajustar a decisão ao doente e ver, com mecânica e com fluidos, o que os critérios mais pesados querem dizer para o corpo. Todas são exploratórias: modelos simplificados, com as hipóteses escritas e verificadas contra soluções conhecidas.

## 8.1 Triagem em larga escala

A base verificada (31 materiais no total, de 5 a 8 por componente) é o fim de um funil, não o ponto de partida. A triagem começou nos dados abertos do Materials Project (Jain et al. 2013; versão de 28 de setembro de 2026, licença CC BY 4.0), com 271 325 compostos. As propriedades do Materials Project são calculadas (teoria do funcional da densidade) e serviram só para filtrar, nunca para decidir.

Os filtros foram aplicados por esta ordem:

- elementos: dos 118 elementos, saíram os radioativos, os da classe 1 da ICH Q3D(R2) (ICH 2022) e os do grupo 1 da IARC; ficaram 212 176 compostos;
- estabilidade termodinâmica: 124 394;
- densidade dentro do limite de desenho: 123 427;
- com dados elásticos calculados: 6 800;
- módulo de Young dentro do intervalo de interesse: 6 479.

Em paralelo, as 73 normas ASTM de materiais para implantes deram as ligas e os polímeros com uso clínico. A passagem dos 6 479 compostos para os 31 materiais da base verificada não é automática: exige processamento, forma do dispositivo e evidência clínica, que não existem nos dados calculados. É também por isso que a base é pequena: cada valor tem fonte e estado.

<!-- figura: funil -->

## 8.2 Perfis de doente e filtros de requisito

A decisão dos capítulos 4 a 7 é para um doente "médio". Para a ajustar, a base de regras em data/perfis_doente.csv tem 44 regras, cada uma com a condição, o efeito, o mecanismo, a fonte e o estado (16 verificadas na fonte, 26 regras do trabalho e 2 por verificar). Os efeitos são de cinco tipos: peso multiplicado e renormalizado (29 regras), nota sem efeito no ranking (9), exclusão (3), mudança da leitura do problema (2) e um critério acrescentado (o teor de níquel no stent). As condições incluem idade, nível de atividade, osteoporose, índice de massa corporal, diabetes, tabagismo, alergias ao níquel, ao cobalto e ao titânio, doença periodontal, bruxismo e o tipo de defeito ósseo. As exclusões por alergia exigem alergia confirmada por teste; a suspeita dá só uma nota a recomendar o teste.

Dois exemplos mostram o efeito:

- num doente jovem e muito ativo, o peso da resistência à fadiga sobe e o Co-Cr-Mo passa a 1.º com o TOPSIS, embora o Ti-6Al-4V ELI continue em 1.º com o WASPAS e o VIKOR;
- num doente com alergia ao níquel, o teor de níquel entra como critério de custo e o Pt-Cr fica em 1.º com os três métodos (no caso de base, o WASPAS preferia o L605).

Três requisitos entram como filtros e não como critérios com peso, para não mudar os rankings do relatório: compatibilidade com a ressonância magnética (não ferromagnético, ASTM F2503), avaliação biológica segundo a ISO 10993-1 e compatibilidade com o método de esterilização (ISO 11135, ISO 11137 e ISO 17665). Nenhum material da base é ferromagnético, e a ISO 10993-1 não exclui nenhum (assinala os que ainda são de investigação). A esterilização é o filtro que mais pesa: impor vapor retira os polímeros sensíveis ao calor. No stent (cenário B), saem o Mg WE43 e o PLLA e o vencedor passa do L605 ao Pt-Cr com o TOPSIS e o VIKOR, uma inversão de ranking ao sair materiais que não ganhavam; no scaffold, saem os polímeros (PCL e o compósito PCL/β-TCP; no cenário B também o PLLA e o PLGA) e passam a ganhar o β-TCP poroso e o vidro bioativo 45S5. O óxido de etileno e a radiação gama não mudam nenhum vencedor.

## 8.3 Simulação da haste por elementos finitos

Um dos critérios com mais peso na haste é o módulo de Young com alvo no osso cortical (0,20, a seguir ao limite de fadiga, com 0,25; secção 4.2). Para ver o efeito desse critério no osso, simulou-se a haste dentro de um fémur e mediu-se a energia de deformação no osso proximal, nas zonas de Gruen 1 e 7 (Gruen et al. 1979), em relação ao fémur intacto. Uma razão baixa quer dizer que o osso deixa de receber carga (*stress shielding*) e tende a perder massa.

O caso principal foi resolvido com ferramentas gratuitas em Python (gmsh, scikit-fem e pyamg), num fémur anatómico (BodyParts3D) com osso cortical (17,5 GPa) e trabecular (0,39 GPa; Li et al. 2014) e uma haste Corail de tamanho 8, colocada por planeamento. A carga é o pico da marcha: força na anca de 238 % do peso corporal (Bergmann et al. 2001), com a direção e os abdutores do caso de carga de Heller et al. 2005, com as componentes lidas numa reprodução da tabela original (Baharuddin et al. 2014, Tabela 3), para um peso de desenho de 75 kg. A interface é colada e a diáfise fica fixa. Compararam-se quatro hastes: aço 316L, Co-Cr-Mo, Ti-6Al-4V ELI e Ti-6Al-4V poroso com 17 GPa (valor de desenho, igual ao alvo do módulo).

Verificações:

- solução analítica: uma barra de Ti-6Al-4V à compressão e à flexão bate com a teoria das vigas com erro abaixo de 2 %;
- equilíbrio: as reações igualam as cargas (erro abaixo de 10⁻⁶ %);
- convergência: quatro malhas de 2,0 a 0,75 mm; a razão em Gruen 1 e 7 varia no máximo 1,9 % entre as duas mais finas;
- segunda ferramenta: o mesmo problema no SOLIDWORKS Simulation, num fémur simplificado, dá a mesma ordem dos materiais;
- ordem de grandeza: as deformações na cortical são cerca de duas vezes os picos calculados por elementos finitos com o conjunto completo de músculos por Edwards et al. 2016, o que se explica por o fémur estar preso só na diáfise e só com os abdutores; Speirs et al. 2007 descrevem o mesmo efeito com estas condições de fronteira, que é igual para todas as hastes.

Resultados (energia no osso face ao fémur intacto, Gruen 1 e Gruen 7; Python e SOLIDWORKS): Co-Cr-Mo 0,53 e 0,12 (0,53 e 0,25); aço 316L 0,54 e 0,13 (0,53 e 0,27); Ti-6Al-4V ELI 0,61 e 0,22 (0,63 e 0,44); Ti-6Al-4V poroso 0,96 e 1,01 (1,31 e 1,41). Junto ao colo (Gruen 7), as hastes de Co-Cr-Mo e de aço deixam ao osso cerca de um oitavo da energia do fémur intacto, a de Ti-6Al-4V cerca de um quinto e a porosa praticamente toda. Com o trabecular a 2,44 GPa (sensibilidade), a ordem não muda.

<!-- figura: fea/sed_corte_coronal -->

## 8.4 Simulação do escoamento no stent

O critério com mais peso no stent é a espessura dos struts (secção 5.2). Para ver o seu efeito no escoamento, simulou-se o sangue a passar numa artéria coronária com o stent, com struts finos (Pt-Cr, 79 µm) e grossos (316L, 135 µm), os valores típicos da base. A grandeza é a tensão de corte na parede: abaixo de 0,4 Pa, o endotélio passa a um fenótipo aterogénico (Malek et al. 1999), e as zonas de corte baixo entre os struts associam-se à hiperplasia da neoíntima (LaDisa et al. 2005). Estudos de CFD e experimentais mostram mais recirculação com struts mais espessos (Jiménez e Davies 2009; Kolandaivelu et al. 2011).

O modelo foi resolvido com o OpenFOAM (gratuito). É um setor de 22,5° de um segmento reto de artéria coronária com 3,0 mm, com planos de simetria nos lados, e o stent em losangos (oito células à volta, struts a 45° do eixo, 90 µm de largura nos dois). O sangue é newtoniano, com 1060 kg/m³ e 3,5 mPa·s (Boldock et al. 2022; newtoniano acima de cerca de 100 s⁻¹, Thondapu et al. 2022). O caudal pulsa como no doente 1 de Chodzyński et al. 2015 (descendente anterior proximal: velocidade média no eixo de 18,6 cm/s, entre 3,7 e 32,9 cm/s, ciclo de 1,06 s), com o pico na diástole (Davies et al. 2006). A parede é rígida, o stent está totalmente encostado e o padrão é periódico; a espessura do strut é do dispositivo, não do material.

Verificações:

- solução analítica: num tubo sem stent, com a mesma malha, o escoamento de Poiseuille bate com a teoria (perfil de velocidade com erro máximo de 1,5 %, tensão de corte na parede com 0,24 % e queda de pressão com 0,44 %);
- convergência da malha: com o caudal médio, três malhas (células de 28, 20 e 14 µm junto à parede); a área com corte baixo varia no máximo 1,5 % entre a malha média e a fina;
- passo de tempo: com o dobro dos passos por ciclo, a área com corte baixo muda @@CFD_PASSO@@ pontos percentuais;
- repetição entre ciclos: o segundo ciclo repete o primeiro com diferença máxima de 0,0 %; as médias são do segundo ciclo.

Resultados (Tabela [n]): com os struts finos de Pt-Cr, 47 % da parede entre os struts fica com a tensão de corte média no ciclo (TAWSS) abaixo de 0,4 Pa; com os struts grossos de 316L, 82 %. A TAWSS média na parede é de 0,41 Pa com o Pt-Cr e 0,23 Pa com o 316L (num tubo sem stent seria cerca de 0,87 Pa, a solução de Poiseuille com o caudal médio). O índice de corte oscilatório médio é de 0,001 com o Pt-Cr e 0,009 com o 316L. As zonas de corte baixo ficam logo a jusante de cada strut, onde o escoamento descola e recircula, e crescem com a altura do strut.

| Stent | Espessura do strut (µm) | TAWSS média (Pa) | Parede abaixo de 0,4 Pa | OSI médio |
|---|---|---|---|---|
| Pt-Cr | 79 | 0,41 | 47 % | 0,001 |
| 316L | 135 | 0,23 | 82 % | 0,009 |

Table: Resultados da simulação do escoamento no stent (fluxo pulsátil, médias no segundo ciclo, parede da artéria entre os struts).

<!-- figura: cfd/tawss_mapas -->

## 8.5 Massa da haste e iões metálicos

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
- níquel: todas as ligas permanentes do stent têm níquel (9 % no Pt-Cr a 35 % no MP35N); a alergia ao níquel afeta cerca de 8 a 19 % dos adultos na Europa (Ahlström et al. 2019), e em doentes com stents de 316L a alergia ao níquel e ao molibdénio foi associada à reestenose (Köster et al. 2000), o que justifica o perfil de doente da secção 8.2.

Com pares metal-polietileno, os níveis de cobalto e crómio são mais baixos do que com metal-metal (Engh et al. 2014); na haste, o que conta é a corrosão nas junções.

## 8.6 Síntese

As duas simulações confirmam, com física, o sentido dos dois critérios mais pesados. Na haste, quanto mais rígida a liga, menos carga chega ao osso junto ao colo, e só a rigidez próxima da do osso (titânio poroso) mantém o osso a trabalhar; é o que o critério-alvo do módulo traduz. No stent, struts mais grossos deixam mais parede com o sangue a passar devagar; é o que o critério de custo da espessura traduz. A massa da haste é desprezável para o corpo, e os iões ficam como argumento qualitativo (cobalto e crómio no par articular, níquel no stent). Nenhuma das extensões substitui os ensaios pré-clínicos indicados na questão 10 de cada caso.
