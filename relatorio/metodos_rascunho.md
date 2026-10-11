# 2. Métodos

## 2.1 Visão geral

Para cada caso clínico seguiu-se o mesmo processo, em seis passos:
1. definição da função do dispositivo e do problema do material atual;
2. escolha dos materiais candidatos;
3. triagem por critérios eliminatórios;
4. definição dos critérios de comparação e dos respetivos pesos;
5. normalização dos valores e ordenação dos materiais por três métodos de decisão multicritério;
6. análise da robustez do resultado.

A implementação foi verificada uma vez, antes de todos os casos, reproduzindo um estudo publicado (capítulo 3).

Três casos (haste femoral, stent coronário expansível por balão e scaffold para regeneração óssea) foram tratados quantitativamente. Os outros dois componentes (par articular da anca e implante dentário) foram tratados de forma semiquantitativa, porque a maior parte do peso dos seus critérios cabia a escalas ordinais (60 % do peso no par articular e 70 % no implante dentário; a regra do trabalho, uma convenção deste trabalho, é não passar de 50 % nos casos quantitativos, que têm 30 a 45 %). Nestes, o ranking é calculado da mesma forma, mas é apresentado como indicação: é numérico no sentido computacional e semiquantitativo na interpretação, porque depende sobretudo de escalas ordinais.

Neste relatório, chama-se quantitativo a um caso em que a maior parte do peso cabe a propriedades físicas medidas, com unidades, e semiquantitativo a um caso em que a maior parte do peso cabe a escalas ordinais.

## 2.2 Materiais candidatos e cenários

Para cada caso, os candidatos incluem os materiais em uso clínico e alternativas em investigação. Para não misturar materiais com graus de evidência muito diferentes, os resultados foram obtidos em dois cenários:
- **Cenário A:** só materiais em uso clínico.
- **Cenário B:** inclui também materiais em investigação (e, no stent, os bioabsorvíveis).

## 2.3 Critérios

Cada critério pertence a um de quatro tipos:
- **Estrito (eliminatório):** o material passa ou não passa (por exemplo, a biocompatibilidade, ou o tipo de expansão do stent). Na biocompatibilidade, foram considerados candidatos com historial de uso clínico ou evidência publicada de biocompatibilidade; não foram feitos ensaios ISO 10993 neste trabalho. Os materiais eliminados ficam registados, com o motivo.
- **Benefício:** quanto maior, melhor (por exemplo, a resistência à fadiga).
- **Custo:** quanto menor, melhor (por exemplo, a densidade ou o custo relativo).
- **Alvo:** o melhor valor é um valor intermédio. É o caso do módulo de Young da haste, que deve aproximar-se do osso cortical para reduzir o stress shielding. Seguiu-se a abordagem de critérios-alvo de Petković et al. 2025. O módulo de Young foi usado como aproximação de primeira ordem da compatibilidade de rigidez entre o implante e o osso. Não substitui uma análise estrutural: a rigidez efetiva de uma haste depende também da geometria, da porosidade e da fixação, e o stress shielding não entra no ranking; foi estimado à parte, numa simulação exploratória por elementos finitos (secção 8.3), como energia de deformação no osso face ao fémur intacto.

Usaram-se também dois índices derivados:
- σy/E, como indicador do recuo elástico do stent;
- E_implante/E_osso, como medida do desajuste de rigidez da haste.

Alguns critérios não têm uma grandeza física simples (resistência à corrosão, compatibilidade com ressonância magnética, fabricabilidade, custo relativo). Para estes usaram-se escalas ordinais de 1 a 5, com uma rubrica escrita para cada nível, apoiada em literatura. As rubricas de cada escala estão no Anexo C. A compatibilidade com ressonância magnética depende do dispositivo completo e não só do material; a nota usada aproxima-a pelo material predominante.

## 2.4 Base de dados e verificação dos valores

Todos os valores estão numa base de dados única (ficheiros CSV). Cada valor tem um mínimo, um máximo, um valor típico, a fonte e um estado de verificação: "Verificado", "Verificado (fornecedor)", "Verificado (derivado)", "Verificado (composição química)", "Verificado (composição nominal)", "Valor de modelação" (número fixado por uma regra do trabalho, sem fonte numérica própria; por exemplo, o tempo de degradação da HA, que praticamente não reabsorve) ou "A verificar".

Os valores de partida vieram de revisões. Os valores com mais influência no resultado foram verificados em fontes primárias (normas, artigos com ensaio, fichas técnicas de fabricantes e de fornecedores), exceto três propriedades do Pt-Cr no stent (módulo, resistência à tração e alongamento), ainda só confirmadas em fontes secundárias; os restantes ficam marcados "A verificar" (@@N_VERIFICADOS@@ das @@N_TOTAL@@ linhas da base estão verificadas). A ordem de verificação seguiu a influência de cada valor no resultado: cada valor foi variado ±20 % com os restantes fixos, e verificaram-se primeiro os que mudavam o vencedor.

