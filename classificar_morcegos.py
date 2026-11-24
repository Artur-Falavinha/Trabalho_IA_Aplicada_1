"""Identifica morcegos por rodadas de supervisão e avalia a SVM na base classificada."""

import argparse
import csv
import sys
from pathlib import Path

import numpy as np
from sklearn.metrics import confusion_matrix
from sklearn.model_selection import StratifiedKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC

PASTA = Path(__file__).resolve().parent
# Com até 20 consultas por rodada, a SVM pode aprender com esse lote antes de escolher o próximo.
TAMANHO_LOTE = 20
# Há outros mamíferos entre os exemplos iniciais: ser mamífero, por si só, não identifica um morcego.
NOMES_INICIAIS = """
    Artibeus_jamaicensis Desmodus_rotundus Myotis_lucifugus Pteropus_vampyrus
    Rhinolophus_monoceros Rousettus_aegyptiacus Tadarida_teniotis Pteronotus_parnellii
    Pipistrellus_abramus Myotis_myotis Artibeus_lituratus Pteropus_alecto
    Homo_sapiens Bos_taurus Equus_caballus Mus_musculus Oryctolagus_cuniculus
    Felis_catus Canis_lupus Sus_scrofa Talpa_europaea Erinaceus_europaeus Sorex_araneus
    Manis_javanica Gallus_gallus Danio_rerio Drosophila_melanogaster Arabidopsis_thaliana
    Saccharomyces_cerevisiae
""".split()


def ler_dados():
    # O número da linha liga o nome às 50 medidas e depois vira o índice.
    # Se a ordem mudar em um dos arquivos, podemos atribuir as medidas de um animal a outro.
    nomes = (PASTA / "Names.txt").read_text(encoding="utf-8").splitlines()
    nomes = [nome.strip() for nome in nomes]
    atributos = np.loadtxt(PASTA / "wpc50.dat")
    if len(nomes) != 8426 or atributos.shape != (len(nomes), 50) or not np.isfinite(atributos).all():
        raise ValueError("A base deve ter 8.426 nomes e 50 valores finitos por linha.")

    with (PASTA / "dados" / "rotulos.csv").open(encoding="utf-8", newline="") as arquivo:
        referencia = list(csv.DictReader(arquivo))
    if [linha["nome"] for linha in referencia] != nomes:
        raise ValueError("Os nomes da referência devem seguir a mesma ordem de Names.txt.")
    # A fonte de cada rótulo permite justificar por que aquela linha recebeu a classe 0 ou 1.
    if any(linha["classe"] not in {"0", "1"} or not linha["fonte"] for linha in referencia):
        raise ValueError("Cada organismo precisa de classe 0 ou 1 e fonte para a consulta.")
    return nomes, atributos, np.array([int(linha["classe"]) for linha in referencia])


def criar_svm():
    # A escala importa porque uma medida com valores altos pode dominar a comparação.
    # O núcleo RBF permite uma fronteira curva. Os pesos dão mais importância aos erros na classe mais rara.
    return make_pipeline(StandardScaler(), SVC(kernel="rbf", class_weight="balanced"))


def avancar(acao):
    input(f"\n[Enter] {acao} ")


def mostrar_dados(nomes, atributos):
    print("\nBASE DE ORGANISMOS")
    print(f"{len(nomes)} linhas, cada uma com {atributos.shape[1]} características.")
    # Pelo nome, encontramos as medidas do morcego-vampiro mesmo se a ordem da base mudar.
    linha = nomes.index("Desmodus_rotundus")
    valores = "  ".join(f"{valor:.4f}" for valor in atributos[linha, :5]).replace(".", ",")
    # Somamos 1 para que o número exibido corresponda à linha no arquivo original.
    print(f"Names.txt  | linha {linha + 1}: {nomes[linha]}")
    print(f"wpc50.dat  | mesma linha, primeiros 5 valores: {valores}")
    print("A SVM recebe os 50 números. O nome serve para conferir a classe.")
    avancar("Conhecer os exemplos iniciais.")


def escolher_candidatos(atributos, classes, consultados):
    restantes = np.flatnonzero(~consultados)
    # Uma linha só pode ensinar o modelo depois que sua classe foi conferida.
    svm = criar_svm().fit(atributos[consultados], classes[consultados])
    pontuacoes = svm.decision_function(atributos[restantes])
    # Acima de zero, a SVM indica morcego. A pontuação ajuda a decidir quem conferir primeiro.
    positivos = pontuacoes > 0
    indicados = restantes[positivos]
    pontuacoes_positivas = pontuacoes[positivos]
    ordem = np.argsort(-pontuacoes_positivas, kind="stable")[:TAMANHO_LOTE]
    return indicados[ordem], pontuacoes_positivas[ordem]


