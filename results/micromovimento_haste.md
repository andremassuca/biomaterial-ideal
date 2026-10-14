# Micromovimento na interface osso-haste (Ansys MAPDL, contacto com atrito)

Gerado por scripts/mapdl_micromovimento.py. Exploratório (fase 2): não entra no relatório. Verificação numérica, não validação experimental. Carga estática do pico da marcha (Heller 2005); limiar de 150 µm e crescimento ósseo até 28 µm: Pilliar RM et al. Clin Orthop Relat Res 1986;(208):108-113 (só resumo).

## Verificação: contacto sempre colado contra a malha colada da comparação (Ti-6Al-4V ELI)

| Grandeza | Contacto colado | Malha colada (fea_haste_mapdl.json) | Diferença |
|---|---|---|---|
| Energia Gruen 1 (J) | 0,02355 | 0,02355 | 0,00 % |
| Energia Gruen 7 (J) | 0,01856 | 0,01856 | 0,00 % |
| Deslocamento máximo (mm) | 6,485 | 6,485 | 0,00 % |
| Micromovimento máximo (µm) | 0,00 | 0 | - |

## Micromovimento com atrito

| Caso | Haste | μ | Nós da interface | Tangencial máx. (µm) | Tangencial P95 (µm) | Tangencial mediana (µm) | Nós > 150 µm | Nós ≤ 28 µm | Abertura máx. (µm) | Relativo total máx. (µm) | Contacto aberto | A escorregar |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| atrito04_Ti | Ti-6Al-4V ELI | 0,4 | 5035 | 78,4 | 64,9 | 48,1 | 0,0 % | 6,3 % | 22,4 | 83,5 | 74,6 % | 12,1 % |
| atrito02_Ti | Ti-6Al-4V ELI | 0,2 | 5035 | 99,1 | 92,2 | 73,3 | 0,0 % | 4,3 % | 32,9 | 101,2 | 75,3 % | 12,2 % |
| atrito04_CoCr | Co-Cr-Mo forjado | 0,4 | 5035 | 64,8 | 55,1 | 45,5 | 0,0 % | 6,5 % | 22,7 | 66,5 | 73,5 % | 12,5 % |
| atrito04_Ti_fkn10 | Ti-6Al-4V ELI | 0,4 | 5035 | 65,7 | 52,4 | 35,2 | 0,0 % | 21,2 % | 7,2 | 71,7 | 74,1 % | 13,9 % |
| atrito04_Ti_rigido | Ti-6Al-4V ELI | 0,4 | 5035 | 63,9 | 50,2 | 33,0 | 0,0 % | 29,7 % | 6,5 | 70,1 | 74,2 % | 13,7 % |
