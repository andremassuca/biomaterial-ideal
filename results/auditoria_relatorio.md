# Auditoria do relatório

Gerado por scripts/auditoria_relatorio.py. Erros: o texto, as tabelas ou as figuras não batem com os resultados. Avisos: sobre resultados deste trabalho, mas não foi possível confirmar automaticamente. Notas: números de outras fontes (registos, literatura, parâmetros), fora do alcance desta auditoria.

| Verificação | Erros | Avisos | Notas | Ok |
|---|---|---|---|---|
| 1. Números dos resumos | 0 | 1 | 26 | 64 |
| 2. Somas do Monte Carlo | 0 | 0 | 0 | 54 |
| 3. Alternativas e cenários | 0 | 0 | 0 | 12 |
| 4. Rankings coerentes | 0 | 0 | 0 | 15 |
| 5. Figuras atualizadas | 0 | 2 | 0 | 6 |
| 6. Semente e versões | 0 | 0 | 0 | 14 |

## Erros (0)

- nenhum

## Avisos (3)

- [1] discussao_rascunho.md:72: "30 a 45 %": não confirmado (caso ou material não identificado)
- [5] fea/sed_corte_coronal (extensoes_rascunho.md): mais antiga do que materiais.csv, criterios.csv, pontuacoes.csv (gerada por outro script; confirmar se depende destes dados)
- [5] cfd/tawss_mapas (extensoes_rascunho.md): mais antiga do que materiais.csv, criterios.csv, pontuacoes.csv (gerada por outro script; confirmar se depende destes dados)

## Notas (números que não são resultados deste trabalho; não verificados) (26)

- [1] 00_resumo_executivo.md:12: "15 %": não é resultado do Monte Carlo; não verificado
- [1] discussao_rascunho.md:10: "31 a 48 %": não é resultado do Monte Carlo; não verificado
- [1] discussao_rascunho.md:10: "48,6 %": não é resultado do Monte Carlo; não verificado
- [1] discussao_rascunho.md:10: "18,1 %": não é resultado do Monte Carlo; não verificado
- [1] discussao_rascunho.md:10: "1 %": não é resultado do Monte Carlo; não verificado
- [1] discussao_rascunho.md:41: "42,5 %": não é resultado do Monte Carlo; não verificado
- [1] discussao_rascunho.md:41: "41,8 %": não é resultado do Monte Carlo; não verificado
- [1] discussao_rascunho.md:41: "62,9 %": não é resultado do Monte Carlo; não verificado
- [1] discussao_rascunho.md:41: "35,7 %": não é resultado do Monte Carlo; não verificado
- [1] discussao_rascunho.md:42: "59 %": não é resultado do Monte Carlo; não verificado
- [1] discussao_rascunho.md:42: "33 %": não é resultado do Monte Carlo; não verificado
- [1] discussao_rascunho.md:42: "97 %": não é resultado do Monte Carlo; não verificado
- [1] discussao_rascunho.md:42: "2 %": não é resultado do Monte Carlo; não verificado
- [1] discussao_rascunho.md:65: "60 %": não é resultado do Monte Carlo; não verificado
- [1] discussao_rascunho.md:65: "59,9 %": não é resultado do Monte Carlo; não verificado
- [1] discussao_rascunho.md:65: "60 %": não é resultado do Monte Carlo; não verificado
- [1] discussao_rascunho.md:67: "47 %": não é resultado do Monte Carlo; não verificado
- [1] discussao_rascunho.md:67: "82 %": não é resultado do Monte Carlo; não verificado
- [1] discussao_rascunho.md:67: "98 %": não é resultado do Monte Carlo; não verificado
- [1] discussao_rascunho.md:67: "99 %": não é resultado do Monte Carlo; não verificado
- [1] conclusao_rascunho.md:12: "2,3 %": não é resultado do Monte Carlo; não verificado
- [1] conclusao_rascunho.md:13: "47 %": não é resultado do Monte Carlo; não verificado
- [1] conclusao_rascunho.md:13: "82 %": não é resultado do Monte Carlo; não verificado
- [1] conclusao_rascunho.md:14: contagem "26 das 44": não confirmada automaticamente
- [1] conclusao_rascunho.md:19: "60 %": não é resultado do Monte Carlo; não verificado
- [1] conclusao_rascunho.md:19: "59,9 %": não é resultado do Monte Carlo; não verificado