def mostrar_indicacoes(rodada, nomes, candidatos, pontuacoes):
    print(f"\nRODADA {rodada} | {len(candidatos)} candidatos para conferir")
    print(f"A SVM escolhe até {TAMANHO_LOTE} linhas com pontuação acima de zero, da maior para a menor.")
    print("Maior e menor pontuação do lote:")
    # O lote já está em ordem de pontuação. Com um único candidato, os dois extremos coincidem.
    extremos = np.unique([0, len(candidatos) - 1])
    for ordem in extremos:
        posicao = candidatos[ordem]
        pontos = f"{pontuacoes[ordem]:+.3f}".replace(".", ",")
        print(f"  {posicao + 1:>4}  {nomes[posicao]:<28} {pontos}")
    avancar("Consultar a classe desses candidatos na referência.")
    return candidatos[extremos]


def mostrar_conferencia(nomes, exemplos, classes, candidatos):
    # Rever os mesmos animais permite comparar o palpite da SVM com o rótulo que vai para o treino.
    print("\nResultado da consulta para os mesmos exemplos:")
    for posicao in exemplos:
        classe = "morcego" if classes[posicao] else "outro organismo"
        print(f"  {posicao + 1:>4}  {nomes[posicao]:<28} {classe}")
    rejeitados = candidatos[classes[candidatos] == 0]
    if rejeitados.size:
        posicao = rejeitados[0]
        print(f"Indicações rejeitadas no lote: {len(rejeitados)}. Exemplo: {nomes[posicao]} (linha {posicao + 1}).")
    print(f"O próximo treino incorpora o lote inteiro. Morcegos acumulados: {classes.sum()}.")


def prospectar(nomes, atributos, referencia, apresentar=False):
    # Para aprender a separar os grupos, o primeiro treino precisa de exemplos de ambos.
    iniciais = np.isin(nomes, NOMES_INICIAIS)
    if iniciais.sum() != len(NOMES_INICIAIS) or set(referencia[iniciais]) != {0, 1}:
        raise ValueError("Os exemplos iniciais precisam estar presentes e incluir as duas classes.")

    # Uma linha ainda sem consulta também começa com zero. A etapa distingue esse caso
    # de um organismo que já conferimos e sabemos que pertence à classe 0.
    classes = np.zeros(len(nomes), dtype=int)
    classes[iniciais] = referencia[iniciais]
    etapas = np.full(len(nomes), "sem indicação", dtype=object)
    etapas[iniciais] = "inicial"
    if apresentar:
        print("\nEXEMPLOS INICIAIS")
        for nome in ("Desmodus_rotundus", "Felis_catus"):
            posicao = nomes.index(nome)
            print(f"Linha {posicao + 1}: {nome} -> classe {classes[posicao]}")
        print("Classe 1 = morcego. Classe 0 = outro organismo.")
    print(f"Pesquisa inicial: {iniciais.sum()} consultas, {classes.sum()} morcegos.")

    rodada = 1
    while (etapas == "sem indicação").any():
        consultados = etapas != "sem indicação"
        if apresentar:
            avancar("Treinar a SVM e procurar candidatos nas linhas restantes.")
            print(f"\nBUSCA COM {consultados.sum()} EXEMPLOS NO TREINO")
            print(f"Ajustando a escala e a SVM. Linhas a examinar: {(~consultados).sum()}.")
        candidatos, pontuacoes = escolher_candidatos(atributos, classes, consultados)
        # Sem indicações, não há um novo lote para ensinar à SVM. A lista será conferida ao final.
        if candidatos.size == 0:
            if apresentar:
                print("Nenhuma pontuação positiva. A busca termina aqui.")
            break
        if apresentar:
            exemplos = mostrar_indicacoes(rodada, nomes, candidatos, pontuacoes)
        # Conferimos só depois da escolha. Um candidato rejeitado também ensina:
        # é um exemplo real de algo que a SVM confundiu com morcego.
        classes[candidatos] = referencia[candidatos]
        etapas[candidatos] = f"rodada {rodada}"
        if apresentar:
            mostrar_conferencia(nomes, exemplos, classes, candidatos)
        print(f"Rodada {rodada}: {len(candidatos)} consultas, {classes[candidatos].sum()} novos morcegos.")
        rodada += 1
    print(f"Fim da busca: {(etapas == 'sem indicação').sum()} linhas ficaram sem indicação da SVM.")
    return classes, etapas