Usaram-se três regras para manter os valores comparáveis:
- **Regra da forma:** quando uma propriedade depende da forma do produto (tubo, fita, fio, chapa), o mínimo e o máximo cobrem só a forma usada no dispositivo; os valores de outras formas ficam registados nas notas, mas não entram no cálculo. Quando a forma do dispositivo tem um único valor, aplica-se uma incerteza de ±10 %. Exceções: quando não havia ficha da forma do dispositivo, usou-se a forma mais próxima, com nota na base (típico do L605 da chapa; cedência do MP35N de fio recozido; WE43 de barra extrudida; PLLA genérico; Pt-Cr sem indicação de forma).
- **Regra da porosidade:** nos scaffolds, as propriedades mecânicas usam-se à porosidade típica do material (±10 pontos percentuais); o típico é a mediana das fontes dentro dessa janela.
- **Materiais permanentes num critério de reabsorção:** recebem o pior valor observado entre os reabsorvíveis do mesmo caso, como valor de modelação.

## 2.5 Normalização

Os critérios têm unidades diferentes (MPa, GPa, µm, escalas 1-5). Antes de os combinar, cada valor foi convertido numa nota adimensional entre 0 e 1. Nos critérios de benefício e de custo, a nota cresce com a proximidade ao melhor valor observado. Nos critérios-alvo, cresce com a proximidade ao valor-alvo, segundo a normalização de Petković et al. 2025 (eq. 2 no TOPSIS; o WASPAS usa as eqs. 9 a 13 e o VIKOR uma distância ao valor de referência, eqs. 17 e 18).

## 2.6 Pesos

Os pesos combinam duas fontes de informação:
- **Pesos subjetivos (w^S):** definidos pelo autor a partir da função de cada dispositivo descrita na literatura e no enunciado; não resultam de uma consulta formal a especialistas, pelo que os resultados dependem deste cenário de prioridades, com a justificação de cada peso indicada na tabela de critérios.
- **Pesos objetivos (w^O):** obtidos dos próprios dados pelo método do desvio-padrão. Um critério em que os materiais diferem mais recebe mais peso, porque distingue melhor as alternativas. Estes pesos medem a capacidade de cada critério distinguir os materiais da amostra, não a sua importância clínica, e por isso foram usados apenas como análise de sensibilidade. Com 4 a 5 materiais, os pesos objetivos são instáveis e aplicam-se também aos critérios ordinais e aos critérios-alvo (medem a dispersão dos valores, não a distância ao alvo).

Os dois combinam-se por w = η · w^S + (1 − η) · w^O. O resultado principal usa η = 1 (só pesos subjetivos). A sensibilidade a η foi analisada de 0 a 1, em passos de 0,1.

## 2.7 Métodos de decisão multicritério

Usaram-se três métodos que combinam os critérios de formas diferentes. Quando concordam, o resultado é mais sólido:
- **TOPSIS:** ordena os materiais pela proximidade relativa a uma solução ideal (o melhor valor em todos os critérios) e pelo afastamento a uma solução anti-ideal. O resultado é o coeficiente C, entre 0 e 1. Um ponto forte pode compensar um ponto fraco.
- **WASPAS:** combina a soma ponderada e o produto ponderado das notas normalizadas (λ = 0,5). A parte multiplicativa penaliza fortemente um critério com nota muito baixa, por isso o método favorece materiais equilibrados.
- **VIKOR:** procura a solução de compromisso. Combina o afastamento total à solução ideal (S) com o maior afastamento num único critério (R), através de um parâmetro v = 0,5. O índice final (P, na notação de Petković et al.) é tanto melhor quanto menor. As posições do VIKOR foram lidas como ordenação; a condição de vantagem aceitável (Anexo A.5) foi verificada à parte, para indicar quando o VIKOR não separa o 1.º dos seguintes (conjunto de compromisso; secção 5.3).

As equações de cada método seguem Petković et al. 2025 e são apresentadas em anexo.

## 2.8 Análise de robustez

