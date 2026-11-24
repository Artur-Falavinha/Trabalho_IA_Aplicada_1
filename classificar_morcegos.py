"""Prospecção e avaliação de morcegos a partir das 50 características fornecidas."""

import csv
from pathlib import Path

import numpy as np
from sklearn.decomposition import PCA
from sklearn.metrics import confusion_matrix, pairwise_distances
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.neighbors import KNeighborsClassifier
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC


PASTA = Path(__file__).resolve().parent
RESULTADOS = PASTA / "resultados"
SEMENTE = 803
RODADAS = 6
INICIAIS = {
    1: """Artibeus_jamaicensis Desmodus_rotundus Myotis_lucifugus Pteropus_vampyrus
    Rhinolophus_monoceros Rousettus_aegyptiacus Tadarida_teniotis Pteronotus_parnellii
    Pipistrellus_abramus Myotis_myotis Artibeus_lituratus Pteropus_alecto""".split(),
    0: """Homo_sapiens Bos_taurus Equus_caballus Mus_musculus Oryctolagus_cuniculus
    Felis_catus Canis_lupus Sus_scrofa Talpa_europaea Erinaceus_europaeus Sorex_araneus
    Manis_javanica Gallus_gallus Danio_rerio Drosophila_melanogaster Arabidopsis_thaliana
    Saccharomyces_cerevisiae""".split(),
}
MEDIDAS = ["vn", "fp", "fn", "vp", "sensibilidade", "precisao", "acuracia", "f1"]


def ler_dados():
    nomes = [linha.strip() for linha in (PASTA / "Names.txt").read_text(encoding="utf-8").splitlines()]
    atributos = np.loadtxt(PASTA / "wpc50.dat")
    if atributos.shape != (8426, 50) or len(nomes) != len(atributos) or not np.isfinite(atributos).all():
        raise ValueError("A base deve conter 8.426 nomes e 8.426 vetores finitos de 50 características.")

    arquivo = PASTA / "dados" / "referencia_taxonomica.csv"
    with arquivo.open(encoding="utf-8", newline="") as origem:
        referencia = list(csv.DictReader(origem))
    chaves_esperadas = list(enumerate(nomes, start=1))
    if [(int(linha["indice"]), linha["nome"]) for linha in referencia] != chaves_esperadas:
        raise ValueError("Os índices e nomes da referência devem seguir a ordem original da base.")
    rotulos = np.array([int(linha["classe"]) for linha in referencia])
    if set(rotulos) != {0, 1} or not all(linha["evidencia"] for linha in referencia):
        raise ValueError("A referência deve conter rótulos binários e evidência para cada linha.")
    grupos = np.array([
        linha["taxid_especie"] or linha["taxid"] or linha["nome"]
        for linha in referencia
    ])
    return np.array(nomes), atributos, rotulos, grupos


def criar_svm():
    return make_pipeline(StandardScaler(), SVC(kernel="rbf", class_weight="balanced"))


def criar_knn():
    return make_pipeline(StandardScaler(), KNeighborsClassifier(n_neighbors=5, weights="distance"))


def selecionar_iniciais(nomes, rotulos, treino):
    classes_esperadas = {nome: classe for classe, lista in INICIAIS.items() for nome in lista}
    iniciais = treino[np.isin(nomes[treino], list(classes_esperadas))]
    for posicao in iniciais:
        if rotulos[posicao] != classes_esperadas[nomes[posicao]]:
            raise ValueError(f"Rótulo inicial divergente para {nomes[posicao]}.")
    if len(np.unique(rotulos[iniciais])) < 2:
        raise ValueError("A amostra inicial precisa incluir as duas classes.")
    return iniciais


def priorizar_candidatos(atributos, rotulos, conhecidos, disponiveis, sorteio):
    svm = criar_svm().fit(atributos[conhecidos], rotulos[conhecidos])
    padronizador = svm.named_steps["standardscaler"]
    positivos = conhecidos[rotulos[conhecidos] == 1]
    distancias = pairwise_distances(
        padronizador.transform(atributos[disponiveis]),
        padronizador.transform(atributos[positivos]),
    ).min(axis=1)
    vizinhos = disponiveis[np.argsort(distancias, kind="stable")[:12]]

    restantes = np.setdiff1d(disponiveis, vizinhos)
    margens = np.abs(svm.decision_function(atributos[restantes]))
    fronteira = restantes[np.argsort(margens, kind="stable")[:12]]

    restantes = np.setdiff1d(restantes, fronteira)
    aleatorios = sorteio.choice(restantes, size=6, replace=False)
    return {"vizinhança": vizinhos, "fronteira SVM": fronteira, "amostra aleatória": aleatorios}


def prospectar(nomes, atributos, rotulos, treino):
    sorteio = np.random.default_rng(SEMENTE)
    conhecidos = selecionar_iniciais(nomes, rotulos, treino)
    historico = [(0, "pesquisa inicial", posicao) for posicao in conhecidos]
    bases_por_rodada = [conhecidos]

    for rodada in range(1, RODADAS + 1):
        disponiveis = np.setdiff1d(treino, conhecidos)
        lotes = priorizar_candidatos(atributos, rotulos, conhecidos, disponiveis, sorteio)
        for criterio, posicoes in lotes.items():
            historico.extend((rodada, criterio, posicao) for posicao in posicoes)
        conhecidos = np.concatenate([conhecidos, *lotes.values()])
        bases_por_rodada.append(conhecidos)

    return historico, bases_por_rodada


