# FEA da haste femoral em SOLIDWORKS Simulation: hipóteses

Confirmação independente da FEA da haste femoral (o caso principal é o modelo em Python, gmsh e scikit-fem). Aqui
usa-se o SOLIDWORKS 2025 SP2 Premium com o Simulation, conduzido por script (API COM, pywin32):
scripts/fea_solidworks.py. Resultados em results/fea_haste_sw.md e results/fea_haste_sw.json; modelos e estudos em
design/cad/fea/; imagens em results/figures/fea_sw/ (os *_malha.png são o gráfico da malha, "Mesh Quality1", sem escala de tensão; até 13 out 2026 tinham
por engano o nome *_von_mises.png; os *_densidade_energia.png são mapas de densidade de energia de deformação, com a barra
de cores na imagem; os mapas de von Mises vêm do MAPDL, em results/figures/fea_mapdl/).
Cotas do fémur em design/cad/cotas_femur_fea.md.

Comandos (cada um arranca uma instância própria do SolidWorks e fecha-a no fim):

    .venv\Scripts\python.exe scripts\fea_solidworks.py anatomico
    .venv\Scripts\python.exe scripts\fea_solidworks.py tudo --malhas 5,3.5
    .venv\Scripts\python.exe scripts\fea_solidworks.py resumo          (sem SolidWorks)
    .venv\Scripts\python.exe scripts\fea_solidworks.py verificar
    .venv\Scripts\python.exe scripts\fea_solidworks.py sensibilidade

## 1. Geometria: porque se usou o fémur simplificado

Tentativa com o fémur anatómico (BodyParts3D FJ3365, 3102 triângulos, já leve, sem simplificação): o STL, posto
no referencial da haste, importa-se como corpo sólido (importação de malha como sólido; ficou em
design/cad/fea/femur_FJ3365_solido.SLDPRT) e a Simulation malha-o (54 354 elementos a 5 mm, em 42 s;
design/cad/fea/anatomico.json). Não se usou nos estudos porque:

- a malha do BodyParts3D é só a superfície exterior: não tem cortical, trabecular nem canal medular, e criá-los
  exigiria uma superfície interior deslocada da exterior, que não há maneira fiável de gerar num sólido de faces
  triangulares no SolidWorks;
- neste fémur a Corail tamanho 8 deixa só 1,2 mm de folga mínima ao exterior (design/cad/planeamento_haste.csv),
  o que deixaria paredes corticais de cerca de 1 mm;
- o offset anatómico deste fémur (33,4 mm) é diferente do da haste (38,3 mm): o fémur intacto e o implantado
  não teriam o mesmo centro da cabeça, e as cargas não seriam comparáveis.

Fémur simplificado (por script, primitivas no referencial da haste): diáfise tubular cortical com canal medular
vazio; metáfise que alarga até 25 mm de raio; colo cilíndrico a 135°; cabeça esférica com o centro igual ao da
cabeça da haste; bloco do grande trocânter; cortical de 8 mm na diáfise e de 2 a 3 mm na metáfise, no colo e na
cabeça (valores de desenho); osso trabecular por dentro, desde 10 mm abaixo da ponta da haste. A forma exterior
foi medida no FJ3365 (função medir_femur_anatomico). Implantado: corte do colo pelo plano perpendicular ao eixo do
colo da haste que passa na base do colo, parado na fossa trocantérica (o grande trocânter fica), e cavidade com a
forma exata da haste (operação Combinar, subtração). Com o perfil escolhido, a haste fica toda dentro do osso
trabecular, com pelo menos 2 mm de folga (teste test_haste_dentro_do_trabecular_com_folga): não toca na cortical.
Não se modela o pequeno trocânter nem a curvatura anterior do fémur.

## 2. Materiais (elásticos lineares e isotrópicos)