O resultado foi testado em várias frentes:
- **Cenários de sensibilidade:** retirar os critérios ordinais (Q; não confundir com o índice Q do WASPAS); variar η de 0 a 1; alterar os valores-alvo (T); dar peso baixo ou elevado ao custo (C-custo); excluir na triagem os materiais com custo relativo acima de 3, sem mudar os pesos (teto de orçamento, O-orçamento); duplicar o peso dos critérios ligados ao problema crítico indicado pelo docente para cada dispositivo, com os restantes renormalizados (P-foco; não confundir com o índice P do VIKOR); no stent, variar o valor atribuído aos permanentes no tempo de reabsorção (R-sentinela).
- **Monte Carlo das propriedades:** 10 000 repetições (semente 42), com cada valor sorteado uniformemente entre o mínimo e o máximo da base. Os valores de uma única fonte, sem intervalo, variaram ±10 % à volta do típico. Como análise de sensibilidade, o Monte Carlo foi repetido com distribuições triangulares (mínimo, valor típico, máximo), com os mesmos vencedores, exceto no stent com o WASPAS: o L605 passa a ficar mais vezes em 1.º lugar (52,7 % das iterações, contra 46,8 % do Pt-Cr). A percentagem de iterações em 1.º lugar é uma frequência sob as hipóteses do modelo, não uma probabilidade de sucesso clínico. Com 10 000 iterações, o erro-padrão de simulação de cada percentagem é, no máximo, 0,5 pontos percentuais.
- **Monte Carlo dos pesos:** 10 000 repetições (semente 42); em cada uma, cada peso foi multiplicado por um fator sorteado uniformemente entre 0,8 e 1,2, de forma independente, e os pesos foram depois renormalizados para somar 1 (w'_j = w_j·u_j / Σ_k w_k·u_k, com u_j ~ U(0,8; 1,2)). As propriedades ficam nos valores típicos.
- **Concordância entre métodos:** coeficiente de correlação de Spearman entre as ordenações (secção 9.3). Com 4 a 8 materiais, o ρ é apenas descritivo: com 4 materiais, uma troca entre dois vizinhos já dá ρ = 0,8.
- **Consenso entre métodos:** calculou-se também um ranking de consenso pela contagem de Borda. Cada método atribui a cada material (m − posição) pontos, sendo m o número de materiais, e os materiais ordenam-se pela soma; em caso de empate, prevalece a posição no TOPSIS. O consenso é um resumo das posições, não uma validação: não acrescenta evidência; apresenta-se ao lado dos três métodos e não os substitui, porque a discordância entre eles é, ela própria, informação sobre a robustez do resultado.
- **Análises complementares (cenário A, valores típicos, η = 1):** (i) retirar uma alternativa de cada vez e ver se a ordem das restantes muda (reversão de ranking); (ii) dupla contagem: agrupar os critérios em dimensões (mecânica, biológica, clínica e económica; o mapa é uma escolha de desenho, em data/dimensoes_criterios.csv), fixar o peso total de cada dimensão e redistribuí-lo dentro dela, com pesos iguais e com 10 000 repartições ao acaso (distribuição de Dirichlet com α = 1, semente 42); (iii) o menor ajuste de um só peso (até ±100 %, com os outros renormalizados) e de um só valor típico (até ±50 %; nos ordinais, em passos inteiros) que troca o vencedor de cada método. A troca conta-se sempre de forma estrita; no TOPSIS indica-se também a variação a partir da qual o vencedor fica em empate (ΔC < 0,01).
- **Regra de empate:** duas posições consecutivas cujo C do TOPSIS difere menos de 0,01 consideram-se empatadas (valor de desenho, correspondente a 1 % da escala do coeficiente C). Neste relatório, "empate" usa-se só neste sentido; quando a diferença é maior, mas o 1.º lugar muda com o método ou com o cenário, diz-se que os materiais ficaram muito próximos.

## 2.9 Verificação da implementação

A implementação foi verificada reproduzindo os casos de estudo 1 e 2 de Petković et al. 2025 (capítulo 3); no caso 2 (prótese da anca), foram reproduzidos os 15 coeficientes C publicados e as posições correspondentes, com uma diferença máxima de cerca de 5 × 10⁻⁶.



## 2.10 Implementação e reprodutibilidade



## 2.11 Caracterização dos biomateriais

O enunciado pede as técnicas mais adequadas para caracterizar a densidade, a dureza, a flexibilidade, a absorção de água, a resistência mecânica, o comportamento térmico, a condutividade elétrica e a microestrutura, e eventualmente a composição por FTIR ou Raman. A Tabela [n] resume, para cada propriedade, a técnica, o princípio e onde se aplica neste trabalho. A questão 11 de cada caso (capítulos 4 a 7) indica o que se mede em cada material e mostra os valores das propriedades que entraram na comparação; os ensaios do dispositivo acabado, com as normas, estão na questão 10.

| Propriedade | Técnica | Princípio | Onde se aplica neste trabalho |
|----------------|------------------|------------------------------|--------------------------|
| Densidade e porosidade | Método de Arquimedes (pesagem a seco e imerso); picnometria de hélio; microtomografia (micro-CT) | O volume obtém-se pela impulsão num líquido de densidade conhecida (Arquimedes) ou pelo gás que o sólido desloca (picnometria); comparar o volume do sólido com o volume aparente dá a porosidade; a micro-CT reconstrói a peça em 3D e dá também o tamanho e a interligação dos poros | Densidade das ligas (massa da haste, secção 8.5); porosidade dos scaffolds (critério com alvo de 70 %) e de uma haste porosa |
| Dureza | Vickers e Knoop (microdureza); nanoindentação; Shore D nos polímeros | Mede-se a impressão deixada por um indentador de diamante sob uma carga conhecida (Vickers, Knoop) ou a curva força-penetração (nanoindentação, que dá também o módulo local); a Shore D mede a penetração de um indentador com mola | Cabeças do par articular (critério de dureza da cabeça); ligas da haste e do implante dentário; revestimentos e camadas finas (nanoindentação) |
| Resistência mecânica | Ensaios de tração e de compressão; ensaios de fadiga | A curva tensão-deformação dá o módulo de Young, a tensão de cedência, a resistência e o alongamento na rotura; a fadiga conta os ciclos até à rotura a cada nível de tensão | Haste (cedência e fadiga); stent (σy/E, tração e alongamento do tubo); scaffold (compressão à porosidade de projeto) |
| Flexibilidade | Flexão em 3 ou 4 pontos; análise mecânica dinâmica (DMA) | A flexão dá o módulo e a resistência à flexão, o ensaio habitual nas cerâmicas frágeis; a DMA aplica uma deformação oscilante e separa a resposta elástica da viscosa, em função da temperatura ou da frequência | Zircónia e ZTA (resistência à flexão); polímeros (PEEK, PCL, PLLA, polietileno) |
| Absorção de água | Gravimetria: massa antes e depois de imersão em água ou em solução fisiológica a 37 °C | O ganho de massa mede a água absorvida; ao longo do tempo, a perda de massa seca mede a degradação | Poliésteres reabsorvíveis do scaffold e do stent (PLLA, PLGA, PCL), que se degradam por hidrólise; PEEK (na zircónia, o efeito da humidade avalia-se pela fração monoclínica, ver Composição e fases) |
| Comportamento térmico | Calorimetria diferencial de varrimento (DSC); termogravimetria (TGA); dilatometria | A DSC mede o calor trocado nas transições (transição vítrea, fusão, cristalização) e dá a cristalinidade; a TGA mede a perda de massa com a temperatura; a dilatometria mede a expansão térmica | Cristalinidade do polietileno e dos poliésteres; teor de cerâmica no compósito PCL/β-TCP; compatibilidade com a esterilização por calor (o PCL funde a cerca de 60 °C) |
| Condutividade elétrica | Método das quatro pontas; espectroscopia de impedância eletroquímica (EIS) | Nas quatro pontas, dois contactos injetam corrente e outros dois medem a queda de tensão, sem o erro da resistência dos contactos; a EIS não mede a condutividade do material: avalia, num eletrólito, a resistência do filme passivo, ligada à corrosão | Ligas metálicas: aquecimento por correntes induzidas em ressonância magnética e corrosão galvânica entre metais diferentes (junção cabeça-cone); estabilidade do filme passivo |
| Microestrutura e superfície | Microscopia ótica; microscopia eletrónica de varrimento (SEM) com espectroscopia de raios X (EDS); microscopia de força atómica (AFM) | Imagem da microestrutura, da superfície e de defeitos; o EDS dá a composição elementar local; o AFM mede a rugosidade à escala nanométrica | Fases das ligas de titânio; fissuras nos struts depois da expansão; poros dos scaffolds; rugosidade dos implantes dentários |
| Composição e fases | Espectroscopia de infravermelho (FTIR) e Raman; difração de raios X (XRD) | O FTIR e o Raman identificam as ligações químicas pela absorção (FTIR) ou pela dispersão (Raman) da luz; o XRD identifica as fases cristalinas | FTIR: oxidação do polietileno reticulado; Raman e XRD: fração de fase monoclínica da zircónia e distinção entre hidroxiapatite e β-TCP |
| Composição química das ligas e libertação de iões | Espectrometria de emissão ótica por faísca ou fluorescência de raios X (XRF); ICP-OES ou ICP-MS depois de dissolução ou de imersão | A emissão ótica e a XRF dão a composição global da liga pelos comprimentos de onda caraterísticos de cada elemento; o ICP-OES e o ICP-MS medem a concentração de cada elemento numa solução (a liga dissolvida ou o meio de imersão) | Teor de níquel das ligas do stent (perfil de alergia, secção 8.2); iões de Co, Cr e Ti libertados (secção 8.5) |

Table: Técnicas de caracterização dos biomateriais: propriedade, técnica, princípio e aplicação neste trabalho.
