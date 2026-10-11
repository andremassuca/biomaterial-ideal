# Robustez complementar (PRELIMINAR: dados por verificar)

Valores típicos da base, η = 1. Monte Carlo das dimensões: 10000 iterações, seed 42, Dirichlet com α = 1 dentro de cada dimensão (peso total da dimensão fixo; mapa critério → dimensão em data/dimensoes_criterios.csv).

Regra de empate: no TOPSIS, ΔC < 0,01 conta como empate. As trocas de vencedor são estritas (outro material passa a ter melhor pontuação); no TOPSIS indica-se também quando o vencedor deixa de ter folga de 0,01 (empate), que acontece sempre antes da troca. Na reversão de ranking, os pares do TOPSIS que trocam com ΔC < 0,01 (antes ou depois) ficam marcados como empate.

Menor ajuste: pesos de -100 % a +100 % (um peso de cada vez, os outros renormalizados na mesma proporção); valores típicos até ±50 % (ordinais 1-5 em passos inteiros dentro da escala); varrimento em passos de 0,5 % e bisseção.

## Haste, cenário A

Vencedores: TOPSIS Ti-6Al-4V ELI (ΔC = 0,175); WASPAS Ti-6Al-4V ELI; VIKOR Ti-6Al-4V ELI.

### a) Retirar uma alternativa

| Retirado | TOPSIS | WASPAS | VIKOR | Pares que trocam |
|---|---|---|---|---|
| Aço inox 316L | sim | não | sim | TOPSIS: Co-Cr-Mo forjado ↔ Ti-13Nb-13Zr; VIKOR: Co-Cr-Mo forjado ↔ Ti cp grau 4 |
| Co-Cr-Mo forjado | não | não | não | nenhum |
| Ti-6Al-4V ELI | não | não | não | nenhum |
| Ti cp grau 4 | não | não | sim | VIKOR: Ti-13Nb-13Zr ↔ Aço inox 316L; Ti-13Nb-13Zr ↔ Co-Cr-Mo forjado |
| Ti-13Nb-13Zr | não | não | sim | VIKOR: Co-Cr-Mo forjado ↔ Aço inox 316L |

O 1.º lugar entre os restantes nunca muda ao retirar um material.

### b) Dupla contagem (pesos redistribuídos dentro de cada dimensão)

Peso por dimensão: mecânica 0,60; biológica 0,15; clínica 0,10; económica 0,15.

| Método | Vencedor (pesos da base) | Pesos iguais na dimensão | MC: mantém o 1.º | Outro 1.º mais frequente |
|---|---|---|---|---|
| TOPSIS | Ti-6Al-4V ELI | Ti-6Al-4V ELI | 92,5 % (93,6 % com empates) | Co-Cr-Mo forjado (5,1 %) |
| WASPAS | Ti-6Al-4V ELI | Ti-6Al-4V ELI | 95,9 % | Ti-13Nb-13Zr (2,4 %) |
| VIKOR | Ti-6Al-4V ELI | Ti-6Al-4V ELI | 84,8 % | Ti-13Nb-13Zr (12,7 %) |

### c) Menor ajuste que troca o 1.º lugar

**Pesos**

| Critério | Peso | TOPSIS | WASPAS | VIKOR |
|---|---|---|---|---|
| Resistência à fadiga a 10⁷ ciclos (σmax, R = 0,1) | 0,250 | +48,6 % (Co-Cr-Mo forjado) | não troca até ±100 % | +85,5 % (Co-Cr-Mo forjado) |
| Módulo de Young | 0,200 | não troca até ±100 % | não troca até ±100 % | não troca até ±100 % |
| Tensão de cedência | 0,100 | não troca até ±100 % | não troca até ±100 % | não troca até ±100 % |
| Resistência à corrosão (ordinal 1-5) | 0,150 | não troca até ±100 % | não troca até ±100 % | não troca até ±100 % |
| Densidade | 0,050 | não troca até ±100 % | não troca até ±100 % | não troca até ±100 % |
| Compatibilidade com RM (ordinal 1-5) | 0,100 | não troca até ±100 % | não troca até ±100 % | não troca até ±100 % |
| Custo relativo de material e fabrico (1-5, 5 = mais caro) | 0,050 | não troca até ±100 % | não troca até ±100 % | não troca até ±100 % |
| Fabricabilidade (ordinal 1-5) | 0,100 | não troca até ±100 % | não troca até ±100 % | não troca até ±100 % |

**Valores típicos (os 12 mais sensíveis)**

