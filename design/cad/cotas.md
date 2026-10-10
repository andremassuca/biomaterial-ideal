# Cotas dos modelos CAD (haste femoral e implante dentário)

Os modelos são ilustrativos (renders do poster, da apresentação e da aplicação), não para fabrico. Cada cota tem
fonte ou fica como "valor de desenho, ilustrativo". O scripts/cad_solidworks.py lê a coluna "chave" e a coluna
"valor" desta tabela (só os números, com vírgula decimal). Fontes abertas e lidas a 6 out 2026.

## Implante dentário (referência: Straumann Bone Level Tapered, Ø 4,1 mm RC)

| chave | valor | unidade | o que é | fonte |
|---|---|---|---|---|
| implante_diametro | 4,1 | mm | diâmetro endo-ósseo do corpo | Straumann, "Implantes Straumann Bone Level Tapered, Informações básicas" (702167/pt, 2021), p. 1 e tabela 2.1: https://straumann.com/content/dam/media-center/straumann/pt-pt/documents/brochure/product-information/BLT%20Informa%C3%A7%C3%B5es%20b%C3%A1sicas_.pdf |
| implante_comprimento | 10 | mm | comprimento endo-ósseo (8 a 18 mm disponíveis no Ø 4,1) | idem, tabela de indicações |
| rosca_passo | 0,8 | mm | passo da rosca | idem, tabela 2.1, linha H ("0,8 mm / 20° / 0,3 mm", célula comum às colunas SDI Ø 2,9 e BLT Ø 3,3, Ø 4,1 e Ø 4,8; confirmado na p. 3 do documento, p. 5 do PDF, a 6 out 2026); o mesmo passo no Bone Level RC 4,1 × 10 em Yamaguchi et al., SpringerPlus 2016, doi:10.1186/s40064-016-2116-6, Tabela 1 |
| rosca_angulo_flanco | 20 | ° | ângulo do flanco | idem, tabela 2.1 |
| rosca_profundidade | 0,3 | mm | profundidade da rosca | idem, tabela 2.1 |
| apice_nucleo | 1,8 | mm | diâmetro do núcleo no ápice | idem, tabela 2.1 (F) |
| apice_rosca | 2,7 | mm | diâmetro exterior da rosca no ápice | idem, tabela 2.1 (G) |
| plataforma_diametro | 3,7 | mm | diâmetro da plataforma no topo | idem, tabela 2.1 (B) |
| conexao_diametro | 3,3 | mm | diâmetro da conexão (RC) | idem, tabela 2.1 (C) |
| parte_conica | 5,3 | mm | comprimento da parte cónica apical (9°) | idem, tabela 2.1 (T, "5,3 mm/9°") |
| pilar_diametro | 4,5 | mm | diâmetro do pilar (RC Variobase para coroa, 022.0026) | Straumann, página do produto: https://shop.straumann.com/us/en_us/p/022.0026 |
| pilar_altura | 5,5 | mm | altura do pilar | idem |
| pilar_altura_gengival | 1,0 | mm | altura gengival do pilar | idem |
| coroa_largura | 10,5 | mm | largura mesiodistal da coroa de um 1.º molar | valor de desenho, ilustrativo, entre 10,12 mm (1.º molar superior) e 10,77 mm (1.º molar inferior), sexo masculino, em Hadwa et al., BMC Oral Health 2026, doi:10.1186/s12903-026-09486-x |
| coroa_altura | 7,5 | mm | altura cervico-oclusal da coroa de um 1.º molar | valor de desenho, ilustrativo. Nota: um estudo radiográfico de 1.os molares inferiores com trauma oclusal e periodontite dá medianas de 7,6 mm (homens) e 7,2 mm (mulheres) ("Crown–Root Ratio as a Predictive Morphometric Indicator in Mandibular First Molars with Occlusal Trauma and Periodontitis", PMC12468253: https://pmc.ncbi.nlm.nih.gov/articles/PMC12468253/); amostra patológica, por isso não serve de fonte. Nos renders, a coroa vem da malha anatómica do molar (BodyParts3D FJ1268; ver fontes_anatomicas.md) |
| rosca_inicio | 1,2 | mm | distância do topo do implante ao início da rosca (colo liso) | valor de desenho, ilustrativo |
| chanfro_topo | 0,3 | mm | chanfro da aresta do topo | valor de desenho, ilustrativo |

Aviso: um estudo in vitro dá passo de 1,1 mm e profundidade de 0,16 a 0,43 mm para o BLT Ø 3,3 × 10 (Int J
Implant Dent 2025, doi:10.1186/s40729-025-00597-8, Tabela 1). Usa-se o valor do fabricante.

## Haste femoral (referência: DePuy Synthes Corail, tamanho 8, offset standard, sem colar)

Tamanho escolhido por planeamento no fémur anatómico dos renders (BodyParts3D FJ3365), como num planeamento
pré-operatório em radiografia AP: scripts/planeamento_haste.py corta o fémur pelo plano coronal que contém o centro
da cabeça e o eixo do canal, coloca cada tamanho do catálogo (8 a 12 standard e 9 a 11 high offset) com o centro da
cabeça no centro anatómico e a ponta no eixo do canal, e mede o contorno da haste nesse plano (sem contar os 4 mm do
topo, que ficam no plano da osteotomia). Resultado em design/cad/planeamento_haste.csv: o tamanho 8 standard é o único
com o contorno todo dentro do osso (folga mínima de 1,2 mm); o 9 fica a 0,3 mm da superfície e os maiores saem do
osso. O high offset sai sempre do osso (o fémur tem offset anatómico pequeno). Nenhum tamanho deixa 2 mm de folga em
todo o contorno, porque este fémur é estreito (cerca de 9 mm do eixo à superfície na diáfise proximal).

Fonte do catálogo: DePuy Synthes, "Sistema de cadera CORAIL, Justificación del producto y Técnica Quirúrgica", p. 28
(tabelas "Offset estándar, sin collar" e "High offset, sin collar"; medidas com cabeça de 28 mm +5,0; cópia num site
hospitalar): https://sectorteruel.salud.aragon.es/documentos/quiroenf/TRAUMATOLOGIA/TECNICAS%20QUIRURGICAS/SYNTHES%20TQ/CADERA/CORAIL_Platform_Brochure_ES.pdf;
12/14 e 135° também no FDA AccessGUDID 10603295446842.

| chave | valor | unidade | o que é | fonte |
|---|---|---|---|---|
| haste_ccd | 135 | ° | ângulo cervicodiafisário | catálogo, tamanho 8 standard (E) |
| haste_comprimento | 115 | mm | comprimento total da haste (A), tamanho 8 | catálogo (A) |
| haste_comprimento_b | 93 | mm | comprimento B, tamanho 8; lido no desenho como a altura a que o eixo do colo cruza o eixo da haste (leitura confirmada pelo André a 8 out 2026: as proporções do desenho batem, 0,82 contra 0,81 na tabela; imagem anotada em partilha\corail_leitura_B_C.png) | catálogo (B) |
| haste_offset | 38,3 | mm | offset, tamanho 8 | catálogo (C) |
| haste_colo | 39 | mm | comprimento do colo, tamanho 8 | catálogo (D) |
| cabeca_diametro | 32 | mm | diâmetro da cabeça (28, 32 e 36 mm no catálogo) | catálogo de cabeças ("32 mm +5") |
| cone_maior | 14 | mm | diâmetro maior do cone 12/14 | designação 12/14 da mesma fonte; a geometria exata do cone não está no catálogo: valor de desenho, ilustrativo |
| cone_menor | 12 | mm | diâmetro menor do cone 12/14 | idem |
| cone_comprimento | 15 | mm | comprimento do cone | valor de desenho, ilustrativo |
| haste_largura_ombro | 23,0 | mm | largura mediolateral da haste no ombro | valor de desenho, ilustrativo: 30 mm pensados para o tamanho 12 (A = 150 mm), proporcionais a A |
| haste_largura_ponta | 6,9 | mm | largura mediolateral na ponta distal | idem (9 mm no tamanho 12) |
| haste_espessura | 10,7 | mm | espessura anteroposterior no ombro | idem (14 mm no tamanho 12) |
| haste_espessura_ponta | 5,4 | mm | espessura anteroposterior na ponta distal | idem (7 mm no tamanho 12) |

O centro da cabeça fica à altura B + C (para 135°) acima da ponta e ao offset C do eixo da haste; o colo é cónico, de
15 mm junto ao corpo a 12,8 mm junto ao cone (valor de desenho, ilustrativo).

Contexto anatómico: ângulo cervicodiafisário médio de 128,8° (98° a 180°) em 5089 ancas de adultos saudáveis
(Boese et al., Skeletal Radiol 2016;45(1):19-28, doi:10.1007/s00256-015-2236-z). Outra haste comum, a Exeter V40,
tem 125°, offset 37,5 mm e 150 mm (Stryker, Exeter V40 Surgical Technique, 2014).
