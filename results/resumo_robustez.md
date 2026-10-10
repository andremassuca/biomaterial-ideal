# Resumo da robustez (PRELIMINAR: dados por verificar)

η = 1 no resultado principal; sensibilidades a partir do cenário A. Monte Carlo: 10000 iterações, seed 42. No MC propriedades, as propriedades quantitativas com mín. = máx. variam ±10 % à volta do típico (data/parametros.csv).

## Haste

Vencedor no cenário A: TOPSIS Ti-6Al-4V ELI; WASPAS Ti-6Al-4V ELI; VIKOR Ti-6Al-4V ELI

### Vencedor por cenário e método

| Cenário | Variante | TOPSIS | WASPAS | VIKOR | ρ mín. entre métodos |
|---|---|---|---|---|---|
| A | A | Ti-6Al-4V ELI | Ti-6Al-4V ELI | Ti-6Al-4V ELI | 0,30 |
| B | B | Ti-6Al-4V ELI | Ti-6Al-4V ELI | Ti-6Al-4V ELI | 0,77 |
| Q | sem ordinais | Ti-6Al-4V ELI | Ti-6Al-4V ELI | Ti-6Al-4V ELI | 0,10 |
| η | η = 0,0 | Ti-6Al-4V ELI | Ti-6Al-4V ELI | Ti cp grau 4 | 0,90 |
| η | η = 0,1 | Ti-6Al-4V ELI | Ti-6Al-4V ELI | Ti-6Al-4V ELI | 1,00 |
| η | η = 0,2 | Ti-6Al-4V ELI | Ti-6Al-4V ELI | Ti-6Al-4V ELI | 1,00 |
| η | η = 0,3 | Ti-6Al-4V ELI | Ti-6Al-4V ELI | Ti-6Al-4V ELI | 1,00 |
| η | η = 0,4 | Ti-6Al-4V ELI | Ti-6Al-4V ELI | Ti-6Al-4V ELI | 0,80 |
| η | η = 0,5 | Ti-6Al-4V ELI | Ti-6Al-4V ELI | Ti-6Al-4V ELI | 0,80 |
| η | η = 0,6 | Ti-6Al-4V ELI | Ti-6Al-4V ELI | Ti-6Al-4V ELI | 0,80 |
| η | η = 0,7 | Ti-6Al-4V ELI | Ti-6Al-4V ELI | Ti-6Al-4V ELI | 0,70 |
| η | η = 0,8 | Ti-6Al-4V ELI | Ti-6Al-4V ELI | Ti-6Al-4V ELI | 0,40 |
| η | η = 0,9 | Ti-6Al-4V ELI | Ti-6Al-4V ELI | Ti-6Al-4V ELI | 0,40 |
| η | η = 1,0 | Ti-6Al-4V ELI | Ti-6Al-4V ELI | Ti-6Al-4V ELI | 0,30 |
| T-haste | alvo 14 GPa | Ti-6Al-4V ELI | Ti-6Al-4V ELI | Ti-6Al-4V ELI | 0,30 |
| T-haste | alvo 15 GPa | Ti-6Al-4V ELI | Ti-6Al-4V ELI | Ti-6Al-4V ELI | 0,30 |
| T-haste | alvo 17 GPa | Ti-6Al-4V ELI | Ti-6Al-4V ELI | Ti-6Al-4V ELI | 0,30 |
| T-haste | alvo 20 GPa | Ti-6Al-4V ELI | Ti-6Al-4V ELI | Ti-6Al-4V ELI | 0,30 |
| T-haste | módulo como custo | Ti-6Al-4V ELI | Ti-6Al-4V ELI | Ti-6Al-4V ELI | 0,70 |
| C-custo | custo baixo (0,01) | Ti-6Al-4V ELI | Ti-6Al-4V ELI | Ti-6Al-4V ELI | 0,30 |
| C-custo | custo elevado (0,25) | Aço inox 316L | Ti-6Al-4V ELI | Ti-6Al-4V ELI | 0,60 |
| P-foco | direta | Ti-6Al-4V ELI | Ti-6Al-4V ELI | Ti-6Al-4V ELI | 0,70 |
| P-foco | direta + indireta | Ti-6Al-4V ELI | Ti-6Al-4V ELI | Ti-6Al-4V ELI | 0,70 |
| O-orçamento | custo ≤ 3 (sai: Ti-13Nb-13Zr) | Ti-6Al-4V ELI | Ti-6Al-4V ELI | Ti-6Al-4V ELI | 0,20 |