| Material | Critério | Valor | Variação que troca | Método(s) | Novo 1.º | Estado | Fonte |
|---|---|---|---|---|---|---|---|
| Ti-6Al-4V ELI | Resistência à fadiga a 10⁷ ciclos (σmax, R = 0,1) | 682 | -18,1 % | TOPSIS | Co-Cr-Mo forjado | Verificado (derivado) | Okazaki 2012 |
| Ti-13Nb-13Zr | Resistência à fadiga a 10⁷ ciclos (σmax, R = 0,1) | 550 | +30,3 % | VIKOR | Ti-13Nb-13Zr | A verificar | Geetha 2009 |
| Ti cp grau 4 | Resistência à fadiga a 10⁷ ciclos (σmax, R = 0,1) | 483 | +48,2 % | VIKOR | Ti cp grau 4 | Verificado (derivado) | Okazaki 2012 |
| Ti-6Al-4V ELI | Resistência à corrosão (ordinal 1-5) | 5 (ordinal) | -3 pontos (-60,0 %) | TOPSIS, WASPAS | Co-Cr-Mo forjado | A verificar | Escala ordinal definida no trabalho |
| Ti-6Al-4V ELI | Compatibilidade com RM (ordinal 1-5) | 4 (ordinal) | -3 pontos (-75,0 %) | WASPAS | Ti-13Nb-13Zr | A verificar | Shellock FG / MRIsafety.com |
| Ti-6Al-4V ELI | Fabricabilidade (ordinal 1-5) | 5 (ordinal) | -4 pontos (-80,0 %) | WASPAS | Ti-13Nb-13Zr | A verificar | Geetha 2009 |

No TOPSIS, menor variação que deixa o vencedor em empate (ΔC < 0,01): peso: Resistência à fadiga a 10⁷ ciclos (σmax, R = 0,1) +45,4 %; valor: Ti-6Al-4V ELI / Resistência à fadiga a 10⁷ ciclos (σmax, R = 0,1) -16,9 %.

## Haste, cenário B

Vencedores: TOPSIS Ti-6Al-4V ELI (ΔC = 0,140); WASPAS Ti-6Al-4V ELI; VIKOR Ti-6Al-4V ELI.

### a) Retirar uma alternativa

| Retirado | TOPSIS | WASPAS | VIKOR | Pares que trocam |
|---|---|---|---|---|
| Aço inox 316L | não | não | não | nenhum |
| Co-Cr-Mo forjado | não | não | não | nenhum |
| Ti-6Al-4V ELI | não | não | não | nenhum |
| Ti cp grau 4 | não | não | não | nenhum |
| Ti-13Nb-13Zr | não | não | não | nenhum |
| Ti-35Nb-7Zr-5Ta (TNZT) | sim | não | sim | TOPSIS: Ti cp grau 4 ↔ Aço inox 316L; Ti cp grau 4 ↔ Co-Cr-Mo forjado; Ti-13Nb-13Zr ↔ Co-Cr-Mo forjado; VIKOR: Ti cp grau 4 ↔ Aço inox 316L; Ti cp grau 4 ↔ Co-Cr-Mo forjado |

O 1.º lugar entre os restantes nunca muda ao retirar um material.

### b) Dupla contagem (pesos redistribuídos dentro de cada dimensão)

Peso por dimensão: mecânica 0,60; biológica 0,15; clínica 0,10; económica 0,15.

| Método | Vencedor (pesos da base) | Pesos iguais na dimensão | MC: mantém o 1.º | Outro 1.º mais frequente |
|---|---|---|---|---|
| TOPSIS | Ti-6Al-4V ELI | Ti-6Al-4V ELI | 91,0 % (93,5 % com empates) | Ti-13Nb-13Zr (5,5 %) |
| WASPAS | Ti-6Al-4V ELI | Ti-6Al-4V ELI | 95,9 % | Ti-13Nb-13Zr (1,9 %) |
| VIKOR | Ti-6Al-4V ELI | Ti-6Al-4V ELI | 79,2 % | Ti-13Nb-13Zr (15,6 %) |

### c) Menor ajuste que troca o 1.º lugar

**Pesos**

| Critério | Peso | TOPSIS | WASPAS | VIKOR |
|---|---|---|---|---|
| Resistência à fadiga a 10⁷ ciclos (σmax, R = 0,1) | 0,250 | não troca até ±100 % | não troca até ±100 % | -65,0 % (Ti-13Nb-13Zr) |
| Módulo de Young | 0,200 | não troca até ±100 % | não troca até ±100 % | +78,2 % (Ti-13Nb-13Zr) |
| Tensão de cedência | 0,100 | não troca até ±100 % | não troca até ±100 % | não troca até ±100 % |
| Resistência à corrosão (ordinal 1-5) | 0,150 | não troca até ±100 % | não troca até ±100 % | não troca até ±100 % |
| Densidade | 0,050 | não troca até ±100 % | não troca até ±100 % | não troca até ±100 % |
| Compatibilidade com RM (ordinal 1-5) | 0,100 | não troca até ±100 % | não troca até ±100 % | não troca até ±100 % |
| Custo relativo de material e fabrico (1-5, 5 = mais caro) | 0,050 | não troca até ±100 % | não troca até ±100 % | não troca até ±100 % |
| Fabricabilidade (ordinal 1-5) | 0,100 | não troca até ±100 % | não troca até ±100 % | não troca até ±100 % |

