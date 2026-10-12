# Teste da aplicação: questionário curto

Objetivo: saber se a aplicação (versão web, https://andremassuca.github.io/biomaterial-ideal/, ou nativa) se
percebe, serve para alguma coisa, inspira a confiança certa e é fácil de usar. Participantes: 3 colegas (C1, C2, C3) e
1 clínico (K1). Duração prevista: 10 minutos de uso livre e 3 minutos de questionário.

Não se registam nomes nem dados pessoais: cada participante é identificado só pelo código (C1, C2, C3, K1). Diga a
cada participante, antes de começar, que a aplicação não é uma ferramenta clínica nem uma recomendação terapêutica.

## Guião (o que pedir ao participante)

1. Abrir a aplicação e escolher um caso (por exemplo, o stent).
2. Ver o resultado e mudar uma prioridade ou um perfil de doente.
3. Correr o Monte Carlo e ler a percentagem em 1.º lugar.
4. Responder às 5 perguntas.

## As 5 perguntas

Escala de 1 a 5 (1 = nada; 5 = totalmente) nas perguntas 1 a 4, com um comentário opcional; a 5 é aberta.

| N.º | Tema | Pergunta |
|---|---|---|
| 1 | Compreensão | Percebeu o que a aplicação compara e o que quer dizer um material ficar em 1.º lugar? |
| 2 | Utilidade | A aplicação ajudou-o a perceber como as prioridades e a incerteza dos dados mudam a escolha do material? |
| 3 | Confiança | Sabendo que não é uma ferramenta clínica, quanto confia nos resultados que a aplicação mostra? |
| 4 | Facilidade | Foi fácil encontrar o que procurava e usar os controlos (caso, prioridades, perfil do doente, Monte Carlo)? |
| 5 | Sugestão | Se pudesse mudar uma coisa na aplicação, qual seria? |

No clínico (K1), o comentário da pergunta 3 é o mais importante: perguntar o que faltaria para a informação lhe ser útil
numa discussão (não numa decisão clínica).

## Como registar as respostas

Opção A (recomendada): abrir `formulario.html` num navegador (duplo clique; funciona sem internet). Preencher uma
resposta por participante e carregar em "Guardar resposta". No fim, carregar em "Descarregar CSV". Nada é enviado
para lado nenhum: as respostas ficam só na página (e no armazenamento local do navegador, se estiver disponível) até
serem descarregadas. Para apagar tudo, "Limpar tudo".

Opção B: copiar `respostas_modelo.csv` e preencher uma linha por participante numa folha de cálculo (separador ponto e
vírgula, UTF-8).

O CSV tem as colunas: participante, perfil, data, versao, dispositivo, duracao_min, p1_compreensao, p1_comentario,
p2_utilidade, p2_comentario, p3_confianca, p3_comentario, p4_facilidade, p4_comentario, p5_sugestao.

## Depois

Guardar o CSV descarregado em `docs/teste_app/respostas.csv` só se os participantes concordarem e sem dados pessoais
(nos comentários, retirar nomes). Resumir: média e intervalo de cada pergunta (com 4 participantes não há estatística,
só indicação) e as sugestões agrupadas por tema.
