# Proposta de patologias e condições do doente (notas)

Ficheiro: patologias_proposta.csv (25 regras novas, mesmo formato que data/perfis_doente.csv).
Estados: 8 Verificado, 15 Regra do trabalho, 2 A verificar.

Como foi verificado: cada DOI foi confirmado na API do Crossref (título, revista, ano, autores) e o
conteúdo que justifica a regra foi lido no resumo do Europe PMC (PubMed). No KDIGO 2017 o resumo
está vazio e a frase foi lida no texto aberto (PMC6340919). Todos os fatores (x2) são valores de
desenho do trabalho ("fator do trabalho").

Força: **forte** = meta-análise, revisão sistemática, guideline ou ensaio grande com a ligação
direta ao mecanismo; **média** = boa fonte para o fator de risco, mas a ligação ao critério é do
trabalho; **fraca** = estudo pequeno, in vitro, animal ou evidência contraditória.

## Haste femoral

**H-RM (RM frequente, peso RM x2), Verificado, média.** Mecanismo: o metal distorce o campo
magnético e apaga ou deforma a imagem à volta da haste; o titânio perturba menos. Fonte: Breit 2023
(fantoma, 0,55/1,5/3 T): pontuação de artefacto menor para ligas de Ti (2,44/2,9/2,7) do que para
aço inox (4,1/3,9/5,1) e Co-Cr (4,1/4,1/5,2), p < 0,001. Månsson 2015: a prótese de titânio deu
artefactos 3 a 4 vezes menores. Fraqueza: fantoma, não doentes.

**H-CORT (corticoterapia, peso módulo x2), Regra do trabalho, média.** Mecanismo: os corticoides
tiram osso; com osso fraco o stress shielding pesa mais (mesmo raciocínio da H-OST). Fonte: guideline
ACR 2022 (Humphrey 2023): define o grupo (mais de 3 meses com 2,5 mg/dia ou mais) e recomenda
avaliar logo o risco de fratura. A guideline é forte para a perda óssea; a ligação ao módulo é nossa.

**H-IRC (TFG < 60, peso módulo x2), Regra do trabalho, média.** Mecanismo: o rim doente altera o
cálcio, o fósforo e a hormona paratiroideia, e o osso fica mais frágil. Fonte: KDIGO 2017, texto:
"patients with CKD G3a-G5D have increased fracture rates compared with the general population".
Guideline forte; ligação ao módulo nossa.

**H-AR (artrite reumatoide, nota), Verificado, forte para o facto.** Mecanismo: o risco é de luxação
(tecidos moles, tamanho da cabeça), não do material da haste. Fonte: Ravi 2012, meta-análise de 40
estudos: OR ajustado de luxação 2,16 (1,52 a 3,07); sem diferença na revisão tardia.

**H-TAB (tabagismo, nota), Verificado, média.** Mecanismo: o tabaco piora a irrigação e a
cicatrização (fixação e infeção). Fonte: Teng 2015, 6 coortes, 8181 doentes: descolamento asséptico
RR 3,05; infeção profunda RR 3,71; revisão RR 2,58. Não há critério do material que responda.

**H-TI (alergia ao titânio, nota), Regra do trabalho, fraca.** Mecanismo: partículas e iões de
titânio podem ativar a imunidade inata ou uma alergia verdadeira. Fonte: Chen & Kurmis 2024 (35
artigos, evidência "poor"): não há teste de rastreio sensível; o teste epicutâneo é pouco fiável.
Ponto para o André decidir: uma exclusão (como a D-TI) deixaria só o 316L e o Co-Cr-Mo.

## Par articular

**P-RM (RM frequente, peso RM x2), Regra do trabalho, fraca.** Mesmo mecanismo da H-RM. A fonte
(Breit 2023) mediu próteses metálicas; a cabeça de ZTA não foi estudada.

**P-IRC (TFG < 15 ou diálise, peso segurança iónica x2), Regra do trabalho, fraca.** Mecanismo: o
cobalto sai pelo rim; com o rim parado acumula-se no sangue. Fontes: Hur 2008 (5 doentes com
insuficiência renal crónica e par metal-metal): cobalto sérico médio 12,5 µg/L, mais de 100 vezes o
dos doentes com rim normal; crómio normal. Manninen 2021 (1244 doentes): sem acumulação de Co ou Cr
na insuficiência ligeira a grave (só 6 doentes em fase terminal). Contraditório; por isso o limiar
fica na fase terminal. Nota: o MoM já sai pela triagem; a regra pesa sobretudo nas cabeças de CoCrMo.

## Stent vascular