**Valores típicos (os 12 mais sensíveis)**

| Material | Critério | Valor | Variação que troca | Método(s) | Novo 1.º | Estado | Fonte |
|---|---|---|---|---|---|---|---|
| Ti-6Al-4V ELI | Resistência à fadiga a 10⁷ ciclos (σmax, R = 0,1) | 682 | -23,5 % | TOPSIS | Ti-13Nb-13Zr | Verificado (derivado) | Okazaki 2012 |
| Ti-13Nb-13Zr | Resistência à fadiga a 10⁷ ciclos (σmax, R = 0,1) | 550 | +25,6 % | VIKOR | Ti-13Nb-13Zr | A verificar | Geetha 2009 |
| Ti-6Al-4V ELI | Resistência à corrosão (ordinal 1-5) | 5 (ordinal) | -2 pontos (-40,0 %) | TOPSIS, VIKOR | Ti-13Nb-13Zr | A verificar | Escala ordinal definida no trabalho |
| Ti-6Al-4V ELI | Compatibilidade com RM (ordinal 1-5) | 4 (ordinal) | -3 pontos (-75,0 %) | WASPAS | Ti-13Nb-13Zr | A verificar | Shellock FG / MRIsafety.com |
| Ti-6Al-4V ELI | Fabricabilidade (ordinal 1-5) | 5 (ordinal) | -4 pontos (-80,0 %) | WASPAS | Ti-13Nb-13Zr | A verificar | Geetha 2009 |

No TOPSIS, menor variação que deixa o vencedor em empate (ΔC < 0,01): peso: Resistência à fadiga a 10⁷ ciclos (σmax, R = 0,1) +95,1 %; valor: Ti-6Al-4V ELI / Resistência à fadiga a 10⁷ ciclos (σmax, R = 0,1) -21,8 %.

## Stent, cenário A

Vencedores: TOPSIS Pt-Cr (ΔC = 0,022); WASPAS Co-Cr L605; VIKOR Pt-Cr.

### a) Retirar uma alternativa

| Retirado | TOPSIS | WASPAS | VIKOR | Pares que trocam |
|---|---|---|---|---|
| Aço inox 316L | sim | não | sim | TOPSIS: Pt-Cr ↔ Co-Cr L605; VIKOR: Pt-Cr ↔ Co-Cr L605 |
| Co-Cr L605 | não | não | não | nenhum |
| Co-Ni-Cr-Mo MP35N | não | não | sim | VIKOR: Pt-Cr ↔ Co-Cr L605 |
| Pt-Cr | não | não | não | nenhum |

O 1.º lugar entre os restantes muda em: TOPSIS sem Aço inox 316L (Pt-Cr → Co-Cr L605); VIKOR sem Aço inox 316L (Pt-Cr → Co-Cr L605); VIKOR sem Co-Ni-Cr-Mo MP35N (Pt-Cr → Co-Cr L605).

### b) Dupla contagem (pesos redistribuídos dentro de cada dimensão)

Peso por dimensão: mecânica 0,65; clínica 0,18; económica 0,18.

| Método | Vencedor (pesos da base) | Pesos iguais na dimensão | MC: mantém o 1.º | Outro 1.º mais frequente |
|---|---|---|---|---|
| TOPSIS | Pt-Cr | Co-Ni-Cr-Mo MP35N | 29,1 % (30,4 % com empates) | Co-Ni-Cr-Mo MP35N (39,6 %) |
| WASPAS | Co-Cr L605 | Co-Cr L605 | 54,3 % | Co-Ni-Cr-Mo MP35N (17,5 %) |
| VIKOR | Pt-Cr | Co-Ni-Cr-Mo MP35N | 29,7 % | Co-Ni-Cr-Mo MP35N (43,0 %) |

### c) Menor ajuste que troca o 1.º lugar

**Pesos**

