# -*- coding: utf-8 -*-
"""
core/kml.py
===========
Responsável por importar arquivos KML/KMZ como camadas vetoriais e por
disponibilizar a camada de satélite (raster XYZ) usada no preview.

Na macro original, o carregamento era feito com `QgsVectorLayer(arquivo, ...,
"ogr")` diretamente dentro do método `selecionar_arquivo`, sem validação de
extensão e sem tratamento de erro (se o arquivo fosse inválido, o restante
do código simplesmente não fazia nada, sem avisar o usuário).
"""

from qgis.core import QgsRasterLayer, QgsVectorLayer

from ..utils import constants


def importar_camada(caminho: str, nome: str = "preview") -> QgsVectorLayer:
    """Importa um KML/KMZ (ou qualquer formato suportado pelo OGR) como
    QgsVectorLayer. Lança ValueError se a camada resultante for inválida.
    """
    camada = QgsVectorLayer(caminho, nome, "ogr")

    if not camada.isValid():
        raise ValueError(
            f"Não foi possível carregar o arquivo:\n{caminho}\n\n"
            "Verifique se o arquivo KML/KMZ não está corrompido."
        )

    return camada


def importar_kml(caminho: str, nome: str = "preview") -> QgsVectorLayer:
    """Importa especificamente um arquivo .kml."""
    if not caminho.lower().endswith(".kml"):
        raise ValueError("O arquivo selecionado não possui extensão .kml.")
    return importar_camada(caminho, nome)


def importar_kmz(caminho: str, nome: str = "preview") -> QgsVectorLayer:
    """Importa especificamente um arquivo .kmz."""
    if not caminho.lower().endswith(".kmz"):
        raise ValueError("O arquivo selecionado não possui extensão .kmz.")
    return importar_camada(caminho, nome)


def importar_kml_ou_kmz(caminho: str, nome: str = "preview") -> QgsVectorLayer:
    """Ponto de entrada único usado pela UI: aceita tanto .kml quanto .kmz."""
    extensao = caminho.lower().rsplit(".", 1)[-1] if "." in caminho else ""

    if extensao == "kml":
        return importar_kml(caminho, nome)
    if extensao == "kmz":
        return importar_kmz(caminho, nome)

    raise ValueError("Selecione um arquivo com extensão .kml ou .kmz.")


def obter_camada_fundo(estilo: str = "satelite", nome: str = "Base do mapa") -> QgsRasterLayer:
    """Cria a camada raster de fundo usada no preview.

    Estilos disponíveis:
    - satelite
    - mapa_base
    - sem_cidades
    """
    selecao = {
        "satelite": constants.URL_SATELITE,
        "mapa_base": constants.URL_MAPA_BASE,
        "sem_cidades": constants.URL_SEM_CIDADES,
    }

    url = selecao.get(estilo, constants.URL_SATELITE)
    camada = QgsRasterLayer(url, nome, "wms")

    if not camada.isValid():
        raise ValueError(
            "Não foi possível carregar a camada de fundo do mapa "
            "(verifique a conexão com a internet)."
        )

    return camada


def obter_camada_satelite(nome: str = "Satélite") -> QgsRasterLayer:
    """Compatibilidade com o código anterior: retorna o estilo satélite."""
    return obter_camada_fundo("satelite", nome)
