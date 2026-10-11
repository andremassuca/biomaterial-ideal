# Verificações pedidas pela revisão por especialistas

Gerado por scripts/verificacoes_revisao.py a partir de data/ (η = 1). O Spearman entre métodos (R22) está em results/spearman.csv.

## R25: conjunto de compromisso do VIKOR (Anexo A.5, eq. 20)

C1: P(2) - P(1) ≥ 1/(m - 1); C2: o 1.º por P também é o melhor em S ou em R.

| Caso | Cenário | Ordem por P (P) | Limiar 1/(m - 1) | C1 | C2 | Conjunto de compromisso |
|---|---|---|---|---|---|---|
| Haste | A | Ti-6Al-4V ELI (0,000); Ti-13Nb-13Zr (0,606); Co-Cr-Mo forjado (0,725); Aço inox 316L (0,767); Ti cp grau 4 (0,853) | 0,250 | sim | sim | Ti-6Al-4V ELI |
| Haste | B | Ti-6Al-4V ELI (0,000); Ti-13Nb-13Zr (0,318); Ti cp grau 4 (0,522); Co-Cr-Mo forjado (0,756); Aço inox 316L (0,785); Ti-35Nb-7Zr-5Ta (TNZT) (0,963) | 0,200 | sim | sim | Ti-6Al-4V ELI |
| Stent | A | Pt-Cr (0,000); Co-Cr L605 (0,025); Co-Ni-Cr-Mo MP35N (0,099); Aço inox 316L (1,000) | 0,333 | não | sim | Pt-Cr, Co-Cr L605, Co-Ni-Cr-Mo MP35N |
| Stent | B | Co-Cr L605 (0,000); Pt-Cr (0,011); Co-Ni-Cr-Mo MP35N (0,048); Aço inox 316L (0,346); Liga de Mg WE43 (bioabsorvível) (0,449); PLLA (bioabsorvível) (1,000) | 0,200 | não | sim | Co-Cr L605, Pt-Cr, Co-Ni-Cr-Mo MP35N |
| Scaffold | A | Compósito PCL/β-TCP (impressão 3D) (0,000); β-TCP poroso (0,097); Vidro bioativo 45S5 poroso (0,571); PCL (0,601); Hidroxiapatite (HA) porosa (1,000) | 0,250 | não | sim | Compósito PCL/β-TCP (impressão 3D), β-TCP poroso |
| Scaffold | B | Compósito PCL/β-TCP (impressão 3D) (0,000); β-TCP poroso (0,098); Vidro bioativo 45S5 poroso (0,389); PCL (0,548); PLLA (0,668); Hidroxiapatite (HA) porosa (0,771); Quitosano/HA (liofilizado) (0,974); PLGA 50:50 (1,000) | 0,143 | não | sim | Compósito PCL/β-TCP (impressão 3D), β-TCP poroso |

## R27: vencedor com o típico e com o ponto médio de cada intervalo (cenário A)

| Caso | Método | Vencedor (típico) | Vencedor (ponto médio) |
|---|---|---|---|
| Haste | TOPSIS | Ti-6Al-4V ELI | Ti-6Al-4V ELI |
| Haste | WASPAS | Ti-6Al-4V ELI | Ti-6Al-4V ELI |
| Haste | VIKOR | Ti-6Al-4V ELI | Ti-6Al-4V ELI |
| Stent | TOPSIS | Pt-Cr | Pt-Cr |
| Stent | WASPAS | Co-Cr L605 | Pt-Cr |
| Stent | VIKOR | Pt-Cr | Pt-Cr |
| Scaffold | TOPSIS | β-TCP poroso | β-TCP poroso |
| Scaffold | WASPAS | Compósito PCL/β-TCP (impressão 3D) | β-TCP poroso |
| Scaffold | VIKOR | Compósito PCL/β-TCP (impressão 3D) | β-TCP poroso |

## R91: tempo de degradação do compósito PCL/β-TCP com o intervalo do PCL (24 a 48 meses)

Sensibilidade: só o compósito muda (intervalo 24-48 meses, o do PCL na base); a base não muda (compósito: 26 meses, Zhong 2026, verificado a 11 out). Vencedor (2.º) por método; ΔC do TOPSIS entre o 1.º e o 2.º.

| Cenário | Típico do compósito (meses) | TOPSIS | WASPAS | VIKOR | ΔC TOPSIS |
|---|---|---|---|---|---|
| A | 24 | β-TCP poroso (Compósito PCL/β-TCP (impressão 3D)) | Compósito PCL/β-TCP (impressão 3D) (β-TCP poroso) | Compósito PCL/β-TCP (impressão 3D) (β-TCP poroso) | 0,014 |
| A | 36 | β-TCP poroso (Vidro bioativo 45S5 poroso) | Compósito PCL/β-TCP (impressão 3D) (β-TCP poroso) | Compósito PCL/β-TCP (impressão 3D) (β-TCP poroso) | 0,038 |
| A | 48 | β-TCP poroso (Vidro bioativo 45S5 poroso) | β-TCP poroso (PCL) | β-TCP poroso (Compósito PCL/β-TCP (impressão 3D)) | 0,038 |
| B | 24 | Compósito PCL/β-TCP (impressão 3D) (β-TCP poroso) | Compósito PCL/β-TCP (impressão 3D) (PCL) | Compósito PCL/β-TCP (impressão 3D) (β-TCP poroso) | 0,021 |
| B | 36 | β-TCP poroso (Compósito PCL/β-TCP (impressão 3D)) | PCL (β-TCP poroso) | Compósito PCL/β-TCP (impressão 3D) (β-TCP poroso) | 0,011 |
| B | 48 | β-TCP poroso (Vidro bioativo 45S5 poroso) | PCL (β-TCP poroso) | β-TCP poroso (Compósito PCL/β-TCP (impressão 3D)) | 0,035 |

## R46: fração da parede do stent com TAWSS abaixo de cada limiar (fluxo pulsátil, malha média)

| Limiar (Pa) | Pt-Cr (79 µm) | 316L (135 µm) |
|---|---|---|
| 0,3 | 35 % | 67 % |
| 0,4 | 47 % | 82 % |
| 0,5 | 59 % | 94 % |
| 0,6 | 73 % | 97 % |
| 0,8 | 98 % | 99 % |
| 1,0 | 100 % | 100 % |

TAWSS média na zona do stent relativa à tensão de corte do tubo sem stent (Poiseuille com a velocidade média do ciclo, 0,868 Pa):

- Pt-Cr: 0,408 Pa, razão 0,47
- 316L: 0,232 Pa, razão 0,27