### Monte Carlo: % de 1.º lugar

**MC propriedades**

| Material | TOPSIS | WASPAS | VIKOR |
|---|---|---|---|
| Ti-6Al-4V ELI | 100,0 % | 100,0 % | 100,0 % |
| Co-Cr-Mo forjado | 0,0 % | 0,0 % | 0,0 % |
| Aço inox 316L | 0,0 % | 0,0 % | 0,0 % |
| Ti cp grau 4 | 0,0 % | 0,0 % | 0,0 % |
| Ti-13Nb-13Zr | 0,0 % | 0,0 % | 0,0 % |

**W pesos ±20 %**

| Material | TOPSIS | WASPAS | VIKOR |
|---|---|---|---|
| Ti-6Al-4V ELI | 100,0 % | 100,0 % | 100,0 % |
| Aço inox 316L | 0,0 % | 0,0 % | 0,0 % |
| Co-Cr-Mo forjado | 0,0 % | 0,0 % | 0,0 % |
| Ti cp grau 4 | 0,0 % | 0,0 % | 0,0 % |
| Ti-13Nb-13Zr | 0,0 % | 0,0 % | 0,0 % |

### Onde o vencedor muda (face ao cenário A)

- η, η = 0,0, VIKOR: Ti-6Al-4V ELI → Ti cp grau 4
- C-custo, custo elevado (0,25), TOPSIS: Ti-6Al-4V ELI → Aço inox 316L

## Stent

Vencedor no cenário A: TOPSIS Pt-Cr; WASPAS Co-Cr L605; VIKOR Pt-Cr

### Vencedor por cenário e método

| Cenário | Variante | TOPSIS | WASPAS | VIKOR | ρ mín. entre métodos |
|---|---|---|---|---|---|
| A | A | Pt-Cr | Co-Cr L605 | Pt-Cr | 0,80 |
| B | B | Co-Cr L605 | Co-Cr L605 | Co-Cr L605 | 1,00 |
| B-bio (comparação) | B-bio | Liga de Mg WE43 (bioabsorvível) | Liga de Mg WE43 (bioabsorvível) | Liga de Mg WE43 (bioabsorvível) | n/a |
| R-sentinela | 60 meses | Co-Cr L605 | Co-Cr L605 | Co-Cr L605 | 1,00 |
| R-sentinela | 120 meses | Co-Cr L605 | Co-Cr L605 | Co-Cr L605 | 1,00 |
| R-sentinela | 600 meses | Co-Cr L605 | Co-Cr L605 | Co-Cr L605 | 0,94 |
| R-sentinela | 1200 meses | Co-Cr L605 | Co-Cr L605 | Co-Cr L605 | 0,94 |
| Q | sem ordinais | Pt-Cr | Co-Cr L605 | Pt-Cr | 0,40 |
| η | η = 0,0 | Co-Cr L605 | Aço inox 316L | Co-Cr L605 | 0,40 |
| η | η = 0,1 | Co-Cr L605 | Aço inox 316L | Co-Cr L605 | 0,40 |
| η | η = 0,2 | Co-Cr L605 | Aço inox 316L | Co-Cr L605 | -0,20 |
| η | η = 0,3 | Co-Cr L605 | Aço inox 316L | Co-Cr L605 | -0,20 |
| η | η = 0,4 | Co-Cr L605 | Co-Cr L605 | Co-Cr L605 | 0,40 |
| η | η = 0,5 | Co-Cr L605 | Co-Cr L605 | Co-Cr L605 | 0,40 |
| η | η = 0,6 | Co-Cr L605 | Co-Cr L605 | Co-Cr L605 | 0,80 |
| η | η = 0,7 | Co-Cr L605 | Co-Cr L605 | Co-Cr L605 | 1,00 |
| η | η = 0,8 | Co-Cr L605 | Co-Cr L605 | Co-Cr L605 | 1,00 |
| η | η = 0,9 | Pt-Cr | Co-Cr L605 | Co-Cr L605 | 0,80 |
| η | η = 1,0 | Pt-Cr | Co-Cr L605 | Pt-Cr | 0,80 |
| C-custo | custo baixo (0,01) | Pt-Cr | Co-Cr L605 | Pt-Cr | 0,80 |
| C-custo | custo elevado (0,25) | Co-Cr L605 | Aço inox 316L | Co-Cr L605 | 0,40 |
| P-foco | direta | Pt-Cr | Co-Cr L605 | Pt-Cr | 0,80 |
| P-foco | direta + indireta | Pt-Cr | Co-Cr L605 | Pt-Cr | 0,80 |
| O-orçamento | custo ≤ 3 (sai: Pt-Cr) | Co-Cr L605 | Co-Cr L605 | Co-Cr L605 | 1,00 |

