# FEA da haste: verificações de sanidade

Gerado por scripts/fea_haste.py --verificacoes (malha de 0,75 mm). Unidades: mm, N, MPa, mJ. Referencial da haste: x lateral, y ao longo da haste (ponta em y = 0), z normal ao plano da haste.

## Equilíbrio (soma das cargas aplicadas e soma das reações no corte da diáfise)

| Modelo | Cargas aplicadas (x; y; z, N) | Reações (x; y; z, N) | Erro (%) | Resíduo nodal máximo (N) |
|---|---|---|---|---|
| Fémur intacto | 121,6; -1047,3; 188,7 | -121,6; 1047,3; -188,7 | 3,8e-08 | 6,7e-10 |
| Ti-6Al-4V | 121,6; -1047,3; 188,7 | -121,6; 1047,3; -188,7 | 5,6e-07 | 1,6e-09 |
| Co-Cr-Mo | 121,6; -1047,3; 188,7 | -121,6; 1047,3; -188,7 | 6,8e-07 | 1,6e-09 |

## Deslocamentos

| Modelo | Máximo (mm) | Onde (x; y; z, mm) | Centro da cabeça (ux; uy; uz, mm) |
|---|---|---|---|
| Fémur intacto | 5,28 | -42; 154; 3 | -3,29; -1,11; 2,86 |
| Ti-6Al-4V | 4,64 | -41; 148; 2 | -3,13; -0,96; 2,56 |
| Co-Cr-Mo | 4,41 | -41; 148; 2 | -2,98; -0,85; 2,50 |

## Deformações principais no osso cortical do fémur intacto (microdeformações)

Diáfise (de 10 mm acima do encastramento até à altura da ponta da haste):

| Grandeza | Mediana | Percentil 95 (ou 5) | Percentil 99 (ou 1) | Extremo |
|---|---|---|---|---|
| Máxima (tração) | 592 | 1921 | 2187 | 2972 |
| Mínima (compressão) | -592 | -2196 | -2441 | -3202 |

Todo o cortical: percentil 99 da máxima 2053; percentil 1 da mínima -2353.

Deformação axial (ao longo da haste) mediana na diáfise: lado lateral 1064, lado medial -1456 (positivo = tração).