| corpo | E | ν | fonte | estado |
|---|---|---|---|---|
| Osso cortical | 17,6 GPa | 0,3 | Li Y et al. Materials 2014;7:1709, doi:10.3390/ma7031709, Tabela 2 (fémur, compressão; texto completo lido a 8 out 2026). Dentro do intervalo de data/tecido.csv (15 a 20 GPa) | Verificado (E); ν: ver abaixo |
| Osso trabecular | 0,39 GPa | 0,3 | idem, Tabela 3 (fémur, osso esponjoso). Dentro do intervalo de data/tecido.csv (50 a 500 MPa) | Verificado (E); ν: ver abaixo |
| Aço inox 316L | 207,5 GPa | 0,3 | data/materiais.csv, coluna "tipico" (Navarro et al. 2008) | E verificado; ν A verificar |
| Co-Cr-Mo forjado | 225 GPa | 0,3 | data/materiais.csv, coluna "tipico" (Navarro et al. 2008) | E verificado; ν A verificar |
| Ti-6Al-4V ELI | 105,5 GPa | 0,3 | data/materiais.csv, coluna "tipico" (Li et al. 2014) | E verificado; ν A verificar |
| Ti-6Al-4V poroso | 17 GPa | 0,3 | valor de desenho (haste isoelástica hipotética, com o E da cortical) | valor de desenho |

ν = 0,3 para osso e implantes é a hipótese de modelação de Li et al., Int J Surg 2024;110(1):296-305,
doi:10.1097/js9.0000000000000810 (FEA de fémures com a Corail; "A Poisson ratio of 0.3 was assigned to both bones
and implants"). É uma escolha de modelação de outro estudo, não uma medição: A verificar para cada liga (não há
coluna de ν em data/materiais.csv). Os DOI foram confirmados na API da Crossref a 8 out 2026.

## 3. Interface, fixação e cargas

- Interface osso/haste colada (contacto global "colado" da Simulation entre corpos que se tocam), como a cortical e
  a trabecular entre si. Representa uma haste já osteointegrada; não há deslizamento nem descolamento.
- Fixação: encastramento da face distal da cortical, 150 mm abaixo da ponta da haste (cerca de 5 diâmetros da
  diáfise; valor de desenho).
- Peso corporal de desenho: 75 kg (735,75 N).
- Carga da marcha de Heller et al. 2005 (J Biomech 38:1155-1163, doi:10.1016/j.jbiomech.2004.05.022), derivada das
  forças de contacto medidas por Bergmann et al. 2001 (J Biomech 34:859-871, doi:10.1016/S0021-9290(01)00040-9),
  com dois grupos: contacto da anca (-54,0; -32,8; -229,2) % do peso e abdutores (58,0; 4,3; 86,5) % do peso, no
  referencial de Heller (x medial, y anterior, z superior). Os valores foram lidos na reprodução de Baharuddin et
  al., BMC Musculoskelet Disord 2014;15:30, doi:10.1186/1471-2474-15-30, Tabela 3 (em N para 700 N); o artigo
  original de Heller 2005 não foi lido [confirmar]. Verificação: o módulo da força de contacto dá 237,7 % do peso,
  igual aos 238 % do doente médio a andar em Bergmann et al. 2001 (resumo).
- Conversão para o modelo (fémur esquerdo; x lateral, y ao longo da diáfise, z anterior): contacto da anca
  (397,3; -1686,3; -241,3) N e abdutores (-426,7; 636,4; 31,6) N. Hipótese: o eixo z de Heller é tomado como o eixo
  da diáfise do modelo, e os sinais dos eixos x e y seguem a física da carga (a anca empurra a cabeça para lateral
  e para baixo; os abdutores puxam o trocânter para medial e para cima) [confirmar no original].
- Aplicação: cargas remotas da Simulation (transferência direta, acoplamento distribuído) com o ponto de aplicação
  no centro da cabeça (o mesmo no intacto e no implantado), aplicadas à superfície da cabeça do fémur (intacto) ou
  à face cónica do cone 12/14 (implantado; não se modela a cabeça protésica); abdutores no centro da face superior
  do grande trocânter. Omitem-se o tensor da fáscia lata e o vasto lateral do mesmo caso de Heller 2005.

