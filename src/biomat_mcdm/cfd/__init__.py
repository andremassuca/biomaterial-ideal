"""Dinâmica de fluidos computacional (CFD) do stent coronário: extensão exploratória sobre a espessura dos struts.

Módulos:
- analitico: escoamento de Poiseuille num tubo (perfil de velocidade e tensão de corte na parede) e números
  adimensionais (Reynolds, Womersley);
- geometria: setor da artéria e struts do stent em losangos (polígono no plano desenrolado e sólido em STL);
- onda: caudal pulsátil ao longo do ciclo cardíaco;
- openfoam: dicionários do OpenFOAM (malha de fundo, snappyHexMesh, condições de fronteira, controlo);
- posproc: tensão de corte média no tempo (TAWSS), índice de corte oscilatório (OSI) e área com corte baixo.
"""