**S-DIAB (diabetes, peso strut x2), Regra do trabalho, média.** Mecanismo: o diabético faz mais
proliferação da parede (reestenose); struts finos reduzem a reestenose. Fonte: Kastrati 1997 (1349
doentes): a diabetes foi o preditor mais forte, OR 1,86 para reestenose binária e 1,45 para nova
revascularização. A ligação à espessura do strut é nossa (Kastrati 2001 já é a fonte do critério).

**S-RM (RM frequente, peso RM x2), Regra do trabalho, fraca.** Mecanismo: o metal do stent apaga o
sinal dentro do lúmen em angio-RM. Fonte: Lenhart 2000 (14 stents in vitro): só um stent de liga de
cobalto deu vazio total; tântalo e quatro de Nitinol foram os melhores; "stent geometry, relative
orientation to the magnetic field, and alloy composition influence" o sinal. A geometria conta tanto
como a liga.

**S-CO (alergia ao cobalto confirmada e reestenose recorrente, exclusão de L605 e MP35N), Regra do
trabalho, fraca.** Mecanismo: reação alérgica local ao metal libertado poderia alimentar a
reestenose. Fontes: Iijima 2005 (174 doentes): sem relação após o primeiro stent (10 % contra 9 %),
mas teste positivo em 39 % contra 12 % com nova reestenose depois de tratar uma reestenose (OR
4,39). Slodownik 2018 (99 doentes): sem associação (28,6 % contra 27,6 %). Por isso a condição exige
as duas coisas. Ficam 316L e Pt-Cr; a ausência de cobalto no Pt-Cr e no 316L não está registada nos
dados (a composição do Pt-Cr vem de Bennett & Dubois, já em materiais.csv para o níquel).
Crómio: não se propõe regra, porque todas as ligas permanentes têm crómio (mesma lógica da S-NI).

**S-IRC (TFG < 60, nota), Verificado, forte para o facto.** Lu 2016, meta-análise de 38 estudos e
123 396 doentes: DES contra stent metálico simples, MACE OR 0,75 e mortalidade OR 0,81. Compara tipos
de stent, não ligas.

**S-IDOSO (idade 75 ou mais, nota), Verificado, forte para o facto.** SENIOR (Varenne 2018, 1200
doentes): DES com antiagregação dupla curta, objetivo composto RR 0,71; hemorragias iguais. Financiado
pela Boston Scientific (declarar se citado). O resumo não diz a liga do DES usado.

## Scaffold ósseo

As quatro regras usam o mesmo raciocínio: quando o doente forma menos osso, o scaffold deve ajudar
mais (osteocondução), e o trabalho sobe o peso da bioatividade. A ligação ao critério é sempre nossa.

**C-DIAB, Regra do trabalho, média.** Jiao 2015 (revisão): a diabetes "interferes with bone
formation, and impairs fracture healing", com mais osteoclastos e menos osteoblastos.

**C-TAB, Regra do trabalho, média a forte para o fator.** Scolaro 2014 (revisão sistemática, 19
estudos): não união OR ajustado 2,32 (1,76 a 3,06) nos fumadores.

**C-OST, Regra do trabalho, fraca.** Gorter 2021 (revisão sistemática, 93 artigos): a evidência do
efeito negativo vem "predominantly from animal studies"; 2 grandes bases de dados a favor e 3
estudos contra. Chandran 2024 (IOF) diz o mesmo: os dados clínicos não confirmam os animais.

**C-CORT, Regra do trabalho, fraca.** Liu 2018 (ratinhos): a prednisona inibiu a ossificação
endocondral e atrasou a consolidação. Só animal.

## Implante dentário

**D-RADIO (radioterapia da cabeça e pescoço, peso osteointegração x2), Verificado, forte.**
Mecanismo: a radiação reduz os vasos e as células do osso (osteorradionecrose), e o osso integra
pior o implante. Fontes: Chrcanovic 2016 (meta-análise): "irradiation negatively affects the survival
of implants", pior com doses altas; sem efeito comprovado do oxigénio hiperbárico. Chen 2013 (51
estudos): RR 2,28 (1,49 a 3,51). Schimmel 2018 (EAO): a sobrevivência é afetada "namely by
radiotherapy".

**D-OST (osteoporose), Regra do trabalho, média.** De Medeiros 2018 (15 estudos, 8859 doentes): sem
diferença na sobrevivência (RR 1,39; IC 0,93 a 2,08); mais 0,18 mm de perda óssea marginal. Chen
2013 também não significativo (RR 1,09). Mesma lógica da D-DIAB.

**D-RM (RM frequente, peso RM x2), Verificado, média.** Mecanismo: a zircónia não é metálica e quase
não perturba o campo. Bohner 2020 (osso de porco, 3 T): artefacto 2,57 mm no titânio e 0,37 mm na
zircónia (p < 0,05). In vitro.

