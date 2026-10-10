# FEA da haste: comparação das duas ferramentas

Razão = energia de deformação no osso com a haste / fémur intacto, nas zonas de Gruen 1 e 7 (malha mais fina de cada ferramenta). Python: fémur anatómico (BodyParts3D), hexaedros de vóxel. SOLIDWORKS Simulation: fémur simplificado modelado por script, tetraedros. Os mesmos materiais, a mesma carga (caso de carga da marcha de Heller 2005: contacto da anca e abdutores) e fixação distal.

| Material da haste | Gruen 1: Python | Gruen 1: SOLIDWORKS | Gruen 7: Python | Gruen 7: SOLIDWORKS |
|---|---|---|---|---|
| Ti-6Al-4V poroso | 0,96 | 1,31 | 1,01 | 1,41 |
| Ti-6Al-4V ELI | 0,61 | 0,63 | 0,22 | 0,44 |
| Aço inox 316L | 0,54 | 0,53 | 0,13 | 0,27 |
| Co-Cr-Mo forjado | 0,53 | 0,53 | 0,12 | 0,25 |

Ordem (mais energia no osso primeiro): Ti-6Al-4V poroso > Ti-6Al-4V ELI > Aço inox 316L > Co-Cr-Mo forjado.
A ordem é a mesma nas duas ferramentas e nas duas zonas.

Os valores absolutos diferem (geometria anatómica contra simplificada, espessura da cortical, posição da fixação, tipo de elemento); a tendência e a ordem são o que se compara.

Haste de Ti-6Al-4V poroso (17 GPa, valor de desenho): com interface colada e rigidez igual à do osso cortical, a energia no osso fica próxima da do osso intacto (razão perto de 1). Uma razão acima de 1 quer dizer só que o osso à volta trabalha um pouco mais do que no fémur intacto.
