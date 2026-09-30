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

from qgis.PyQt.QtCore import QEvent, QObject, QPoint, QTimer, Qt
from qgis.PyQt.QtGui import QColor
from qgis.PyQt.QtWidgets import QLabel
from qgis.core import (
    QgsCoordinateReferenceSystem,
    QgsCoordinateTransform,
    QgsGeometry,
    QgsPointXY,
    QgsProject,
    QgsRectangle,
    QgsVectorLayer,
    QgsWkbTypes,
)
from qgis.gui import QgsMapToolIdentify, QgsRubberBand

from . import kml, municipios
from ..utils import constants, helpers


def zoomar_brasil(dlg) -> None:
    """Enquadra o Brasil no CRS atual do canvas sem ampliar para o mundo."""
    canvas = dlg.canvas_preview
    extensao_brasil = QgsRectangle(-74.0, -34.0, -34.0, 5.5)

    try:
        destino = canvas.destinationCrs()
    except AttributeError:
        destino = canvas.mapSettings().destinationCrs()

    origem = QgsCoordinateReferenceSystem("EPSG:4326")
    if destino.isValid() and destino != origem:
        transformador = QgsCoordinateTransform(
            origem,
            destino,
            QgsProject.instance(),
        )
        extensao_brasil = transformador.transformBoundingBox(extensao_brasil)

    canvas.setExtent(extensao_brasil)
    canvas.refresh()


