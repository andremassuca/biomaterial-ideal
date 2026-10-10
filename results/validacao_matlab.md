# Validação em MATLAB do TOPSIS, WASPAS e VIKOR

Gerado por matlab/validar_mcdm.m (25.2.0.3055257 (R2025b) Update 2). Implementação independente dos três métodos com critérios-alvo (Petković et al. 2025), sobre os mesmos problemas de decisão (app-nativa/dados/caso_*.json, gerados de data/), comparada com results/pontuacoes.csv (Python).

| Caso | Cenário | Materiais | Diferença máx. em C (TOPSIS) | em Q (WASPAS) | em P (VIKOR) |
|---|---|---|---|---|---|
| Haste | A | 5 | 1,1e-16 | 1,1e-16 | 1,1e-16 |
| Haste | B | 6 | 1,1e-16 | 1,1e-16 | 1,1e-16 |
| Stent | A | 4 | 0,0e+00 | 0,0e+00 | 0,0e+00 |
| Stent | B | 6 | 2,8e-17 | 0,0e+00 | 0,0e+00 |
| Scaffold | A | 5 | 1,1e-16 | 1,1e-16 | 0,0e+00 |
| Scaffold | B | 8 | 0,0e+00 | 1,1e-16 | 4,4e-16 |

Diferença máxima em todos os casos: 4,4e-16 (34 materiais). Critério: abaixo de 1e-6. Cumpre.
