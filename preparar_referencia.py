"""Cruza Names.txt com uma cópia do taxdump do NCBI Taxonomy."""

import argparse
import csv
import hashlib
import tarfile
from collections import defaultdict
from functools import cache
from pathlib import Path


PASTA = Path(__file__).resolve().parent
REFERENCIA = PASTA / "dados" / "referencia_taxonomica.csv"
EXCECOES = PASTA / "dados" / "nomes_revisados.csv"
CHIROPTERA = 9397
CLASSES_DE_NOME = {"scientific name", "synonym", "equivalent name", "misspelling", "genbank synonym", "includes"}
COLUNAS = ["indice", "nome", "classe", "taxid", "taxid_especie", "metodo", "evidencia"]
SEPARADORES = str.maketrans("_.-'\"", "     ")


def normalizar(nome):
    return " ".join(nome.translate(SEPARADORES).casefold().split())


def partes_ncbi(arquivo, membro):
    with tarfile.open(arquivo, "r:gz") as taxdump:
        with taxdump.extractfile(membro) as linhas:
            for linha in linhas:
                yield linha.decode("utf-8").rstrip("\r\n").removesuffix("\t|").split("\t|\t")


def carregar_taxonomia(arquivo, nomes):
    pais = {}
    especies = set()
    generos = set()
    for taxid, pai, nivel, *_ in partes_ncbi(arquivo, "nodes.dmp"):
        identificador = int(taxid)
        pais[identificador] = int(pai)
        if nivel == "species":
            especies.add(identificador)
        elif nivel == "genus":
            generos.add(identificador)
    if CHIROPTERA not in pais:
        raise ValueError("O taxdump não contém Chiroptera.")

    candidatos = defaultdict(list)
    for taxid, nome, nome_unico, tipo in partes_ncbi(arquivo, "names.dmp"):
        chave = normalizar(nome)
        if chave in nomes and tipo in CLASSES_DE_NOME:
            candidatos[chave].append((int(taxid), tipo))
        if nome_unico and normalizar(nome_unico) in nomes and tipo in CLASSES_DE_NOME:
            candidatos[normalizar(nome_unico)].append((int(taxid), tipo))

    @cache
    def classe_e_especie(taxid):
        pai = pais[taxid]
        if pai == taxid:
            return 0, None
        classe, especie = classe_e_especie(pai)
        return int(taxid == CHIROPTERA or classe), taxid if taxid in especies else especie

    return candidatos, generos, classe_e_especie


def possibilidades(nome):
    palavras = normalizar(nome).split()
    for quantidade in range(len(palavras), 0, -1):
        yield " ".join(palavras[:quantidade]), quantidade == len(palavras), quantidade == 1


def identificar(nome, candidatos, generos, classe_e_especie):
    for chave, exato, palavra_unica in possibilidades(nome):
        encontrados = candidatos[chave]
        if not exato:
            encontrados = [(taxid, tipo) for taxid, tipo in encontrados if tipo != "includes"]
        if palavra_unica and not exato:
            encontrados = [(taxid, tipo) for taxid, tipo in encontrados if taxid in generos]
        oficiais = [(taxid, tipo) for taxid, tipo in encontrados if tipo == "scientific name"]
        encontrados = sorted(set(oficiais or encontrados))
        if not encontrados:
            continue

        taxid, tipo = encontrados[0]
        classe, especie = classe_e_especie(taxid)
        if len(encontrados) > 1 and any(classe_e_especie(outro)[0] != classe for outro, _ in encontrados):
            return None
        metodo = "nome exato" if exato else "gênero" if palavra_unica else "prefixo taxonômico"
        evidencia = f"https://www.ncbi.nlm.nih.gov/Taxonomy/Browser/wwwtax.cgi?id={taxid}"
        return classe, taxid, especie, f"NCBI · {metodo} ({tipo})", evidencia
    return None


def principal():
    argumentos = argparse.ArgumentParser(description=__doc__)
    argumentos.add_argument("taxdump", type=Path, help="caminho de taxdump.tar.gz do NCBI")
    arquivo = argumentos.parse_args().taxdump
    with arquivo.open("rb") as origem:
        print(f"SHA-256 do taxdump: {hashlib.file_digest(origem, 'sha256').hexdigest()}")
    nomes = (PASTA / "Names.txt").read_text(encoding="utf-8").splitlines()
    nomes = [nome.strip() for nome in nomes]
    chaves = {chave for nome in nomes for chave, _, _ in possibilidades(nome)}
    candidatos, generos, classe_e_especie = carregar_taxonomia(arquivo, chaves)
    excecoes = {}
    if EXCECOES.exists():
        with EXCECOES.open(encoding="utf-8", newline="") as origem:
            excecoes = {linha["nome"]: linha for linha in csv.DictReader(origem)}

    linhas = []
    pendencias = []
    for indice, nome in enumerate(nomes, start=1):
        if nome in excecoes:
            revisao = excecoes[nome]
            resultado = tuple(revisao[campo] for campo in COLUNAS[2:])
        else:
            resultado = identificar(nome, candidatos, generos, classe_e_especie)
        if resultado is None:
            pendencias.append(f"{indice}: {nome}")
        else:
            linhas.append((indice, nome, *resultado))

    if pendencias:
        raise SystemExit(f"{len(pendencias)} nomes exigem revisão:\n" + "\n".join(pendencias))
    REFERENCIA.parent.mkdir(exist_ok=True)
    with REFERENCIA.open("w", encoding="utf-8", newline="") as destino:
        escritor = csv.writer(destino)
        escritor.writerow(COLUNAS)
        escritor.writerows(linhas)
    print(f"{len(linhas)} rótulos verificados em {REFERENCIA.name}.")


if __name__ == "__main__":
    principal()