## 4. Malha, solução e medição

- Tetraedros parabólicos (qualidade alta), malhador por omissão da Simulation; dois tamanhos globais (5 e 3,5 mm);
  o malhador refina sozinho junto aos boleados da haste. Solver por omissão (estático linear).
- Limite da malha: a cortical proximal (metáfise e colo) tem 2 a 3 mm (secção 1), por isso a malha de 3,5 mm tem
  cerca de um elemento na espessura dessa cortical. A diferença de 1 a 1,6 % entre as duas malhas
  (results/fea_haste_sw.md, "Sensibilidade à malha") mostra estabilidade dos resultados, não convergência; parte
  da diferença face ao modelo em Python na zona de Gruen 7 pode ser discretização. Para demonstrar convergência,
  faltaria uma 3.ª malha com controlo local de 1 a 1,5 mm na cortical proximal.
- A Simulation mostra, nos modelos com a haste, o aviso modal "Excessive displacements detected" (deslocamentos
  excessivos). O script responde "No" (acabar a análise linear sem passar a grandes deslocamentos), com registo
  no ficheiro .log de cada corrida. Ver a secção 5 (aviso): é o critério interno do Simulation para deslocamentos
  grandes, não um problema do modelo.
- Medição: energia de deformação de cada elemento de osso (componente ENERGY dos resultados de deformação, em J)
  e centro de cada elemento (dados da malha); soma-se a energia dos elementos cujo centro cai em cada zona de Gruen.
- Zonas de Gruen (Gruen TA, McNeice GM, Amstutz HC. Clin Orthop Relat Res 1979;(141):17-27, PMID 477100; na
  radiografia anteroposterior, sete zonas à volta da haste: 1 a 3 laterais, 4 na ponta, 5 a 7 mediais, em terços
  do comprimento da haste). No modelo 3D: lado lateral x > 0 e medial x < 0 (plano que contém o eixo da haste);
  zona 1 e zona 7 de y = 2L/3 (76,7 mm acima da ponta, L = 115 mm) até ao corte do colo, com o grande trocânter na
  zona 1; zona 4 de 0 a 20 mm abaixo da ponta (valor de desenho). No fémur intacto contam-se só os elementos abaixo
  do corte do colo (a mesma região do implantado). A divisão em terços é a da definição original; o limite a 2L/3
  e a divisão lateral/medial pelo eixo são a tradução para 3D usada aqui (A verificar contra a prática da
  literatura de FEA).
- Comparação: razão entre a energia na zona com a haste e a do fémur intacto com o mesmo tamanho de malha.

## 5. Verificações

Comando: `.venv\Scripts\python.exe scripts\fea_solidworks.py verificar` (volta a resolver, sem gravar as peças, o
fémur intacto e a haste de Co-Cr-Mo forjado com a malha de 5 mm, e a mesma haste com 10 % da carga). Números em
results/fea_haste_sw_verificacoes.json.

**a) Equilíbrio.** Soma das cargas aplicadas (contacto da anca e abdutores): (-29,43; -1049,92; -209,69) N. Soma das
reações nos 142 nós do apoio distal (GetReactionForcesAndMoments, todos os nós somados): (29,43; 1049,92; 209,69) N
no intacto e (29,43; 1049,92; 209,69) N com a haste de Co-Cr-Mo. Erro |R + F| / |F|: 4·10⁻⁶ % no intacto e
1·10⁻⁶ % com a haste (abaixo de 1 %). Com 10 % da carga, as reações são 10 % das anteriores (erro 3·10⁻⁶ %).