| Critério | Peso | TOPSIS | WASPAS | VIKOR |
|---|---|---|---|---|
| Alongamento na rotura | 0,118 | -13,2 % (Co-Cr L605) | +86,0 % (Pt-Cr) | -3,4 % (Co-Cr L605) |
| Índice material de recuo elástico σy/E (proxy) | 0,118 | +36,5 % (Co-Cr L605) | não troca até ±100 % | +4,2 % (Co-Cr L605) |
| Radiopacidade (ordinal 1-5) | 0,118 | -48,9 % (Co-Cr L605) | +49,1 % (Pt-Cr) | -21,8 % (Co-Cr L605) |
| Resistência à tração | 0,118 | +35,3 % (Co-Cr L605) | -71,2 % (Pt-Cr) | +24,5 % (Co-Cr L605) |
| Fabricabilidade (ordinal 1-5) | 0,059 | +42,9 % (Co-Cr L605) | não troca até ±100 % | +27,6 % (Co-Cr L605) |
| Módulo de Young | 0,059 | +57,7 % (Co-Cr L605) | não troca até ±100 % | +48,0 % (Co-Cr L605) |
| Custo relativo de material e fabrico (1-5, 5 = mais caro) | 0,059 | +88,4 % (Co-Cr L605) | não troca até ±100 % | +91,0 % (Co-Cr L605) |
| Espessura típica de strut | 0,235 | não troca até ±100 % | não troca até ±100 % | não troca até ±100 % |
| Compatibilidade com RM (ordinal 1-5) | 0,059 | não troca até ±100 % | não troca até ±100 % | não troca até ±100 % |
| Compatibilidade com esterilização (ordinal 1-5) | 0,059 | não troca até ±100 % | não troca até ±100 % | não troca até ±100 % |

**Valores típicos (os 12 mais sensíveis)**

| Material | Critério | Valor | Variação que troca | Método(s) | Novo 1.º | Estado | Fonte |
|---|---|---|---|---|---|---|---|
| Co-Cr L605 | Alongamento na rotura | 40 | +0,8 % | VIKOR | Co-Cr L605 | Verificado (fornecedor) | Lamineries Matthey |
| Aço inox 316L | Alongamento na rotura | 40 | -0,9 % | VIKOR | Co-Cr L605 | Verificado (fornecedor) | Alleima |
| Co-Ni-Cr-Mo MP35N | Alongamento na rotura | 40 | -0,9 % | VIKOR | Co-Cr L605 | Verificado (fornecedor) | K-Tube |
| Co-Cr L605 | Espessura típica de strut | 81 | -3,3 % | VIKOR | Co-Cr L605 | Verificado | Macaya-Ten 2024 |
| Pt-Cr | Espessura típica de strut | 79 | +3,4 % | VIKOR | Co-Cr L605 | Verificado (fornecedor) | Boston Scientific |
| Co-Cr L605 | Módulo de Young | 225 | +3,4 % | VIKOR | Co-Cr L605 | Verificado (fornecedor) | Lamineries Matthey |
| Co-Ni-Cr-Mo MP35N | Módulo de Young | 234,4 | -3,6 % | VIKOR | Co-Cr L605 | Verificado (fornecedor) | K-Tube |
| Pt-Cr | Resistência à tração | 834 | -7,4 % | VIKOR | Co-Cr L605 | A verificar | Huibregtse et al. 2011 |
| Co-Cr L605 | Índice material de recuo elástico σy/E (proxy) | 0,00211556 | -8,6 % | VIKOR | Co-Cr L605 | Verificado (derivado) | Calculado: tensão de cedência / módulo d... |
| Pt-Cr | Alongamento na rotura | 45 | -11,1 % | TOPSIS, VIKOR | Co-Cr L605 | A verificar | Samant 2021 |
| Co-Cr L605 | Resistência à tração | 996 | -12,2 % | WASPAS | Pt-Cr | Verificado (fornecedor) | Lamineries Matthey |
| Co-Ni-Cr-Mo MP35N | Espessura típica de strut | 90 | -12,9 % | VIKOR | Co-Ni-Cr-Mo MP35N | Verificado | Brami 2023 |

No TOPSIS, menor variação que deixa o vencedor em empate (ΔC < 0,01): peso: Alongamento na rotura -7,1 %; valor: Co-Cr L605 / Alongamento na rotura +1,3 %.

## Stent, cenário B

Vencedores: TOPSIS Co-Cr L605 (ΔC = 0,002, empate); WASPAS Co-Cr L605; VIKOR Co-Cr L605.

### a) Retirar uma alternativa

| Retirado | TOPSIS | WASPAS | VIKOR | Pares que trocam |
|---|---|---|---|---|
| Aço inox 316L | não | não | não | nenhum |
| Co-Cr L605 | não | não | não | nenhum |
| Co-Ni-Cr-Mo MP35N | não | não | não | nenhum |
| Pt-Cr | não | não | não | nenhum |
| Liga de Mg WE43 (bioabsorvível) | não | não | não | nenhum |
| PLLA (bioabsorvível) | não | não | não | nenhum |

O 1.º lugar entre os restantes nunca muda ao retirar um material.

### b) Dupla contagem (pesos redistribuídos dentro de cada dimensão)

Peso por dimensão: mecânica 0,55; clínica 0,15; económica 0,15; biológica 0,15.

