# FEA da haste femoral em SOLIDWORKS Simulation (confirmação independente)

Gerado por `python scripts/fea_solidworks.py resumo` a partir de results/fea_haste_sw.json. Hipóteses, fontes e limitações em docs/FEA_HASTE_SW.md; cotas do fémur em design/cad/cotas_femur_fea.md.

O que se mediu: energia de deformação total (J) dos elementos de osso (cortical e trabecular) cujo centro fica em cada zona de Gruen, obtida por elemento na Simulation (componente ENERGY), com o centro de cada elemento lido na malha. Zona 1: lateral (x > 0), do terço proximal da haste (y de 2L/3 = 76,7 mm) até ao corte do colo, incluindo o grande trocânter; zona 7: medial (x < 0), mesma faixa de alturas (calcar). A razão é a energia na zona com a haste a dividir pela do fémur intacto com o mesmo tamanho de malha (1 = igual ao intacto; abaixo de 1 = blindagem de tensões).

## Malha de 3,5 mm (tetraedros parabólicos)

| caso | E da haste (GPa) | nós | elementos | Gruen 1 (mJ) | Gruen 1 / intacto | Gruen 7 (mJ) | Gruen 7 / intacto |
|---|---|---|---|---|---|---|---|
| Intacto | - | 88076 | 54520 | 37,55 | 1,00 | 41,58 | 1,00 |
| Aço inox 316L | 207,5 | 176453 | 111978 | 20,09 | 0,53 | 11,19 | 0,27 |
| Co-Cr-Mo forjado | 225,0 | 176511 | 112022 | 19,83 | 0,53 | 10,54 | 0,25 |
| Ti-6Al-4V ELI | 105,5 | 176622 | 112111 | 23,69 | 0,63 | 18,46 | 0,44 |
| Ti-6Al-4V poroso | 17,0 | 176606 | 112091 | 49,35 | 1,31 | 58,64 | 1,41 |

## Malha de 5,0 mm (tetraedros parabólicos)

| caso | E da haste (GPa) | nós | elementos | Gruen 1 (mJ) | Gruen 1 / intacto | Gruen 7 (mJ) | Gruen 7 / intacto |
|---|---|---|---|---|---|---|---|
| Intacto | - | 35577 | 20985 | 38,08 | 1,00 | 42,09 | 1,00 |
| Aço inox 316L | 207,5 | 127035 | 79182 | 20,22 | 0,53 | 11,37 | 0,27 |
| Co-Cr-Mo forjado | 225,0 | 127066 | 79211 | 19,95 | 0,52 | 10,66 | 0,25 |
| Ti-6Al-4V ELI | 105,5 | 126962 | 79117 | 23,96 | 0,63 | 18,76 | 0,45 |
| Ti-6Al-4V poroso | 17,0 | 127014 | 79165 | 50,12 | 1,32 | 59,25 | 1,41 |

## Ordem dos materiais (malha de 3,5 mm, da maior para a menor energia no osso)

- Gruen 1: Ti-6Al-4V poroso > Ti-6Al-4V ELI > Aço inox 316L > Co-Cr-Mo forjado
- Gruen 7: Ti-6Al-4V poroso > Ti-6Al-4V ELI > Aço inox 316L > Co-Cr-Mo forjado

Leitura da haste de Ti-6Al-4V poroso: deixa no osso proximal uma carga próxima da do osso intacto (razões um pouco acima de 1), porque a interface é colada e a rigidez da haste é igual à do osso cortical (17 GPa, valor de desenho). Lê-se como próxima do osso intacto: a parte acima de 1 é efeito do modelo (haste colada, de rigidez igual à da cortical, dentro de osso trabecular mole), não um ganho clínico.

## Sensibilidade à malha (5,0 mm face a 3,5 mm)

| caso | Gruen 1 (%) | Gruen 7 (%) | mesma ordem nas duas malhas |
|---|---|---|---|
| Intacto | 1,4 | 1,2 | Gruen 1: sim; Gruen 7: sim |
| Aço inox 316L | 0,7 | 1,6 | Gruen 1: sim; Gruen 7: sim |
| Co-Cr-Mo forjado | 0,6 | 1,1 | Gruen 1: sim; Gruen 7: sim |
| Ti-6Al-4V ELI | 1,1 | 1,6 | Gruen 1: sim; Gruen 7: sim |
| Ti-6Al-4V poroso | 1,6 | 1,0 | Gruen 1: sim; Gruen 7: sim |

## Deslocamento máximo e tensão máxima (malha de 3,5 mm)

Nos modelos com a haste a Simulation mostra o aviso de deslocamentos excessivos, respondido com No (ver docs/FEA_HASTE_SW.md); os deslocamentos máximos ficam perto dos do fémur intacto. As imagens em results/figures/fea_sw/ têm a forma deformada exagerada e a escala de cores automática de cada estudo.

| caso | deslocamento máximo (mm) | von Mises máximo no modelo (MPa) |
|---|---|---|
| Intacto | 7,29 | 50,2 |
| Aço inox 316L | 6,28 | 208,8 |
| Co-Cr-Mo forjado | 6,26 | 209,4 |
| Ti-6Al-4V ELI | 6,48 | 202,6 |
| Ti-6Al-4V poroso | 7,51 | 188,0 |