def montar_texto_preview(dados: dict) -> str:
    """Monta o texto do label de preview a partir de um dicionário de
    dados, em vez de editar o texto anterior por índice de linha (como
    fazia a macro original — uma técnica frágil: bastava o texto inicial
    mudar de formato para o índice `linhas[2]`/`linhas[3]` apontar para a
    linha errada).
    """
    return (
        "PREVIEW DO EMPREENDIMENTO\n\n"
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


def _reposicionar_rotulos_preview(dlg) -> None:
    sincronizador = getattr(dlg, "_preview_label_pan_sync", None)
    if sincronizador is not None and sincronizador.pan_start is not None:
        return

    canvas = dlg.canvas_preview
    for label in getattr(dlg, "_rotulos_preview", {}).values():
        ponto = getattr(label, "_preview_ponto_mapa", None)
        if ponto is None:
            continue
        try:
            pixel = _pixel_do_mapa(canvas, ponto)
        except Exception:
            continue
        label.move(round(pixel.x()) + 6, round(pixel.y()) + 6)
        label.raise_()


class PreviewLabelPanSync(QObject):
    def __init__(self, dlg, parent=None):
        super().__init__(parent)
        self.dlg = dlg
        self.pan_start = None
        self.label_positions = {}

    @staticmethod
    def _event_position(event):
        if hasattr(event, "position"):
            return event.position().toPoint()
        return event.pos()

    def eventFilter(self, watched, event):
        if event.type() == QEvent.Type.MouseButtonPress and event.button() == Qt.MouseButton.MiddleButton:
            self.pan_start = self._event_position(event)
            self.label_positions = {
                nome: label.pos()
                for nome, label in getattr(self.dlg, "_rotulos_preview", {}).items()
            }
        elif (
            event.type() == QEvent.Type.MouseMove
            and self.pan_start is not None
            and event.buttons() & Qt.MouseButton.MiddleButton
        ):
            deslocamento = self._event_position(event) - self.pan_start
            for nome, label in getattr(self.dlg, "_rotulos_preview", {}).items():
                posicao_inicial = self.label_positions.get(nome)
                if posicao_inicial is not None:
                    label.move(posicao_inicial + deslocamento)
        elif event.type() == QEvent.Type.MouseButtonRelease and event.button() == Qt.MouseButton.MiddleButton:
            self.pan_start = None
            QTimer.singleShot(0, lambda: _reposicionar_rotulos_preview(self.dlg))
        return False


def _conectar_atualizacao_rotulos(dlg) -> None:
    if getattr(dlg, "_preview_rotulos_conectados", False):
        return

    canvas = dlg.canvas_preview
    canvas.extentsChanged.connect(
        lambda *_args: _reposicionar_rotulos_preview(dlg)
    )
    sinal_render = getattr(canvas, "mapCanvasRefreshed", None)
    if sinal_render is not None:
        sinal_render.connect(
            lambda *_args: _reposicionar_rotulos_preview(dlg)
        )
    sincronizador = PreviewLabelPanSync(dlg, canvas.viewport())
    canvas.viewport().installEventFilter(sincronizador)
    dlg._preview_label_pan_sync = sincronizador
    dlg._preview_rotulos_conectados = True


def _remover_aviso_preview(dlg) -> None:
    aviso = getattr(dlg, "_aviso_preview", None)
    if aviso is not None:
        try:
            aviso.deleteLater()
        except Exception:
            pass
    dlg._aviso_preview = None


class PreviewMoveTool(QgsMapToolIdentify):
    """Permite arrastar o centro do preview na tela sem mexer no mapa real."""

    def __init__(self, canvas, dlg):
        super().__init__(canvas)
        self.dlg = dlg
        self._arrastando = False
        self._centro_original = None
        self._coordenada_original = None
        self._centros_originais = {}

    def setCursor(self, cursor):
        try:
            self.canvas().setCursor(cursor)
        except Exception:
            pass

    def _pixel_para_coordenada(self, pos):
        canvas = self.canvas()
        transform = getattr(canvas, "getCoordinateTransform", None)
        if callable(transform):
            try:
                return transform().toMapCoordinates(pos)
            except Exception:
                pass

        if hasattr(canvas, "mapToPixel"):
            try:
                return canvas.mapToPixel(pos)
            except Exception:
                pass

        raise AttributeError("Nenhuma API compatível de conversão pixel -> coordenada foi encontrada no QGIS atual.")

    def canvasPressEvent(self, event):
        if event.button() != Qt.MouseButton.LeftButton:
            return
        if not hasattr(self.dlg, "camada_preview"):
            return

        self._arrastando = True
        self.setCursor(Qt.CursorShape.ClosedHandCursor)
        self._centro_original = getattr(
            self.dlg,
            "_preview_centro",
            self.dlg.camada_preview.extent().center(),
        )
        self._coordenada_original = self._pixel_para_coordenada(event.pos())
        self._centros_originais = dict(getattr(self.dlg, "_preview_centros", {}))

    def canvasMoveEvent(self, event):
        if not self._arrastando:
            self.setCursor(Qt.CursorShape.OpenHandCursor)
            return

        coordenada_atual = self._pixel_para_coordenada(event.pos())
        delta_x = coordenada_atual.x() - self._coordenada_original.x()
        delta_y = coordenada_atual.y() - self._coordenada_original.y()

        for chave in ("001", "002", "003"):
            if self.dlg._layout_locked.get(chave, False):
                continue

            centro_original = self._centros_originais.get(chave, self._centro_original)
            novo_centro = QgsPointXY(
                centro_original.x() + delta_x,
                centro_original.y() + delta_y,
            )
            self.dlg._preview_centros[chave] = novo_centro

        if not any(not self.dlg._layout_locked.get(chave, False) for chave in ("001", "002", "003")):
            self.dlg._preview_centro = self._centro_original
        else:
            self.dlg._preview_centro = self.dlg._preview_centros["001"]

        desenhar_retangulos(self.dlg)

    def canvasReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._arrastando = False
            self._centro_original = None
            self._coordenada_original = None
            self.setCursor(Qt.CursorShape.OpenHandCursor)

    def canvasLeaveEvent(self, event):
        if not self._arrastando:
            self.setCursor(Qt.CursorShape.ArrowCursor)


def _pixel_do_mapa(canvas, ponto: QgsPointXY):
    configuracao = getattr(canvas, "mapSettings", lambda: None)()
    if configuracao is not None and hasattr(configuracao, "mapToPixel"):
        try:
            transformacao = configuracao.mapToPixel()
            if hasattr(transformacao, "transform"):
                return transformacao.transform(ponto)
        except TypeError:
            return configuracao.mapToPixel(ponto)
    if hasattr(canvas, "getCoordinateTransform"):
        try:
            transform = canvas.getCoordinateTransform()
            return transform.transform(ponto)
        except Exception:
            pass
    raise AttributeError("QgsMapCanvas não oferece conversão de coordenadas para pixel nesta API do QGIS.")


def _adicionar_rotulo_preview(dlg, nome_layout: str, retangulo: QgsRectangle) -> None:
    canvas = dlg.canvas_preview
    ponto = QgsPointXY(retangulo.xMinimum(), retangulo.yMaximum())
    _conectar_atualizacao_rotulos(dlg)
    try:
        pixel = _pixel_do_mapa(canvas, ponto)
    except Exception:
        return

    cores_layout = {
        "LAYOUT 1": "#ec008b",
        "LAYOUT 2": "#f79138",
        "LAYOUT 3": "#00c4d2",
    }
    cor_layout = cores_layout.get(nome_layout, "#1e49b1")
    tamanho_fonte = "5pt" if nome_layout == "LAYOUT 3" else "6.5pt"
    espacamento = "1px 2px" if nome_layout == "LAYOUT 3" else "1px 4px"
    label = QLabel(nome_layout, canvas.viewport())
    label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
    label.setStyleSheet(
        "QLabel {"
        "  color: #17212b;"
        "  background-color: rgba(255,255,255,235);"
        f"  border: 1px solid {cor_layout};"
        "  border-radius: 4px;"
        f"  padding: {espacamento};"
        f"  font-size: {tamanho_fonte};"
        "  font-weight: 700;"
        "  qproperty-alignment: AlignCenter;"
        "}"
    )
    label.adjustSize()
    label._preview_ponto_mapa = ponto
    label.move(round(pixel.x()) + 6, round(pixel.y()) + 6)
    label.raise_()
    label.show()
    QTimer.singleShot(0, lambda: _reposicionar_rotulos_preview(dlg))

    rotulos = getattr(dlg, "_rotulos_preview", {})
    rotulos[nome_layout] = label
    dlg._rotulos_preview = rotulos


def _atualizar_aviso_preview(dlg, retangulos):
    _remover_aviso_preview(dlg)
    if not hasattr(dlg, "camada_preview"):
        return

    try:
        feicao = next(dlg.camada_preview.getFeatures(), None)
    except Exception:
        return
    if feicao is None:
        return

    ponto = feicao.geometry().centroid().asPoint()
    if any(retangulo.contains(ponto) for retangulo in retangulos):
        return

    aviso = QLabel("ATENÇÃO  |  A usina está fora dos previews.", dlg.canvas_preview.viewport())
    aviso.setObjectName("previewWarning")
    aviso.setStyleSheet(
        "QLabel {"
        "  color: #7c2d12;"
        "  background: rgba(255, 237, 213, 200);"
        "  border: 1px solid rgba(251, 146, 60, 180);"
        "  border-radius: 8px;"
        "  padding: 6px 10px;"
        "  font-size: 11px;"
        "  font-weight: 700;"
        "  qproperty-alignment: AlignCenter;"
        "}"
    )
    aviso.adjustSize()
    aviso.move(12, 12)
    aviso.raise_()
    aviso.show()
    dlg._aviso_preview = aviso


def desenhar_retangulos(dlg) -> None:
    """Desenha os 3 retângulos de preview (vermelho/azul/verde), centrados
    no centróide da camada importada, e atualiza os labels de escala.
    """
    _remover_rubber_band(dlg, "rb_500")
    _remover_rubber_band(dlg, "rb_100")
    _remover_rubber_band(dlg, "rb_25")
    _remover_rotulos_preview(dlg)
    _remover_aviso_preview(dlg)

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

    if not hasattr(dlg, "_preview_centro"):
        dlg._preview_centro = dlg.camada_preview.extent().center()
    if not hasattr(dlg, "_preview_centros"):
        dlg._preview_centros = {"001": dlg._preview_centro, "002": dlg._preview_centro, "003": dlg._preview_centro}
    for chave in ("001", "002", "003"):
        if dlg._preview_centros.get(chave) is None:
            dlg._preview_centros[chave] = dlg._preview_centro

    proporcao = constants.PROPORCAO_RETANGULO

    configuracoes = [
        ("rb_500", largura_001, "001", QColor(236, 0, 139, 180), "LAYOUT 1"),
        ("rb_100", largura_002, "002", QColor(247, 145, 56, 180), "LAYOUT 2"),
        ("rb_25", largura_003, "003", QColor(0, 196, 210, 170), "LAYOUT 3"),
    ]

    retangulos_preview = []
    for atributo_rb, largura, chave_escala, cor, nome_layout in configuracoes:
        altura = largura / proporcao
        centro = dlg._preview_centros.get(chave_escala, dlg._preview_centro)

        rb = QgsRubberBand(dlg.canvas_preview, QgsWkbTypes.PolygonGeometry)

        retangulo = QgsRectangle(
            centro.x() - largura, centro.y() - altura,
            centro.x() + largura, centro.y() + altura,
        )
        retangulos_preview.append(retangulo)

        rb.setToGeometry(QgsGeometry.fromRect(retangulo), None)
        rb.setStrokeColor(cor)
        rb.setFillColor(QColor(cor.red(), cor.green(), cor.blue(), 25))
        rb.setWidth(2)
        rb.setLineStyle(Qt.PenStyle.DashLine)

        setattr(dlg, atributo_rb, rb)
        _adicionar_rotulo_preview(dlg, nome_layout, retangulo)

    _atualizar_aviso_preview(dlg, retangulos_preview)
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