### Monte Carlo: % de 1.º lugar

**MC propriedades**

| Material | TOPSIS | WASPAS | VIKOR |
|---|---|---|---|
| Pt-Cr | 69,7 % | 55,9 % | 58,1 % |
| Co-Cr L605 | 27,0 % | 41,3 % | 31,8 % |
| Co-Ni-Cr-Mo MP35N | 3,3 % | 2,8 % | 10,1 % |
| Aço inox 316L | 0,0 % | 0,0 % | 0,0 % |

**W pesos ±20 %**

| Material | TOPSIS | WASPAS | VIKOR |
|---|---|---|---|
| Pt-Cr | 83,2 % | 0,0 % | 59,0 % |
| Co-Cr L605 | 16,8 % | 100,0 % | 40,7 % |
| Aço inox 316L | 0,0 % | 0,0 % | 0,0 % |
| Co-Ni-Cr-Mo MP35N | 0,0 % | 0,0 % | 0,3 % |

### Onde o vencedor muda (face ao cenário A)

- B, B, TOPSIS: Pt-Cr → Co-Cr L605
- B, B, VIKOR: Pt-Cr → Co-Cr L605
- R-sentinela, 60 meses, TOPSIS: Pt-Cr → Co-Cr L605
- R-sentinela, 60 meses, VIKOR: Pt-Cr → Co-Cr L605
- R-sentinela, 120 meses, TOPSIS: Pt-Cr → Co-Cr L605
- R-sentinela, 120 meses, VIKOR: Pt-Cr → Co-Cr L605
- R-sentinela, 600 meses, TOPSIS: Pt-Cr → Co-Cr L605
- R-sentinela, 600 meses, VIKOR: Pt-Cr → Co-Cr L605
- R-sentinela, 1200 meses, TOPSIS: Pt-Cr → Co-Cr L605
- R-sentinela, 1200 meses, VIKOR: Pt-Cr → Co-Cr L605
- η, η = 0,0, TOPSIS: Pt-Cr → Co-Cr L605
- η, η = 0,0, WASPAS: Co-Cr L605 → Aço inox 316L
- η, η = 0,0, VIKOR: Pt-Cr → Co-Cr L605
- η, η = 0,1, TOPSIS: Pt-Cr → Co-Cr L605
- η, η = 0,1, WASPAS: Co-Cr L605 → Aço inox 316L
- η, η = 0,1, VIKOR: Pt-Cr → Co-Cr L605
- η, η = 0,2, TOPSIS: Pt-Cr → Co-Cr L605
- η, η = 0,2, WASPAS: Co-Cr L605 → Aço inox 316L
- η, η = 0,2, VIKOR: Pt-Cr → Co-Cr L605
- η, η = 0,3, TOPSIS: Pt-Cr → Co-Cr L605
- η, η = 0,3, WASPAS: Co-Cr L605 → Aço inox 316L
- η, η = 0,3, VIKOR: Pt-Cr → Co-Cr L605
- η, η = 0,4, TOPSIS: Pt-Cr → Co-Cr L605
- η, η = 0,4, VIKOR: Pt-Cr → Co-Cr L605
- η, η = 0,5, TOPSIS: Pt-Cr → Co-Cr L605
- η, η = 0,5, VIKOR: Pt-Cr → Co-Cr L605
- η, η = 0,6, TOPSIS: Pt-Cr → Co-Cr L605
- η, η = 0,6, VIKOR: Pt-Cr → Co-Cr L605
- η, η = 0,7, TOPSIS: Pt-Cr → Co-Cr L605
- η, η = 0,7, VIKOR: Pt-Cr → Co-Cr L605
- η, η = 0,8, TOPSIS: Pt-Cr → Co-Cr L605
- η, η = 0,8, VIKOR: Pt-Cr → Co-Cr L605
- η, η = 0,9, VIKOR: Pt-Cr → Co-Cr L605
- C-custo, custo elevado (0,25), TOPSIS: Pt-Cr → Co-Cr L605
- C-custo, custo elevado (0,25), WASPAS: Co-Cr L605 → Aço inox 316L
- C-custo, custo elevado (0,25), VIKOR: Pt-Cr → Co-Cr L605
- O-orçamento, custo ≤ 3 (sai: Pt-Cr), TOPSIS: Pt-Cr → Co-Cr L605
- O-orçamento, custo ≤ 3 (sai: Pt-Cr), VIKOR: Pt-Cr → Co-Cr L605