## Confirmado (165)

- [1] resumo_rascunho.md:7: "pelo menos 9 999 das 10 000 repetições" (Ti-6Al-4V ELI, Haste): mínimo nos resultados = 9 999 (três métodos, propriedades e pesos)
- [1] resumo_rascunho.md:7: "5 das 6 combinações" (Compósito PCL/β-TCP (impressão 3D), Scaffold): nos resultados, 1.º em 5 de 6
- [1] resumo_rascunho.md:7: Ti-6Al-4V ELI 1.º com os três métodos nos dois cenários (Haste)
- [1] resumo_rascunho.md:7: Pt-Cr mais vezes em 1.º (Stent, MC propriedades): lidera em TOPSIS, WASPAS, VIKOR de TOPSIS, WASPAS, VIKOR
- [1] resumo_rascunho.md:7: β-TCP poroso mais vezes em 1.º (Scaffold, MC propriedades): lidera em TOPSIS, WASPAS, VIKOR de TOPSIS, WASPAS, VIKOR
- [1] resumo_rascunho.md:7: ZTA / ZTA (CoC) com a melhor pontuação (Par articular): 1.º em 3 de 3 combinações
- [1] resumo_rascunho.md:7: Ti cp grau 4 com a melhor pontuação (Implante dentário): 1.º em 12 de 12 combinações
- [1] abstract_rascunho.md:7: "at least 9,999 of the 10,000 Monte Carlo repetitions" (Ti-6Al-4V ELI, Haste): mínimo nos resultados = 9 999 (três métodos, propriedades e pesos)
- [1] abstract_rascunho.md:7: "5 of the 6 method and scenario combinations" (Compósito PCL/β-TCP (impressão 3D), Scaffold): nos resultados, 1.º em 5 de 6
- [1] abstract_rascunho.md:7: Ti-6Al-4V ELI 1.º com os três métodos nos dois cenários (Haste)
- [1] abstract_rascunho.md:7: Pt-Cr mais vezes em 1.º (Stent, MC propriedades): lidera em TOPSIS, WASPAS, VIKOR de TOPSIS, WASPAS, VIKOR
- [1] abstract_rascunho.md:7: β-TCP poroso mais vezes em 1.º (Scaffold, MC propriedades): lidera em TOPSIS, WASPAS, VIKOR de TOPSIS, WASPAS, VIKOR
- [1] abstract_rascunho.md:7: ZTA / ZTA (CoC) com a melhor pontuação (Par articular): 1.º em 3 de 3 combinações
- [1] abstract_rascunho.md:7: Ti cp grau 4 com a melhor pontuação (Implante dentário): 1.º em 12 de 12 combinações
- [1] 00_resumo_executivo.md:14: "5 das 6 combinações" (Compósito PCL/β-TCP (impressão 3D), Scaffold): nos resultados, 1.º em 5 de 6
- [1] discussao_rascunho.md:6: "pelo menos 9 999 das 10 000 repetições" (Ti-6Al-4V ELI, Haste): mínimo nos resultados = 9 999 (três métodos, propriedades e pesos)
- [1] discussao_rascunho.md:6: Ti-6Al-4V ELI 1.º com os três métodos nos dois cenários (Haste)
- [1] discussao_rascunho.md:7: "56 a 70 %" (Pt-Cr, Stent, MC propriedades): nos resultados, 55.90 a 69.67 %
- [1] discussao_rascunho.md:7: Pt-Cr mais vezes em 1.º (Stent, MC propriedades): lidera em TOPSIS, WASPAS, VIKOR de TOPSIS, WASPAS, VIKOR
- [1] discussao_rascunho.md:7: "±20 %": análise do Monte Carlo
- [1] discussao_rascunho.md:7: "99,97 %": Co-Cr L605, W pesos ±20 %, WASPAS (99.97 %)
- [1] discussao_rascunho.md:7: "83,2 %": Pt-Cr, W pesos ±20 %, TOPSIS (83.22 %)
- [1] discussao_rascunho.md:7: "59,0 %": Pt-Cr, W pesos ±20 %, VIKOR (59.01 %)
- [1] discussao_rascunho.md:7: ΔC = 0,022 (Stent, A): resultados 0.0222
- [1] discussao_rascunho.md:7: ΔC = 0,002 (Stent, B): resultados 0.0021
- [1] discussao_rascunho.md:7: ΔC = 0,002 (Stent, B): resultados 0.0021
- [1] discussao_rascunho.md:8: "5 das 6 combinações" (Compósito PCL/β-TCP (impressão 3D), Scaffold): nos resultados, 1.º em 5 de 6
- [1] discussao_rascunho.md:8: "5 das 6 combinações" (Compósito PCL/β-TCP (impressão 3D), Scaffold): nos resultados, 1.º em 5 de 6
- [1] discussao_rascunho.md:8: β-TCP poroso mais vezes em 1.º (Scaffold, MC propriedades): lidera em TOPSIS, WASPAS, VIKOR de TOPSIS, WASPAS, VIKOR
- [1] discussao_rascunho.md:8: "66,9 %": β-TCP poroso, MC propriedades, TOPSIS (66.90 %)
- [1] discussao_rascunho.md:8: "46,1 %": β-TCP poroso, MC propriedades, WASPAS (46.12 %)
- [1] discussao_rascunho.md:8: "54,0 %": β-TCP poroso, MC propriedades, VIKOR (54.05 %)
- [1] discussao_rascunho.md:8: "7,2 %": Compósito PCL/β-TCP (impressão 3D), MC propriedades, TOPSIS (7.24 %)
- [1] discussao_rascunho.md:8: "27,5 %": Compósito PCL/β-TCP (impressão 3D), MC propriedades, WASPAS (27.50 %)
- [1] discussao_rascunho.md:8: "16,7 %": Compósito PCL/β-TCP (impressão 3D), MC propriedades, VIKOR (16.66 %)
- [1] discussao_rascunho.md:8: "±20 %": análise do Monte Carlo
- [1] discussao_rascunho.md:8: "98,7 %": Compósito PCL/β-TCP (impressão 3D), W pesos ±20 %, WASPAS (98.72 %)
- [1] discussao_rascunho.md:8: "68,0 %": Compósito PCL/β-TCP (impressão 3D), W pesos ±20 %, VIKOR (67.96 %)
- [1] discussao_rascunho.md:8: "74,5 %": β-TCP poroso, W pesos ±20 %, TOPSIS (74.51 %)
- [1] discussao_rascunho.md:8: ΔC = 0,019 (Scaffold, A): resultados 0.0190
- [1] discussao_rascunho.md:8: ΔC = 0,016 (Scaffold, B): resultados 0.0158
- [1] discussao_rascunho.md:12: "84,6 %": β-TCP poroso, MC triangular, TOPSIS (84.63 %)
- [1] discussao_rascunho.md:12: "56,9 %": β-TCP poroso, MC triangular, WASPAS (56.92 %)
- [1] discussao_rascunho.md:12: "71,2 %": β-TCP poroso, MC triangular, VIKOR (71.21 %)
- [1] discussao_rascunho.md:80: "±20 %": análise do Monte Carlo
- [1] conclusao_rascunho.md:9: "pelo menos 9 999 de 10 000 repetições" (Ti-6Al-4V ELI, Haste): mínimo nos resultados = 9 999 (três métodos, propriedades e pesos)
- [1] conclusao_rascunho.md:9: ΔC = 0,175 (Haste, A): resultados 0.1746
- [1] conclusao_rascunho.md:10: "56 a 70 %" (Pt-Cr, Stent, MC propriedades): nos resultados, 55.90 a 69.67 %
- [1] conclusao_rascunho.md:10: "99,97 %": Co-Cr L605, W pesos ±20 %, WASPAS (99.97 %)
- [1] conclusao_rascunho.md:10: "±20 %": análise do Monte Carlo
- [1] conclusao_rascunho.md:10: ΔC = 0,022 (Stent, A): resultados 0.0222
- [1] conclusao_rascunho.md:10: ΔC = 0,002 (Stent, B): resultados 0.0021
- [1] conclusao_rascunho.md:11: "5 das 6 combinações" (Compósito PCL/β-TCP (impressão 3D), Scaffold): nos resultados, 1.º em 5 de 6
- [1] conclusao_rascunho.md:11: "46 a 67 %" (β-TCP poroso, Scaffold, MC propriedades): nos resultados, 46.12 a 66.90 %
- [1] conclusao_rascunho.md:19: "pelo menos 9 999 das 10 000 repetições" (Ti-6Al-4V ELI, Haste): mínimo nos resultados = 9 999 (três métodos, propriedades e pesos)
- [1] conclusao_rascunho.md:20: ZTA / ZTA (CoC) com a melhor pontuação (Par articular): 1.º em 3 de 3 combinações
- [1] conclusao_rascunho.md:21: "56 a 70 %" (Pt-Cr, Stent, MC propriedades): nos resultados, 55.90 a 69.67 %
- [1] conclusao_rascunho.md:21: Pt-Cr mais vezes em 1.º (Stent, MC propriedades): lidera em TOPSIS, WASPAS, VIKOR de TOPSIS, WASPAS, VIKOR
- [1] conclusao_rascunho.md:21: "99,97 %": Co-Cr L605, W pesos ±20 %, WASPAS (99.97 %)
- [1] conclusao_rascunho.md:21: ΔC = 0,002 (Stent, B): resultados 0.0021
- [1] conclusao_rascunho.md:22: "5 das 6 combinações" (Compósito PCL/β-TCP (impressão 3D), Scaffold): nos resultados, 1.º em 5 de 6
- [1] conclusao_rascunho.md:22: "5 das 6 combinações" (Compósito PCL/β-TCP (impressão 3D), Scaffold): nos resultados, 1.º em 5 de 6
- [1] conclusao_rascunho.md:22: β-TCP poroso mais vezes em 1.º (Scaffold, MC propriedades): lidera em TOPSIS, WASPAS, VIKOR de TOPSIS, WASPAS, VIKOR
- [1] conclusao_rascunho.md:22: ΔC = 0,019 (Scaffold, A): resultados 0.0190
- [2] Haste, MC propriedades, TOPSIS: soma de pct_primeiro = 100.000 %
- [2] Haste, MC propriedades, TOPSIS: soma de pct_segundo = 100.000 %
- [2] Haste, MC propriedades, TOPSIS: soma de pct_terceiro = 100.000 %
- [2] Haste, MC propriedades, WASPAS: soma de pct_primeiro = 100.000 %
- [2] Haste, MC propriedades, WASPAS: soma de pct_segundo = 100.000 %
- [2] Haste, MC propriedades, WASPAS: soma de pct_terceiro = 100.000 %
- [2] Haste, MC propriedades, VIKOR: soma de pct_primeiro = 100.000 %
- [2] Haste, MC propriedades, VIKOR: soma de pct_segundo = 100.000 %
- [2] Haste, MC propriedades, VIKOR: soma de pct_terceiro = 100.000 %
- [2] Haste, W pesos ±20 %, TOPSIS: soma de pct_primeiro = 100.000 %
- [2] Haste, W pesos ±20 %, TOPSIS: soma de pct_segundo = 100.000 %
- [2] Haste, W pesos ±20 %, TOPSIS: soma de pct_terceiro = 100.000 %
- [2] Haste, W pesos ±20 %, WASPAS: soma de pct_primeiro = 100.000 %
- [2] Haste, W pesos ±20 %, WASPAS: soma de pct_segundo = 100.000 %
- [2] Haste, W pesos ±20 %, WASPAS: soma de pct_terceiro = 100.000 %
- [2] Haste, W pesos ±20 %, VIKOR: soma de pct_primeiro = 100.000 %
- [2] Haste, W pesos ±20 %, VIKOR: soma de pct_segundo = 100.000 %
- [2] Haste, W pesos ±20 %, VIKOR: soma de pct_terceiro = 100.000 %
- [2] Stent, MC propriedades, TOPSIS: soma de pct_primeiro = 100.000 %
- [2] Stent, MC propriedades, TOPSIS: soma de pct_segundo = 100.000 %
- [2] Stent, MC propriedades, TOPSIS: soma de pct_terceiro = 100.000 %
- [2] Stent, MC propriedades, WASPAS: soma de pct_primeiro = 100.000 %
- [2] Stent, MC propriedades, WASPAS: soma de pct_segundo = 100.000 %
- [2] Stent, MC propriedades, WASPAS: soma de pct_terceiro = 100.000 %
- [2] Stent, MC propriedades, VIKOR: soma de pct_primeiro = 100.000 %
- [2] Stent, MC propriedades, VIKOR: soma de pct_segundo = 100.000 %
- [2] Stent, MC propriedades, VIKOR: soma de pct_terceiro = 100.000 %
- [2] Stent, W pesos ±20 %, TOPSIS: soma de pct_primeiro = 100.000 %
- [2] Stent, W pesos ±20 %, TOPSIS: soma de pct_segundo = 100.000 %
- [2] Stent, W pesos ±20 %, TOPSIS: soma de pct_terceiro = 100.000 %
- [2] Stent, W pesos ±20 %, WASPAS: soma de pct_primeiro = 100.000 %
- [2] Stent, W pesos ±20 %, WASPAS: soma de pct_segundo = 100.000 %
- [2] Stent, W pesos ±20 %, WASPAS: soma de pct_terceiro = 100.000 %
- [2] Stent, W pesos ±20 %, VIKOR: soma de pct_primeiro = 100.000 %
- [2] Stent, W pesos ±20 %, VIKOR: soma de pct_segundo = 100.000 %
- [2] Stent, W pesos ±20 %, VIKOR: soma de pct_terceiro = 100.000 %
- [2] Scaffold, MC propriedades, TOPSIS: soma de pct_primeiro = 100.000 %
- [2] Scaffold, MC propriedades, TOPSIS: soma de pct_segundo = 100.000 %
- [2] Scaffold, MC propriedades, TOPSIS: soma de pct_terceiro = 100.000 %
- [2] Scaffold, MC propriedades, WASPAS: soma de pct_primeiro = 100.000 %
- [2] Scaffold, MC propriedades, WASPAS: soma de pct_segundo = 100.000 %
- [2] Scaffold, MC propriedades, WASPAS: soma de pct_terceiro = 100.000 %
- [2] Scaffold, MC propriedades, VIKOR: soma de pct_primeiro = 100.090 %
- [2] Scaffold, MC propriedades, VIKOR: soma de pct_segundo = 99.990 %
- [2] Scaffold, MC propriedades, VIKOR: soma de pct_terceiro = 99.950 %
- [2] Scaffold, W pesos ±20 %, TOPSIS: soma de pct_primeiro = 100.000 %
- [2] Scaffold, W pesos ±20 %, TOPSIS: soma de pct_segundo = 100.000 %
- [2] Scaffold, W pesos ±20 %, TOPSIS: soma de pct_terceiro = 100.000 %
- [2] Scaffold, W pesos ±20 %, WASPAS: soma de pct_primeiro = 100.000 %
- [2] Scaffold, W pesos ±20 %, WASPAS: soma de pct_segundo = 100.000 %
- [2] Scaffold, W pesos ±20 %, WASPAS: soma de pct_terceiro = 100.000 %
- [2] Scaffold, W pesos ±20 %, VIKOR: soma de pct_primeiro = 100.000 %
- [2] Scaffold, W pesos ±20 %, VIKOR: soma de pct_segundo = 100.000 %
- [2] Scaffold, W pesos ±20 %, VIKOR: soma de pct_terceiro = 100.000 %
- [3] results/pontuacoes.csv, Haste A: 5 materiais, todos presentes
- [3] tabelas/haste_resultados.md, Haste A: 5 materiais, todos presentes
- [3] results/pontuacoes.csv, Haste B: 6 materiais, todos presentes
- [3] tabelas/haste_resultados.md, Haste B: 6 materiais, todos presentes
- [3] results/pontuacoes.csv, Stent A: 4 materiais, todos presentes
- [3] tabelas/stent_resultados.md, Stent A: 4 materiais, todos presentes
- [3] results/pontuacoes.csv, Stent B: 6 materiais, todos presentes
- [3] tabelas/stent_resultados.md, Stent B: 6 materiais, todos presentes
- [3] results/pontuacoes.csv, Scaffold A: 5 materiais, todos presentes
- [3] tabelas/scaffold_resultados.md, Scaffold A: 5 materiais, todos presentes
- [3] results/pontuacoes.csv, Scaffold B: 8 materiais, todos presentes
- [3] tabelas/scaffold_resultados.md, Scaffold B: 8 materiais, todos presentes
- [4] results/pontuacoes.csv, Haste A: 5 materiais coerentes
- [4] results/pontuacoes.csv, Haste B: 6 materiais coerentes
- [4] results/pontuacoes.csv, Stent A: 4 materiais coerentes
- [4] results/pontuacoes.csv, Stent B: 6 materiais coerentes
- [4] results/pontuacoes.csv, Scaffold A: 5 materiais coerentes
- [4] results/pontuacoes.csv, Scaffold B: 8 materiais coerentes
- [4] tabelas/haste_resultados.md, Haste A: 5 materiais coerentes
- [4] tabelas/haste_resultados.md, Haste B: 6 materiais coerentes
- [4] tabela Haste: 11 linhas iguais a pontuacoes.csv
- [4] tabelas/stent_resultados.md, Stent A: 4 materiais coerentes
- [4] tabelas/stent_resultados.md, Stent B: 6 materiais coerentes
- [4] tabela Stent: 10 linhas iguais a pontuacoes.csv
- [4] tabelas/scaffold_resultados.md, Scaffold A: 5 materiais coerentes
- [4] tabelas/scaffold_resultados.md, Scaffold B: 8 materiais coerentes
- [4] tabela Scaffold: 13 linhas iguais a pontuacoes.csv
- [5] fig_a_rigidez_haste (caso_anca_rascunho.md): igual à figura refeita com os dados atuais
- [5] fig_b_posicoes (caso_anca_rascunho.md, caso_scaffold_rascunho.md, caso_stent_rascunho.md): igual à figura refeita com os dados atuais
- [5] fig_c_monte_carlo (caso_anca_rascunho.md, caso_scaffold_rascunho.md, caso_stent_rascunho.md): igual à figura refeita com os dados atuais
- [5] fig_d_vencedor_eta (caso_anca_rascunho.md, caso_scaffold_rascunho.md, caso_stent_rascunho.md): igual à figura refeita com os dados atuais
- [5] fig_f_semiquantitativos (caso_anca_rascunho.md, caso_dentario_rascunho.md): igual à figura refeita com os dados atuais
- [5] funil (extensoes_rascunho.md): posterior aos dados e às pontuações
- [6] semente (42): declarado
- [6] iterações (10 000): declarado
- [6] versão do Python: declarado
- [6] versão de NumPy: declarado
- [6] versão de pandas: declarado
- [6] versão de SciPy: declarado
- [6] versão de Matplotlib: declarado
- [6] versão de gmsh: declarado
- [6] versão de scikit-fem: declarado
- [6] versão de pyamg: declarado
- [6] versão do OpenFOAM: declarado
- [6] versão do Ansys: declarado
- [6] versão do SOLIDWORKS: declarado
- [6] versão do MATLAB: declarado
