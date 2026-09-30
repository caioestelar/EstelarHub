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

from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QColor
from qgis.PyQt.QtWidgets import QLabel
from qgis.core import (
    QgsGeometry,
    QgsPointXY,
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


def _remover_rotulos_preview(dlg) -> None:
    rotulos = getattr(dlg, "_rotulos_preview", {})
    for label in list(rotulos.values()):
        try:
            label.deleteLater()
        except Exception:
            pass
    dlg._rotulos_preview = {}


def _pixel_do_mapa(canvas, ponto: QgsPointXY):
    configuracao = getattr(canvas, "mapSettings", lambda: None)()
    if configuracao is not None and hasattr(configuracao, "mapToPixel"):
        return configuracao.mapToPixel(ponto)
    if hasattr(canvas, "mapToPixel"):
        return canvas.mapToPixel(ponto)
    raise AttributeError("QgsMapCanvas não oferece conversão de coordenadas para pixel nesta API do QGIS.")


def _adicionar_rotulo_preview(dlg, nome_layout: str, retangulo: QgsRectangle) -> None:
    canvas = dlg.canvas_preview
    ponto = QgsPointXY(retangulo.xMinimum(), retangulo.yMaximum())
    try:
        pixel = _pixel_do_mapa(canvas, ponto)
    except Exception:
        return

    label = QLabel(nome_layout, canvas.viewport())
    label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
    label.setStyleSheet(
        "QLabel {"
        "  color: #111827;"
        "  background-color: rgba(255,255,255,90);"
        "  border: 1px solid rgba(17,24,39,60);"
        "  border-radius: 5px;"
        "  padding: 2px 6px;"
        "  font-size: 9px;"
        "  font-weight: 600;"
        "  qproperty-alignment: AlignCenter;"
        "}"
    )
    label.adjustSize()
    label.move(pixel.x() + 8, pixel.y() + 8)
    label.raise_()
    label.show()

    rotulos = getattr(dlg, "_rotulos_preview", {})
    rotulos[nome_layout] = label
    dlg._rotulos_preview = rotulos


def desenhar_retangulos(dlg) -> None:
    """Desenha os 3 retângulos de preview (vermelho/azul/verde), centrados
    no centróide da camada importada, e atualiza os labels de escala.
    """
    _remover_rubber_band(dlg, "rb_500")
    _remover_rubber_band(dlg, "rb_100")
    _remover_rubber_band(dlg, "rb_25")
    _remover_rotulos_preview(dlg)

    if not hasattr(dlg, "camada_preview"):
        return

    if hasattr(dlg, "spin_001") and hasattr(dlg, "spin_002") and hasattr(dlg, "spin_003"):
        largura_001 = dlg.spin_001.value()
        largura_002 = min(dlg.spin_002.value(), largura_001)
        largura_003 = min(dlg.spin_003.value(), largura_002)
        dlg.spin_002.setValue(largura_002)
        dlg.spin_003.setValue(largura_003)
    else:
        largura_001 = getattr(dlg, "spin_001", None).value() if hasattr(dlg, "spin_001") else 0
        largura_002 = getattr(dlg, "spin_002", None).value() if hasattr(dlg, "spin_002") else 0
        largura_003 = getattr(dlg, "spin_003", None).value() if hasattr(dlg, "spin_003") else 0

    centro = dlg.camada_preview.extent().center()
    proporcao = constants.PROPORCAO_RETANGULO

    configuracoes = [
        ("rb_500", largura_001, "001", QColor(236, 0, 139, 180), "LAYOUT 1"),
        ("rb_100", largura_002, "002", QColor(247, 145, 56, 180), "LAYOUT 2"),
        ("rb_25", largura_003, "003", QColor(0, 196, 210, 170), "LAYOUT 3"),
    ]

    for atributo_rb, largura, chave_escala, cor, nome_layout in configuracoes:
        altura = largura / proporcao

        rb = QgsRubberBand(dlg.canvas_preview, QgsWkbTypes.PolygonGeometry)

        retangulo = QgsRectangle(
            centro.x() - largura, centro.y() - altura,
            centro.x() + largura, centro.y() + altura,
        )

        rb.setToGeometry(QgsGeometry.fromRect(retangulo), None)
        rb.setStrokeColor(cor)
        rb.setFillColor(QColor(cor.red(), cor.green(), cor.blue(), 25))
        rb.setWidth(2)
        rb.setLineStyle(Qt.PenStyle.DashLine)

        setattr(dlg, atributo_rb, rb)
        _adicionar_rotulo_preview(dlg, nome_layout, retangulo)

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
