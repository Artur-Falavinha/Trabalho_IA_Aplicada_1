# É morcego?

Trabalho de reconhecimento de padrões da disciplina DS803 da UFPR. O objetivo é identificar os morcegos em uma lista de **8.426 organismos**, a partir das 50 características fornecidas para cada linha. [Enunciado do trabalho](https://drive.google.com/file/d/1rgFNyVS6eeG3GUL6dRMKwjYgZm-r98P2/view)

Começamos com 29 exemplos conhecidos. Em quatro rodadas, uma SVM indicou 73 linhas para conferência. Dessas, 67 eram morcegos. Somadas aos 12 morcegos iniciais, completaram os **79 registros positivos**.

[Resolução passo a passo](docs/resolucao.md) · [Relatório](relatorio_morcegos.pdf) · [Slides em PDF](output/pdf/slides_morcegos.pdf) · [Roteiro de apresentação](output/pdf/roteiro_apresentacao_morcegos.pdf)

## Como executar

**Na hora da apresentação**, abra a pasta do projeto no Explorador de Arquivos do Windows e dê dois cliques em **`apresentar.cmd`**. A janela mostra a pesquisa inicial, as quatro rodadas e as três métricas. Ela fica aberta até você pressionar uma tecla.

Para mostrar a execução diretamente no PowerShell, use `.\.venv\Scripts\python.exe classificar_morcegos.py`.

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

Rode `apresentar.cmd` uma vez para ensaiar. A partir daí, a demonstração funciona sem internet, com os dados e a [tabela de rótulos](dados/rotulos.csv) da própria pasta. Se mudar o projeto de pasta ou de computador, refaça o preparo no destino.

## O que o programa entrega

| Arquivo | Conteúdo |
| --- | --- |
| [Classificação](resultados/classificacao.csv) | Uma linha por organismo com índice, nome, classe e etapa da busca. A classe 1 indica morcego e a classe 0 indica outro organismo. |
| [Índices dos morcegos](resultados/indices_morcegos.txt) | Os 79 números de linha positivos, na ordem dos arquivos do professor. A primeira linha tem índice 1. |

O programa imprime as contagens de cada rodada e as três métricas da avaliação final. Em cinco partes de validação, a SVM encontrou os 79 morcegos e indicou um outro organismo por engano: **100,00% de sensibilidade, 98,75% de precisão e 99,99% de acurácia**.
