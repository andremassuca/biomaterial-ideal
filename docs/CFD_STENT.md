# CFD do stent coronário: hipóteses, fontes e limitações

Extensão exploratória do caso do stent: ver o efeito da espessura dos struts no escoamento junto à parede da
artéria, comparando struts finos (Pt-Cr) com struts grossos (316L). Código em src/biomat_mcdm/cfd/ e
scripts/cfd_stent.py; resultados em results/cfd_stent.md, results/cfd_malhas.csv, results/cfd_pulsatil.json e
results/figures/cfd/.

Ferramenta gratuita: OpenFOAM v2406 (GPL; imagem opencfd/openfoam-default:2406 do Docker), com blockMesh,
snappyHexMesh, simpleFoam e pimpleFoam. A geometria dos struts é feita em Python (gmsh para a área dos struts
no plano desenrolado); o pós-processamento usa pyvista e numpy. Os casos correm numa pasta de trabalho fora do
repositório; cada caso é gerado de novo a partir do código.

## 1. Pergunta e grandezas

- Tensão de corte na parede (WSS): o "atrito" do sangue no endotélio. Abaixo de 0,4 Pa (4 dyn/cm²) o
  endotélio passa a um fenótipo aterogénico (Malek AM, Alper SL, Izumo S. JAMA 1999;282:2035-42,
  doi:10.1001/jama.282.21.2035; só resumo). Em stents, as zonas de WSS baixa associam-se à hiperplasia da
  neoíntima (LaDisa JF et al. Am J Physiol Heart Circ Physiol 2005;288:H2465-75,
  doi:10.1152/ajpheart.01107.2004; só resumo).
- No fluxo pulsátil: TAWSS (média no tempo da magnitude da WSS num ciclo) e OSI (índice de corte oscilatório,
  0 quando o atrito aponta sempre para o mesmo lado, 0,5 quando muda de sentido metade do tempo).
- Resultado principal: fração da área da parede exposta (entre os struts, na zona do stent) com TAWSS abaixo
  de 0,4 Pa.

## 2. Geometria (valores de desenho iguais nos dois stents; só muda a espessura)

| Grandeza | Valor | Fonte ou estado |
|---|---|---|
| Diâmetro do lúmen | 3,0 mm | tamanho de stent 3,00 mm (ficha SYNERGY citada em data/materiais.csv); valor de desenho |
| Espessura do strut, Pt-Cr | 79 µm | data/materiais.csv, coluna "tipico" (SYNERGY 3,00-3,50 mm) |
| Espessura do strut, 316L | 135 µm | data/materiais.csv, coluna "tipico" (Express 132 µm, Bx Velocity 140 µm; Nikam 2014) |
| Largura do strut | 90 µm | valor de desenho, igual nos dois |
| Células à volta | 8 losangos | como nos renders (scripts/renders_blender.py); valor de desenho |
| Ângulo dos struts com o eixo | 45° | valor de desenho (losangos com a mesma largura e altura) |
| Comprimento com stent | 6 struts no setor (3 losangos, 3,53 mm) | valor de desenho |
| Entrada e saída | 1,0 mm antes e 3,0 mm depois do stent | valor de desenho |

Hipóteses:
- stent totalmente encostado à parede (os struts entram no lúmen com toda a espessura; não ficam enterrados);
- struts de secção retangular, com cantos vivos e vértices em X (sem coroas arredondadas nem pontes);
- parede rígida e cilíndrica (sem curvatura da artéria, sem movimento do coração, sem placa);
- padrão periódico à volta da artéria: modela-se um setor de 22,5° (meio losango) com planos de simetria
  nos lados, o que exige escoamento sem rotação (artéria direita).

## 3. Sangue e escoamento

| Grandeza | Valor | Fonte |
|---|---|---|
| Densidade | 1060 kg/m³ | Boldock L et al. PLoS One 2022;17:e0271469 (texto completo; CFD de stents coronários) |
| Viscosidade | 3,5 mPa.s (newtoniano) | Boldock 2022; newtoniano acima de 100-200 1/s (Thondapu V et al. Front Cardiovasc Med 2022;9:835270) |
| Onda de velocidade | doente 1 de Chodzyński 2015 | Chodzyński KJ et al. Biomed Eng Online 2015;14:77, Tabela 1 (descendente anterior proximal, D = 3,39 mm): no eixo, mínima 3,7, média 18,6 e máxima 32,9 cm/s; período 1,06 s |
| Pico na diástole | 65 % do ciclo | Davies JE et al. Circulation 2006;113:1768-78 ("Coronary blood flow peaks in diastole"; só resumo); a posição exata é valor de desenho |

Hipóteses:
- a velocidade do Doppler é a do eixo; com perfil parabólico, a velocidade média na secção é metade
  (9,3 cm/s em média; caudal médio de cerca de 39 mL/min no tubo de 3 mm);
- onda de um só harmónico (cosseno) ajustada à média e à amplitude medidas; a onda real tem mais harmónicos;
- à entrada impõe-se o perfil parabólico em cada instante (quase estacionário); justifica-se pelo número de
  Womersley baixo (cerca de 2,0 com R = 1,5 mm e 1/1,06 Hz; os perfis de Womersley com alfa = 2,5 usados por
  McCarthy RP et al. Sci Rep 2025;15:15868 são próximos da parábola);
- escoamento laminar (Reynolds médio cerca de 85, máximo cerca de 150);
- saída com pressão constante.

## 4. Verificações

1. Teste analítico (Poiseuille): tubo sem stent, com o mesmo tipo de malha e a mesma célula junto à parede da
   malha média, escoamento periódico com a velocidade média do ciclo. Compara-se o perfil de velocidade, a
   tensão de corte na parede (4 mu U / R) e a queda de pressão (8 mu U / R²) com a teoria; critério: erro
   abaixo de 2 %.
2. Convergência da malha: três malhas (célula junto à parede, na zona do stent, de 28, 20 e 14 µm; razão de
   refinamento raiz de 2; o snappyHexMesh refina mais um nível à volta dos struts), no estacionário com o
   caudal médio, para os dois stents. Critério: variação abaixo de 5 % entre a malha média e a fina. O índice
   de convergência da malha (GCI, Roache) só se calcula quando as diferenças diminuem de malha para malha; aqui
   as variações são pequenas (até 1,5 %) mas não diminuem, por isso fica só a variação.
3. Passo de tempo: 316L na malha grossa com 1000 e 2000 passos por ciclo.
4. Fluxo pulsátil: dois ciclos; as médias (TAWSS e OSI) são do segundo ciclo. Verifica-se que o segundo ciclo
   repete o primeiro (tensão média na parede no mesmo instante dos dois ciclos).

Malha: setor em três blocos (núcleo junto ao eixo com 30 % do raio e dois blocos exteriores). Uma primeira
versão em coordenadas polares, com prismas no eixo, travava o escoamento junto ao eixo (velocidade no eixo
de 3 cm/s em vez de 19 cm/s) e falhou o teste de Poiseuille; com o núcleo a 50 % do raio, o erro do perfil
junto ao eixo era de 2,8 %. A entrada usa uma expressão do OpenFOAM (exprFixedValue), sem código compilado.

## 5. Limitações

- Geometria idealizada; os stents reais diferem também na largura dos struts, no desenho das células e nas
  pontes, e a espessura de strut é uma propriedade do dispositivo, não do material (o 316L também existiu
  com struts finos).
- Não há biologia: a área de WSS baixa é um indicador hemodinâmico, não uma previsão de reestenose ou de
  trombose.
- Sangue newtoniano; sem hematócrito nem fármaco.