**b) Unidades.** A geometria está em mm (lida em m na API e convertida), as forças em N, as tensões em Pa ou N/mm²
e a energia em J. Verificações: o von Mises máximo do intacto dá 48 260 212 Pa e 48,260 N/mm² (fator 10⁶); o
deslocamento máximo dá 7,2862 mm e 0,0072862 m (fator 10³). A soma da energia de deformação de todos os elementos
(componente ENERGY) dá 1,736 J no intacto e 1,558 J com a haste; o trabalho das cargas, ½ Σ F·u (N × m, com o
deslocamento dos nós mais próximos dos pontos de aplicação), dá 1,738 J e 1,552 J (diferenças de 0,1 % e 0,4 %,
explicadas por o deslocamento ser lido num nó e não no ponto remoto). Logo a energia está em J (N·m) e as
energias por zona do resumo são coerentes. Com 10 % da carga a energia cai para 1 % (0,0156 J): resposta linear.

**c) Deformações principais no cortical do fémur intacto.** Por elemento (E1 = principal máxima, E3 = principal
mínima), malha de 5 mm. Diáfise (y de -100 a 0 mm): E1 com percentil 95 de 1699 µε (máximo 2114 µε) e E3 com
percentil 5 de -1928 µε (mínimo -2332 µε). Metáfise (y de 0 a 100 mm): 1601 µε e -1911 µε (extremos 2115 e
-2453 µε). Gama fisiológica: em extensómetros implantados na tíbia humana, as deformações principais na marcha são
cerca de um terço das da corrida em ziguezague, que chegam a cerca de 2000 µε, e ficam abaixo de 2000 µε mesmo em
atividade vigorosa (Burr DB et al. Bone 1996;18(5):405-410, doi:10.1016/8756-3282(96)00028-2; resumo; DOI
confirmado na Crossref). No fémur, Speirs et al. 2007 (J Biomech 40:2318-2323, doi:10.1016/j.jbiomech.2006.10.038;
resumo; DOI confirmado na Crossref) referem variações de até 600 µε na diáfise na marcha entre condições de
fronteira. Leitura: as deformações do modelo ficam abaixo dos 2000 µε na maior parte do cortical (o percentil 95)
mas cerca de 2 a 3 vezes acima das da marcha medidas in vivo (algumas centenas de µε). A causa é a mesma do ponto d)
(flexão da diáfise exagerada pela fixação distal com só dois grupos de forças). É plausível para estas condições de
fronteira, mas não é um valor fisiológico absoluto.

**d) Deslocamento máximo (cerca de 7 mm).** Onde: no topo da cabeça do fémur intacto (nó em x = -43,6, y = 153,5,
z = 0 mm; 7,29 mm) e, com a haste, no cone 12/14 (x = -36,3, y = 137,6 mm; 6,26 mm). Perfil ao longo da diáfise
(intacto; deslocamento total na superfície lateral): 0 no apoio, 0,23 mm a y = -100, 0,84 mm a -50, 1,84 mm à
altura da ponta da haste (y = 0), 3,20 mm a 50, 4,92 mm a 100 e 6,39 mm no centro da cabeça, sobretudo para medial
(-x) e para posterior (-z). É a curva de uma consola: a diáfise, encastrada no corte distal, flete sob o momento
das cargas. Estimativa de viga (tubo da diáfise, E = 17,6 GPa, raios 14,5 e 6,5 mm, I = 33 317 mm⁴, comprimento
livre de 281,3 mm do apoio ao centro da cabeça, momento frontal de 84 410 N·mm e força anteroposterior de 210 N):
5,7 mm no plano frontal e 2,7 mm no anteroposterior, 6,3 mm no total, contra 6,4 mm no centro da cabeça na
Simulation. O deslocamento vem portanto da flexão da diáfise ao longo do comprimento livre (150 mm abaixo da ponta
mais o fémur proximal); o módulo do trabecular quase não conta (o deslocamento é igual no intacto e com a haste
até y = 50 mm, e com a haste é menor no topo, 6,07 contra 6,39 mm). Literatura: Speirs et al. 2007 mostram que um
fémur com a diáfise fixa e só com o contacto da anca e os abdutores (o caso A deles, igual a este) dá deflexões
excessivas, e que só condições de fronteira fisiológicas, com todos os músculos, dão deflexões da cabeça abaixo de
2,0 mm nos planos frontal e sagital. Os 6 a 7 mm deste modelo são assim um efeito conhecido destas condições de
fronteira, não um erro.

