# FEA da haste femoral: energia de deformação no osso nas zonas de Gruen 1 e 7

Gerado por scripts/fea_haste.py. Hipóteses e fontes em docs/FEA_HASTE.md. Extensão exploratória: modelo linear, estático, osso isotrópico e interface colada.

Malha mais fina: 0,75 mm (hexaedros de vóxel). Energia em mJ (N·mm); por volume em mJ/mm³.
Razão = implantado / intacto no mesmo osso; stress shielding = 1 - razão.

| Material da haste | E (GPa) | Gruen 1: energia | Gruen 1: por volume | Gruen 1: razão | Gruen 1: SS | Gruen 7: energia | Gruen 7: por volume | Gruen 7: razão | Gruen 7: SS |
|---|---|---|---|---|---|---|---|---|---|
| Fémur intacto |  | 39,339 | 1,23e-03 | 1,000 | 0,000 | 43,813 | 2,46e-03 | 1,000 | 0,000 |
| 316L | 207,5 | 21,169 | 6,60e-04 | 0,538 | 0,462 | 5,584 | 3,14e-04 | 0,127 | 0,873 |
| Co-Cr-Mo | 225,0 | 20,951 | 6,53e-04 | 0,533 | 0,467 | 5,270 | 2,96e-04 | 0,120 | 0,880 |
| Ti-6Al-4V | 105,5 | 23,901 | 7,45e-04 | 0,608 | 0,392 | 9,624 | 5,40e-04 | 0,220 | 0,780 |
| Ti-6Al-4V poroso | 17,0 | 37,874 | 1,18e-03 | 0,963 | 0,037 | 44,055 | 2,47e-03 | 1,006 | -0,006 |

## Convergência da malha

| Malha (mm) | Elementos (implantado) | Graus de liberdade | Material | Gruen 1 (mJ) | Gruen 7 (mJ) | Razão G1 | Razão G7 |
|---|---|---|---|---|---|---|---|
| 2 | 25650 | 97755 | Fémur intacto | 42,937 | 47,822 | 1,000 | 1,000 |
| 2 | 20494 | 80841 | 316L | 22,623 | 5,670 | 0,527 | 0,119 |
| 2 | 20494 | 80841 | Co-Cr-Mo | 22,399 | 5,384 | 0,522 | 0,113 |
| 2 | 20494 | 80841 | Ti-6Al-4V | 25,424 | 9,298 | 0,592 | 0,194 |
| 2 | 20494 | 80841 | Ti-6Al-4V poroso | 40,459 | 40,967 | 0,942 | 0,857 |
| 1,5 | 60955 | 219711 | Fémur intacto | 42,719 | 48,754 | 1,000 | 1,000 |
| 1,5 | 48793 | 180639 | 316L | 22,572 | 5,817 | 0,528 | 0,119 |
| 1,5 | 48793 | 180639 | Co-Cr-Mo | 22,326 | 5,488 | 0,523 | 0,113 |
| 1,5 | 48793 | 180639 | Ti-6Al-4V | 25,587 | 9,977 | 0,599 | 0,205 |
| 1,5 | 48793 | 180639 | Ti-6Al-4V poroso | 40,510 | 44,412 | 0,948 | 0,911 |
| 1 | 206006 | 700932 | Fémur intacto | 40,603 | 44,961 | 1,000 | 1,000 |
| 1 | 165500 | 573672 | 316L | 21,865 | 5,631 | 0,539 | 0,125 |
| 1 | 165500 | 573672 | Co-Cr-Mo | 21,630 | 5,304 | 0,533 | 0,118 |
| 1 | 165500 | 573672 | Ti-6Al-4V | 24,764 | 9,813 | 0,610 | 0,218 |
| 1 | 165500 | 573672 | Ti-6Al-4V poroso | 39,215 | 45,291 | 0,966 | 1,007 |
| 0,75 | 487787 | 1610370 | Fémur intacto | 39,339 | 43,813 | 1,000 | 1,000 |
| 0,75 | 391561 | 1311720 | 316L | 21,169 | 5,584 | 0,538 | 0,127 |
| 0,75 | 391561 | 1311720 | Co-Cr-Mo | 20,951 | 5,270 | 0,533 | 0,120 |
| 0,75 | 391561 | 1311720 | Ti-6Al-4V | 23,901 | 9,624 | 0,608 | 0,220 |
| 0,75 | 391561 | 1311720 | Ti-6Al-4V poroso | 37,874 | 44,055 | 0,963 | 1,006 |

Variação entre as duas malhas mais finas (1 e 0,75 mm), em %:

| Material | Gruen 1 (energia) | Gruen 7 (energia) | Razão G1 | Razão G7 |
|---|---|---|---|---|
| Fémur intacto | 3,2 | 2,6 | 0,0 | 0,0 |
| 316L | 3,3 | 0,8 | 0,1 | 1,7 |
| Co-Cr-Mo | 3,2 | 0,7 | 0,0 | 1,9 |
| Ti-6Al-4V | 3,6 | 2,0 | 0,4 | 0,6 |
| Ti-6Al-4V poroso | 3,5 | 2,8 | 0,3 | 0,2 |

Critério (variação abaixo de 5 % entre as duas malhas mais finas): a razão implantado / intacto (e portanto o stress shielding) cumpre (máximo 1,9 %); a energia absoluta cumpre (máximo 3,6 %).

Ordem pela energia de deformação no osso (malha mais fina, do maior para o menor):

- Gruen 1: Ti-6Al-4V poroso > Ti-6Al-4V > 316L > Co-Cr-Mo
- Gruen 7: Ti-6Al-4V poroso > Ti-6Al-4V > 316L > Co-Cr-Mo

Haste de Ti-6Al-4V poroso (17 GPa, valor de desenho): com interface colada e rigidez igual à do osso cortical, a energia no osso fica próxima da do osso intacto (razão perto de 1); uma razão acima de 1 quer dizer só que o osso à volta trabalha um pouco mais do que no fémur intacto.
