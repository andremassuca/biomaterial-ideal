# FEA da haste femoral: hipóteses, fontes e limitações

Extensão exploratória do caso da haste femoral: estimar o stress shielding no osso proximal (zonas de Gruen 1 e 7)
para quatro materiais da haste, com o fémur intacto como referência. Código em src/biomat_mcdm/fea/ e
scripts/fea_haste.py; resultados em results/fea_haste.md, results/fea_haste.csv e results/figures/fea/.
Ferramentas gratuitas: gmsh (malha da barra de verificação), scikit-fem (elementos e rigidez), pyamg
(resolvedor multigrelha), numpy e scipy. Instalação: `pip install -e .[fea]`.

## 1. Verificação analítica

Barra de Ti-6Al-4V (E = 105,5 GPa, coluna "tipico" de data/materiais.csv; nu = 0,34, valor de desenho) com
200 x 10 x 10 mm e 1000 N:

- compressão (rolete na base): delta = F L / (E A);
- flexão em consola (base encastrada, força na ponta): viga de Timoshenko,
  delta = F L^3 / (3 E I) + F L / (kappa G A), kappa = 10 (1 + nu) / (12 + 11 nu).

Resultados (tests/test_fea_verificacao.py, tolerância de 2 %):

| Malha | Elemento | Compressão | Flexão |
|---|---|---|---|
| gmsh, tamanho 5 mm (794 tetraedros) | tetraedro quadrático (P2) | erro < 1e-6 % | -0,6 % |
| vóxeis de 1,25 mm (8 na espessura) | hexaedro trilinear (o do fémur) | erro < 1e-6 % | -1,5 % |
| vóxeis de 2,5 mm (4 na espessura) | hexaedro trilinear | erro < 1e-6 % | -4,2 % (não usado no teste) |

O hexaedro trilinear é um pouco rígido demais à flexão (bloqueio por corte); com 8 elementos na espessura o
erro fica abaixo de 2 %. No fémur, a camada cortical tem 1,8 a 4,8 mm, ou seja, 2 a 6 elementos na malha de
0,75 mm: a energia na cortical fina (calcar, zona 7) é a parte menos resolvida (ver convergência).

## 2. Geometria

- Fémur direito do BodyParts3D (FJ3365, malha em recursos\bodyparts3d\obj, a mesma dos
  renders; ver scripts/obter_recursos.py). A malha tem 3102 triângulos e alguns pequenos buracos (66 arestas
  soltas); o interior decide-se por raios em x, y e z com voto de maioria.
- Haste Corail tamanho 8, offset standard (design/cad/stl/haste_femoral_haste.STL, do SolidWorks; cotas em
  design/cad/cotas.md). Posição igual à dos renders: as funções de scripts/geometria_3d.py
  (ajustar_esfera, eixo_principal, colocar_haste) e de scripts/cad_solidworks.py (ler_cotas, eixo_colo) são
  chamadas diretamente (src/biomat_mcdm/fea/_scripts.py); o centro da cabeça da haste coincide com o centro
  da cabeça anatómica (raio ajustado: 22,8 mm).
- Cabeça da prótese: esfera de 32 mm (cotas.md), colada à haste, em Co-Cr-Mo forjado (o mesmo em todos os
  casos; hipótese).
- Osso cortical: camada exterior com espessura variável, 4,8 mm na diáfise e 1,8 mm na metáfise e na cabeça,
  a afinar entre 91 e 51 mm abaixo do centro da cabeça (valores de desenho dos renders, ilustrativos, não
  medidos). Osso trabecular: interior acima de 96 mm abaixo do centro da cabeça. Abaixo disso, o canal
  medular fica vazio (a medula não tem rigidez relevante; hipótese).
- Osteotomia do colo (só no modelo implantado): plano normal ao eixo do colo, 3 mm além da base do colo,
  limitado a um cilindro de 24 mm de raio à volta do eixo do colo (poupa o grande trocânter), como nos
  renders.
- Corte da diáfise 100 mm abaixo da ponta da haste.
- Malha: hexaedros de vóxel (cubos) no referencial da haste. As regiões definem-se numa grelha fina de
  passo próximo de 0,35 mm (no máximo 0,375 mm; um submúltiplo inteiro do passo da malha, para a geometria
  ser quase a mesma em todas as malhas); cada elemento fica com o material da maioria dos seus vóxeis finos.
  Empates: decide o vóxel fino do canto do elemento (amostra sem preferência; dar sempre a vitória ao osso
  engrossava a cortical em cerca de 6 % na malha de 0,75 mm e estragava a convergência). Pedaços soltos
  retiram-se (maior componente ligada pelas faces). Passos de 2,0, 1,5, 1,0 e 0,75 mm.