## Scaffold

Vencedor no cenário A: TOPSIS Compósito PCL/β-TCP (impressão 3D); WASPAS Compósito PCL/β-TCP (impressão 3D); VIKOR Compósito PCL/β-TCP (impressão 3D)

### Vencedor por cenário e método

| Cenário | Variante | TOPSIS | WASPAS | VIKOR | ρ mín. entre métodos |
|---|---|---|---|---|---|
| A | A | Compósito PCL/β-TCP (impressão 3D) | Compósito PCL/β-TCP (impressão 3D) | Compósito PCL/β-TCP (impressão 3D) | 0,90 |
| B | B | Compósito PCL/β-TCP (impressão 3D) | Compósito PCL/β-TCP (impressão 3D) | Compósito PCL/β-TCP (impressão 3D) | 0,81 |
| Q | sem ordinais | Compósito PCL/β-TCP (impressão 3D) | Compósito PCL/β-TCP (impressão 3D) | Compósito PCL/β-TCP (impressão 3D) | 1,00 |
| η | η = 0,0 | Compósito PCL/β-TCP (impressão 3D) | Compósito PCL/β-TCP (impressão 3D) | Compósito PCL/β-TCP (impressão 3D) | 0,90 |
| η | η = 0,1 | Compósito PCL/β-TCP (impressão 3D) | Compósito PCL/β-TCP (impressão 3D) | Compósito PCL/β-TCP (impressão 3D) | 1,00 |
| η | η = 0,2 | Compósito PCL/β-TCP (impressão 3D) | Compósito PCL/β-TCP (impressão 3D) | Compósito PCL/β-TCP (impressão 3D) | 1,00 |
| η | η = 0,3 | Compósito PCL/β-TCP (impressão 3D) | Compósito PCL/β-TCP (impressão 3D) | Compósito PCL/β-TCP (impressão 3D) | 1,00 |
| η | η = 0,4 | Compósito PCL/β-TCP (impressão 3D) | Compósito PCL/β-TCP (impressão 3D) | Compósito PCL/β-TCP (impressão 3D) | 0,90 |
| η | η = 0,5 | Compósito PCL/β-TCP (impressão 3D) | Compósito PCL/β-TCP (impressão 3D) | Compósito PCL/β-TCP (impressão 3D) | 0,90 |
| η | η = 0,6 | Compósito PCL/β-TCP (impressão 3D) | Compósito PCL/β-TCP (impressão 3D) | Compósito PCL/β-TCP (impressão 3D) | 0,90 |
| η | η = 0,7 | Compósito PCL/β-TCP (impressão 3D) | Compósito PCL/β-TCP (impressão 3D) | Compósito PCL/β-TCP (impressão 3D) | 0,90 |
| η | η = 0,8 | Compósito PCL/β-TCP (impressão 3D) | Compósito PCL/β-TCP (impressão 3D) | Compósito PCL/β-TCP (impressão 3D) | 0,70 |
| η | η = 0,9 | Compósito PCL/β-TCP (impressão 3D) | Compósito PCL/β-TCP (impressão 3D) | Compósito PCL/β-TCP (impressão 3D) | 0,70 |
| η | η = 1,0 | Compósito PCL/β-TCP (impressão 3D) | Compósito PCL/β-TCP (impressão 3D) | Compósito PCL/β-TCP (impressão 3D) | 0,90 |
| T-scaffold | Resistência à compressão: 2 | β-TCP poroso | β-TCP poroso | β-TCP poroso | 0,80 |
| T-scaffold | Resistência à compressão: 12 | Compósito PCL/β-TCP (impressão 3D) | Compósito PCL/β-TCP (impressão 3D) | Compósito PCL/β-TCP (impressão 3D) | 0,90 |
| T-scaffold | Módulo de compressão: 50 | Compósito PCL/β-TCP (impressão 3D) | Compósito PCL/β-TCP (impressão 3D) | Compósito PCL/β-TCP (impressão 3D) | 0,70 |
| T-scaffold | Módulo de compressão: 500 | Compósito PCL/β-TCP (impressão 3D) | Compósito PCL/β-TCP (impressão 3D) | Compósito PCL/β-TCP (impressão 3D) | 0,90 |
| T-scaffold | Porosidade: 50 | Compósito PCL/β-TCP (impressão 3D) | Compósito PCL/β-TCP (impressão 3D) | Compósito PCL/β-TCP (impressão 3D) | 0,90 |
| T-scaffold | Porosidade: 90 | Compósito PCL/β-TCP (impressão 3D) | Compósito PCL/β-TCP (impressão 3D) | Compósito PCL/β-TCP (impressão 3D) | 0,60 |
| T-scaffold | Tempo de degradação: x0,5 | Compósito PCL/β-TCP (impressão 3D) | Compósito PCL/β-TCP (impressão 3D) | Compósito PCL/β-TCP (impressão 3D) | 0,90 |
| T-scaffold | Tempo de degradação: x2,0 | Compósito PCL/β-TCP (impressão 3D) | Compósito PCL/β-TCP (impressão 3D) | Compósito PCL/β-TCP (impressão 3D) | 0,70 |
| C-custo | custo baixo (0,01) | Compósito PCL/β-TCP (impressão 3D) | Compósito PCL/β-TCP (impressão 3D) | Compósito PCL/β-TCP (impressão 3D) | 1,00 |
| C-custo | custo elevado (0,25) | Compósito PCL/β-TCP (impressão 3D) | Compósito PCL/β-TCP (impressão 3D) | Compósito PCL/β-TCP (impressão 3D) | 0,90 |
| P-foco | direta | β-TCP poroso | Compósito PCL/β-TCP (impressão 3D) | β-TCP poroso | 0,80 |
| P-foco | direta + indireta | Compósito PCL/β-TCP (impressão 3D) | Compósito PCL/β-TCP (impressão 3D) | Compósito PCL/β-TCP (impressão 3D) | 0,90 |
| O-orçamento | custo ≤ 3 (sai: Vidro bioativo 45S5 poroso) | Compósito PCL/β-TCP (impressão 3D) | Compósito PCL/β-TCP (impressão 3D) | Compósito PCL/β-TCP (impressão 3D) | 0,80 |