| Método | Vencedor (pesos da base) | Pesos iguais na dimensão | MC: mantém o 1.º | Outro 1.º mais frequente |
|---|---|---|---|---|
| TOPSIS | Co-Cr L605 | Co-Cr L605 | 69,3 % (90,3 % com empates) | Pt-Cr (20,4 %) |
| WASPAS | Co-Cr L605 | Co-Cr L605 | 53,6 % | Aço inox 316L (17,6 %) |
| VIKOR | Co-Cr L605 | Liga de Mg WE43 (bioabsorvível) | 70,5 % | Pt-Cr (18,4 %) |

### c) Menor ajuste que troca o 1.º lugar

**Pesos**

| Critério | Peso | TOPSIS | WASPAS | VIKOR |
|---|---|---|---|---|
| Radiopacidade (ordinal 1-5) | 0,100 | +9,6 % (Pt-Cr) | +48,1 % (Pt-Cr) | +35,5 % (Pt-Cr) |
| Espessura típica de strut | 0,200 | +72,2 % (Pt-Cr) | não troca até ±100 % | -15,7 % (Liga de Mg WE43 (bioabsorvível)) |
| Resistência à tração | 0,100 | -16,0 % (Pt-Cr) | -67,1 % (Pt-Cr) | -54,3 % (Pt-Cr) |
| Fabricabilidade (ordinal 1-5) | 0,050 | -17,9 % (Pt-Cr) | não troca até ±100 % | -44,9 % (Pt-Cr) |
| Tempo de reabsorção | 0,150 | +25,1 % (Pt-Cr) | não troca até ±100 % | +18,7 % (Liga de Mg WE43 (bioabsorvível)) |
| Custo relativo de material e fabrico (1-5, 5 = mais caro) | 0,050 | -22,9 % (Pt-Cr) | não troca até ±100 % | não troca até ±100 % |
| Alongamento na rotura | 0,100 | +23,5 % (Pt-Cr) | +85,1 % (Pt-Cr) | +66,0 % (Pt-Cr) |
| Índice material de recuo elástico σy/E (proxy) | 0,100 | não troca até ±100 % | não troca até ±100 % | não troca até ±100 % |
| Módulo de Young | 0,050 | não troca até ±100 % | não troca até ±100 % | não troca até ±100 % |
| Compatibilidade com RM (ordinal 1-5) | 0,050 | não troca até ±100 % | não troca até ±100 % | não troca até ±100 % |
| Compatibilidade com esterilização (ordinal 1-5) | 0,050 | não troca até ±100 % | não troca até ±100 % | não troca até ±100 % |

**Valores típicos (os 12 mais sensíveis)**

| Material | Critério | Valor | Variação que troca | Método(s) | Novo 1.º | Estado | Fonte |
|---|---|---|---|---|---|---|---|
| Pt-Cr | Tempo de reabsorção | 48 | -0,7 % | TOPSIS | Pt-Cr | Valor de modelação | Hanawa 2009 |
| Co-Cr L605 | Tempo de reabsorção | 48 | +0,7 % | TOPSIS | Pt-Cr | Valor de modelação | Hanawa 2009 |
| Co-Cr L605 | Espessura típica de strut | 81 | +1,6 % | TOPSIS | Pt-Cr | Verificado | Macaya-Ten 2024 |
| Pt-Cr | Espessura típica de strut | 79 | -1,7 % | TOPSIS | Pt-Cr | Verificado (fornecedor) | Boston Scientific |
| Co-Ni-Cr-Mo MP35N | Tempo de reabsorção | 48 | -4,0 % | VIKOR | Co-Ni-Cr-Mo MP35N | Valor de modelação | Hanawa 2009 |
| Co-Cr L605 | Alongamento na rotura | 40 | -5,2 % | TOPSIS | Pt-Cr | Verificado (fornecedor) | Lamineries Matthey |
| Pt-Cr | Alongamento na rotura | 45 | +5,6 % | TOPSIS | Pt-Cr | A verificar | Samant 2021 |
| Pt-Cr | Resistência à tração | 834 | +5,9 % | TOPSIS | Pt-Cr | A verificar | Huibregtse et al. 2011 |
| Co-Cr L605 | Resistência à tração | 996 | -6,0 % | TOPSIS | Pt-Cr | Verificado (fornecedor) | Lamineries Matthey |
| Pt-Cr | Índice material de recuo elástico σy/E (proxy) | 0,00236453 | -14,1 % | WASPAS | Pt-Cr | A verificar (derivado) | Calculado: tensão de cedência / módulo d... |
| Co-Ni-Cr-Mo MP35N | Espessura típica de strut | 90 | -14,4 % | WASPAS | Co-Ni-Cr-Mo MP35N | Verificado | Brami 2023 |
| Co-Cr L605 | Índice material de recuo elástico σy/E (proxy) | 0,00211556 | +16,7 % | WASPAS | Pt-Cr | Verificado (derivado) | Calculado: tensão de cedência / módulo d... |