## 3. Materiais (elásticos lineares e isotrópicos)

| Material | E | nu | Fonte | Estado |
|---|---|---|---|---|
| Aço inox 316L | 207,5 GPa | 0,30 | E: data/materiais.csv (Navarro et al. 2008, doi:10.1098/rsif.2008.0151) | E verificado; nu A verificar |
| Co-Cr-Mo forjado | 225 GPa | 0,30 | E: data/materiais.csv | E verificado; nu A verificar |
| Ti-6Al-4V ELI | 105,5 GPa | 0,34 | E: data/materiais.csv | E verificado; nu A verificar |
| Ti-6Al-4V poroso | 17 GPa | 0,34 | valor de desenho (alvo: osso cortical), nu do Ti-6Al-4V | valor de desenho |
| Osso cortical | 17,5 GPa | 0,30 | E: ponto médio de 15-20 GPa em data/tecido.csv (Li et al. 2014, Materials 7:1709, doi:10.3390/ma7031709) | E verificado; nu A verificar |
| Osso trabecular | 0,39 GPa | 0,30 | Li et al. 2014, Materials (Tabelas 2 e 3), o mesmo valor do estudo de confirmação no SOLIDWORKS (docs/FEA_HASTE_SW.md) e dentro do intervalo 50-500 MPa de data/tecido.csv | alinhado a 8 out 2026; a relação de Morgan et al. 2003 (E = 6,850 rho^1,49 GPa, colo do fémur; com rho = 0,5 g/cm3 dá 2,44 GPa) fica como sensibilidade (função modulo_trabecular) |

DOIs confirmados na Crossref a 8 out 2026 (Morgan 2003, Oftadeh 2015, Li 2014, Johnson 2023, Bergmann 2001,
Bergmann 2016, Heller 2001, Heller 2005, Baharuddin 2014, Aamodt 1997, Edwards 2016, Speirs 2007, Gruen 1979). nu = 0,3 para o osso é o valor usado, por exemplo, por Johnson et al.
2023 (doi:10.1177/11795972231166240); a base de dados não tem coeficientes de Poisson para as ligas: os
valores da tabela são valores de desenho usuais e ficam "A verificar". Nota: a primeira versão usou o E do trabecular
da relação de Morgan (2,44 GPa, colo do fémur), acima do intervalo 50-500 MPa de data/tecido.csv; a 8 out 2026 passou
a 0,39 GPa (Li et al. 2014), o mesmo do estudo no SOLIDWORKS, para as duas ferramentas usarem os mesmos materiais. A
ordem dos materiais não mudou com esta alteração.

## 4. Cargas (pico da marcha)

- Peso corporal de desenho: 75 kg (valor de desenho).
- Caso de carga da marcha de Heller et al. 2005 (J Biomech 38:1155-1163, doi:10.1016/j.jbiomech.2004.05.022), o
  mesmo do estudo no SOLIDWORKS: contacto da anca (-54,0; -32,8; -229,2) % do peso corporal (módulo 238,4 %, ou
  seja 1754 N) e abdutores (58,0; 4,3; 86,5) % do peso (módulo 104,2 %, ou seja 767 N).
- Confirmação (8 out 2026). O texto de Heller 2005 não está em acesso aberto e o OrthoLoad (orthoload.com) só lista o
  artigo, sem a tabela; a página das cargas normalizadas não abre (HTTP 404). Os valores coincidem em duas
  reproduções independentes revistas por pares: Baharuddin et al. 2014 (BMC Musculoskelet Disord 15:30,
  doi:10.1186/1471-2474-15-30, Tabela 3, em N para um peso de 700 N: contacto -378; -229,6; -1604,4 e abdutores
  406; 30,1; 605,5, que dão exatamente as percentagens acima; cita Heller 2005) e, para os abdutores, Johnson et al.
  2023 (Biomed Eng Comput Biol 14, doi:10.1177/11795972231166240, Tabela 2). Fica [confirmar no original] só por o
  texto de Heller 2005 não ter sido lido.
