"""Análise por elementos finitos (FEA) da haste femoral: extensão exploratória sobre o stress shielding.

Módulos:
- materiais: módulos de elasticidade e coeficientes de Poisson (base de dados e osso);
- malha: malha da barra de verificação (gmsh) e malhas de vóxeis (hexaedros) a partir de etiquetas;
- solver: rigidez, resolução do sistema e energia de deformação por elemento;
- geometria: referencial do fémur e da haste (o mesmo dos renders) e etiquetas de cada região;
- cargas: forças da marcha (contacto da anca e abdutores) e distribuição pelos nós;
- gruen: zonas de Gruen à volta da haste;
- posproc: energia por zona, razões face ao fémur intacto e convergência.
"""
