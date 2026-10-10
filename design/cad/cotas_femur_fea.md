# Cotas do fémur simplificado para a FEA da haste (SolidWorks)

Fémur simplificado usado na confirmação independente da FEA da haste femoral em SOLIDWORKS Simulation
(scripts/fea_solidworks.py; hipóteses em docs/FEA_HASTE_SW.md). Não é um fémur anatómico: é um modelo de
primitivas (revolução, cilindro, esfera e um bloco para o grande trocânter), com a forma exterior medida no fémur
BodyParts3D FJ3365 (o mesmo dos renders e do planeamento da haste) e o resto com fonte ou como "valor de desenho,
ilustrativo". O script lê a coluna "chave" e a coluna "valor" (vírgula decimal).

Referencial (o mesmo da haste em design/cad/haste_femoral.SLDPRT): plano frontal XY; y ao longo do eixo da
diáfise, para cima, com y = 0 na ponta da haste; x mediolateral, com o lado medial em x negativo (o colo da haste
vai para x negativo); z anteroposterior (anterior em z positivo, fémur esquerdo). Medidas em mm.

Medições no FJ3365: função medir_femur_anatomico() de scripts/fea_solidworks.py (cortes perpendiculares ao eixo
do canal ajustado como em scripts/planeamento_haste.py). Resultado: raio da cabeça 22,8 mm; centro da cabeça a
33,4 mm do eixo do canal; distância do eixo à superfície exterior da diáfise de 13,8 a 16,8 mm (lado lateral) e
14,7 mm (lado medial) entre 100 e 140 mm abaixo do centro da cabeça; grande trocânter a 25 a 27 mm do eixo
(lado lateral) entre 10 e 20 mm abaixo do centro da cabeça; topo do grande trocânter entre o centro da cabeça e
10 mm acima (há osso lateral no corte à altura do centro e já não há 10 mm acima).

| chave | valor | unidade | o que é | fonte |
|---|---|---|---|---|
| cabeca_raio | 22,8 | mm | raio da cabeça do fémur intacto | medido no FJ3365 (ajuste de esfera, como em planeamento_haste.py) |
| cabeca_offset | 38,3 | mm | distância do centro da cabeça ao eixo da diáfise | valor de desenho: igual ao offset da Corail tamanho 8 (cotas.md), para a cabeça do fémur intacto e a da prótese terem o mesmo centro e as cargas o mesmo braço; no FJ3365 mede 33,4 mm |
| cabeca_altura | 131,3 | mm | altura do centro da cabeça acima da ponta da haste | igual ao centro da cabeça da haste (B + C, cotas.md), pela mesma razão |
| colo_ccd | 135 | ° | ângulo cervicodiafisário do fémur | valor de desenho: igual ao da haste (cotas.md); a média em adultos é 128,8° (Boese et al. 2016, doi:10.1007/s00256-015-2236-z) |
| colo_raio | 15,0 | mm | raio exterior do colo do fémur (cilindro) | valor de desenho, ilustrativo |
| diafise_raio | 14,5 | mm | raio exterior da diáfise | medido no FJ3365 (13,8 a 16,8 mm do eixo à superfície; valor intermédio arredondado) |
| canal_raio | 6,5 | mm | raio do canal medular no istmo | valor de desenho, ilustrativo |
| metafise_raio | 25,0 | mm | raio exterior da metáfise proximal | medido no FJ3365 (23 a 27 mm do eixo à superfície, lados medial e lateral, entre 20 e 40 mm abaixo do centro da cabeça) |
| cortical_metafise | 3,0 | mm | espessura da cortical na metáfise e no grande trocânter | valor de desenho, ilustrativo |
| cortical_colo | 3,0 | mm | espessura da cortical do colo | valor de desenho, ilustrativo |
| cortical_cabeca | 2,0 | mm | espessura da cortical da cabeça | valor de desenho, ilustrativo |
| trocanter_topo | 133 | mm | altura do topo do grande trocânter | medido no FJ3365 (entre o centro da cabeça, 131,3, e 10 mm acima); valor de desenho dentro desse intervalo |
| trocanter_largura | 34 | mm | largura anteroposterior do bloco do grande trocânter | valor de desenho, ilustrativo |
| trocanter_lateral | 29 | mm | distância máxima do trocânter ao eixo, do lado lateral | valor de desenho; no FJ3365 mede 25 a 27 mm entre 10 e 20 mm abaixo do centro da cabeça |
| trabecular_base | -10 | mm | altura onde acaba o osso trabecular no canal (abaixo fica o canal vazio) | valor de desenho, ilustrativo: 10 mm abaixo da ponta da haste |
| fixacao_y | -150 | mm | altura do corte distal encastrado | valor de desenho: 150 mm abaixo da ponta da haste (cerca de 5 diâmetros da diáfise) |
| osteotomia_lateral | 6 | mm | limite lateral do corte do colo (fossa trocantérica) | valor de desenho, ilustrativo |

Perfil exterior e interior (revolução à volta do eixo y): pares (y, raio) em perfil_exterior() e perfil_interior()
de scripts/fea_solidworks.py, entre os raios desta tabela; as transições (y = 40 a 105 mm) são valores de desenho.
Corte do colo (osteotomia): plano perpendicular ao eixo do colo da haste que passa pela base do colo da haste
(onde o colo encontra o corpo), parado na fossa trocantérica (x = osteotomia_lateral), para manter o grande
trocânter, como no corte do colo da técnica da Corail (valor de desenho, ilustrativo). Não se modela o pequeno
trocânter.
