# -*- coding: utf-8 -*-
"""
core/recorte.py
================
Substitui o uso do QgsRubberBand como "geometria final" (na macro original
o retângulo vermelho do preview era puramente visual e nunca era usado
para nenhum recorte real — um dos problemas mais relevantes identificados
na macro).

Aqui a geometria do retângulo vermelho (rb_500) é transformada em uma
camada vetorial temporária real chamada AREA_ESTUDO, que passa a ser usada
como máscara para o recorte de rios, municípios e estradas, e fica
disponível no projeto para uso em futuras exportações.
"""

import os
from typing import Iterable, Optional

from qgis.core import (
    QgsCoordinateReferenceSystem,
    QgsCoordinateTransform,
    QgsFeature,
    QgsGeometry,
    QgsProject,
    QgsSpatialIndex,
    QgsVectorLayer,
)

from ..utils import constants


def criar_area_estudo(
    projeto: QgsProject,
    geometria: QgsGeometry,
    crs_origem: QgsCoordinateReferenceSystem,
    nome: str = constants.AREA_ESTUDO_LAYER_NAME,
) -> QgsVectorLayer:
    """Cria (ou recria) a camada de memória AREA_ESTUDO com a geometria do
    retângulo vermelho de preview, já reprojetada para o SRC do projeto.

    Se já existir uma camada AREA_ESTUDO no projeto (de uma execução
    anterior do plugin), ela é removida antes de criar a nova, evitando
    acumular camadas duplicadas a cada vez que o usuário gera o projeto.
    """
    # Remove instâncias anteriores da camada, se existirem.
    for camada_antiga in projeto.mapLayersByName(nome):
        projeto.removeMapLayer(camada_antiga.id())

    crs_destino = projeto.crs()

    geometria_final = QgsGeometry(geometria)
    if crs_origem and crs_origem.isValid() and crs_destino.isValid() and crs_origem != crs_destino:
        transformador = QgsCoordinateTransform(crs_origem, crs_destino, projeto)
        geometria_final.transform(transformador)

    camada = QgsVectorLayer(f"Polygon?crs={crs_destino.authid()}", nome, "memory")

    provedor = camada.dataProvider()
    feicao = QgsFeature()
    feicao.setGeometry(geometria_final)
    provedor.addFeature(feicao)
    camada.updateExtents()

    projeto.addMapLayer(camada)

    return camada


def _geometria_mascara(camada_mascara: QgsVectorLayer) -> Optional[QgsGeometry]:
    """Extrai a geometria única (dissolvida) da camada de máscara."""
    geometrias = [f.geometry() for f in camada_mascara.getFeatures() if not f.geometry().isEmpty()]

    if not geometrias:
        return None

    geometria = geometrias[0]
    for outra in geometrias[1:]:
        geometria = geometria.combine(outra)

    return geometria


def recortar_camadas(
    projeto: QgsProject,
    camada_mascara: QgsVectorLayer,
    nomes_camadas: Iterable[str],
) -> None:
    """Filtra (via setSubsetString) cada camada listada em `nomes_camadas`,
    mantendo apenas as feições que intersectam a área de estudo.

    Melhoria de performance em relação à macro original: em vez de testar
    `geometria.intersects()` feição a feição contra o polígono do estado
    inteiro (o que, para camadas grandes de rios/estradas, é caro), um
    QgsSpatialIndex é construído primeiro para pré-filtrar candidatas pela
    caixa envolvente (bounding box) antes do teste geométrico exato.
    """
    geometria_mascara = _geometria_mascara(camada_mascara)

    if geometria_mascara is None:
        return

    for nome_camada in nomes_camadas:
        camadas = projeto.mapLayersByName(nome_camada)

        if not camadas:
            continue

        camada = camadas[0]

        try:
            # Reprojeta a máscara para o SRC da camada-alvo, se necessário.
            geometria_no_crs_alvo = QgsGeometry(geometria_mascara)
            if camada.crs().isValid() and camada.crs() != projeto.crs():
                transformador = QgsCoordinateTransform(projeto.crs(), camada.crs(), projeto)
                geometria_no_crs_alvo.transform(transformador)

            indice = QgsSpatialIndex(camada.getFeatures())
            candidatos = indice.intersects(geometria_no_crs_alvo.boundingBox())

            ids = []
            for fid in candidatos:
                feicao = camada.getFeature(fid)
                if feicao.geometry().intersects(geometria_no_crs_alvo):
                    ids.append(fid)

            if ids:
                camada.setSubsetString(f'"fid" IN ({",".join(map(str, ids))})')
            else:
                camada.setSubsetString("1=0")

        except Exception:
            # Uma camada com problema não deve interromper o recorte das
            # demais camadas da lista.
            continue


def remover_feicoes_fora_da_area(
    projeto: QgsProject,
    camada_mascara: QgsVectorLayer,
    pasta_projeto: str,
) -> int:
    """Remove feições externas somente das bases copiadas para o projeto.

    A camada DEFINIR_AREA, a AREA_ESTUDO e qualquer fonte externa à pasta do
    projeto são preservadas para não alterar dados originais ou de rede.
    """
    geometria_mascara = _geometria_mascara(camada_mascara)
    if geometria_mascara is None:
        return 0

    pasta_normalizada = os.path.normcase(os.path.abspath(pasta_projeto))
    nomes_preservados = {
        constants.AREA_ESTUDO_LAYER_NAME,
        constants.LAYER_DEFINIR_AREA,
        "DEFINIR_AREA",
    }
    total_removido = 0

    for camada in list(projeto.mapLayers().values()):
        if not isinstance(camada, QgsVectorLayer):
            continue
        if camada.name() in nomes_preservados:
            continue

        caminho_fonte = camada.source().split("|", 1)[0]
        fonte_normalizada = os.path.normcase(os.path.abspath(caminho_fonte))
        if not fonte_normalizada.startswith(pasta_normalizada + os.sep):
            continue

        try:
            geometria_no_crs_alvo = QgsGeometry(geometria_mascara)
            if camada.crs().isValid() and camada.crs() != projeto.crs():
                transformador = QgsCoordinateTransform(
                    projeto.crs(), camada.crs(), projeto
                )
                geometria_no_crs_alvo.transform(transformador)

            camada.setSubsetString("")
            ids_remover = [
                feicao.id()
                for feicao in camada.getFeatures()
                if feicao.geometry().isEmpty()
                or not feicao.geometry().intersects(geometria_no_crs_alvo)
            ]

            if not ids_remover or not camada.startEditing():
                continue

            if camada.deleteFeatures(ids_remover) and camada.commitChanges():
                total_removido += len(ids_remover)
            else:
                camada.rollBack()
        except Exception:
            if camada.isEditable():
                camada.rollBack()

    return total_removido
