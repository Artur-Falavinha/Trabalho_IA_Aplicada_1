# Como identificamos os morcegos

## 1. Ligar o nome às 50 características

A linha 2291 de [Names.txt](../Names.txt) contém `Desmodus_rotundus`, o morcego-vampiro. Na mesma linha de [wpc50.dat](../wpc50.dat) estão os 50 números que o professor forneceu para esse organismo. A posição liga os dois arquivos. Usamos o nome para conferir a classe e os números para o modelo aprender.

## 2. Começar com exemplos das duas classes

Um rótulo é a resposta conhecida para um exemplo. Atribuímos **1** aos morcegos, que pertencem à ordem *Chiroptera*, e **0** aos demais organismos. A [tabela de rótulos](../dados/rotulos.csv) registra o nome, a classe e a fonte taxonômica usada. Ela já está preparada para o experimento. Nas rodadas, o programa consulta a classe dos exemplos iniciais e de cada candidato depois de escolhê-lo.

Começamos com **12 morcegos e 17 outros organismos**. Entre eles estão *Desmodus rotundus* (classe 1) e o gato *Felis catus* (classe 0). Há outros mamíferos entre os negativos para que o treino inclua exemplos que compartilham características com os morcegos.

## 3. Procurar novos morcegos em rodadas

Usamos um único classificador, a **SVM**. Ele aprende uma fronteira entre as duas classes. O kernel RBF permite que a fronteira seja curva. Antes do treino, colocamos as características em escalas comparáveis. Os pesos das classes levam em conta a quantidade de exemplos de cada uma.

1. Treinamos a SVM com as linhas que já têm classe conhecida.
2. Aplicamos o modelo às linhas restantes. Uma pontuação acima de zero indica um possível morcego. Escolhemos até 20 candidatos por vez, começando pelas maiores pontuações.
3. Conferimos as classes desses candidatos na tabela de rótulos. Todos entram no treino seguinte, inclusive os que o modelo indicou por engano.
4. Repetimos até a SVM deixar de indicar novas linhas. As linhas que ficaram sem indicação recebem classe 0.

Na primeira rodada, a SVM indicou a linha **3942**, de *Lasiurus borealis*. A referência confirmou que era morcego. Já a linha **2649**, de *Eremitalpa granti*, foi indicada na quarta rodada e recebeu classe 0 após a consulta.

| Etapa | Linhas consultadas na etapa | Morcegos na etapa | Total de morcegos |
| --- | ---: | ---: | ---: |
| Pesquisa inicial | 29 | 12 | 12 |
| Rodada 1 | 20 | 20 | 32 |
| Rodada 2 | 20 | 20 | 52 |
| Rodada 3 | 20 | 20 | 72 |
| Rodada 4 | 13 | 7 | 79 |

Ao todo, consultamos **102 linhas durante a busca**. Após o último treino, a SVM deixou de indicar candidatos entre as 8.324 restantes. Esse foi o critério de parada. Para verificar se algum morcego tinha ficado de fora, comparamos a lista pronta com os rótulos de referência. As 8.426 classes coincidiram.

## 4. Medir o desempenho depois de fechar a lista

Para descobrir com que frequência a SVM acerta uma linha que ficou fora do seu treino, dividimos a base rotulada em **cinco partes**, mantendo proporções semelhantes de morcegos. Treinamos em quatro partes e testamos na outra. Repetimos até que cada parte tivesse sido usada para teste uma vez. Em cada treino, o ajuste de escala usou apenas as quatro partes disponíveis para aprender.

| Métrica | Pergunta | Resultado |
| --- | --- | ---: |
| Sensibilidade | Dos 79 morcegos, quantos a SVM encontrou? | 79 de 79 = 100,00% |
| Precisão | Das 80 indicações de morcego, quantas estavam certas? | 79 de 80 = 98,75% |
| Acurácia | De todas as 8.426 previsões, quantas estavam certas? | 8.425 de 8.426 = 99,99% |

O único erro da validação foi marcar *Scapanulus oweni* (linha 7013) como morcego. A lista entregue contém a classe correta desse organismo. Isso é possível porque a lista registra o resultado da busca com conferência dos candidatos, enquanto as métricas contam as previsões da SVM antes de qualquer correção. Os resultados descrevem o desempenho em linhas da base da disciplina.

## 5. Localizar o resultado

A [classificação completa](../resultados/classificacao.csv) traz a classe de cada linha e permite ver se ela estava na amostra inicial, em qual rodada foi conferida ou se ficou sem indicação. A [lista dos índices positivos](../resultados/indices_morcegos.txt) reúne os **79 morcegos** na ordem original. Para reproduzir a solução, siga as [instruções do README](../README.md#como-executar).
