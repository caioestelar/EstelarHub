# -*- coding: utf-8 -*-
"""
core/preview.py
================
Lógica do mapa de preview exibido dentro da JanelaProjeto: desenho dos 3
retângulos (QgsRubberBand) vermelho/azul/verde e atualização do texto e do
QgsMapCanvas quando o usuário seleciona um KML/KMZ ou altera obra/tipo.

Estas funções recebem o diálogo (`dlg`) como parâmetro e leem/escrevem
atributos nele (`dlg.rb_500`, `dlg.camada_preview`, etc.) — o mesmo padrão
de estado usado na macro original, só que agora isolado da construção de
widgets, o que facilita testar a lógica sem precisar instanciar toda a UI.
"""

from qgis.PyQt.QtGui import QColor
from qgis.core import (
    QgsGeometry,
    QgsProject,
    QgsRectangle,
    QgsVectorLayer,
    QgsWkbTypes,
)
from qgis.gui import QgsRubberBand

from . import kml, municipios
from ..utils import constants, helpers


def montar_texto_preview(dados: dict) -> str:
    """Monta o texto do label de preview a partir de um dicionário de
    dados, em vez de editar o texto anterior por índice de linha (como
    fazia a macro original — uma técnica frágil: bastava o texto inicial
    mudar de formato para o índice `linhas[2]`/`linhas[3]` apontar para a
    linha errada).
    """
    return (
        "📋 PREVIEW DO EMPREENDIMENTO\n\n"
        f"Obra: {dados.get('obra', '-')}\n"
        f"Tipo: {dados.get('tipo', '-')}\n"
        f"Município: {dados.get('municipio', '-')}\n"
        f"UF: {dados.get('uf', '-')}\n"
        f"Zona UTM: {dados.get('zona_utm', '-')}\n"
        f"Área: {dados.get('area', '-')}"
    )


def atualizar_preview(dlg) -> None:
    """Atualiza apenas os campos 'Obra' e 'Tipo' do preview (chamado ao
    trocar os combos de obra/tipo de projeto).
    """
    dlg._preview_dados["obra"] = (
        dlg.cmb_obra.currentData()
        or dlg.cmb_obra.currentText().strip()
        or "-"
    )
    dlg._preview_dados["tipo"] = dlg.cmb_tipo.currentText()
    dlg.lbl_preview.setText(montar_texto_preview(dlg._preview_dados))


def carregar_arquivo_preview(dlg, caminho: str) -> None:
    """Carrega o KML/KMZ selecionado no mapa de preview: adiciona a camada
    do empreendimento e o raster de fundo do mapa ao canvas, calcula
    município/UF/zona UTM/área e redesenha os retângulos de escala.
    """
    dlg.camada_preview = kml.importar_kml_ou_kmz(caminho, "preview")

    estilo = getattr(dlg, "_estilo_mapa", "satelite")
    camada_fundo = kml.obter_camada_fundo(estilo)

    if hasattr(dlg, "camada_base") and dlg.camada_base is not None:
        try:
            QgsProject.instance().removeMapLayer(dlg.camada_base.id())
        except Exception:
            pass

    # As camadas de preview são adicionadas ao registro do projeto sem
    # aparecer na árvore de camadas (addToLegend=False), pois servem
    # apenas ao QgsMapCanvas interno do diálogo.
    QgsProject.instance().addMapLayer(camada_fundo, False)
    QgsProject.instance().addMapLayer(dlg.camada_preview, False)
    dlg.camada_base = camada_fundo

    dlg.canvas_preview.setDestinationCrs(dlg.camada_preview.crs())
    dlg.canvas_preview.setLayers([dlg.camada_preview, dlg.camada_base])

    extensao = dlg.camada_preview.extent()
    extensao.scale(5.0)
    dlg.canvas_preview.setExtent(extensao)
    dlg.canvas_preview.zoomToFullExtent()
    dlg.canvas_preview.refresh()

    feicao = next(dlg.camada_preview.getFeatures(), None)

    if feicao is None:
        return

    geom = feicao.geometry()
    ponto = geom.centroid().asPoint()

    zona_utm = municipios.calcular_zona_utm(ponto)

    try:
        area_ha = round(geom.area() / 10000, 2)
    except Exception:
        area_ha = 0

    municipio, uf = municipios.descobrir_municipio(QgsProject.instance(), geom)

    dlg._preview_dados.update({
        "obra": (
            dlg.cmb_obra.currentData()
            or dlg.cmb_obra.currentText().strip()
            or "-"
        ),
        "tipo": dlg.cmb_tipo.currentText(),
        "municipio": municipio or "-",
        "uf": uf or "-",
        "zona_utm": zona_utm,
        "area": f"{area_ha:,.2f} ha",
    })

    dlg.lbl_preview.setText(montar_texto_preview(dlg._preview_dados))

    desenhar_retangulos(dlg)


def _remover_rubber_band(dlg, atributo: str) -> None:
    rb = getattr(dlg, atributo, None)
    if rb is not None:
        dlg.canvas_preview.scene().removeItem(rb)


def desenhar_retangulos(dlg) -> None:
    """Desenha os 3 retângulos de preview (vermelho/azul/verde), centrados
    no centróide da camada importada, e atualiza os labels de escala.
    """
    _remover_rubber_band(dlg, "rb_500")
    _remover_rubber_band(dlg, "rb_100")
    _remover_rubber_band(dlg, "rb_25")

    if not hasattr(dlg, "camada_preview"):
        return

    centro = dlg.camada_preview.extent().center()
    proporcao = constants.PROPORCAO_RETANGULO

    configuracoes = [
        ("rb_500", dlg.spin_001, "001", "red"),
        ("rb_100", dlg.spin_002, "002", "blue"),
        ("rb_25", dlg.spin_003, "003", "green"),
    ]

    for atributo_rb, spin, chave_escala, cor in configuracoes:
        largura = spin.value()
        altura = largura / proporcao

        rb = QgsRubberBand(dlg.canvas_preview, QgsWkbTypes.PolygonGeometry)

        retangulo = QgsRectangle(
            centro.x() - largura, centro.y() - altura,
            centro.x() + largura, centro.y() + altura,
        )

        rb.setToGeometry(QgsGeometry.fromRect(retangulo), None)
        rb.setStrokeColor(QColor(cor))
        rb.setWidth(2)

        setattr(dlg, atributo_rb, rb)

    _atualizar_labels_escala(dlg)


def _atualizar_labels_escala(dlg) -> None:
    ref_001 = constants.ESCALAS_REFERENCIA["001"]
    ref_002 = constants.ESCALAS_REFERENCIA["002"]
    ref_003 = constants.ESCALAS_REFERENCIA["003"]

    escala_001 = helpers.calcular_escala(dlg.spin_001.value(), ref_001["escala_referencia"], ref_001["largura_referencia"])
    escala_002 = helpers.calcular_escala(dlg.spin_002.value(), ref_002["escala_referencia"], ref_002["largura_referencia"])
    escala_003 = helpers.calcular_escala(dlg.spin_003.value(), ref_003["escala_referencia"], ref_003["largura_referencia"])

    dlg.lbl_001.setText(helpers.formatar_escala(escala_001))
    dlg.lbl_002.setText(helpers.formatar_escala(escala_002))
    dlg.lbl_003.setText(helpers.formatar_escala(escala_003))
