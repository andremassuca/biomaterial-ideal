# CFD do stent: sangue newtoniano contra Carreau

Gerado por scripts/cfd_stent.py resumo_carreau. Exploratório (fase 2): não entra no relatório. Malha média, mesmas condições do docs/CFD_STENT.md; só muda a viscosidade.

Carreau: mu0 = 0,056 Pa.s, mu_inf = 0,0035 Pa.s, lambda = 3,313 s, n = 0,3568 (Cho e Kensey 1991 [confirmar], lidos em Kumar et al., arXiv:2503.23049, Tabela II).

| Caso | Strut | Área < 0,4 Pa newtoniano | Área < 0,4 Pa Carreau | Diferença (p.p.) | Tensão média newt. (Pa) | Tensão média Carreau (Pa) |
|---|---|---|---|---|---|---|
| Estacionário (caudal médio) | Pt-Cr (79 µm) | 46,2 % | 36,8 % | -9,4 | 0,410 | 0,509 |
| Estacionário (caudal médio) | 316L (135 µm) | 80,9 % | 68,4 % | -12,5 | 0,233 | 0,298 |
| Estacionário, Carreau com 8000 iterações | Pt-Cr (79 µm) | 46,2 % | 36,8 % | -9,4 | 0,410 | 0,509 |
| Estacionário, Carreau com 8000 iterações | 316L (135 µm) | 80,9 % | 68,5 % | -12,4 | 0,233 | 0,297 |