**D-IDOSO (idade 75 ou mais, nota), Verificado, forte.** Schimmel 2018 (revisão do consenso EAO):
sobrevivência 97,3 % a 1 ano e 96,1 % a 5 anos com 75 anos ou mais; "predictable treatment option".
Srinivasan 2017 (65 anos ou mais): 96,2 % a 5 anos. A idade não justifica mudar o ranking.

**D-IRC (diálise), Regra do trabalho, fraca.** Yuan 2017 é uma revisão com orientação clínica: lista
lesões ósseas, infeções, hemorragia e fármacos; não dá taxas de falha.

**D-AR (artrite reumatoide com doença do tecido conjuntivo), Regra do trabalho, fraca.** Krennmair
2010 (34 doentes): artrite isolada com sobrevivência de 100 %; com doença do tecido conjuntivo, perda
óssea 3,1 contra 2,1 mm (p < 0,01).

**D-CORT (corticoterapia), A verificar, fraca.** Só a guideline ACR (perda óssea) e analogia com a
D-OST. Não encontrei revisão sobre corticoides e falha de implantes dentários: falta fonte
[confirmar].

**D-HTA (hipertensão, nota), A verificar, fraca.** O resumo de Schimmel 2018 só fala em "doença
cardiovascular" (sobrevivência igual ou superior); falta confirmar no texto que inclui a hipertensão.

## Fontes melhores ou complementares para regras existentes

- **D-BRUX**: Chrcanovic 2016 é uma análise de uma coorte. Há duas meta-análises: Zhou Y et al. Clin
  Implant Dent Relat Res 2016;18(2):410-420, doi:10.1111/cid.12300 (OR 4,72 por prótese e 3,83 por
  doente) e Ionfrida JA et al. Dent J (Basel) vol. 13(1):11, publicado a 26 dez 2024,
  doi:10.3390/dj13010011 (15 estudos, OR 4,68; conclui que o bruxismo é "a probable risk factor for
  mechanical issues"). A segunda reforça a ligação à tenacidade (falhas mecânicas); a D-BRUX poderia
  passar a Verificado se o André concordar.
- **D-TI**: a regra exige "alergia confirmada por teste", mas Müller-Heupt 2022 (Int J Implant Dent
  8:29, doi:10.1186/s40729-022-00428-0, revisão sistemática) conclui que
  os testes (epicutâneo, LTT, MELISA) dão resultados inconsistentes e "should be regarded cautiously".
  Convém acrescentar esta ressalva à justificação da D-TI e da D-TI-NOTA.
- **D-TAB**: Chen 2013 (PLoS One, 51 estudos) dá RR 1,92 (1,67 a 2,21); pode juntar-se ao Chrcanovic
  2015.
- **D-DIAB**: Chen 2013 (RR 0,90, não significativo) e Schimmel 2018 ("high implant survival" na
  diabetes tipo 2) confirmam o "inconclusivo" da regra atual.
- **D-PERIO**: a guideline S3 da EFP (Herrera 2023, doi:10.1111/jcpe.13823) existe, mas o resumo não
  refere a história de periodontite como fator de risco; Schwarz 2018 continua a ser a melhor fonte.
- **H-OST**: não encontrei fonte melhor do que Sychterz 1996 nesta pesquisa.

## Condições sem regra nova (e porquê)

- **Hipertensão** (anca, stent, scaffold): não encontrei fonte que ligue a hipertensão a um critério
  do material.
- **Obesidade/IMC** fora da haste (par, stent, implante, scaffold): não encontrei fonte com ligação
  ao material. A H-IMC já existe.
- **Diabetes na anca**: o risco conhecido é de infeção periprotésica, que nenhum critério do material
  cobre.
- **Idade avançada na anca**: já coberta pela H-OST e pela nova H-RM (a justificação do critério de RM
  em criterios.csv diz "doentes idosos precisam frequentemente de RM", sem fonte).
- **Doença periodontal**: já coberta pela D-PERIO.

## Pontos para o André decidir

1. O estado "A verificar" não está definido em data/leia_me.md (só Verificado e Regra do trabalho);
   foi usado como pedido para as 2 regras sem fonte confirmada.
2. Novos códigos de condição: rm_frequente, corticoterapia, tfg (número), artrite_reumatoide,
   doenca_tecido_conjuntivo, tabagismo, alergia_titanio, alergia_cobalto_confirmada,
   reestenose_recorrente, radioterapia_cabeca_pescoco, dialise, hipertensao, idade (já existia).
   O tfg<60 da H-IRC e o tfg<15 da P-IRC usam o mesmo código com limiares diferentes.
3. Várias regras sobem o mesmo critério no mesmo dispositivo (por exemplo D-TAB, D-DIAB, D-RADIO e
   D-OST na osteointegração): pela regra atual usa-se o maior fator e não o produto.
4. S-CO usa exclusão; a alternativa mais prudente é "nota".