- Verificação com fontes lidas no original: o módulo do contacto (238,4 %) é igual ao pico da marcha do doente médio
  medido in vivo, 238 % do peso a cerca de 4 km/h (Bergmann et al. 2001, J Biomech 34:859-871,
  doi:10.1016/S0021-9290(01)00040-9, resumo). A direção (13,3° do eixo do fémur no plano frontal e 8,1° no sagital) é
  coerente com as cargas normalizadas medidas in vivo em 10 doentes (Bergmann et al. 2016, PLOS ONE 11:e0155612,
  doi:10.1371/journal.pone.0155612, Tabela 5: marcha com 17° no plano frontal, intervalo 9° a 21°, e 11° no sagital).
- Correção feita: a primeira versão usava a direção do contacto (-77,9; -26,6; -240,3) % da Tabela 2 de Johnson et al.
  2023, que afinal vem de Bergmann 2001 e Heller 2001 (referências 38 e 39 desse artigo, outro instante e outro
  conjunto de dados) e não de Heller 2005; passou ao contacto de Heller 2005, igual ao do SOLIDWORKS.
- Referencial: x medial, y anterior, z proximal (o referencial de Heller, como indicado no estudo do SOLIDWORKS;
  coerente com os sinais: os abdutores puxam o trocânter para cima e para dentro e o contacto empurra a cabeça para
  baixo e para fora). Bergmann et al. 2016 usam, para o fémur direito, x lateral, y anterior e z ao longo do eixo do
  fémur (do ponto onde a linha média cruza o eixo do colo ao centro da chanfradura intercondiliana); aqui o eixo z é
  o eixo da diáfise proximal (os mesmos 70 a 230 mm abaixo da cabeça dos renders), uma aproximação.
- Omitidos: tensor da fáscia lata e vasto lateral (fazem parte do caso de carga de Heller 2005 para a
  marcha); a sua omissão muda a flexão da diáfise e a energia nas zonas 1 e 7 (limitação).
- Aplicação: contacto repartido por igual pelos nós da superfície da cabeça (anatómica ou da prótese)
  dentro de um cone de 30° à volta da direção da força; abdutores repartidos pelos nós da superfície do osso
  a menos de 10 mm do topo do grande trocânter (vértice mais alto da malha anatómica do lado lateral). Raio e
  cone: valores de desenho.

## 5. Fixação e interface

- Corte da diáfise encastrado (todos os deslocamentos nulos).
- Haste ligada ao osso (interface colada: nós partilhados; osteointegração completa; hipótese). Sem atrito,
  sem micromovimento e sem separação. Haste e cabeça da prótese também coladas.

## 6. Zonas de Gruen

Gruen, McNeice e Amstutz 1979 (Clin Orthop Relat Res 141:17-27, doi:10.1097/00003086-197906000-00002): 7 zonas
na radiografia de frente, 1 a 3 laterais, 4 na ponta, 5 a 7 mediais. Implementação: a parte da haste dentro do
osso (da ponta até ao ponto onde o plano da osteotomia corta o eixo da haste, 118,7 mm) divide-se em terços ao
longo do eixo; a fronteira lateral/medial é o plano do eixo da haste (x = 0); as zonas 1 e 7 vão até onde houver
osso (grande trocânter e calcar); a zona 4 vai até um terço do comprimento abaixo da ponta. Em cada zona soma-se
todo o osso (cortical e trabecular) em toda a profundidade anteroposterior. Divisão em terços e altura da zona 4:
convenção usual [confirmar a definição exata no original].

Comparação: a energia do fémur intacto soma-se nos mesmos elementos de osso que existem no modelo implantado
(o osso retirado pela osteotomia e pelo canal da haste não conta). Razão = implantado / intacto; stress
shielding = 1 - razão.

## 7. Convergência

Quatro malhas (2,0, 1,5, 1,0 e 0,75 mm; a mais fina com cerca de 0,49 milhões de elementos e 1,6 milhões de
graus de liberdade no fémur intacto; pico de memória de cerca de 3,6 GB; cerca de 6 min por malha fina).
Critério: variação da grandeza de interesse abaixo de 5 % entre as duas malhas mais finas. Entre 1,0 e 0,75 mm,
a razão implantado / intacto (o stress shielding) varia no máximo 1,9 % e a energia absoluta no máximo 3,6 %:
ambas cumprem. A energia absoluta ainda desce de forma monótona de 1,5 para 0,75 mm (no intacto, cerca de 5 % de 1,5 para 1,0 mm e 3 % de 1,0 para 0,75 mm),
por isso o valor absoluto tem um erro de discretização de alguns por cento; a razão é a grandeza mais
estável. Não se correu uma malha de 0,6 mm: a memória estimada (cerca de 7 GB) ficava perto do limite de 8 GB.
Resultados e tabelas em results/fea_haste.md.