def avaliar(atributos, classes, nomes, apresentar=False):
    # Há poucos morcegos. Manter proporções parecidas nas cinco partes ajuda a testar essa classe
    # em todas elas. A semente fixa permite repetir a avaliação com a mesma divisão.
    divisoes = StratifiedKFold(n_splits=5, shuffle=True, random_state=803)
    previsoes = np.empty_like(classes)
    if apresentar:
        avancar("Testar a SVM em cinco partes.")
        print("\nVALIDAÇÃO | Cada linha fica fora do treino uma vez.")
        print("Parte   Linhas de treino   Linhas de teste   Erros no teste")
    for parte, (treino, teste) in enumerate(divisoes.split(atributos, classes), start=1):
        # Recomeçamos em cada parte para que nem o ajuste da escala nem a SVM tenham visto o teste.
        modelo = criar_svm().fit(atributos[treino], classes[treino])
        previsoes[teste] = modelo.predict(atributos[teste])
        if apresentar:
            erros = np.count_nonzero(previsoes[teste] != classes[teste])
            print(f"{parte:>5}   {len(treino):>15}   {len(teste):>15}   {erros:>14}")
    vn, fp, fn, vp = confusion_matrix(classes, previsoes, labels=[0, 1]).ravel()
    if apresentar:
        avancar("Comparar as previsões com as classes confirmadas.")
        print("\nRESULTADO DO TESTE   Previu outro   Previu morcego")
        print(f"Era outro            {vn:>11}   {fp:>14}")
        print(f"Era morcego          {fn:>11}   {vp:>14}")
        for posicao in np.flatnonzero(previsoes != classes)[:3]:
            print(f"Linha {posicao + 1}, {nomes[posicao]}: previsão {previsoes[posicao]}, classe real {classes[posicao]}.")
    else:
        print(f"Validação em cinco partes: positivos corretos = {vp}, negativos corretos = {vn}, "
              f"falsos positivos = {fp}, falsos negativos = {fn}.")
    # Com tantos outros organismos, a acurácia pode ser alta mesmo se algum morcego passar batido.
    # A sensibilidade mostra que fração dos morcegos encontramos. A precisão diz que fração das indicações acertamos.
    for nome, acertos, total in [
        ("Sensibilidade", vp, vp + fn), ("Precisão", vp, vp + fp), ("Acurácia", vp + vn, len(classes)),
    ]:
        percentual = f"{acertos / total:.2%}".replace(".", ",") if total else "indefinida"
        print(f"{nome}: {acertos}/{total} = {percentual}")


def exportar(nomes, classes, etapas):
    # A etapa registra se a classe veio da consulta inicial, de uma rodada ou da falta de indicação.
    # Os índices começam em 1 para quem quiser localizar um morcego nos arquivos disponibilizados.
    destino = PASTA / "resultados"
    destino.mkdir(exist_ok=True)
    with (destino / "classificacao.csv").open("w", encoding="utf-8", newline="") as arquivo:
        tabela = csv.writer(arquivo)
        tabela.writerow(["indice", "nome", "classe", "etapa"])
        for indice, (nome, classe, etapa) in enumerate(zip(nomes, classes, etapas), start=1):
            tabela.writerow([indice, nome, classe, etapa])
    indices = np.flatnonzero(classes == 1) + 1
    (destino / "indices_morcegos.txt").write_text("".join(f"{indice}\n" for indice in indices), encoding="utf-8")


def principal(apresentar=False):
    nomes, atributos, referencia = ler_dados()
    if apresentar:
        mostrar_dados(nomes, atributos)
    classes, etapas = prospectar(nomes, atributos, referencia, apresentar)
    # A SVM parar de indicar candidatos não garante que encontrou todos os morcegos.
    # A comparação com a referência completa permite descobrir se algum ficou de fora.
    divergencias = np.flatnonzero(classes != referencia) + 1
    if divergencias.size:
        raise ValueError(f"A busca divergiu da referência nos índices: {divergencias.tolist()}.")
    print(f"Auditoria das {len(nomes)} linhas: {classes.sum()} morcegos e nenhuma divergência.")
    avaliar(atributos, classes, nomes, apresentar)
    if apresentar:
        avancar("Gravar a classificação e os índices dos morcegos.")
    exportar(nomes, classes, etapas)
    if apresentar:
        print(f"\nresultados/classificacao.csv       {len(classes)} linhas de dados")
        print(f"resultados/indices_morcegos.txt    {classes.sum()} índices positivos")


if __name__ == "__main__":
    argumentos = argparse.ArgumentParser(description=__doc__)
    argumentos.add_argument("--apresentar", action="store_true", help="avança por etapas com a tecla Enter")
    try:
        principal(argumentos.parse_args().apresentar)
    except EOFError:
        sys.exit(1)
    except KeyboardInterrupt:
        sys.exit(130)
