# É morcego?

Trabalho de reconhecimento de padrões da disciplina DS803 da UFPR. O objetivo é identificar os morcegos em uma lista de **8.426 organismos**, a partir das 50 características fornecidas para cada linha. [Enunciado do trabalho](https://drive.google.com/file/d/1rgFNyVS6eeG3GUL6dRMKwjYgZm-r98P2/view)

Começamos com 29 exemplos conhecidos. Em quatro rodadas, uma SVM indicou 73 linhas para conferência. Dessas, 67 eram morcegos. Somadas aos 12 morcegos iniciais, completaram os **79 registros positivos**.

[Resolução passo a passo](docs/resolucao.md) · [Relatório](relatorio_morcegos.pdf) · [Slides em PDF](output/pdf/slides_morcegos.pdf) · [Roteiro de apresentação](output/pdf/roteiro_apresentacao_morcegos.pdf)

## Como executar

**Para apresentar em aula**, abra o PowerShell na pasta do projeto, com o [ambiente já preparado](#antes-da-apresentação), e execute o comando abaixo.

```powershell
.\.venv\Scripts\python.exe .\classificar_morcegos.py --apresentar
```

Pressione **Enter** em cada pausa para avançar pelas etapas.

1. **Entradas e exemplos conhecidos.** Na linha 2291, `Names.txt` traz `Desmodus_rotundus` e `wpc50.dat` traz 50 medidas do mesmo organismo. As três primeiras são aproximadamente −1,8551, −0,1310 e −1,1553. O treino começa com 12 morcegos e 17 outros organismos.
2. **Busca em quatro rodadas.** Primeiro aparecem as pontuações da SVM. Na primeira rodada, a linha 3942, de *Lasiurus borealis*, tem pontuação de aproximadamente +1,235. A SVM escolhe até 20 linhas com pontuação positiva, das maiores para as menores. Avance para conferir os rótulos dos candidatos e ver quantos morcegos entram no treino seguinte.
3. **Validação em cinco partes.** Em cada teste, a SVM treina em quatro partes e prevê a classe das linhas da quinta. Ao final, as previsões das cinco partes dão a sensibilidade, a precisão e a acurácia.

**Para uma execução rápida**, rode `.\.venv\Scripts\python.exe .\classificar_morcegos.py` no PowerShell ou dê dois cliques em `apresentar.cmd` no Explorador de Arquivos. As duas opções percorrem as rodadas automaticamente.

Se o professor pedir para ver a entrega, abra `resultados\indices_morcegos.txt` para mostrar os 79 índices ou `resultados\classificacao.csv` para mostrar o nome, a classe e a etapa de cada uma das 8.426 linhas.

### Antes da apresentação

Faça o preparo uma vez **no computador que será usado**, com internet. Se baixou o projeto como ZIP, extraia a pasta inteira primeiro. Com Python 3.14 instalado, abra o PowerShell na pasta que contém `apresentar.cmd` e execute:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Se já usa `uv`, o preparo equivalente é:

```powershell
uv venv --python 3.14 .venv
uv pip install --python .venv\Scripts\python.exe -r requirements.txt
```

Depois da instalação, ensaie com `--apresentar`. A demonstração funciona sem internet, com os dados e a [tabela de rótulos](dados/rotulos.csv) da própria pasta. Se mudar o projeto de pasta ou de computador, refaça o preparo no destino.

## O que o programa entrega

| Arquivo | Conteúdo |
| --- | --- |
| [Classificação](resultados/classificacao.csv) | Uma linha por organismo com índice, nome, classe e etapa da busca. A classe 1 indica morcego e a classe 0 indica outro organismo. |
| [Índices dos morcegos](resultados/indices_morcegos.txt) | Os 79 números de linha positivos, na ordem dos arquivos do professor. A primeira linha tem índice 1. |

O programa imprime as contagens de cada rodada e as três métricas da avaliação final. Em cinco partes de validação, a SVM encontrou os 79 morcegos e indicou um outro organismo por engano: **100,00% de sensibilidade, 98,75% de precisão e 99,99% de acurácia**.