def calcular_metricas(referencia, previsoes):
    vn, fp, fn, vp = (int(valor) for valor in confusion_matrix(referencia, previsoes, labels=[0, 1]).ravel())
    return dict(zip(MEDIDAS, [
        vn, fp, fn, vp,
        vp / (vp + fn) if vp + fn else 0.0,
        vp / (vp + fp) if vp + fp else 0.0,
        (vp + vn) / len(referencia),
        2 * vp / (2 * vp + fp + fn) if vp + fp + fn else 0.0,
    ]))


def avaliar_rodadas(atributos, rotulos, bases_por_rodada, teste):
    medidas = []
    for rodada, conhecidos in enumerate(bases_por_rodada):
        svm = criar_svm().fit(atributos[conhecidos], rotulos[conhecidos])
        previsoes = svm.predict(atributos[teste])
        medidas.append({
            "rodada": rodada,
            "rotulos_acumulados": len(conhecidos),
            "morcegos_acumulados": int(rotulos[conhecidos].sum()),
            **calcular_metricas(rotulos[teste], previsoes),
        })
    return medidas


def avaliar_base_final(atributos, rotulos, particoes):
    previsoes = {"SVM RBF": np.zeros_like(rotulos), "k-NN (k=5)": np.zeros_like(rotulos),
                 "Sempre outro": np.zeros_like(rotulos)}
    numero_particao = np.zeros_like(rotulos)
    for numero, (treino, teste) in enumerate(particoes, start=1):
        numero_particao[teste] = numero
        for nome, modelo in [("SVM RBF", criar_svm()), ("k-NN (k=5)", criar_knn())]:
            modelo.fit(atributos[treino], rotulos[treino])
            previsoes[nome][teste] = modelo.predict(atributos[teste])
    medidas = [{"modelo": nome, **calcular_metricas(rotulos, valores)} for nome, valores in previsoes.items()]
    return medidas, previsoes, numero_particao


def escrever_csv(nome, colunas, linhas):
    with (RESULTADOS / nome).open("w", encoding="utf-8", newline="") as destino:
        escritor = csv.writer(destino)
        escritor.writerow(colunas)
        escritor.writerows(linhas)


def exportar_classificacao(nomes, rotulos):
    escrever_csv("classificacao.csv", ["indice", "nome", "classe"],
                 ((indice, nome, classe) for indice, (nome, classe) in enumerate(zip(nomes, rotulos), start=1)))
    (RESULTADOS / "indices_morcegos.txt").write_text(
        "".join(f"{posicao + 1}\n" for posicao in np.flatnonzero(rotulos == 1)), encoding="utf-8"
    )


def exportar_pca(atributos):
    pca = PCA(n_components=2, svd_solver="full")
    coordenadas = pca.fit_transform(atributos)
    escrever_csv("visualizacao_pca.csv", ["indice", "pc1", "pc2"],
                 ((indice, *linha) for indice, linha in enumerate(coordenadas, start=1)))
    variancias = 100 * pca.explained_variance_ratio_
    escrever_csv("variancia_pca.csv", ["componente", "variancia_percentual"], enumerate(variancias, start=1))


def principal():
    nomes, atributos, rotulos, grupos = ler_dados()
    separador = StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=SEMENTE)
    particoes = list(separador.split(atributos, rotulos, grupos))
    treino, teste = particoes[0]
    historico, bases_por_rodada = prospectar(nomes, atributos, rotulos, treino)
    medidas_rodadas = avaliar_rodadas(atributos, rotulos, bases_por_rodada, teste)
    medidas_finais, previsoes, numero_particao = avaliar_base_final(atributos, rotulos, particoes)

    RESULTADOS.mkdir(exist_ok=True)
    exportar_classificacao(nomes, rotulos)
    escrever_csv("candidatos.csv", ["rodada", "criterio", "indice", "nome", "classe_confirmada"],
                 ((rodada, criterio, posicao + 1, nomes[posicao], rotulos[posicao])
                  for rodada, criterio, posicao in historico))
    escrever_csv("rodadas.csv", list(medidas_rodadas[0]), (linha.values() for linha in medidas_rodadas))
    escrever_csv("metricas.csv", list(medidas_finais[0]), (linha.values() for linha in medidas_finais))
    escrever_csv("previsoes_validacao.csv", ["indice", "particao", "classe", "svm", "knn"],
                 ((posicao + 1, numero_particao[posicao], rotulos[posicao],
                   previsoes["SVM RBF"][posicao], previsoes["k-NN (k=5)"][posicao])
                  for posicao in range(len(nomes))))
    exportar_pca(atributos)
    print(f"{len(nomes):,} instâncias, {rotulos.sum()} morcegos, {len(historico)} rótulos na prospecção.")
    for linha in medidas_finais:
        print(f"{linha['modelo']}: sensibilidade {linha['sensibilidade']:.2%}, "
              f"precisão {linha['precisao']:.2%}, acurácia {linha['acuracia']:.2%}.")


if __name__ == "__main__":
    principal()