### Monte Carlo: % de 1.º lugar

**MC propriedades**

| Material | TOPSIS | WASPAS | VIKOR |
|---|---|---|---|
| β-TCP poroso | 52,2 % | 24,8 % | 38,6 % |
| Compósito PCL/β-TCP (impressão 3D) | 39,0 % | 68,3 % | 46,3 % |
| Vidro bioativo 45S5 poroso | 8,8 % | 5,6 % | 15,1 % |
| PCL | 0,0 % | 1,3 % | 0,0 % |
| Hidroxiapatite (HA) porosa | 0,0 % | 0,0 % | 0,0 % |

**W pesos ±20 %**

| Material | TOPSIS | WASPAS | VIKOR |
|---|---|---|---|
| Compósito PCL/β-TCP (impressão 3D) | 95,7 % | 100,0 % | 99,6 % |
| β-TCP poroso | 4,3 % | 0,0 % | 0,4 % |
| Hidroxiapatite (HA) porosa | 0,0 % | 0,0 % | 0,0 % |
| PCL | 0,0 % | 0,0 % | 0,0 % |
| Vidro bioativo 45S5 poroso | 0,0 % | 0,0 % | 0,0 % |

### Onde o vencedor muda (face ao cenário A)

- T-scaffold, Resistência à compressão: 2, TOPSIS: Compósito PCL/β-TCP (impressão 3D) → β-TCP poroso
- T-scaffold, Resistência à compressão: 2, WASPAS: Compósito PCL/β-TCP (impressão 3D) → β-TCP poroso
- T-scaffold, Resistência à compressão: 2, VIKOR: Compósito PCL/β-TCP (impressão 3D) → β-TCP poroso
- P-foco, direta, TOPSIS: Compósito PCL/β-TCP (impressão 3D) → β-TCP poroso
- P-foco, direta, VIKOR: Compósito PCL/β-TCP (impressão 3D) → β-TCP poroso

