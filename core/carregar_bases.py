from qgis.core import (
    QgsProject,
    QgsVectorLayer
)
from qgis.PyQt.QtWidgets import QApplication

from osgeo import ogr
import os
import shutil

PASTA_BASES_REDE = r"Q:\STL-TEMPLATE-QGIZ\BASES"


def copiar_bases_para_projeto(pasta_projeto: str, progresso=None) -> str:
    """Copia GeoPackages da rede para uma pasta BASES ao lado do projeto."""
    if not os.path.isdir(pasta_projeto):
        raise FileNotFoundError(f"Pasta do projeto não encontrada: {pasta_projeto}")

    if not os.path.isdir(PASTA_BASES_REDE):
        raise FileNotFoundError(f"Pasta de bases da rede não encontrada: {PASTA_BASES_REDE}")

    pasta_destino = os.path.abspath(os.path.join(pasta_projeto, "BASES"))
    pasta_origem = os.path.normcase(os.path.abspath(PASTA_BASES_REDE))
    destino_normalizado = os.path.normcase(pasta_destino)
    if (
        destino_normalizado == pasta_origem
        or destino_normalizado.startswith(pasta_origem + os.sep)
    ):
        raise ValueError("Escolha uma pasta de projeto fora da pasta BASES da rede.")

    arquivos = sorted(
        arquivo for arquivo in os.listdir(PASTA_BASES_REDE)
        if arquivo.lower().endswith(".gpkg")
    )
    if not arquivos:
        raise FileNotFoundError(
            f"Nenhum GeoPackage encontrado em: {PASTA_BASES_REDE}"
        )

    tamanho_total = sum(
        os.path.getsize(os.path.join(PASTA_BASES_REDE, arquivo))
        for arquivo in arquivos
    )
    if progresso is not None:
        progresso.setRange(0, tamanho_total)

    os.makedirs(pasta_destino, exist_ok=True)
    bytes_copiados = 0

    for arquivo in arquivos:
        origem = os.path.join(PASTA_BASES_REDE, arquivo)
        destino = os.path.join(pasta_destino, arquivo)
        if os.path.exists(destino):
            bytes_copiados += os.path.getsize(origem)
            if progresso is not None:
                progresso.setValue(bytes_copiados)
            continue

        temporario = destino + ".copying"
        try:
            if progresso is not None:
                progresso.setLabelText(f"Copiando {arquivo} para a pasta do projeto...")

            with open(origem, "rb") as arquivo_origem, open(temporario, "wb") as arquivo_destino:
                while True:
                    bloco = arquivo_origem.read(8 * 1024 * 1024)
                    if not bloco:
                        break
                    arquivo_destino.write(bloco)
                    bytes_copiados += len(bloco)

                    if progresso is not None:
                        progresso.setValue(bytes_copiados)
                        QApplication.processEvents()
                        if progresso.wasCanceled():
                            raise InterruptedError("Cópia das bases cancelada pelo usuário.")

            shutil.copystat(origem, temporario)
            os.replace(temporario, destino)
        finally:
            if os.path.exists(temporario):
                os.remove(temporario)

    return pasta_destino


def _remover_bases_da_rede(projeto: QgsProject) -> None:
    origem_normalizada = os.path.normcase(os.path.abspath(PASTA_BASES_REDE))
    for camada in list(projeto.mapLayers().values()):
        caminho_fonte = camada.source().split("|", 1)[0]
        fonte_normalizada = os.path.normcase(os.path.abspath(caminho_fonte))
        if (
            fonte_normalizada == origem_normalizada
            or fonte_normalizada.startswith(origem_normalizada + os.sep)
        ):
            projeto.removeMapLayer(camada.id())


def carregar_bases_estelar(pasta: str = None) -> None:
    pasta = pasta or PASTA_BASES_REDE
    if not os.path.isdir(pasta):
        raise FileNotFoundError(f"Pasta de bases não encontrada: {pasta}")

    projeto = QgsProject.instance()
    if os.path.normcase(os.path.abspath(pasta)) != os.path.normcase(
        os.path.abspath(PASTA_BASES_REDE)
    ):
        _remover_bases_da_rede(projeto)

    for arquivo in os.listdir(pasta):

        caminho = os.path.join(
            pasta,
            arquivo
        )

        if arquivo.lower().endswith(".gpkg"):

            ds = ogr.Open(caminho)

            if ds:

                for i in range(ds.GetLayerCount()):

                    layer_ogr = ds.GetLayerByIndex(i)

                    nome = layer_ogr.GetName()

                    uri = f"{caminho}|layername={nome}"

                    if projeto.mapLayersByName(nome):
                        continue

                    camada = QgsVectorLayer(
                        uri,
                        nome,
                        "ogr"
                    )

                    if camada.isValid():

                        projeto.addMapLayer(camada)

                        print(f"✓ {nome}")

        elif arquivo.lower().endswith(".shp"):

            nome = os.path.splitext(
                arquivo
            )[0]

            camada = QgsVectorLayer(
                caminho,
                nome,
                "ogr"
            )

            if camada.isValid():

                projeto.addMapLayer(camada)

                print(f"✓ {nome}")