No TOPSIS, o vencedor já está em empate (ΔC < 0,01) no caso de base.

## Scaffold, cenário A

Vencedores: TOPSIS β-TCP poroso (ΔC = 0,019); WASPAS Compósito PCL/β-TCP (impressão 3D); VIKOR Compósito PCL/β-TCP (impressão 3D).

### a) Retirar uma alternativa

| Retirado | TOPSIS | WASPAS | VIKOR | Pares que trocam |
|---|---|---|---|---|
| PCL | sim | não | sim | TOPSIS: Compósito PCL/β-TCP (impressão 3D) ↔ Vidro bioativo 45S5 poroso; VIKOR: Compósito PCL/β-TCP (impressão 3D) ↔ β-TCP poroso |
| Hidroxiapatite (HA) porosa | sim | sim | sim | TOPSIS: Compósito PCL/β-TCP (impressão 3D) ↔ Vidro bioativo 45S5 poroso; WASPAS: PCL ↔ Vidro bioativo 45S5 poroso; VIKOR: Compósito PCL/β-TCP (impressão 3D) ↔ β-TCP poroso |
| β-TCP poroso | não | não | não | nenhum |
| Vidro bioativo 45S5 poroso | sim | sim | não | TOPSIS: β-TCP poroso ↔ Compósito PCL/β-TCP (impressão 3D); WASPAS: β-TCP poroso ↔ PCL; Compósito PCL/β-TCP (impressão 3D) ↔ PCL |
| Compósito PCL/β-TCP (impressão 3D) | não | não | não | nenhum |

O 1.º lugar entre os restantes muda em: VIKOR sem PCL (Compósito PCL/β-TCP (impressão 3D) → β-TCP poroso); VIKOR sem Hidroxiapatite (HA) porosa (Compósito PCL/β-TCP (impressão 3D) → β-TCP poroso); TOPSIS sem Vidro bioativo 45S5 poroso (β-TCP poroso → Compósito PCL/β-TCP (impressão 3D)); WASPAS sem Vidro bioativo 45S5 poroso (Compósito PCL/β-TCP (impressão 3D) → PCL).

### b) Dupla contagem (pesos redistribuídos dentro de cada dimensão)

Peso por dimensão: mecânica 0,25; biológica 0,45; económica 0,30.

| Método | Vencedor (pesos da base) | Pesos iguais na dimensão | MC: mantém o 1.º | Outro 1.º mais frequente |
|---|---|---|---|---|
| TOPSIS | β-TCP poroso | β-TCP poroso | 31,2 % (35,9 % com empates) | Compósito PCL/β-TCP (impressão 3D) (39,9 %) |
| WASPAS | Compósito PCL/β-TCP (impressão 3D) | Compósito PCL/β-TCP (impressão 3D) | 48,4 % | β-TCP poroso (23,2 %) |
| VIKOR | Compósito PCL/β-TCP (impressão 3D) | Compósito PCL/β-TCP (impressão 3D) | 42,2 % | β-TCP poroso (27,4 %) |

### c) Menor ajuste que troca o 1.º lugar

**Pesos**

| Critério | Peso | TOPSIS | WASPAS | VIKOR |
|---|---|---|---|---|
| Imprimibilidade 3D (ordinal 1-5) | 0,100 | +11,2 % (Compósito PCL/β-TCP (impressão 3D)) | -48,7 % (β-TCP poroso) | -31,5 % (β-TCP poroso) |
| Compatibilidade com esterilização (ordinal 1-5) | 0,100 | -12,8 % (Compósito PCL/β-TCP (impressão 3D)) | +69,7 % (β-TCP poroso) | +26,2 % (β-TCP poroso) |
| Bioatividade (ordinal 1-5) | 0,150 | -27,0 % (Compósito PCL/β-TCP (impressão 3D)) | -40,6 % (PCL) | -14,0 % (PCL) |
| Resistência à compressão (scaffold) | 0,150 | +29,6 % (PCL) | +33,0 % (PCL) | +15,0 % (PCL) |
| Tempo de degradação | 0,150 | -35,4 % (Compósito PCL/β-TCP (impressão 3D)) | +76,3 % (β-TCP poroso) | +25,1 % (β-TCP poroso) |
| Custo relativo de material e fabrico (1-5, 5 = mais caro) | 0,100 | +30,1 % (Compósito PCL/β-TCP (impressão 3D)) | +65,0 % (PCL) | não troca até ±100 % |
| Porosidade | 0,150 | +32,0 % (Compósito PCL/β-TCP (impressão 3D)) | -51,0 % (PCL) | -59,6 % (β-TCP poroso) |
| Módulo de compressão (scaffold) | 0,100 | não troca até ±100 % | não troca até ±100 % | não troca até ±100 % |

**Valores típicos (os 12 mais sensíveis)**

