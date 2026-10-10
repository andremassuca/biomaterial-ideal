# 2. Métodos

## 2.1 Visão geral

Para cada caso clínico seguiu-se o mesmo processo, em sete passos:
1. definição da função do dispositivo e do problema do material atual;
2. escolha dos materiais candidatos;
3. triagem por critérios eliminatórios;
4. definição dos critérios de comparação e dos respetivos pesos;
5. normalização dos valores e ordenação dos materiais por três métodos de decisão multicritério;
6. análise da robustez do resultado;
7. validação da implementação contra um estudo publicado.

Três casos (haste femoral, stent coronário expansível por balão e scaffold para regeneração óssea) foram tratados quantitativamente. Os outros dois componentes (par articular da anca e implante dentário) foram tratados de forma semiquantitativa, porque a maior parte do peso dos seus critérios cabia a escalas ordinais (60 % do peso no par articular e 70 % no implante dentário; a regra do trabalho é não passar de 50 % nos casos quantitativos, que têm 30 a 45 %). Nestes, o ranking é calculado da mesma forma, mas é apresentado como indicação: é numérico no sentido computacional e semiquantitativo na interpretação, porque depende sobretudo de escalas ordinais.

Neste relatório, chama-se quantitativo a um caso em que a maior parte do peso cabe a propriedades físicas medidas, com unidades, e semiquantitativo a um caso em que a maior parte do peso cabe a escalas ordinais.

## 2.2 Materiais candidatos e cenários

Para cada caso, os candidatos incluem os materiais em uso clínico e alternativas em investigação. Para não misturar materiais com graus de evidência muito diferentes, os resultados foram obtidos em dois cenários:
- **Cenário A:** só materiais em uso clínico.
- **Cenário B:** inclui também materiais em investigação (e, no stent, os bioabsorvíveis).

## 2.3 Critérios

Cada critério pertence a um de quatro tipos:
- **Estrito (eliminatório):** o material passa ou não passa (por exemplo, a biocompatibilidade, ou o tipo de expansão do stent). Na biocompatibilidade, foram considerados candidatos com historial de uso clínico ou evidência publicada de biocompatibilidade; não foram feitos ensaios ISO 10993 neste trabalho. Os materiais eliminados ficam registados, com o motivo.
- **Benefício:** quanto maior, melhor (por exemplo, o limite de fadiga).
- **Custo:** quanto menor, melhor (por exemplo, a densidade ou o custo relativo).
- **Alvo:** o melhor valor é um valor intermédio. É o caso do módulo de Young da haste, que deve aproximar-se do osso cortical para reduzir o stress shielding. Seguiu-se a abordagem de critérios-alvo de Petković et al. 2025. O módulo de Young foi usado como aproximação de primeira ordem da compatibilidade de rigidez entre o implante e o osso. Não substitui uma análise estrutural: a rigidez efetiva de uma haste depende também da geometria, da porosidade e da fixação, e o stress shielding não foi calculado diretamente.

Usaram-se também dois índices derivados:
- σy/E, como indicador do recuo elástico do stent;
- E_implante/E_osso, como medida do desajuste de rigidez da haste.

Alguns critérios não têm uma grandeza física simples (resistência à corrosão, compatibilidade com ressonância magnética, fabricabilidade, custo relativo). Para estes usaram-se escalas ordinais de 1 a 5, com uma rubrica escrita para cada nível, apoiada em literatura. As rubricas de cada escala estão no Anexo C. A compatibilidade com ressonância magnética depende do dispositivo completo e não só do material; a nota usada aproxima-a pelo material predominante.

## 2.4 Base de dados e verificação dos valores

Todos os valores estão numa base de dados única (ficheiros CSV). Cada valor tem um mínimo, um máximo, um valor típico, a fonte e um estado de verificação: "Verificado", "Verificado (fornecedor)", "Verificado (derivado)", "Verificado (composição química)", "Verificado (composição nominal)" ou "A verificar".

Os valores de partida vieram de revisões. Os valores com mais influência no resultado foram verificados em fontes primárias (normas, artigos com ensaio, fichas técnicas de fabricantes e de fornecedores); os restantes ficam marcados "A verificar" (@@N_VERIFICADOS@@ das @@N_TOTAL@@ linhas da base estão verificadas). A ordem de verificação seguiu a influência de cada valor no resultado: cada valor foi variado ±20 % com os restantes fixos, e verificaram-se primeiro os que mudavam o vencedor.

Usaram-se três regras para manter os valores comparáveis:
- **Regra da forma:** quando uma propriedade depende da forma do produto (tubo, fita, fio, chapa), o mínimo e o máximo cobrem só a forma usada no dispositivo; os valores de outras formas ficam registados nas notas, mas não entram no cálculo. Quando a forma do dispositivo tem um único valor, aplica-se uma incerteza de ±10 %.
- **Regra da porosidade:** nos scaffolds, as propriedades mecânicas usam-se à porosidade típica do material (±10 pontos percentuais); o típico é a mediana das fontes dentro dessa janela.
- **Materiais permanentes num critério de reabsorção:** recebem o pior valor observado entre os reabsorvíveis do mesmo caso, como valor de modelação.

## 2.5 Normalização

