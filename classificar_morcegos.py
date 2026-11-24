"""Identifica morcegos por rodadas de supervisão e avalia a SVM na base classificada."""

import csv
from pathlib import Path

import numpy as np
from sklearn.metrics import confusion_matrix
from sklearn.model_selection import StratifiedKFold, cross_val_predict
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


def escolher_candidatos(atributos, classes, consultados):
    restantes = np.flatnonzero(~consultados)
    svm = criar_svm().fit(atributos[consultados], classes[consultados])
    pontuacoes = svm.decision_function(atributos[restantes])
    positivos = pontuacoes > 0
    indicados = restantes[positivos]
    ordem = np.argsort(-pontuacoes[positivos], kind="stable")
    return indicados[ordem[:TAMANHO_LOTE]]


def prospectar(nomes, atributos, referencia):
    iniciais = np.isin(nomes, NOMES_INICIAIS)
    if iniciais.sum() != len(NOMES_INICIAIS) or set(referencia[iniciais]) != {0, 1}:
        raise ValueError("Os exemplos iniciais precisam estar presentes e incluir as duas classes.")

    classes = np.zeros(len(nomes), dtype=int)
    classes[iniciais] = referencia[iniciais]
    etapas = np.full(len(nomes), "sem indicação", dtype=object)
    etapas[iniciais] = "inicial"
    print(f"Pesquisa inicial: {iniciais.sum()} consultas, {classes.sum()} morcegos.")

    rodada = 1
    while (etapas == "sem indicação").any():
        candidatos = escolher_candidatos(atributos, classes, etapas != "sem indicação")
        if candidatos.size == 0:
            break
        classes[candidatos] = referencia[candidatos]
        etapas[candidatos] = f"rodada {rodada}"
        print(f"Rodada {rodada}: {len(candidatos)} consultas, {classes[candidatos].sum()} novos morcegos.")
        rodada += 1
    print(f"Fim da busca: {(etapas == 'sem indicação').sum()} linhas ficaram sem indicação da SVM.")
    return classes, etapas


def avaliar(atributos, classes):
    divisoes = StratifiedKFold(n_splits=5, shuffle=True, random_state=803)
    previsoes = cross_val_predict(criar_svm(), atributos, classes, cv=divisoes)
    vn, fp, fn, vp = confusion_matrix(classes, previsoes, labels=[0, 1]).ravel()
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


def principal():
    nomes, atributos, referencia = ler_dados()
    classes, etapas = prospectar(nomes, atributos, referencia)
    divergencias = np.flatnonzero(classes != referencia) + 1
    if divergencias.size:
        raise ValueError(f"A busca divergiu da referência nos índices: {divergencias.tolist()}.")
    print(f"Auditoria das {len(nomes)} linhas: {classes.sum()} morcegos e nenhuma divergência.")
    avaliar(atributos, classes)
    exportar(nomes, classes, etapas)


if __name__ == "__main__":
    principal()
