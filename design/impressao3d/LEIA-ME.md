# Modelos para impressão 3D

Modelos de demonstração (BioJornadas, aulas, apresentação). Não são para uso clínico nem para fabrico de implantes.
Gerados por `scripts/impressao3d.py` (testes em `tests/test_impressao3d.py`); as medidas e a verificação de cada malha
estão em `medidas.csv`. Todos os ficheiros são STL binários em milímetros; todas as malhas são fechadas (manifold),
com orientação coerente das faces e um só corpo (verificado com trimesh e manifold3d).

Para gerar de novo: `python scripts/impressao3d.py` (precisa de `pip install trimesh manifold3d`).

## Ficheiros

| Ficheiro | Escala | Dimensões (mm) | Volume (cm³) | Notas |
|---|---|---|---|---|
| haste_femoral_corail8_1para1.stl | 1:1 | 56,1 x 137,7 x 15,0 | 23,8 | haste inteira, deitada |
| haste_femoral_corail8_1para1_metadeA.stl | 1:1 | 56,1 x 137,7 x 7,5 | 11,9 | metade, face do corte na mesa |
| haste_femoral_corail8_1para1_metadeB.stl | 1:1 | 56,1 x 137,7 x 7,5 | 11,9 | a outra metade (espelho) |
| scaffold_0_90_celula_10x.stl | 10:1 | 12,0 x 12,0 x 4,8 | 0,16 | célula unitária (2 camadas) |
| scaffold_0_90_bloco_3x3x6_10x.stl | 10:1 | 36,0 x 36,0 x 14,4 | 4,4 | 3 x 3 células, 6 camadas |

## Haste femoral (Corail tamanho 8, offset standard, sem colar)

- Geometria: a do modelo CAD do trabalho (design/cad/haste_femoral.SLDPRT, exportado para
  design/cad/stl/haste_femoral_haste.STL), a mesma da FEA no SOLIDWORKS (docs/FEA_HASTE_SW.md). Cotas e fontes em
  design/cad/cotas.md: comprimento A = 115 mm, offset 38,3 mm, colo de 39 mm e ângulo de 135° do catálogo do
  fabricante; larguras e espessuras são valores de desenho, ilustrativos. O comprimento total do STL (137,7 mm) inclui
  o colo e o cone 12/14. Sem cabeça femoral.
- Escala 1:1 (tamanho real). Cabe em qualquer impressora doméstica (mesa de 180 x 180 mm ou maior, na diagonal se
  for preciso).
- Recomendado: imprimir as duas metades (A e B), cada uma com a face plana do corte na mesa, sem suportes, e colá-las
  (cola de cianoacrilato para PLA). A face do corte tem cerca de 2 290 mm² de contacto e não há saliências.
- Peça inteira (alternativa): deitada sobre a face anteroposterior, com suportes em todo o lado (árvore ou normais,
  ângulo de 50°) e borda (brim) de 5 mm; o cone e as faces são curvos e a peça só toca na mesa numa linha.
- Material: PLA (cinzento ou prateado, para lembrar o titânio). Camada de 0,2 mm, 3 perímetros, enchimento de 15 a
  20 %. Tempo e massa dependem do programa de fatiar (cerca de 24 cm³ de peça; com 20 % de enchimento usa bem menos
  material).

## Scaffold de filamentos cruzados 0/90 (compósito PCL/β-TCP impresso)

- Arquitetura: Sparks et al. (2023), Science Advances 9(18):eadd6071, doi:10.1126/sciadv.add6071 (Materials and
  Methods, "Scaffold preparation"): filamento de 300 µm, separação de 1200 µm, padrão 0/90° e porosidade de 70 %. É
  a mesma referência do relatório (Q9 do scaffold) e da base de dados (porosidade do compósito).
- Hipóteses do modelo (valores de desenho, não da fonte):
  - a separação de 1200 µm é tomada como distância entre eixos dos filamentos (a fonte não diz se é entre eixos ou
    entre bordos);
  - o passo entre camadas é 0,8 do diâmetro (240 µm), para os filamentos de camadas vizinhas se fundirem e o sólido
    ficar ligado e fechado;
  - filamentos cilíndricos perfeitos, cortados pela caixa (faces laterais e base planas).
- Porosidade geométrica do modelo: 77,0 % na célula e 76,3 % no bloco, acima dos 70 % declarados. A diferença vem das
  hipóteses acima (filamentos achatados e mais fundidos na impressão real dão menos poros); o modelo mostra a
  arquitetura, não reproduz a porosidade medida.
- Escala 10:1: à escala real o filamento (0,3 mm) é mais fino do que o bico de uma FDM doméstica (0,4 mm). Ampliado 10
  vezes, o filamento passa a 3 mm, a célula a 12 x 12 x 4,8 mm e o bloco a 36 x 36 x 14,4 mm. Para outra escala:
  `python scripts/impressao3d.py --escala-scaffold 5` (a 5:1, filamentos de 1,5 mm; abaixo disso fica frágil).
- Impressão: PLA, bico de 0,4 mm, camada de 0,2 mm, base na mesa tal como está no ficheiro (a primeira camada de
  filamentos fica cortada e plana). Sem suportes: as pontes entre filamentos têm 9 mm (12 mm entre eixos menos 3 mm),
  que uma FDM doméstica faz bem. Borda (brim) de 3 a 5 mm na célula unitária, que tem pouca área na mesa (cerca de
  22 mm²). Enchimento de 100 % (os filamentos são finos) ou 3 perímetros.

## Verificação (medidas.csv)

Para cada ficheiro: fechada, orientação coerente, volume válido, número de corpos (1), triângulos, volume, dimensões,
porosidade geométrica (scaffold) e tamanho do ficheiro (todos abaixo de 2 MB, por isso ficam versionados).