| Material | Critério | Valor | Variação que troca | Método(s) | Novo 1.º | Estado | Fonte |
|---|---|---|---|---|---|---|---|
| Compósito PCL/β-TCP (impressão 3D) | Porosidade | 70 | -4,2 % | VIKOR | β-TCP poroso | Verificado | Sparks 2023 |
| β-TCP poroso | Porosidade | 65 | +5,9 % | VIKOR | β-TCP poroso | Verificado (fornecedor) | FDA 510(k) K120152 |
| Vidro bioativo 45S5 poroso | Porosidade | 80 | -7,6 % | TOPSIS | Compósito PCL/β-TCP (impressão 3D) | A verificar | Karageorgiou et al. 2005 |
| PCL | Porosidade | 61 | +9,2 % | WASPAS | PCL | Verificado | Zein 2002 |
| Compósito PCL/β-TCP (impressão 3D) | Resistência à compressão (scaffold) | 2,2 | -9,3 % | VIKOR | β-TCP poroso | Verificado | Kawai 2018 |
| β-TCP poroso | Resistência à compressão (scaffold) | 2 | +10,3 % | VIKOR | β-TCP poroso | Verificado | Montelongo 2021 |
| PCL | Resistência à compressão (scaffold) | 6 | +16,7 % | WASPAS | PCL | A verificar | Woodruff et al. 2010 |
| Compósito PCL/β-TCP (impressão 3D) | Imprimibilidade 3D (ordinal 1-5) | 5 (ordinal) | -1 ponto (-20,0 %) | VIKOR | β-TCP poroso | A verificar | Escala ordinal definida no trabalho |
| β-TCP poroso | Compatibilidade com esterilização (ordinal 1-5) | 5 (ordinal) | -1 ponto (-20,0 %) | TOPSIS | Compósito PCL/β-TCP (impressão 3D) | Verificado (fornecedor) | FDA 510(k) K032409 |
| β-TCP poroso | Bioatividade (ordinal 1-5) | 4 (ordinal) | -1 ponto (-25,0 %) | TOPSIS, VIKOR | Compósito PCL/β-TCP (impressão 3D) | Verificado | Kotani 1991 |
| Compósito PCL/β-TCP (impressão 3D) | Tempo de degradação | 26 | -28,7 % | TOPSIS | Compósito PCL/β-TCP (impressão 3D) | Verificado | Zhong 2026 |
| Compósito PCL/β-TCP (impressão 3D) | Bioatividade (ordinal 1-5) | 3 (ordinal) | +1 ponto (+33,3 %) | TOPSIS, WASPAS | Compósito PCL/β-TCP (impressão 3D) | Verificado | Bruyas 2018 |

No TOPSIS, menor variação que deixa o vencedor em empate (ΔC < 0,01): peso: Imprimibilidade 3D (ordinal 1-5) +5,4 %; valor: β-TCP poroso / Porosidade -3,1 %.

## Scaffold, cenário B

Vencedores: TOPSIS Compósito PCL/β-TCP (impressão 3D) (ΔC = 0,016); WASPAS Compósito PCL/β-TCP (impressão 3D); VIKOR Compósito PCL/β-TCP (impressão 3D).

### a) Retirar uma alternativa

| Retirado | TOPSIS | WASPAS | VIKOR | Pares que trocam |
|---|---|---|---|---|
| PCL | não | não | não | nenhum |
| PLLA | não | não | não | nenhum |
| PLGA 50:50 | sim | sim | não | TOPSIS: Compósito PCL/β-TCP (impressão 3D) ↔ β-TCP poroso; WASPAS: PCL ↔ β-TCP poroso |
| Hidroxiapatite (HA) porosa | não | sim | não | WASPAS: PCL ↔ β-TCP poroso; PLLA ↔ Vidro bioativo 45S5 poroso |
| β-TCP poroso | não | não | não | nenhum |
| Vidro bioativo 45S5 poroso | não | sim | não | WASPAS: PCL ↔ β-TCP poroso |
| Compósito PCL/β-TCP (impressão 3D) | não | não | não | nenhum |
| Quitosano/HA (liofilizado) | sim (só empates, ΔC < 0,01) | sim | sim | TOPSIS: Vidro bioativo 45S5 poroso ↔ PCL (empate); WASPAS: PCL ↔ β-TCP poroso; VIKOR: Vidro bioativo 45S5 poroso ↔ PCL; PLLA ↔ Hidroxiapatite (HA) porosa |

O 1.º lugar entre os restantes muda em: TOPSIS sem PLGA 50:50 (Compósito PCL/β-TCP (impressão 3D) → β-TCP poroso).

### b) Dupla contagem (pesos redistribuídos dentro de cada dimensão)

Peso por dimensão: mecânica 0,25; biológica 0,45; económica 0,30.

