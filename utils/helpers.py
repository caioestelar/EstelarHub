# -*- coding: utf-8 -*-
"""
utils/helpers.py
=================
Funções utilitárias puras (sem estado, sem UI) reaproveitadas por vários
módulos do plugin. Centralizar essas pequenas funções elimina a duplicação
que existia na macro original (o mesmo cálculo de escala e a mesma
formatação de string apareciam repetidos em pelo menos dois lugares).
"""

from qgis.core import (
    QgsCoordinateReferenceSystem,
    QgsCoordinateTransform,
    QgsExpressionContextUtils,
    QgsPointXY,
    QgsProject,
)


def formatar_escala(escala: int) -> str:
    """Formata um inteiro de escala como '1:500.000' (separador BR)."""
    return f"Escala: 1:{int(escala):,}".replace(",", ".")


def calcular_escala(largura_atual: float, escala_referencia: int, largura_referencia: float) -> int:
    """Calcula a escala final a partir da largura do retângulo de preview.

    Reproduz a fórmula original: escala = escala_referencia * largura / largura_referencia
    """
    if not largura_referencia:
        return 0
    return round(escala_referencia * largura_atual / largura_referencia)


def largura_a_partir_da_escala(escala_salva, escala_referencia: int, largura_referencia: float) -> float:
    """Operação inversa de `calcular_escala`: a partir de uma escala salva
    como variável de projeto, recupera a largura que deve ser exibida no
    QDoubleSpinBox ao reabrir a janela.
    """
    try:
        if escala_salva:
            return float(escala_salva) * largura_referencia / escala_referencia
    except (TypeError, ValueError):
        pass
    return largura_referencia


def obter_variavel_projeto(projeto: QgsProject, nome: str, padrao=""):
    """Wrapper seguro para leitura de variável de projeto."""
    valor = QgsExpressionContextUtils.projectScope(projeto).variable(nome)
    return valor if valor not in (None, "") else padrao


def definir_variavel_projeto(projeto: QgsProject, nome: str, valor) -> None:
    """Wrapper para escrita de variável de projeto (facilita mocks em teste)."""
    QgsExpressionContextUtils.setProjectVariable(projeto, nome, valor)


def definir_variaveis_projeto(projeto: QgsProject, valores: dict) -> None:
    """Escreve várias variáveis de projeto de uma vez, evitando blocos
    repetidos de `setProjectVariable` como havia na macro original.
    """
    for nome, valor in valores.items():
        QgsExpressionContextUtils.setProjectVariable(projeto, nome, valor)


def transformar_ponto(ponto: QgsPointXY, crs_origem: QgsCoordinateReferenceSystem,
                       crs_destino: QgsCoordinateReferenceSystem) -> QgsPointXY:
    """Reprojeta um ponto entre dois SRCs.

    Correção de um bug da macro original: as variáveis de projeto
    `coord_x`/`coord_y` eram gravadas com as coordenadas no SRC do KML
    (geralmente graus, WGS84), mesmo depois do SRC do projeto ser alterado
    para uma projeção UTM métrica — deixando a variável inconsistente com
    o restante do projeto. Aqui o ponto é sempre reprojetado para o SRC
    final do projeto antes de ser salvo.
    """
    if crs_origem == crs_destino:
        return QgsPointXY(ponto)
    transformador = QgsCoordinateTransform(crs_origem, crs_destino, QgsProject.instance())
    return transformador.transform(ponto)


def nome_do_arquivo(caminho: str) -> str:
    """Retorna apenas o nome do arquivo a partir de um caminho completo."""
    return caminho.replace("\\", "/").split("/")[-1]
