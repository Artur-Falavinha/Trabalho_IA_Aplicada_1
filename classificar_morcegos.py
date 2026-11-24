"""Identifica morcegos por rodadas de supervisão e avalia a SVM na base classificada."""

import argparse
import csv
from pathlib import Path

import numpy as np
from sklearn.metrics import confusion_matrix
from sklearn.model_selection import StratifiedKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC


PASTA = Path(__file__).resolve().parent
TAMANHO_LOTE = 20
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
    nomes = (PASTA / "Names.txt").read_text(encoding="utf-8").splitlines()
    nomes = [nome.strip() for nome in nomes]
    atributos = np.loadtxt(PASTA / "wpc50.dat")
    if len(nomes) != 8426 or atributos.shape != (len(nomes), 50) or not np.isfinite(atributos).all():
        raise ValueError("A base deve ter 8.426 nomes e 50 valores finitos por linha.")

    with (PASTA / "dados" / "rotulos.csv").open(encoding="utf-8", newline="") as arquivo:
        referencia = list(csv.DictReader(arquivo))
    if [linha["nome"] for linha in referencia] != nomes:
        raise ValueError("Os nomes da referência devem seguir a mesma ordem de Names.txt.")
    if any(linha["classe"] not in {"0", "1"} or not linha["fonte"] for linha in referencia):
        raise ValueError("Cada organismo precisa de classe 0 ou 1 e fonte para a consulta.")
    return nomes, atributos, np.array([int(linha["classe"]) for linha in referencia])


def criar_svm():
    return make_pipeline(StandardScaler(), SVC(kernel="rbf", class_weight="balanced"))


def avancar(acao):
    input(f"\n[Enter] {acao} ")


def mostrar_dados(nomes, atributos):
    print("\nBASE DE ORGANISMOS")
    print(f"{len(nomes)} linhas, cada uma com {atributos.shape[1]} características.")
    linha = nomes.index("Desmodus_rotundus")
    valores = "  ".join(f"{valor:.4f}" for valor in atributos[linha, :5]).replace(".", ",")
    print(f"Names.txt  | linha {linha + 1}: {nomes[linha]}")
    print(f"wpc50.dat  | mesma linha, primeiros 5 valores: {valores}")
    print("A SVM recebe os 50 números. O nome serve para conferir a classe.")
    avancar("Conhecer os exemplos iniciais.")


def escolher_candidatos(atributos, classes, consultados):
    restantes = np.flatnonzero(~consultados)
    svm = criar_svm().fit(atributos[consultados], classes[consultados])
    pontuacoes = svm.decision_function(atributos[restantes])
    positivos = pontuacoes > 0
    indicados = restantes[positivos]
    pontuacoes_positivas = pontuacoes[positivos]
    ordem = np.argsort(-pontuacoes_positivas, kind="stable")[:TAMANHO_LOTE]
    return indicados[ordem], pontuacoes_positivas[ordem]


def mostrar_indicacoes(rodada, nomes, candidatos, pontuacoes):
    print(f"\nRODADA {rodada} | {len(candidatos)} candidatos para conferir")
    print(f"A SVM escolhe até {TAMANHO_LOTE} linhas com pontuação acima de zero, da maior para a menor.")
    print("Compare as pontuações nas extremidades do lote:")
    extremos = np.unique([0, len(candidatos) - 1])
    for ordem in extremos:
        posicao = candidatos[ordem]
        pontos = f"{pontuacoes[ordem]:+.3f}".replace(".", ",")
        print(f"  {posicao + 1:>4}  {nomes[posicao]:<28} {pontos}")
    avancar("Consultar a classe desses candidatos na referência.")
    return candidatos[extremos]


def mostrar_conferencia(nomes, exemplos, classes, candidatos):
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
    iniciais = np.isin(nomes, NOMES_INICIAIS)
    if iniciais.sum() != len(NOMES_INICIAIS) or set(referencia[iniciais]) != {0, 1}:
        raise ValueError("Os exemplos iniciais precisam estar presentes e incluir as duas classes.")

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
        if candidatos.size == 0:
            if apresentar:
                print("Nenhuma pontuação positiva. A busca termina aqui.")
            break
        if apresentar:
            exemplos = mostrar_indicacoes(rodada, nomes, candidatos, pontuacoes)
        classes[candidatos] = referencia[candidatos]
        etapas[candidatos] = f"rodada {rodada}"
        if apresentar:
            mostrar_conferencia(nomes, exemplos, classes, candidatos)
        print(f"Rodada {rodada}: {len(candidatos)} consultas, {classes[candidatos].sum()} novos morcegos.")
        rodada += 1
    print(f"Fim da busca: {(etapas == 'sem indicação').sum()} linhas ficaram sem indicação da SVM.")
    return classes, etapas


def avaliar(atributos, classes, nomes, apresentar=False):
    divisoes = StratifiedKFold(n_splits=5, shuffle=True, random_state=803)
    previsoes = np.empty_like(classes)
    if apresentar:
        avancar("Testar a SVM em cinco partes.")
        print("\nVALIDAÇÃO | Cada linha fica fora do treino uma vez.")
        print("Parte   Linhas de treino   Linhas de teste   Erros no teste")
    for parte, (treino, teste) in enumerate(divisoes.split(atributos, classes), start=1):
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
    for nome, acertos, total in [
        ("Sensibilidade", vp, vp + fn), ("Precisão", vp, vp + fp), ("Acurácia", vp + vn, len(classes)),
    ]:
        percentual = f"{acertos / total:.2%}".replace(".", ",") if total else "indefinida"
        print(f"{nome}: {acertos}/{total} = {percentual}")


def exportar(nomes, classes, etapas):
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
        raise SystemExit("A apresentação precisa de entrada pelo teclado. Abra o PowerShell ou execute sem --apresentar.")
    except KeyboardInterrupt:
        print("\nExecução interrompida.")
        raise SystemExit(130)
