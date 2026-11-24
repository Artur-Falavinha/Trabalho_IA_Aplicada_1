# É morcego?

Trabalho de reconhecimento de padrões da disciplina DS803 da UFPR. O objetivo é identificar os morcegos em uma lista de **8.426 organismos**, a partir das 50 características fornecidas para cada linha. [Enunciado do trabalho](https://drive.google.com/file/d/1rgFNyVS6eeG3GUL6dRMKwjYgZm-r98P2/view)

Começamos com 29 exemplos conhecidos. Em quatro rodadas, uma SVM indicou 73 linhas para conferência. Dessas, 67 eram morcegos. Somadas aos 12 morcegos iniciais, completaram os **79 registros positivos**.

[Resolução passo a passo](docs/resolucao.md) · [Relatório](relatorio_morcegos.pdf) · [Slides em PDF](output/pdf/slides_morcegos.pdf) · [Roteiro de apresentação](output/pdf/roteiro_apresentacao_morcegos.pdf)

## Como executar

Com Python 3.14, abra o PowerShell na pasta do projeto e execute:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe classificar_morcegos.py
```

Se usar `uv`, o comando equivalente é `uv run --python 3.14 --with-requirements requirements.txt python classificar_morcegos.py`. A execução usa os arquivos do professor e uma [tabela local de rótulos e fontes](dados/rotulos.csv). Após instalar as dependências, funciona sem internet.

## O que o programa entrega

| Arquivo | Conteúdo |
| --- | --- |
| [Classificação](resultados/classificacao.csv) | Uma linha por organismo com índice, nome, classe e etapa da busca. A classe 1 indica morcego e a classe 0 indica outro organismo. |
| [Índices dos morcegos](resultados/indices_morcegos.txt) | Os 79 números de linha positivos, na ordem dos arquivos do professor. A primeira linha tem índice 1. |

O programa imprime as contagens de cada rodada e as três métricas da avaliação final. Em cinco partes de validação, a SVM encontrou os 79 morcegos e indicou um outro organismo por engano: **100,00% de sensibilidade, 98,75% de precisão e 99,99% de acurácia**.