## 8. Verificações de sanidade

Números em results/fea_haste_verificacoes.md (scripts/fea_haste.py --verificacoes, malha de 0,75 mm, carga e
materiais do caso principal). Testes: tests/test_fea_modulos.py (equilíbrio e deformações num caso pequeno) e
tests/test_fea_verificacao.py (barra).

(a) Equilíbrio. Soma das cargas aplicadas (contacto + abdutores) no referencial da haste: (121,6; -1047,3; 188,7) N.
Soma das reações nos nós encastrados do corte da diáfise: (-121,6; 1047,3; -188,7) N no intacto, com a haste de
Ti-6Al-4V e com a de Co-Cr-Mo. Erro relativo |R + F| / |F| de 4e-8 % (intacto), 6e-7 % (Ti-6Al-4V) e 7e-7 % (Co-Cr-Mo),
muito abaixo de 1 %; resíduo nodal máximo nos nós livres de 2e-9 N (tolerância do gradiente conjugado: 1e-9).

(b) Unidades. Coordenadas em mm (BodyParts3D e STL do SolidWorks em mm; cotas.md em mm); forças em N (percentagem do
peso x 75 kg x 9,81 m/s2 / 100); módulos em MPa = N/mm2 (GPa da base x 1000); tensões em MPa; energia em N·mm = mJ;
densidade de energia em mJ/mm3 (= MJ/m3); deformações adimensionais (microdeformações = 1e-6). A verificação analítica
(capítulo 1) confirma a cadeia: delta = F L / (E A) e energia = F delta / 2 batem com a solução (teste
test_compressao_hexaedros_voxel_e_energia).

(c) Deformações principais no osso cortical do fémur intacto, na diáfise (de 10 mm acima do encastramento até à
altura da ponta da haste): mediana +592 / -592 microdeformações; percentil 95 da máxima 1921 e percentil 5 da mínima
-2196; extremos +2972 e -3202. Deformação axial mediana: +1064 no lado lateral (tração) e -1456 no medial
(compressão). Comparação: (i) o padrão (tração lateral, compressão medial) é o medido in vivo com extensómetros no
fémur proximal lateral durante a marcha (Aamodt et al. 1997, J Orthop Res 15:927-931, doi:10.1002/jor.1100150620:
tração axial lateral em todas as atividades, deformação principal de tração a menos de 22° do eixo do fémur); (ii) a
grandeza fica cerca de 2 vezes acima dos picos de FEA do fémur na marcha com o conjunto completo de músculos
(Edwards et al. 2016, J Biomech 49:1206-1213, doi:10.1016/j.jbiomech.2016.03.007: 752 a 945 de tração e -859 a -1271
de compressão). Explicação: este modelo tem só o contacto e os abdutores, com a diáfise encastrada; Speirs et al.
2007 (J Biomech 40:2318-2323, doi:10.1016/j.jbiomech.2006.10.038) mostram que este tipo de condição (o seu caso A:
diáfise presa, contacto e abdutores) dá deformação e flexão do fémur excessivas e que as deformações da diáfise
mudam até 600 microdeformações na marcha só com as condições de fronteira. Conclusão: ordem de grandeza plausível
(abaixo das deformações de cedência do osso cortical [fonte a indicar]), padrão correto,
magnitude sobrestimada pela carga simplificada; a mesma condição aplica-se ao intacto e aos implantados, por isso
a razão implantado / intacto é menos afetada do que os valores absolutos. Não se corrigiu (manter os dois grupos de
carga do estudo no SOLIDWORKS); acrescentar o tensor da fáscia lata e o vasto lateral (Baharuddin 2014, Tabela 3)
fica como melhoria.