## Par articular (SEMIQUANTITATIVO: ordinais > 50 % do peso; só indicação)

| Cenário | Variante | TOPSIS | WASPAS | VIKOR |
|---|---|---|---|---|
| A | A | ZTA / ZTA (CoC) | ZTA / ZTA (CoC) | ZTA / ZTA (CoC) |
| P-foco | direta | ZTA / ZTA (CoC) | ZTA / ZTA (CoC) | ZTA / ZTA (CoC) |
| P-foco | direta + indireta | ZTA / ZTA (CoC) | ZTA / ZTA (CoC) | ZTA / ZTA (CoC) |

## Implante dentário (SEMIQUANTITATIVO: ordinais > 50 % do peso; só indicação)

| Cenário | Variante | TOPSIS | WASPAS | VIKOR |
|---|---|---|---|---|
| A | A | Ti cp grau 4 | Ti cp grau 4 | Ti cp grau 4 |
| P-foco | direta | Ti cp grau 4 | Ti cp grau 4 | Ti cp grau 4 |
| P-foco | direta + indireta | Ti cp grau 4 | Ti cp grau 4 | Ti cp grau 4 |
| Valor | Ti-Zr: corrosão 4 | Ti cp grau 4 | Ti cp grau 4 | Ti cp grau 4 |

## Cenários

- **A**: Só materiais em uso clínico (stent: só permanentes, 316L, L605, MP35N, Pt-Cr)
- **B**: Inclui investigação e bioabsorvíveis (stent: A + Mg WE43 e PLLA; permanentes com o pior valor observado no tempo de reabsorção, opção O2)
- **B-bio**: Só bioabsorvíveis (Mg WE43 e PLLA) com o tempo de reabsorção; comparação, não ranking (opção O3)
- **R-sentinela**: Sensibilidade do tempo de reabsorção atribuído aos permanentes: 60, 120, 600 e 1200 meses (opção O1)
- **Q**: Só critérios quantitativos (sem ordinais)
- **W**: Sensibilidade dos pesos
- **η**: Sensibilidade ao nível de confiança η de 0 a 1, passo 0,1 (resultado principal: η = 1)
- **M**: Concordância entre métodos
- **T-scaffold**: Sensibilidade dos alvos
- **T-haste**: Sensibilidade do alvo de E (inclui 14 GPa, Petković et al. 2025, vs 17 GPa)
- **C-custo**: Peso do custo relativo baixo (0,01) vs elevado (0,25), restantes pesos redistribuídos
- **MC**: Incerteza das propriedades
- **P-foco**: Foco no problema crítico do professor (2 out 2026): peso dos critérios de ligação direta x2 (fator_foco_problema), restantes renormalizados; sensibilidade: direta + indireta (data/problemas_criticos.csv). Par articular: sensibilidade semiquantitativa à parte
- **O-orçamento**: Teto de orçamento: exclui na triagem os materiais com custo relativo acima de teto_custo_relativo (3), sem mudar os pesos; cenário A
## Perfis de doente (cenário A; regras de data/perfis_doente.csv)