Sensibilidade (comando `sensibilidade`, results/fea_haste_sw_sensibilidade.json, malha de 5 mm): com o caso da
marcha completo de Heller 2005 (mais o tensor da fáscia lata, aplicado com os abdutores no grande trocânter, e o
vasto lateral, aplicado na superfície lateral a y = 85 mm, ponto de desenho), o deslocamento máximo do intacto
desce de 7,29 para 6,05 mm e as deformações da diáfise para 1305 µε (E1, percentil 95) e -1679 µε (E3, percentil
5). As razões ao intacto quase não mudam e a ordem dos materiais é a mesma: Gruen 1 / Gruen 7 = 0,60 / 0,28
(316L), 0,59 / 0,27 (Co-Cr-Mo), 0,71 / 0,45 (Ti-6Al-4V ELI) e 1,42 / 1,42 (Ti-6Al-4V poroso), contra 0,53 / 0,27,
0,52 / 0,25, 0,63 / 0,45 e 1,32 / 1,41 com dois grupos de forças. Os resultados principais ficam com o caso
combinado (contacto da anca e abdutores); não foi preciso corrigir o modelo.

**Aviso "Excessive displacements detected".** Aparece em todos os modelos com a haste (8 vezes nos estudos, 1 vez
na verificação) e nunca no intacto. Com a mesma haste e 10 % da carga o aviso não aparece, e o resultado é
exatamente 10 % do anterior (deslocamento máximo 0,626 contra 6,259 mm, no mesmo nó). Como o modelo é linear e a
deformada é a mesma a menos da escala, o aviso não indica uma ligação em falta nem um mecanismo (o equilíbrio está
certo e não há movimento de corpo rígido); é o critério interno do Simulation que compara o deslocamento calculado
com as dimensões do modelo e sugere uma análise de grandes deslocamentos. Que o critério dispare com a haste e não
no intacto, com deslocamentos parecidos, deve vir de a haste ter partes pequenas (cone e colo) que se deslocam
6 mm, grandes face às suas dimensões; o critério exato não está documentado na API [confirmar no artigo
QA00000118617 da base de conhecimento da Dassault, de acesso restrito]. Responder "No" mantém a análise linear, que
é a hipótese do estudo (deformações abaixo de 0,3 %).

**Haste de Ti-6Al-4V poroso.** As razões um pouco acima de 1 leem-se como carga no osso "próxima da do osso
intacto" (interface colada e rigidez da haste igual à da cortical); as razões acima de 1 são efeito do modelo.

## 6. Limitações

- Fémur de primitivas, sem anatomia real, sem pequeno trocânter e sem curvatura; ossos homogéneos e isotrópicos
  (o cortical é anisotrópico e o trabecular varia muito com a densidade).
- A haste fica toda no osso trabecular (não há apoio cortical distal); a interface é colada (haste osteointegrada),
  sem o período pós-operatório com atrito.
- Um só caso de carga (marcha, instante do pico) e só dois grupos de forças.
- A geometria da haste é a do modelo CAD do trabalho (design/cad/cotas.md), com cotas de desenho no afilamento e na
  espessura.
- É uma confirmação qualitativa (ordem dos materiais e grandeza do efeito), não um valor absoluto de remodelação.

## 7. A verificar

- Valores de Heller 2005 no artigo original (lidos numa reprodução) e a convenção dos eixos.
- ν = 0,3 das três ligas e dos dois ossos.
- Tradução 3D das zonas de Gruen (limites).
- Todas as cotas marcadas "valor de desenho, ilustrativo" em design/cad/cotas_femur_fea.md.