(d) Deslocamento máximo: 5,28 mm no fémur intacto, 4,64 mm com Ti-6Al-4V e 4,41 mm com Co-Cr-Mo, sempre no topo da
cabeça (anatómica ou da prótese), o ponto mais afastado do encastramento; o centro da cabeça desloca-se cerca de
4,5 mm no intacto ((-3,3; -1,1; 2,9) mm no referencial da haste: 3,3 mm para medial, 1,1 mm para baixo ao longo
da haste e 2,9 mm na normal ao plano da haste). Porquê: o fémur funciona como uma consola de cerca de 230 mm (da fixação, 100 mm abaixo da ponta da haste,
até à cabeça) com o colo como braço; a flexão da diáfise e do colo domina; o trabecular de 0,39 GPa pouco conta na
diáfise (é a cortical que a segura); a haste metálica no colo e na metáfise torna a parte de cima mais rígida e
reduz o deslocamento (4,4 a 4,6 mm). O SOLIDWORKS dá 6,3 a 7,5 mm com a fixação 150 mm abaixo da ponta da haste
(consola cerca de 50 mm mais longa: numa consola a flecha cresce com o cubo do comprimento, (280/230)^3 = 1,8) e
com o contacto e os abdutores iguais; a diferença é coerente. Plausibilidade: com condições fisiológicas a cabeça
desloca-se menos de 2 mm (Speirs et al. 2007); com a diáfise presa e só contacto e abdutores (o caso A deles) as
deflexões são excessivas, como aqui. É um artefacto conhecido das condições de fronteira simplificadas, comum às
duas ferramentas e aos cinco modelos.

## 9. Sensibilidade ao módulo do osso trabecular

Caso principal com 0,39 GPa (Li 2014); sensibilidade com 2,44 GPa (relação de Morgan et al. 2003 para o colo do
fémur, rho = 0,5 g/cm3), na malha de 0,75 mm (results/fea_haste_sensibilidade.md):

| Material da haste | Razão G1 (0,39 GPa) | Razão G1 (2,44 GPa) | Razão G7 (0,39 GPa) | Razão G7 (2,44 GPa) |
|---|---|---|---|---|
| 316L | 0,538 | 0,496 | 0,127 | 0,122 |
| Co-Cr-Mo | 0,533 | 0,487 | 0,120 | 0,112 |
| Ti-6Al-4V | 0,608 | 0,597 | 0,220 | 0,249 |
| Ti-6Al-4V poroso | 0,963 | 0,964 | 1,006 | 1,405 |

A ordem dos materiais não muda em nenhuma das zonas (poroso > Ti-6Al-4V > 316L > Co-Cr-Mo). Com o trabecular mais
rígido, o stress shielding das ligas densas muda pouco (até 0,05 na razão); a razão da haste porosa no calcar
(G7) sobe de 1,0 para 1,4: com um trabecular rígido à volta, uma haste da rigidez do osso põe mais carga no osso
medial do que o fémur intacto.

## 10. Leitura da haste porosa

Com interface colada e rigidez igual à do osso cortical (17 GPa, valor de desenho), a energia no osso fica próxima
da do osso intacto (razão 0,96 em G1 e 1,01 em G7). Uma razão acima de 1 quer dizer só que o osso à volta trabalha
um pouco mais do que no fémur intacto; não é uma comparação de qualidade entre a haste e o osso.

## 11. Limitações

- Osso isotrópico e homogéneo por região (o osso real é anisotrópico e com densidade variável; a relação de
  Morgan dá E no eixo das trabéculas).
- Espessura da cortical de desenho (dos renders), não medida em TC.
- Interface colada (osteointegração perfeita): sobrestima a transferência de carga proximal face a uma haste
  com contacto parcial; não estuda o micromovimento.
- Carga estática num só instante (pico da marcha), sem os outros músculos; não há fadiga nem remodelação
  óssea (só o estímulo inicial, sem simulação adaptativa).
- Malha de vóxeis com superfície em degraus; hexaedro trilinear algo rígido à flexão nas camadas finas
  (cortical de 1,8 mm com 2 a 3 elementos na malha de 0,75 mm).
- A zona de Gruen 1 contém a zona de aplicação da força dos abdutores (topo do trocânter): a energia nessa
  zona depende da forma como a força é repartida (carga concentrada, valor de desenho).
- Fixação distal encastrada a 100 mm da ponta da haste (fémur truncado).
- Componentes das forças lidas em reproduções (Baharuddin 2014, Johnson 2023), não no original de Heller 2005
  [confirmar no original].
- Fémur de um só indivíduo (BodyParts3D), malha anatómica grosseira (3102 triângulos).
