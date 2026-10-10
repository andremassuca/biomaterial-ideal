# Massa e centro de massa da haste femoral

Gerado por scripts/massa_haste.py. Haste Corail tamanho 8 (design/cad/stl/haste_femoral_haste.STL), densidades típicas de data/materiais.csv. A forma é a mesma em todos os materiais.

Volume: 23,8 cm³. Centro de massa da haste (referencial do STL, mm): (-6,3; 82,1; 0,0). Como a densidade é uniforme, o centro de massa da haste é o mesmo com qualquer material (é o centroide da forma).

| Material | Densidade (g/cm³) | Massa da haste (g) |
|---|---|---|
| Co-Cr-Mo forjado | 8,28 | 197 |
| Aço inox 316L | 8,00 | 190 |
| Ti-35Nb-7Zr-5Ta (TNZT) | 5,70 | 136 |
| Ti-13Nb-13Zr | 5,00 | 119 |
| Ti cp grau 4 | 4,51 | 107 |
| Ti-6Al-4V ELI | 4,43 | 105 |

Diferença entre a haste mais pesada e a mais leve: 92 g.

## Efeito no centro de massa do corpo

Com 75 kg de massa corporal (valor de desenho, o da FEA) e a haste a menos de 0,5 m do centro de massa do corpo (majorante de desenho), trocar a haste mais leve pela mais pesada desloca o centro de massa do corpo, no máximo, 0,61 mm (dm x d / M).

Comparação: na marcha normal, o centro de massa sobe e desce 2,7 a 4,8 cm e oscila 3,9 a 7,0 cm para os lados a cada passo (Orendurff MS et al. J Rehabil Res Dev 2004;41:829-834, doi:10.1682/jrrd.2003.10.0150; só resumo). A coxa pesa cerca de 10,6 kg (14,2 % da massa corporal; de Leva P. J Biomech 1996;29:1223-1230, valores lidos numa reprodução da tabela, Healthcare 2022;10:2054, Tabela 5 [confirmar no original]); a diferença entre materiais é 0,9 % da massa da coxa.

Conclusão: o efeito no centro de massa do corpo é desprezável (menos de 0,7 mm, pelo menos 44 vezes menos do que a subida e descida do próprio centro de massa a cada passo). O material da haste não muda o equilíbrio nem a marcha por causa da massa; o que muda é a rigidez (FEA, results/fea_haste.md).

Nota: a massa da haste não é toda massa acrescentada, porque substitui osso e medula retirados. Num estudo que pesou o que se retira e o que se coloca, o ganho mediano com a prótese total não cimentada foi de 145 g (Marmor S et al. Orthop Traumatol Surg Res 2023, doi:10.1016/j.otsr.2022.103298; só resumo).
