# É morcego?

Trabalho de reconhecimento de padrões da disciplina DS803, UFPR. A classe `1` representa morcegos (ordem Chiroptera) e a classe `0` representa os demais organismos. O índice começa em 1 e corresponde à linha nos dois arquivos do professor.

[Enunciado do trabalho no Drive da disciplina](https://drive.google.com/file/d/1rgFNyVS6eeG3GUL6dRMKwjYgZm-r98P2/view).

[Leia a resolução passo a passo](docs/resolucao.md) para entender como os dados foram rotulados, como as rodadas encontraram candidatos e o que significam as métricas.

## Executar

Com Python 3.14, abra o PowerShell nesta pasta e rode:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe classificar_morcegos.py
```

Se você usa `uv`, execute `uv run --python 3.14 --with-requirements requirements.txt python classificar_morcegos.py`. A referência taxonômica já está em `dados/`. Após instalar as dependências, o experimento pode ser executado sem internet.

## Como explicar o código

1. `ler_dados` confere o alinhamento por linha entre os nomes, as 50 características e a tabela de referência.
2. `prospectar` começa com exemplos pesquisados. Em cada rodada, `priorizar_candidatos` escolhe 12 vizinhos de morcegos conhecidos, 12 pontos perto da fronteira da SVM e 6 exemplos ao acaso. A base de treino cresce com os rótulos desses 30 candidatos confirmados na referência.
3. `avaliar_rodadas` mede a SVM em uma partição reservada. A referência completa permite estratificar a divisão, mas a função de seleção usa os rótulos somente das linhas já confirmadas.
4. `avaliar_base_final` compara SVM e k-NN em cinco partes sobre o conjunto supervisionado. Cada previsão foi gerada por um modelo que treinou nas outras quatro partes. Registros com o mesmo TaxID de espécie ficam juntos quando disponível. O código usa o TaxID encontrado como alternativa nos demais casos.
5. `exportar_classificacao` grava as classes confirmadas na ordem original. `exportar_pca` gera uma visão em duas dimensões para o relatório.

## Arquivos da entrega

| Arquivo | Conteúdo |
|---|---|
| `resultados/classificacao.csv` | Classe das 8.426 linhas na ordem original |
| `resultados/indices_morcegos.txt` | Índices dos 79 morcegos, um por linha |
| `resultados/candidatos.csv` | Exemplos iniciais e candidatos confirmados por rodada e critério |
| `resultados/rodadas.csv` | Evolução da base e desempenho na partição reservada |
| `resultados/metricas.csv` | Matriz de confusão e métricas agregadas por modelo |
| `resultados/previsoes_validacao.csv` | Partição, classe e previsões de SVM e k-NN para cada linha |
| `dados/referencia_taxonomica.csv` | Nome original, rótulo, TaxID, método e fonte de cada confirmação |
| `relatorio_morcegos.pdf` | Relatório com método, resultados, referências e campo de autoria editável |

## Reconstruir a referência taxonômica

Esta etapa é opcional. `preparar_referencia.py` usa `names.dmp` e `nodes.dmp` do [taxdump público do NCBI](https://ftp.ncbi.nlm.nih.gov/pub/taxonomy/taxdump.tar.gz). O cruzamento normaliza maiúsculas e separadores, busca o nome completo e, quando necessário, um prefixo taxonômico. A tabela `dados/nomes_revisados.csv` registra os casos revisados com fonte específica.

```powershell
python preparar_referencia.py caminho\para\taxdump.tar.gz
```

A referência entregue corresponde à cópia de 24 de novembro de 2026. O SHA-256 do arquivo consultado é `8cb819bc271aebd6c5a7c56ccc23f296d3283369d7049dab5849de373f502eb5`. Versões futuras do NCBI podem trocar nomes e TaxIDs. Para reproduzir os números do relatório, use o CSV de referência incluído.
