# FEA da haste: sensibilidade ao módulo do osso trabecular

Gerado por scripts/fea_haste.py --sensibilidade-trabecular 2440 (malha de 0,75 mm). Caso principal: 0,39 GPa; sensibilidade: 2,44 GPa.

| Material da haste | Razão G1 (0,39 GPa) | Razão G1 (2,44 GPa) | Razão G7 (0,39 GPa) | Razão G7 (2,44 GPa) |
|---|---|---|---|---|
| 316L | 0,538 | 0,496 | 0,127 | 0,122 |
| Co-Cr-Mo | 0,533 | 0,487 | 0,120 | 0,112 |
| Ti-6Al-4V | 0,608 | 0,597 | 0,220 | 0,249 |
| Ti-6Al-4V poroso | 0,963 | 0,964 | 1,006 | 1,405 |

- Gruen 1: ordem igual (sensibilidade: Ti-6Al-4V poroso > Ti-6Al-4V > 316L > Co-Cr-Mo).
- Gruen 7: ordem igual (sensibilidade: Ti-6Al-4V poroso > Ti-6Al-4V > 316L > Co-Cr-Mo).
