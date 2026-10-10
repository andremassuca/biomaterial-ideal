# CFD do stent coronário: struts finos (Pt-Cr) contra grossos (316L)

Gerado por scripts/cfd_stent.py resumo. Hipóteses e fontes em docs/CFD_STENT.md. Extensão exploratória: OpenFOAM v2406, sangue newtoniano, parede rígida, setor de 22.5° com planos de simetria.

## 1. Teste analítico: Poiseuille num tubo

Tubo de 3,0 mm, escoamento periódico com a velocidade média do ciclo (9,3 cm/s), malha média (39375 células).

| Grandeza | Teoria | CFD | Erro |
|---|---|---|---|
| Tensão de corte na parede (Pa) | 0,8680 | 0,8701 | 0,24 % (máximo local 0,25 %) |
| Queda de pressão (Pa/m) | 1157,33 | 1162,40 | 0,44 % |
| Perfil de velocidade | parábola | 39375 células | máximo 1,49 %, médio quadrático 0,23 % (em fração da velocidade no eixo) |

Critério: erro abaixo de 2 %. Cumpre.

## 2. Convergência da malha (estacionário, caudal médio)

Tensão de corte na parede da artéria na zona do stent (sem a superfície dos struts).

| Material | Malha | Célula junto à parede (µm) | Células | Tensão média (Pa) | Área abaixo de 0,4 Pa |
|---|---|---|---|---|---|
| Pt-Cr | grossa | 28 | 155278 | 0,410 | 45,8 % |
| Pt-Cr | media | 20 | 380091 | 0,410 | 46,2 % |
| Pt-Cr | fina | 14 | 1069077 | 0,407 | 46,8 % |
| 316L | grossa | 28 | 161120 | 0,235 | 80,5 % |
| 316L | media | 20 | 385556 | 0,233 | 80,9 % |
| 316L | fina | 14 | 1098971 | 0,230 | 81,6 % |

- Pt-Cr, tensão média: variação da malha média para a fina 0,7 %; as diferenças entre malhas não diminuem, por isso a ordem e o GCI não se calculam
- Pt-Cr, área abaixo de 0,4 Pa: variação da malha média para a fina 1,5 %; as diferenças entre malhas não diminuem, por isso a ordem e o GCI não se calculam
- 316L, tensão média: variação da malha média para a fina 1,3 %; as diferenças entre malhas não diminuem, por isso a ordem e o GCI não se calculam
- 316L, área abaixo de 0,4 Pa: variação da malha média para a fina 0,8 %; as diferenças entre malhas não diminuem, por isso a ordem e o GCI não se calculam

## 3. Fluxo pulsátil (malha média, segundo ciclo)

| Material | Espessura do strut (µm) | TAWSS média (Pa) | Área com TAWSS abaixo de 0,4 Pa | OSI médio | Área com OSI acima de 0,1 |
|---|---|---|---|---|---|
| Pt-Cr | 79 | 0,408 | 46,5 % | 0,001 | 0,1 % |
| 316L | 135 | 0,232 | 82,1 % | 0,009 | 1,6 % |

Repetição entre ciclos (tensão média na parede no mesmo instante do 1.º e do 2.º ciclo, na última metade do ciclo):

- Pt-Cr: diferença máxima 0,0 %
- 316L: diferença máxima 0,0 %

## 4. Passo de tempo (316L, malha grossa)

| Passos por ciclo | TAWSS média (Pa) | Área abaixo de 0,4 Pa |
|---|---|---|
| 1000 | 0,234 | 81,4 % |
| 2000 | 0,234 | 81,4 % |

Variação: TAWSS 0,06 %; área 0,05 pontos percentuais.

