# -*- coding: utf-8 -*-
"""
core/variaveis.py
==================
Leitura, escrita e limpeza das variáveis de projeto (QgsExpressionContextUtils)
usadas pelo STL-TEMPLATE. Concentrar essas operações aqui elimina a
duplicação que existia na macro original (o mesmo bloco de `setProjectVariable`
para 'tipo_projeto' e para os laços de limpeza de variáveis apareciam
repetidos duas vezes seguidas — aparentemente um copiar/colar acidental).
"""

from typing import Optional

from qgis.core import QgsProject

from ..utils import constants, helpers


def salvar_variaveis(
    projeto: QgsProject,
    *,
    obra: str,
    tipo_projeto: str,
    zona_utm: str,
    sigla_projetista: str,
    sigla_verificacao: str,
    escala_001: int,
    escala_002: int,
    escala_003: int,
    municipio: Optional[str],
    uf: Optional[str],
    coord_x: float,
    coord_y: float,
) -> None:
    """Grava, em uma única chamada, todas as variáveis de projeto geradas
    ao concluir a configuração do STL-TEMPLATE.

    Observação sobre compatibilidade: a macro original gravava a UF do
    empreendimento na variável de projeto `area_estudo` (nome pouco claro,
    provavelmente um erro de nomenclatura do autor original). Para não
    quebrar layouts existentes que já referenciam `@area_estudo`, o valor
    continua sendo gravado ali, mas agora também é gravado com o nome
    correto `uf`, para uso em novos layouts.
    """
    helpers.definir_variaveis_projeto(projeto, {
        "obra": obra,
        "tipo_projeto": tipo_projeto,
        "zona_utm": zona_utm,
        "sigla_projetista": sigla_projetista,
        "sigla_verificacao": sigla_verificacao,
        "layout_001": escala_001,
        "layout_002": escala_002,
        "layout_003": escala_003,
        "municipio": municipio or "",
        "area_estudo": uf or "",  # compatibilidade com layouts existentes
        "uf": uf or "",
        "coord_x": coord_x,
        "coord_y": coord_y,
    })


def carregar_variaveis(projeto: QgsProject) -> dict:
    """Lê as variáveis de projeto relevantes para pré-preencher a UI
    (escalas dos 3 layouts) ao reabrir a janela de configuração.
    """
    return {
        "layout_001": helpers.obter_variavel_projeto(projeto, "layout_001", None),
        "layout_002": helpers.obter_variavel_projeto(projeto, "layout_002", None),
        "layout_003": helpers.obter_variavel_projeto(projeto, "layout_003", None),
        "obra": helpers.obter_variavel_projeto(projeto, "obra", ""),
        "tipo_projeto": helpers.obter_variavel_projeto(projeto, "tipo_projeto", ""),
        "zona_utm": helpers.obter_variavel_projeto(projeto, "zona_utm", "AUTOMÁTICO"),
        "sigla_projetista": helpers.obter_variavel_projeto(projeto, "sigla_projetista", ""),
        "sigla_verificacao": helpers.obter_variavel_projeto(projeto, "sigla_verificacao", ""),
    }


def limpar_variaveis(projeto: QgsProject) -> None:
    """Zera todas as variáveis de projeto gerenciadas pelo plugin.

    Na macro original esse laço aparecia duplicado (dois `for` idênticos
    em sequência); aqui existe uma única implementação.
    """
    helpers.definir_variaveis_projeto(
        projeto,
        {nome: "" for nome in constants.VARIAVEIS_PROJETO},
    )