| Método | Vencedor (pesos da base) | Pesos iguais na dimensão | MC: mantém o 1.º | Outro 1.º mais frequente |
|---|---|---|---|---|
| TOPSIS | Compósito PCL/β-TCP (impressão 3D) | Compósito PCL/β-TCP (impressão 3D) | 40,2 % (44,3 % com empates) | β-TCP poroso (24,9 %) |
| WASPAS | Compósito PCL/β-TCP (impressão 3D) | Compósito PCL/β-TCP (impressão 3D) | 35,2 % | β-TCP poroso (24,3 %) |
| VIKOR | Compósito PCL/β-TCP (impressão 3D) | Compósito PCL/β-TCP (impressão 3D) | 38,2 % | β-TCP poroso (21,6 %) |

### c) Menor ajuste que troca o 1.º lugar

**Pesos**

| Critério | Peso | TOPSIS | WASPAS | VIKOR |
|---|---|---|---|---|
| Imprimibilidade 3D (ordinal 1-5) | 0,100 | -9,7 % (β-TCP poroso) | -29,9 % (β-TCP poroso) | -36,6 % (β-TCP poroso) |
| Compatibilidade com esterilização (ordinal 1-5) | 0,100 | +13,9 % (β-TCP poroso) | +45,0 % (β-TCP poroso) | +45,7 % (β-TCP poroso) |
| Bioatividade (ordinal 1-5) | 0,150 | +14,9 % (β-TCP poroso) | -18,1 % (PCL) | -19,2 % (PCL) |
| Resistência à compressão (scaffold) | 0,150 | +30,0 % (PCL) | +15,8 % (PCL) | +21,4 % (PCL) |
| Tempo de degradação | 0,150 | +24,4 % (β-TCP poroso) | +48,6 % (β-TCP poroso) | +44,9 % (β-TCP poroso) |
| Custo relativo de material e fabrico (1-5, 5 = mais caro) | 0,100 | -35,6 % (β-TCP poroso) | +31,3 % (PCL) | não troca até ±100 % |
| Porosidade | 0,150 | -52,1 % (β-TCP poroso) | -33,5 % (PCL) | -93,2 % (β-TCP poroso) |
| Módulo de compressão (scaffold) | 0,100 | não troca até ±100 % | não troca até ±100 % | não troca até ±100 % |

**Valores típicos (os 12 mais sensíveis)**

| Material | Critério | Valor | Variação que troca | Método(s) | Novo 1.º | Estado | Fonte |
|---|---|---|---|---|---|---|---|
| Compósito PCL/β-TCP (impressão 3D) | Porosidade | 70 | -5,1 % | WASPAS | PCL | Verificado | Sparks 2023 |
| β-TCP poroso | Porosidade | 65 | +6,0 % | WASPAS | β-TCP poroso | Verificado (fornecedor) | FDA 510(k) K120152 |
| PCL | Porosidade | 61 | +6,7 % | WASPAS | PCL | Verificado | Zein 2002 |
| Compósito PCL/β-TCP (impressão 3D) | Resistência à compressão (scaffold) | 2,2 | -14,2 % | VIKOR | β-TCP poroso | Verificado | Kawai 2018 |
| PCL | Resistência à compressão (scaffold) | 6 | +15,7 % | WASPAS | PCL | A verificar | Woodruff et al. 2010 |
| β-TCP poroso | Resistência à compressão (scaffold) | 2 | +16,1 % | VIKOR | β-TCP poroso | Verificado | Montelongo 2021 |
| Quitosano/HA (liofilizado) | Porosidade | 87,5 | +16,7 % | WASPAS | PCL | Verificado | Gaihre et al. 2018 |
| PCL | Tempo de degradação | 36 | -17,6 % | WASPAS | PCL | Verificado | Woodruff et al. 2010 |
| Compósito PCL/β-TCP (impressão 3D) | Imprimibilidade 3D (ordinal 1-5) | 5 (ordinal) | -1 ponto (-20,0 %) | TOPSIS, WASPAS, VIKOR | β-TCP poroso | A verificar | Escala ordinal definida no trabalho |
| Compósito PCL/β-TCP (impressão 3D) | Tempo de degradação | 26 | +23,6 % | TOPSIS | β-TCP poroso | Verificado | Zhong 2026 |
| β-TCP poroso | Bioatividade (ordinal 1-5) | 4 (ordinal) | +1 ponto (+25,0 %) | TOPSIS, WASPAS, VIKOR | β-TCP poroso | Verificado | Kotani 1991 |
| PLGA 50:50 | Porosidade | 80 | +27,6 % | WASPAS | PCL | Verificado | Lu 2000 |

No TOPSIS, menor variação que deixa o vencedor em empate (ΔC < 0,01): peso: Imprimibilidade 3D (ordinal 1-5) -3,5 %; valor: Compósito PCL/β-TCP (impressão 3D) / Porosidade -2,0 %.