Os critérios têm unidades diferentes (MPa, GPa, µm, escalas 1-5). Antes de os combinar, cada valor foi convertido numa nota adimensional entre 0 e 1. Nos critérios de benefício e de custo, a nota cresce com a proximidade ao melhor valor observado. Nos critérios-alvo, cresce com a proximidade ao valor-alvo, segundo a normalização de Petković et al. 2025 (eq. 2 no TOPSIS; o WASPAS usa as eqs. 9 a 13 e o VIKOR uma distância ao valor de referência, eqs. 17 e 18).

## 2.6 Pesos

Os pesos combinam duas fontes de informação:
- **Pesos subjetivos (w^S):** definidos pelo autor a partir da função de cada dispositivo descrita na literatura e no enunciado; não resultam de uma consulta formal a especialistas, pelo que os resultados dependem deste cenário de prioridades, com a justificação de cada peso indicada na tabela de critérios.
- **Pesos objetivos (w^O):** obtidos dos próprios dados pelo método do desvio-padrão. Um critério em que os materiais diferem mais recebe mais peso, porque distingue melhor as alternativas. Estes pesos medem a capacidade de cada critério distinguir os materiais da amostra, não a sua importância clínica, e por isso foram usados apenas como análise de sensibilidade.

Os dois combinam-se por w = η · w^S + (1 − η) · w^O. O resultado principal usa η = 1 (só pesos subjetivos). A sensibilidade a η foi analisada de 0 a 1, em passos de 0,1.

## 2.7 Métodos de decisão multicritério

Usaram-se três métodos que combinam os critérios de formas diferentes. Quando concordam, o resultado é mais sólido:
- **TOPSIS:** ordena os materiais pela proximidade relativa a uma solução ideal (o melhor valor em todos os critérios) e pelo afastamento a uma solução anti-ideal. O resultado é o coeficiente C, entre 0 e 1. Um ponto forte pode compensar um ponto fraco.
- **WASPAS:** combina a soma ponderada e o produto ponderado das notas normalizadas (λ = 0,5). A parte multiplicativa penaliza fortemente um critério com nota muito baixa, por isso o método favorece materiais equilibrados.
- **VIKOR:** procura a solução de compromisso. Combina o afastamento total à solução ideal (S) com o maior afastamento num único critério (R), através de um parâmetro v = 0,5. O índice final (P, na notação de Petković et al.) é tanto melhor quanto menor. As posições do VIKOR foram lidas como ordenação; a condição de vantagem aceitável (Anexo A.5) não foi usada para declarar conjuntos de compromisso.

As equações de cada método seguem Petković et al. 2025 e são apresentadas em anexo.

## 2.8 Análise de robustez

O resultado foi testado em várias frentes:
- **Cenários de sensibilidade:** retirar os critérios ordinais (Q); variar η de 0 a 1; alterar os valores-alvo (T); dar peso baixo ou elevado ao custo (C-custo); excluir na triagem os materiais com custo relativo acima de 3, sem mudar os pesos (teto de orçamento, O-orçamento); duplicar o peso dos critérios ligados ao problema crítico indicado pelo docente para cada dispositivo, com os restantes renormalizados (P-foco); no stent, variar o valor atribuído aos permanentes no tempo de reabsorção (R-sentinela).
- **Monte Carlo das propriedades:** 10 000 repetições (semente 42), com cada valor sorteado uniformemente entre o mínimo e o máximo da base. Os valores de uma única fonte, sem intervalo, variaram ±10 % à volta do típico. Como análise de sensibilidade, o Monte Carlo foi repetido com distribuições triangulares (mínimo, valor típico, máximo), com os mesmos vencedores, exceto no stent com o WASPAS: o L605 passa a ficar mais vezes em 1.º lugar (52,7 % das iterações, contra 46,8 % do Pt-Cr). A percentagem de iterações em 1.º lugar é uma frequência sob as hipóteses do modelo, não uma probabilidade de sucesso clínico.
- **Monte Carlo dos pesos:** 10 000 repetições (semente 42); em cada uma, cada peso foi multiplicado por um fator sorteado uniformemente entre 0,8 e 1,2, de forma independente, e os pesos foram depois renormalizados para somar 1 (w'_j = w_j·u_j / Σ_k w_k·u_k, com u_j ~ U(0,8; 1,2)). As propriedades ficam nos valores típicos.
- **Concordância entre métodos:** coeficiente de correlação de Spearman entre as ordenações.
- **Consenso entre métodos:** calculou-se também um ranking de consenso pela contagem de Borda. Cada método atribui a cada material (m − posição) pontos, sendo m o número de materiais, e os materiais ordenam-se pela soma; em caso de empate, prevalece a posição no TOPSIS. O consenso apresenta-se ao lado dos três métodos e não os substitui, porque a discordância entre eles é, ela própria, informação sobre a robustez do resultado.
- **Regra de empate:** duas posições consecutivas cujo C do TOPSIS difere menos de 0,01 consideram-se empatadas (valor de desenho, correspondente a 1 % da escala do coeficiente C).

## 2.9 Validação da implementação

A implementação foi validada reproduzindo o caso de estudo da prótese da anca de Petković et al. 2025. Foram reproduzidos os 15 coeficientes C publicados e as posições correspondentes, com uma diferença máxima de cerca de 5 × 10⁻⁶.



## 2.10 Implementação e reprodutibilidade

