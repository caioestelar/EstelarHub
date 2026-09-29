# -*- coding: utf-8 -*-
"""
core/municipios.py
===================
Descoberta automática de município/UF por interseção espacial, e cálculo
automático da zona UTM/SIRGAS 2000 a partir de um ponto em coordenadas
geográficas (lon/lat), exatamente como fazia a macro original.
"""

from typing import Optional, Tuple

from qgis.core import QgsGeometry, QgsPointXY, QgsProject

from ..utils import constants


def calcular_zona_utm(ponto: QgsPointXY) -> str:
    """Calcula a zona UTM (ex: '22S') a partir de um ponto em coordenadas
    geográficas (longitude/latitude, graus decimais — como vem de um KML,
    que é sempre WGS84).
    """
    lon = ponto.x()
    lat = ponto.y()

    zona = int((lon + 180) / 6) + 1
    hemisferio = "S" if lat < 0 else "N"

    return f"{zona}{hemisferio}"


def obter_epsg_zona(zona_utm: str) -> Optional[str]:
    """Retorna o código EPSG (SIRGAS 2000/UTM) correspondente à zona informada."""
    return constants.EPSG_ZONAS.get(zona_utm)


def descobrir_municipio(projeto: QgsProject, geometria: QgsGeometry) -> Tuple[Optional[str], Optional[str]]:
    """Percorre a camada MUNICIPIOS_BRASIL procurando qual feição intersecta
    a geometria informada, retornando (municipio, uf).

    Retorna (None, None) se a camada não existir no projeto ou se nenhuma
    feição intersectar a geometria.
    """
    camadas = projeto.mapLayersByName(constants.LAYER_MUNICIPIOS)

    if not camadas:
        return None, None

    camada_municipio = camadas[0]

    for feicao in camada_municipio.getFeatures():
        if feicao.geometry().intersects(geometria):
            return feicao["NM_MUN"], feicao["SIGLA_UF"]

    return None, None


def descobrir_uf(projeto: QgsProject, geometria: QgsGeometry) -> Optional[str]:
    """Atalho para obter apenas a UF (reaproveita `descobrir_municipio`,
    evitando duplicar a lógica de varredura da camada).
    """
    _, uf = descobrir_municipio(projeto, geometria)
    return uf


def obter_geometria_estado(projeto: QgsProject, uf: str) -> Optional[QgsGeometry]:
    """Busca na camada DEFINIR_ÁREA a feição cujo campo 'sigla' corresponde
    à UF informada e retorna sua geometria (usada, na macro original, como
    limite para o recorte de rios).
    """
    if not uf:
        return None

    camadas = projeto.mapLayersByName(constants.LAYER_DEFINIR_AREA)

    if not camadas:
        return None

    camada_estado = camadas[0]

    for feicao in camada_estado.getFeatures():
        if feicao["sigla"] == uf:
            return feicao.geometry()

    return None
