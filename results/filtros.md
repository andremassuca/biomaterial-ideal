# Filtros de requisito e cenário da esterilização

Gerado por scripts/run_all.py (src/biomat_mcdm/filtros.py; dados em data/filtros_material.csv). Os filtros não entram como critérios com peso; os rankings do relatório não mudam.

## RM (ASTM F2503) e ISO 10993-1

| Material | RM | ISO 10993-1 |
|---|---|---|
| Aço inox 316L | passa | avaliada em dispositivos clínicos |
| Co-Cr-Mo forjado | passa | avaliada em dispositivos clínicos |
| Ti-6Al-4V ELI | passa | avaliada em dispositivos clínicos |
| Ti cp grau 4 | passa | avaliada em dispositivos clínicos |
| Ti-13Nb-13Zr | A verificar | avaliada em dispositivos clínicos |
| Ti-35Nb-7Zr-5Ta (TNZT) | A verificar | por demonstrar no dispositivo final |
| CoCrMo / UHMWPE convencional (MoP) | A verificar | avaliada em dispositivos clínicos |
| CoCrMo / HXLPE (MoXLPE) | A verificar | avaliada em dispositivos clínicos |
| ZTA / HXLPE (CoXLPE) | A verificar | avaliada em dispositivos clínicos |
| ZTA / ZTA (CoC) | passa | avaliada em dispositivos clínicos |
| CoCrMo / CoCrMo (MoM) | passa | avaliada em dispositivos clínicos |
| Ti-Zr (~15% Zr) | A verificar | avaliada em dispositivos clínicos |
| Zircónia Y-TZP | passa | avaliada em dispositivos clínicos |
| PEEK | passa | avaliada em dispositivos clínicos |
| Co-Cr L605 | passa | avaliada em dispositivos clínicos |
| Co-Ni-Cr-Mo MP35N | passa | avaliada em dispositivos clínicos |
| Pt-Cr | A verificar | avaliada em dispositivos clínicos |
| Nitinol (autoexpansível) | passa | fora do ranking |
| Liga de Mg WE43 (bioabsorvível) | passa | avaliada em dispositivos clínicos |
| PLLA (bioabsorvível) | passa | avaliada em dispositivos clínicos |
| PCL | A verificar | avaliada em dispositivos clínicos |
| PLLA | passa | por demonstrar no dispositivo final |
| PLGA 50:50 | passa | por demonstrar no dispositivo final |
| Hidroxiapatite (HA) porosa | passa | avaliada em dispositivos clínicos |
| β-TCP poroso | passa | avaliada em dispositivos clínicos |
| Vidro bioativo 45S5 poroso | A verificar | avaliada em dispositivos clínicos |
| Compósito PCL/β-TCP (impressão 3D) | A verificar | avaliada em dispositivos clínicos |
| Quitosano/HA (liofilizado) | A verificar | por demonstrar no dispositivo final |

Nenhum material é ferromagnético na base; os que estão "A verificar" não têm fonte direta.

## Esterilização imposta (sensibilidade)

Saem os materiais incompatíveis com o método; "com restrições" e "A verificar" ficam.

| Caso | Cenário | Método | Saem | Vencedor antes (T/W/V) | Vencedor depois (T/W/V) |
|---|---|---|---|---|---|
| Stent | B | vapor | Liga de Mg WE43 (bioabsorvível); PLLA (bioabsorvível) | Co-Cr L605 / Co-Cr L605 / Co-Cr L605 | Pt-Cr / Co-Cr L605 / Pt-Cr |
| Scaffold | A | vapor | PCL; Compósito PCL/β-TCP (impressão 3D) | β-TCP poroso / Compósito PCL/β-TCP (impressão 3D) / Compósito PCL/β-TCP (impressão 3D) | Vidro bioativo 45S5 poroso / β-TCP poroso / β-TCP poroso |
| Scaffold | B | vapor | PCL; PLLA; PLGA 50:50; Compósito PCL/β-TCP (impressão 3D) | Compósito PCL/β-TCP (impressão 3D) / Compósito PCL/β-TCP (impressão 3D) / Compósito PCL/β-TCP (impressão 3D) | β-TCP poroso / β-TCP poroso / β-TCP poroso |

Combinações sem linha: nenhum material incompatível (o ranking não muda).