| Perfil | Caso | Regras | TOPSIS | WASPAS | VIKOR | Borda | Mudanças no consenso |
|---|---|---|---|---|---|---|---|
| H1 Jovem ativo | Haste | H-JOV | Co-Cr-Mo forjado | Ti-6Al-4V ELI | Ti-6Al-4V ELI | Ti-6Al-4V ELI | Aço inox 316L 4.º → 3.º; Co-Cr-Mo forjado 3.º → 2.º; Ti-13Nb-13Zr 2.º → 4.º |
| H2 Idosa com osteoporose | Haste | H-OST | Ti-6Al-4V ELI | Ti-6Al-4V ELI | Ti-6Al-4V ELI | Ti-6Al-4V ELI | Aço inox 316L 4.º → 5.º; Co-Cr-Mo forjado 3.º → 4.º; Ti cp grau 4 5.º → 3.º |
| H3 IMC 38 | Haste | H-IMC | Co-Cr-Mo forjado | Ti-6Al-4V ELI | Ti-6Al-4V ELI | Ti-6Al-4V ELI | Aço inox 316L 4.º → 3.º; Co-Cr-Mo forjado 3.º → 2.º; Ti-13Nb-13Zr 2.º → 4.º |
| S1 Alergia ao níquel | Stent | S-NI | Pt-Cr | Pt-Cr | Pt-Cr | Pt-Cr | sem mudanças |
| S2 Vaso de 2,5 mm com alergia ao níquel | Stent | S-NI; S-VASO | Pt-Cr | Pt-Cr | Pt-Cr | Pt-Cr | sem mudanças |
| C1 Defeito com carga | Scaffold | C-CARGA | Compósito PCL/β-TCP (impressão 3D) | Compósito PCL/β-TCP (impressão 3D) | Compósito PCL/β-TCP (impressão 3D) | Compósito PCL/β-TCP (impressão 3D) | sem mudanças |
| C2 Defeito sem carga | Scaffold | C-SEMCARGA | β-TCP poroso | Compósito PCL/β-TCP (impressão 3D) | β-TCP poroso | β-TCP poroso | β-TCP poroso 2.º → 1.º; Compósito PCL/β-TCP (impressão 3D) 1.º → 2.º |
| D1 Gengiva fina | Implante dentário | D-GENG | Ti cp grau 4 | Ti cp grau 4 | Ti cp grau 4 | Ti cp grau 4 | Ti-6Al-4V ELI 3.º → 5.º; Ti-Zr (~15% Zr) 2.º → 3.º; Zircónia Y-TZP 5.º → 2.º |
| D2 Bruxismo | Implante dentário | D-BRUX | Ti cp grau 4 | Ti cp grau 4 | Ti cp grau 4 | Ti cp grau 4 | sem mudanças |
| D3 Alergia ao titânio confirmada por teste | Implante dentário | D-TI | Zircónia Y-TZP | PEEK | Zircónia Y-TZP | Zircónia Y-TZP | Zircónia Y-TZP 5.º → 1.º; PEEK 4.º → 2.º; excluídos: Ti cp grau 4; Ti-6Al-4V ELI; Ti-Zr (~15% Zr) |
