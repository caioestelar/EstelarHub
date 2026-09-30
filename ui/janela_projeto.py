# -*- coding: utf-8 -*-
"""
ui/janela_projeto.py
=====================
Janela de configuração do STL-TEMPLATE (antiga classe `JanelaProjeto`
definida dentro da macro `openProject`).

Esta classe é responsável exclusivamente pela construção dos widgets e
pela ligação (connect) dos eventos de interface. Toda a lógica de negócio
foi extraída para o pacote `core` (importação de KML, descoberta de
município/UF, cálculo de escala, geração do projeto etc.), seguindo o
princípio de separação de responsabilidades pedido na reestruturação do
plugin.
"""

from qgis.PyQt.QtCore import (
    QPropertyAnimation,
    QEasingCurve,
    QSequentialAnimationGroup,
    QSettings,
    QSize,
    QTimer,
    Qt,
)
from qgis.PyQt.QtGui import QColor, QIcon, QPainter, QPainterPath, QPen, QPixmap, QRadialGradient
from qgis.PyQt.QtWidgets import QGraphicsOpacityEffect
from qgis.PyQt.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QCompleter,
    QDialog,
    QDoubleSpinBox,
    QFileDialog,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QProgressBar,
    QScrollArea,
    QSizeGrip,
    QSlider,
    QStackedWidget,
    QTextEdit,
    QStyle,
    QToolButton,
    QVBoxLayout,
    QWidget,
    QTabWidget

)
from qgis.core import QgsCoordinateReferenceSystem, QgsProject
from qgis.gui import QgsMapCanvas

from ..core import kml as core_kml
from ..core import preview as core_preview
from ..core import projeto as core_projeto
from ..core import variaveis as core_variaveis
from ..utils import constants, helpers
import os
from qgis.PyQt.QtGui import QPalette


def criar_icone_estelar(nome: str, cor: str = "#00e5ff") -> QIcon:
    """Cria ícones vetoriais compactos, consistentes e independentes de fonte."""
    pixmap = QPixmap(24, 24)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setPen(QPen(QColor(cor), 1.8, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
    painter.setBrush(Qt.BrushStyle.NoBrush)

    if nome == "folder":
        painter.drawPath(_caminho_icone([(3, 7), (9, 7), (11, 9), (21, 9), (21, 19), (3, 19), (3, 7)]))
    elif nome == "folder_open":
        painter.drawPath(_caminho_icone([(3, 8), (9, 8), (11, 10), (20, 10), (18, 18), (4, 18), (3, 8)]))
    elif nome == "copy":
        painter.drawRect(8, 4, 11, 14)
        painter.drawRect(4, 8, 11, 12)
    elif nome == "file":
        painter.drawPath(_caminho_icone([(6, 3), (14, 3), (19, 8), (19, 21), (6, 21), (6, 3)]))
        painter.drawLine(14, 3, 14, 8)
        painter.drawLine(14, 8, 19, 8)
    elif nome == "project":
        painter.drawRoundedRect(3, 5, 18, 14, 3, 3)
        painter.drawEllipse(6, 10, 4, 4)
        painter.drawLine(12, 10, 18, 10)
        painter.drawLine(12, 14, 17, 14)
    elif nome == "layouts":
        painter.drawRect(3, 4, 8, 7)
        painter.drawRect(13, 4, 8, 7)
        painter.drawRect(3, 13, 8, 7)
        painter.drawRect(13, 13, 8, 7)
    elif nome == "summary":
        painter.drawLine(5, 19, 5, 12)
        painter.drawLine(12, 19, 12, 7)
        painter.drawLine(19, 19, 19, 4)
        painter.drawLine(3, 20, 21, 20)
    elif nome == "play":
        painter.drawPath(_caminho_icone([(8, 5), (19, 12), (8, 19), (8, 5)]))
    elif nome == "reset":
        painter.drawArc(4, 5, 16, 16, 45 * 16, 285 * 16)
        painter.drawLine(5, 5, 5, 10)
        painter.drawLine(5, 5, 10, 5)
    elif nome == "lock":
        painter.drawRoundedRect(6, 10, 12, 10, 2, 2)
        painter.drawArc(8, 4, 8, 11, 0, 180 * 16)
    elif nome == "unlock":
        painter.drawRoundedRect(6, 10, 12, 10, 2, 2)
        painter.drawArc(8, 4, 8, 11, 35 * 16, 145 * 16)
    elif nome == "close":
        painter.drawLine(6, 6, 18, 18)
        painter.drawLine(18, 6, 6, 18)
    elif nome == "minimize":
        painter.drawLine(6, 12, 18, 12)

    painter.end()
    return QIcon(pixmap)


def _caminho_icone(pontos):
    caminho = QPainterPath()
    caminho.moveTo(*pontos[0])
    for ponto in pontos[1:]:
        caminho.lineTo(*ponto)
    return caminho


class LuzAmbienteNeon(QWidget):
    """Camada decorativa leve, sem interação, para dar profundidade ao painel."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self._fase = 0.0
        self._timer = QTimer(self)
        self._timer.setInterval(45)
        self._timer.timeout.connect(self._avancar)
        self._timer.start()

    def _avancar(self):
        self._fase = (self._fase + 0.004) % 1.0
        self.update()

    def paintEvent(self, _event):
        if self.width() <= 0 or self.height() <= 0:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        largura = float(self.width())
        altura = float(self.height())
        deslocamento = (self._fase * 2.0) - 0.5

        pontos = [
            (largura * (0.15 + deslocamento * 0.22), altura * 0.20, (0, 229, 255)),
            (largura * (0.85 - deslocamento * 0.18), altura * 0.78, (8, 113, 180)),
        ]
        for x, y, cor in pontos:
            raio = max(largura, altura) * 0.42
            gradiente = QRadialGradient(x, y, raio)
            gradiente.setColorAt(0.0, QColor(cor[0], cor[1], cor[2], 18))
            gradiente.setColorAt(0.55, QColor(cor[0], cor[1], cor[2], 7))
            gradiente.setColorAt(1.0, QColor(cor[0], cor[1], cor[2], 0))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(gradiente)
            painter.drawRect(0, 0, self.width(), self.height())

        painter.end()


class AbaHover(QTabWidget):
    """QTabWidget com troca de conteúdo apenas por clique."""

    def __init__(self, parent=None):
        super().__init__(parent)


class BarraTitulo(QWidget):
    """Barra personalizada que permite arrastar a janela sem moldura."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._posicao_arraste = None

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            posicao_global = self._posicao_global(event)
            self._posicao_arraste = posicao_global - self.window().frameGeometry().topLeft()
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if (
            self._posicao_arraste is not None
            and event.buttons() & Qt.MouseButton.LeftButton
        ):
            self.window().move(self._posicao_global(event) - self._posicao_arraste)
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._posicao_arraste = None
            event.accept()
            return
        super().mouseReleaseEvent(event)

    @staticmethod
    def _posicao_global(event):
        if hasattr(event, "globalPosition"):
            return event.globalPosition().toPoint()
        return event.globalPos()


class JanelaProjeto(QDialog):
    """Diálogo de configuração do template de mapa de localização."""

    def _iniciar_animacoes_ambiente(self) -> None:
        self._luz_ambiente = LuzAmbienteNeon(self)
        self._luz_ambiente.setGeometry(self.rect())
        self._luz_ambiente.lower()

        efeito_botao = QGraphicsOpacityEffect(self.btn_ok)
        self.btn_ok.setGraphicsEffect(efeito_botao)
        entrada = QPropertyAnimation(efeito_botao, b"opacity", self)
        entrada.setDuration(1100)
        entrada.setStartValue(0.82)
        entrada.setEndValue(1.0)
        entrada.setEasingCurve(QEasingCurve.Type.InOutSine)

        saida = QPropertyAnimation(efeito_botao, b"opacity", self)
        saida.setDuration(1100)
        saida.setStartValue(1.0)
        saida.setEndValue(0.82)
        saida.setEasingCurve(QEasingCurve.Type.InOutSine)

        self._animacao_pulso = QSequentialAnimationGroup(self)
        self._animacao_pulso.addAnimation(entrada)
        self._animacao_pulso.addAnimation(saida)
        self._animacao_pulso.setLoopCount(-1)
        self._animacao_pulso.start()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        luz = getattr(self, "_luz_ambiente", None)
        if luz is not None:
            luz.setGeometry(self.rect())

    def _animar_aba(self, indice: int) -> None:
        if not hasattr(self, "_abas_principais"):
            return

        pagina = self._abas_principais.widget(indice)
        if pagina is None:
            return

        efeito = pagina.graphicsEffect()
        if not isinstance(efeito, QGraphicsOpacityEffect):
            efeito = QGraphicsOpacityEffect(pagina)
            pagina.setGraphicsEffect(efeito)

        efeito.setOpacity(0.35)
        animacao = QPropertyAnimation(efeito, b"opacity", pagina)
        animacao.setDuration(180)
        animacao.setStartValue(0.35)
        animacao.setEndValue(1.0)
        animacao.setEasingCurve(QEasingCurve.Type.OutCubic)
        animacao.start(QPropertyAnimation.DeletionPolicy.DeleteWhenStopped)
        self._animacao_aba = animacao
        self._animar_cartoes(pagina)

    def _animar_cartoes(self, pagina: QWidget) -> None:
        cartoes = pagina.findChildren(QGroupBox)
        if not cartoes:
            return

        sequencia = QSequentialAnimationGroup(self)
        for cartao in cartoes:
            efeito = cartao.graphicsEffect()
            if not isinstance(efeito, QGraphicsOpacityEffect):
                efeito = QGraphicsOpacityEffect(cartao)
                cartao.setGraphicsEffect(efeito)

            efeito.setOpacity(0.2)
            entrada = QPropertyAnimation(efeito, b"opacity", cartao)
            entrada.setDuration(170)
            entrada.setStartValue(0.2)
            entrada.setEndValue(1.0)
            entrada.setEasingCurve(QEasingCurve.Type.OutCubic)
            pausa = QPropertyAnimation(efeito, b"opacity", cartao)
            pausa.setDuration(45)
            pausa.setStartValue(1.0)
            pausa.setEndValue(1.0)
            sequencia.addAnimation(entrada)
            sequencia.addAnimation(pausa)

        sequencia.start(QPropertyAnimation.DeletionPolicy.DeleteWhenStopped)
        self._animacao_cartoes = sequencia

    def _icone_lock_layout(self, bloqueado: bool):
        return criar_icone_estelar("lock" if bloqueado else "unlock")

    def __init__(self, parent=None):
        super().__init__(parent)

        caminho_qss = os.path.join(
            os.path.dirname(__file__),
            "styles.qss"
        )

        with open(
            caminho_qss,
            "r",
            encoding="utf-8"
        ) as arquivo:

            self.setStyleSheet(
                arquivo.read()
            )

        self.arquivo = ""
        self.settings = QSettings()
        self._restaurando_estado = True
        self.ultimo_projeto_gerado = None
        self._preview_dados = {
            "obra": "-", "tipo": "-", "municipio": "-",
            "uf": "-", "zona_utm": "-", "area": "-",
        }
        self._estilo_mapa = self.settings.value("EstelarTemplate/ultimo_estilo_mapa", "satelite", type=str)
        self._presets = {
            "Padrão": {"tipo": "PCH", "zona": "AUTOMÁTICO"},
            "UHE": {"tipo": "UHE", "zona": "AUTOMÁTICO"},
            "CGH": {"tipo": "CGH", "zona": "AUTOMÁTICO"},
            "UFV": {"tipo": "UFV", "zona": "AUTOMÁTICO"},
            "Personalizado": {"tipo": "OUTRO", "zona": "AUTOMÁTICO"},
        }

        projeto = QgsProject.instance()
        self._variaveis_salvas = core_variaveis.carregar_variaveis(projeto)
        self._preview_centros = {"001": None, "002": None, "003": None}
        self._layout_locked = {"001": False, "002": False, "003": False}

        self.setWindowTitle(constants.NOME_PLUGIN)
        self.setWindowFlags(
            Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint
        )
        self.resize(1040, 600)
        self.setMinimumSize(840, 520)
        self.setMaximumSize(1400, 820)

        layout_principal = QVBoxLayout()
        layout_principal.setContentsMargins(10, 8, 10, 8)
        layout_principal.setSpacing(8)

        # Cabeçalho permanece fora das abas
        self._construir_cabecalho(layout_principal)

        # Conteúdo principal: navegação lateral + páginas empilhadas.
        aba_projeto = QWidget()
        layout_projeto = QVBoxLayout()
        layout_projeto.setContentsMargins(4, 4, 4, 4)
        layout_projeto.setSpacing(7)

        self._construir_campos_obra(layout_projeto)
        aba_projeto.setLayout(layout_projeto)

        scroll_projeto = QScrollArea()
        scroll_projeto.setWidgetResizable(True)
        scroll_projeto.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_projeto.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_projeto.setWidget(aba_projeto)

        aba_layouts = QWidget()
        layout_layouts = QVBoxLayout()
        layout_layouts.setContentsMargins(4, 4, 4, 4)
        layout_layouts.setSpacing(7)

        self._construir_preview(layout_layouts)
        aba_layouts.setLayout(layout_layouts)

        scroll_layouts = QScrollArea()
        scroll_layouts.setWidgetResizable(True)
        scroll_layouts.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_layouts.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_layouts.setWidget(aba_layouts)

        aba_config = QWidget()
        layout_config = QVBoxLayout()
        layout_config.setContentsMargins(8, 8, 8, 8)
        layout_config.setSpacing(8)

        resumo = QGroupBox("Resumo do template")
        resumo.setObjectName("summaryPanel")
        resumo_layout = QVBoxLayout()
        resumo_layout.setSpacing(6)
        for texto in [
            "• Validação da obra e do arquivo de entrada.",
            "• Detecção automática do município, UF e zona UTM.",
            "• Atualização do preview e dos layouts de impressão.",
            "• Reset do template com confirmação antes da execução.",
        ]:
            label = QLabel(texto)
            label.setObjectName("summaryItem")
            resumo_layout.addWidget(label)
        resumo.setLayout(resumo_layout)
        layout_config.addWidget(resumo)

        self.resumo_geracao = QGroupBox("Resumo da geração")
        self.resumo_geracao.setObjectName("summaryPanel")
        layout_resumo_geracao = QVBoxLayout()
        self.lbl_resumo_geracao = QLabel()
        self.lbl_resumo_geracao.setWordWrap(True)
        self.lbl_resumo_geracao.setObjectName("previewInfo")
        layout_resumo_geracao.addWidget(self.lbl_resumo_geracao)
        self.resumo_geracao.setLayout(layout_resumo_geracao)
        layout_config.addWidget(self.resumo_geracao)
        self._atualizar_resumo_geracao()

        self.log_geracao = QTextEdit()
        self.log_geracao.setReadOnly(True)
        self.log_geracao.setMaximumHeight(150)
        self.log_geracao.setPlaceholderText("Log da geração...")
        self.log_geracao.setObjectName("logPanel")
        self._adicionar_log("Sistema pronto. Aguardando a geração do projeto.")
        layout_config.addWidget(self.log_geracao)
        aba_config.setLayout(layout_config)

        paginas = QStackedWidget()
        paginas.setObjectName("mainStack")
        paginas.addWidget(scroll_projeto)
        paginas.addWidget(scroll_layouts)
        paginas.addWidget(aba_config)
        paginas.setMinimumHeight(360)

        navegacao = QFrame()
        navegacao.setObjectName("sideNav")
        navegacao.setFixedWidth(58)
        navegacao_layout = QVBoxLayout(navegacao)
        navegacao_layout.setContentsMargins(6, 8, 6, 8)
        navegacao_layout.setSpacing(8)

        botoes_navegacao = []
        itens_navegacao = [
            ("project", "Projeto", "Dados do empreendimento e arquivo de entrada."),
            ("layouts", "Layouts", "Preview, escalas e posições dos layouts."),
            ("summary", "Resumo", "Resumo da configuração e log de geração."),
        ]
        for indice, (icone, titulo, dica) in enumerate(itens_navegacao):
            botao = QToolButton(navegacao)
            botao.setObjectName("sideNavButton")
            botao.setCheckable(True)
            botao.setAutoExclusive(True)
            botao.setIcon(criar_icone_estelar(icone))
            botao.setIconSize(QSize(21, 21))
            botao.setToolTip(f"{titulo}: {dica}")
            botao.clicked.connect(
                lambda _checked, pagina=indice: paginas.setCurrentIndex(pagina)
            )
            navegacao_layout.addWidget(botao)
            botoes_navegacao.append(botao)

        navegacao_layout.addStretch()
        botoes_navegacao[0].setChecked(True)
        self._abas_principais = paginas
        self._botoes_navegacao = botoes_navegacao
        paginas.currentChanged.connect(self._animar_aba)

        area_principal = QHBoxLayout()
        area_principal.setContentsMargins(0, 0, 0, 0)
        area_principal.setSpacing(8)
        area_principal.addWidget(navegacao)
        area_principal.addWidget(paginas, 1)
        layout_principal.addLayout(area_principal, 1)

        self._construir_fluxo_geracao(layout_principal)

        # Botões ficam fora das abas
        self._construir_botoes(layout_principal)
        self._carregar_configuracao_destino()
        self._restaurar_estado_formulario()
        self._atualizar_estado_botao()

        self._construir_rodape(layout_principal)
        self._atualizar_fluxo_geracao()

        self.setLayout(layout_principal)
        self._iniciar_animacoes_ambiente()
        QTimer.singleShot(0, lambda: self._animar_aba(paginas.currentIndex()))



    # ------------------------------------------------------------------
    # Construção da UI
    # ------------------------------------------------------------------
    def _construir_cabecalho(
        self,
        layout: QVBoxLayout
    ) -> None:

        caminho_logo = os.path.join(
            os.path.dirname(__file__),
            "assets",
            "logo.png"
        )

        barra = BarraTitulo()
        barra.setObjectName("titleBar")
        barra.setMinimumHeight(58)
        cabecalho = QHBoxLayout(barra)
        cabecalho.setContentsMargins(10, 4, 8, 4)
        cabecalho.setSpacing(10)

        logo = QLabel()
        logo.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)

        pixmap = QPixmap(caminho_logo)
        if not pixmap.isNull():
            logo.setPixmap(
                pixmap.scaled(
                    48,
                    48,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )
            logo.setFixedSize(52, 48)
            logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
            cabecalho.addWidget(logo)

        textos = QVBoxLayout()
        textos.setSpacing(1)

        titulo = QLabel(constants.NOME_PLUGIN)
        titulo.setObjectName("dialogTitle")
        titulo.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)

        subtitulo = QLabel("Template de Mapa de Localização")
        subtitulo.setObjectName("dialogSubtitle")
        subtitulo.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)

        textos.addWidget(titulo)
        textos.addWidget(subtitulo)
        cabecalho.addLayout(textos)
        cabecalho.addStretch()

        self.btn_minimizar = QPushButton()
        self.btn_minimizar.setObjectName("btnMinimize")
        self.btn_minimizar.setFixedSize(30, 30)
        self.btn_minimizar.setIcon(criar_icone_estelar("minimize", "#83eaff"))
        self.btn_minimizar.setIconSize(QSize(16, 16))
        self.btn_minimizar.setToolTip("Minimizar janela")
        self.btn_minimizar.clicked.connect(self.showMinimized)
        cabecalho.addWidget(self.btn_minimizar)

        self.btn_fechar = QPushButton()
        self.btn_fechar.setObjectName("btnClose")
        self.btn_fechar.setFixedSize(30, 30)
        self.btn_fechar.setIcon(criar_icone_estelar("close", "#ffab8b"))
        self.btn_fechar.setIconSize(QSize(16, 16))
        self.btn_fechar.setToolTip("Fechar janela")
        self.btn_fechar.clicked.connect(self.reject)
        cabecalho.addWidget(self.btn_fechar)

        layout.addWidget(barra)

        divisor = QFrame()
        divisor.setObjectName("headerDivider")
        divisor.setFrameShape(QFrame.Shape.HLine)
        divisor.setFrameShadow(QFrame.Shadow.Plain)
        layout.addWidget(divisor)

    def _construir_campos_obra(self, layout: QVBoxLayout) -> None:
        grupo_projeto = QGroupBox("Dados do projeto")
        grupo_layout = QGridLayout()
        grupo_layout.setColumnStretch(0, 3)
        grupo_layout.setColumnStretch(1, 2)
        grupo_layout.setHorizontalSpacing(10)
        grupo_layout.setVerticalSpacing(8)

        self.lbl_obra = QLabel("Nome da obra *")
        self.lbl_obra.setObjectName("fieldLabel")
        grupo_layout.addWidget(self.lbl_obra, 0, 0)

        self.lbl_preset = QLabel("Perfil rápido")
        self.lbl_preset.setObjectName("fieldLabel")
        grupo_layout.addWidget(self.lbl_preset, 0, 1)

        self.cmb_obra = QComboBox()
        self.cmb_obra.setEditable(True)
        self.cmb_obra.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.cmb_obra.setPlaceholderText("Selecione ou digite a obra")
        self.cmb_obra.setAccessibleName("Nome da obra")
        self.cmb_obra.setAccessibleDescription(
            "Obrigatório. Selecione uma obra cadastrada ou digite um nome."
        )
        self.cmb_obra.setMaximumWidth(520)
        opcoes_obra = [f"{sigla} - {nome}" for sigla, nome in sorted(constants.OBRAS.items())]
        for texto in opcoes_obra:
            self.cmb_obra.addItem(texto)
        completer_obra = QCompleter(opcoes_obra, self.cmb_obra)
        completer_obra.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        completer_obra.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        completer_obra.popup().setObjectName("obraCompleterPopup")
        self.cmb_obra.setCompleter(completer_obra)
        for indice, (sigla, _nome) in enumerate(sorted(constants.OBRAS.items())):
            self.cmb_obra.setItemData(indice, sigla)
        self.cmb_obra.setCurrentIndex(-1)
        grupo_layout.addWidget(self.cmb_obra, 1, 0)

        self.cmb_preset = QComboBox()
        self.cmb_preset.setAccessibleName("Perfil rápido")
        self.cmb_preset.setMaximumWidth(240)
        self.cmb_preset.addItems(list(self._presets.keys()))
        self.cmb_preset.currentTextChanged.connect(self._aplicar_preset)
        self._carregar_preset_salvo()
        grupo_layout.addWidget(self.cmb_preset, 1, 1)

        lbl_tipo = QLabel("Tipo de projeto")
        lbl_tipo.setObjectName("fieldLabel")
        grupo_layout.addWidget(lbl_tipo, 2, 0)

        lbl_zona = QLabel("Zona UTM")
        lbl_zona.setObjectName("fieldLabel")
        grupo_layout.addWidget(lbl_zona, 2, 1)

        self.cmb_tipo = QComboBox()
        self.cmb_tipo.setAccessibleName("Tipo de projeto")
        self.cmb_tipo.addItems(constants.TIPOS_PROJETO)
        self.cmb_tipo.setMaximumWidth(360)
        grupo_layout.addWidget(self.cmb_tipo, 3, 0)

        self.cmb_zona = QComboBox()
        self.cmb_zona.setAccessibleName("Zona UTM")
        self.cmb_zona.addItems(constants.ZONAS_UTM)
        self.cmb_zona.setMaximumWidth(240)
        self.cmb_zona.setCurrentText(
            self._variaveis_salvas.get("zona_utm") or "AUTOMÁTICO"
        )
        grupo_layout.addWidget(self.cmb_zona, 3, 1)

        self.cmb_obra.currentIndexChanged.connect(self._atualizar_preview)
        self.cmb_obra.currentTextChanged.connect(self._atualizar_estado_botao)
        self.cmb_obra.currentTextChanged.connect(self._salvar_estado_formulario)
        self.cmb_tipo.currentIndexChanged.connect(self._atualizar_preview)
        self.cmb_tipo.currentTextChanged.connect(self._atualizar_estado_botao)
        self.cmb_tipo.currentTextChanged.connect(self._salvar_estado_formulario)
        self.cmb_zona.currentTextChanged.connect(self._salvar_estado_formulario)

        self.chk_modo_avancado = QCheckBox("Modo avançado")
        self.chk_modo_avancado.toggled.connect(self._alternar_modo_avancado)
        self.chk_modo_avancado.toggled.connect(self._salvar_estado_formulario)
        grupo_layout.addWidget(self.chk_modo_avancado, 4, 0, 1, 2)

        self.lbl_sigla_projetista = QLabel("Sigla projetista")
        self.lbl_sigla_projetista.setObjectName("fieldLabel")
        grupo_layout.addWidget(self.lbl_sigla_projetista, 5, 0)

        self.lbl_sigla_verificacao = QLabel("Sigla verificação")
        self.lbl_sigla_verificacao.setObjectName("fieldLabel")
        grupo_layout.addWidget(self.lbl_sigla_verificacao, 5, 1)

        self.txt_sigla_projetista = QLineEdit()
        self.txt_sigla_projetista.setPlaceholderText("Ex.: CCC")
        self.txt_sigla_projetista.setAccessibleName("Sigla projetista")
        self.txt_sigla_projetista.textChanged.connect(self._salvar_estado_formulario)
        grupo_layout.addWidget(self.txt_sigla_projetista, 6, 0)

        self.txt_sigla_verificacao = QLineEdit()
        self.txt_sigla_verificacao.setPlaceholderText("Ex.: JRM")
        self.txt_sigla_verificacao.setAccessibleName("Sigla verificação")
        self.txt_sigla_verificacao.textChanged.connect(self._salvar_estado_formulario)
        grupo_layout.addWidget(self.txt_sigla_verificacao, 6, 1)

        self._alternar_modo_avancado(False)

        grupo_projeto.setLayout(grupo_layout)
        layout.addWidget(grupo_projeto)

        grupo_arquivo = QGroupBox("Arquivo de entrada *")
        layout_arquivo = QVBoxLayout()
        layout_arquivo.setSpacing(8)

        self.btn_kml = QPushButton("Importar KML/KMZ")
        self.btn_kml.setIcon(criar_icone_estelar("folder"))
        self.btn_kml.setAccessibleName("Importar arquivo KML ou KMZ")
        self.btn_kml.setAccessibleDescription("Obrigatório para gerar o projeto.")
        self.btn_kml.clicked.connect(self._selecionar_arquivo)
        layout_arquivo.addWidget(self.btn_kml)

        self.lbl_status = QLabel("Importe um arquivo KML/KMZ para continuar.")
        self.lbl_status.setObjectName("statusInfo")
        self.lbl_status.setWordWrap(True)
        layout_arquivo.addWidget(self.lbl_status)

        grupo_arquivo.setLayout(layout_arquivo)
        layout.addWidget(grupo_arquivo)

        grupo_destino = QGroupBox("Salvar projeto em *")
        layout_destino = QVBoxLayout()
        layout_destino.setSpacing(8)

        linha_destino = QHBoxLayout()
        linha_destino.setSpacing(6)
        self.txt_pasta_projeto = QLineEdit()
        self.txt_pasta_projeto.setPlaceholderText("Escolha a pasta de destino")
        self.txt_pasta_projeto.setAccessibleName("Pasta de destino do projeto")
        self.txt_pasta_projeto.setAccessibleDescription(
            "Obrigatório. Escolha uma pasta existente para salvar o projeto."
        )
        self.txt_pasta_projeto.textChanged.connect(self._atualizar_estado_botao)
        self.txt_pasta_projeto.textChanged.connect(self._salvar_configuracao_destino)
        linha_destino.addWidget(self.txt_pasta_projeto, 1)

        self.btn_pasta_projeto = QPushButton("Selecionar pasta...")
        self.btn_pasta_projeto.setIcon(criar_icone_estelar("folder"))
        self.btn_pasta_projeto.clicked.connect(self._selecionar_pasta_projeto)
        linha_destino.addWidget(self.btn_pasta_projeto)

        linha_acoes_destino = QHBoxLayout()
        linha_acoes_destino.setSpacing(6)

        self.btn_abrir_pasta_projeto = QPushButton("Abrir pasta")
        self.btn_abrir_pasta_projeto.setIcon(criar_icone_estelar("folder_open"))
        self.btn_abrir_pasta_projeto.clicked.connect(self._abrir_pasta_projeto)
        linha_acoes_destino.addWidget(self.btn_abrir_pasta_projeto)

        self.btn_copiar_caminho = QPushButton("Copiar caminho")
        self.btn_copiar_caminho.setIcon(criar_icone_estelar("copy"))
        self.btn_copiar_caminho.clicked.connect(self._copiar_caminho_projeto)
        linha_acoes_destino.addWidget(self.btn_copiar_caminho)

        self.btn_abrir_projeto = QPushButton("Abrir projeto")
        self.btn_abrir_projeto.setIcon(criar_icone_estelar("file"))
        self.btn_abrir_projeto.setEnabled(False)
        self.btn_abrir_projeto.clicked.connect(self._abrir_projeto_gerado)
        linha_acoes_destino.addWidget(self.btn_abrir_projeto)

        self.btn_copiar_caminho.setEnabled(bool(self.txt_pasta_projeto.text().strip()))
        self.btn_abrir_projeto.setEnabled(bool(self.ultimo_projeto_gerado and os.path.isfile(self.ultimo_projeto_gerado)))
        layout_destino.addLayout(linha_destino)
        layout_destino.addLayout(linha_acoes_destino)

        dica_destino = QLabel(
            "O GeoPackage será copiado para uma subpasta BASES; a origem da rede não será alterada."
        )
        dica_destino.setObjectName("destinationHint")
        dica_destino.setWordWrap(True)
        layout_destino.addWidget(dica_destino)

        grupo_destino.setLayout(layout_destino)
        layout.addWidget(grupo_destino)

        self._atualizar_status()

    def _construir_preview(self, layout: QVBoxLayout) -> None:
        grupo_preview = QGroupBox("Preview do empreendimento")
        grupo_layout = QVBoxLayout()
        grupo_layout.setSpacing(8)

        self.canvas_preview = QgsMapCanvas()
        self.canvas_preview.setMinimumHeight(280)
        self.canvas_preview.enableAntiAliasing(True)
        self.canvas_preview.setBackgroundRole(QPalette.ColorRole.Window)
        self.canvas_preview.viewport().setMouseTracking(True)

        self._preview_tool = core_preview.PreviewMoveTool(self.canvas_preview, self)
        self.canvas_preview.setMapTool(self._preview_tool)

        try:
            self.camada_base = core_kml.obter_camada_fundo(self._estilo_mapa)
            QgsProject.instance().addMapLayer(self.camada_base, False)
            self.canvas_preview.setLayers([self.camada_base])
            self.canvas_preview.zoomToFullExtent()
        except Exception:
            self.camada_base = None
            self.canvas_preview.setLayers([])

        mapa_container = QWidget()
        mapa_layout = QGridLayout(mapa_container)
        mapa_layout.setContentsMargins(0, 0, 0, 0)
        mapa_layout.setSpacing(0)
        mapa_layout.addWidget(self.canvas_preview, 0, 0)

        preview_overlay = QWidget(mapa_container)
        preview_overlay.setObjectName("mapOverlay")
        preview_overlay.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        preview_overlay.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        preview_layout = QVBoxLayout(preview_overlay)
        preview_layout.setContentsMargins(10, 8, 10, 8)
        preview_layout.setSpacing(6)

        self.lbl_preview = QLabel(core_preview.montar_texto_preview(self._preview_dados))
        self.lbl_preview.setWordWrap(True)
        self.lbl_preview.setObjectName("previewInfo")
        self.lbl_preview.setMaximumWidth(220)
        if not self.camada_base:
            self.lbl_preview.setText(
                "PREVIEW DO EMPREENDIMENTO\n\n"
                "Importe um KML/KMZ para carregar o empreendimento\n"
                "e visualizar a área de estudo no mapa."
            )
        preview_layout.addWidget(self.lbl_preview, 0, Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)

        estilo_box = QWidget(mapa_container)
        estilo_box.setObjectName("mapStylePanel")
        estilo_box.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
        estilo_layout = QHBoxLayout(estilo_box)
        estilo_layout.setContentsMargins(6, 4, 6, 4)
        estilo_layout.setSpacing(5)

        lbl_estilo = QLabel("Base")
        lbl_estilo.setObjectName("mapStyleLabel")
        self.cmb_estilo_mapa = QComboBox()
        self.cmb_estilo_mapa.setMinimumWidth(110)
        self.cmb_estilo_mapa.setMaximumWidth(140)
        self.cmb_estilo_mapa.setEditable(False)
        self.cmb_estilo_mapa.addItem("Satélite", "satelite")
        self.cmb_estilo_mapa.addItem("Mapa", "mapa_base")
        self.cmb_estilo_mapa.addItem("Sem cidades", "sem_cidades")
        self.cmb_estilo_mapa.setCurrentIndex(
            self.cmb_estilo_mapa.findData(self._estilo_mapa)
        )
        self.cmb_estilo_mapa.currentIndexChanged.connect(self._alterar_estilo_mapa)

        estilo_layout.addWidget(lbl_estilo)
        estilo_layout.addWidget(self.cmb_estilo_mapa)
        mapa_layout.addWidget(estilo_box, 0, 0)
        mapa_layout.setAlignment(estilo_box, Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight)

        escala_layout = QVBoxLayout()
        escala_layout.setContentsMargins(0, 0, 0, 0)
        escala_layout.setSpacing(6)

        self.spin_001 = self._criar_slider_escala(escala_layout, "001", "LAYOUT 1 (ROSA)", "lbl_001")
        self.spin_002 = self._criar_slider_escala(escala_layout, "002", "LAYOUT 2 (LARANJA)", "lbl_002")
        self.spin_003 = self._criar_slider_escala(escala_layout, "003", "LAYOUT 3 (VERDE)", "lbl_003")

        self.spin_001.valueChanged.connect(self._desenhar_retangulos)
        self.spin_002.valueChanged.connect(self._desenhar_retangulos)
        self.spin_003.valueChanged.connect(self._desenhar_retangulos)

        panel_escala = QWidget(mapa_container)
        panel_escala.setObjectName("scalePanel")
        panel_escala.setLayout(escala_layout)
        panel_escala.setMinimumWidth(260)
        panel_escala.setMaximumWidth(320)
        panel_escala.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        panel_escala.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
        mapa_layout.addWidget(panel_escala, 0, 0)
        mapa_layout.setAlignment(panel_escala, Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignLeft)
        panel_escala.raise_()

        mapa_layout.addWidget(preview_overlay, 0, 0)
        preview_overlay.lower()
        grupo_layout.addWidget(mapa_container)

        grupo_preview.setLayout(grupo_layout)
        layout.addWidget(grupo_preview)

    def _alternar_lock_layout(self, chave: str) -> None:
        if chave not in self._layout_locked:
            return
        self._layout_locked[chave] = not self._layout_locked[chave]
        botao = getattr(self, f"lock_{chave}", None)
        if botao is not None:
            icon = self._icone_lock_layout(self._layout_locked[chave])
            botao.setText("")
            botao.setIcon(icon)
            botao.setIconSize(QSize(16, 16))
            botao.setToolTip("Layout bloqueado" if self._layout_locked[chave] else "Layout desbloqueado")
        self._desenhar_retangulos()

    def _alterar_estilo_mapa(self, _indice: int) -> None:
        self._estilo_mapa = self.cmb_estilo_mapa.currentData() or "satelite"
        self.settings.setValue("EstelarTemplate/ultimo_estilo_mapa", self._estilo_mapa)

        if not hasattr(self, "canvas_preview"):
            return

        if not hasattr(self, "camada_preview"):
            try:
                self.camada_base = core_kml.obter_camada_fundo(self._estilo_mapa)
                QgsProject.instance().addMapLayer(self.camada_base, False)
                self.canvas_preview.setLayers([self.camada_base])
                self.canvas_preview.zoomToFullExtent()
            except Exception as erro:
                QMessageBox.warning(self, constants.NOME_PLUGIN, f"Não foi possível alterar o estilo do mapa:\n{erro}")
            return

        try:
            if hasattr(self, "camada_base") and self.camada_base is not None:
                QgsProject.instance().removeMapLayer(self.camada_base.id())

            self.camada_base = core_kml.obter_camada_fundo(self._estilo_mapa)
            QgsProject.instance().addMapLayer(self.camada_base, False)
            self.canvas_preview.setLayers([self.camada_preview, self.camada_base])
            self.canvas_preview.refresh()
        except Exception as erro:
            QMessageBox.warning(self, constants.NOME_PLUGIN, f"Não foi possível alterar o estilo do mapa:\n{erro}")

    def _construir_layouts_escala(self, layout: QVBoxLayout) -> None:
        grupo_layouts = QGroupBox("Escalas e layouts")
        grupo_layout = QVBoxLayout()

        self.spin_001 = self._criar_slider_escala(grupo_layout, "001", "LAYOUT 1 (VERMELHO)", "lbl_001")
        self.spin_002 = self._criar_slider_escala(grupo_layout, "002", "LAYOUT 2 (AZUL)", "lbl_002")
        self.spin_003 = self._criar_slider_escala(grupo_layout, "003", "LAYOUT 3 (VERDE)", "lbl_003")

        self.spin_001.valueChanged.connect(self._normalizar_ordem_layouts)
        self.spin_001.valueChanged.connect(self._desenhar_retangulos)
        self.spin_002.valueChanged.connect(self._normalizar_ordem_layouts)
        self.spin_002.valueChanged.connect(self._desenhar_retangulos)
        self.spin_003.valueChanged.connect(self._normalizar_ordem_layouts)
        self.spin_003.valueChanged.connect(self._desenhar_retangulos)

        grupo_layouts.setLayout(grupo_layout)
        layout.addWidget(grupo_layouts)

    def _construir_card_escala(self, chave: str, titulo: str, nome_label: str) -> QWidget:
        card = QWidget()
        card.setObjectName("layoutCard")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(8, 8, 8, 8)
        card_layout.setSpacing(6)

        self._criar_slider_escala(card_layout, chave, titulo, nome_label)
        return card

    def _criar_slider_escala(self, layout: QVBoxLayout, chave: str, titulo: str, nome_label: str) -> QDoubleSpinBox:
        ref = constants.ESCALAS_REFERENCIA[chave]

        spin = QDoubleSpinBox()
        spin.setDecimals(6)
        spin.setMinimum(0.01)
        spin.setMaximum(10000.00)

        valor_inicial = ref["escala_referencia"]
        spin.setValue(
            helpers.largura_a_partir_da_escala(
                valor_inicial, ref["escala_referencia"], ref["largura_referencia"]
            )
        )
        spin.hide()

        slider = QSlider(Qt.Orientation.Horizontal)
        escala_minima = 5000
        escala_maxima = 2000000
        passo_escala = 5000

        slider.setRange(
            escala_minima // passo_escala,
            escala_maxima // passo_escala,
        )
        slider.setSingleStep(1)
        slider.setPageStep(1)
        slider.setTickPosition(QSlider.TickPosition.NoTicks)
        slider.setMinimumHeight(18)

        escala_atual = helpers.calcular_escala(
            spin.value(), ref["escala_referencia"], ref["largura_referencia"]
        )
        valor_inicial = max(
            escala_minima // passo_escala,
            min(escala_maxima // passo_escala, round(escala_atual / passo_escala)),
        )
        slider.setValue(valor_inicial)

        def atualizar_largura(unidades_escala: int) -> None:
            escala = unidades_escala * passo_escala
            largura = (
                escala * ref["largura_referencia"]
                / ref["escala_referencia"]
            )
            spin.setValue(largura)

        atualizar_largura(slider.value())
        slider.valueChanged.connect(atualizar_largura)

        label_escala = QLabel(helpers.formatar_escala(slider.value() * passo_escala))
        setattr(self, nome_label, label_escala)
        label_escala.setObjectName("scaleValue")
        label_escala.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label_escala.setMinimumWidth(120)

        cabecalho = QHBoxLayout()
        cabecalho.setContentsMargins(0, 0, 0, 0)
        cabecalho.setSpacing(6)
        titulo_label = QLabel(titulo)
        titulo_label.setObjectName("scaleTitle")
        cabecalho.addWidget(titulo_label)
        cabecalho.addStretch()

        btn_lock = QPushButton()
        btn_lock.setObjectName("layoutLockButton")
        btn_lock.setFixedSize(26, 26)
        btn_lock.setCheckable(True)
        btn_lock.setChecked(False)
        btn_lock.setToolTip("Bloquear layout no preview")
        btn_lock.setText("")
        btn_lock.setIcon(self._icone_lock_layout(False))
        btn_lock.setIconSize(QSize(16, 16))
        btn_lock.clicked.connect(lambda _checked, k=chave: self._alternar_lock_layout(k))
        cabecalho.addWidget(btn_lock)
        setattr(self, f"lock_{chave}", btn_lock)

        cabecalho.addWidget(label_escala)

        linha = QHBoxLayout()
        linha.setContentsMargins(0, 0, 0, 0)
        linha.setSpacing(8)
        linha.addWidget(slider, 1)

        card = QFrame()
        card.setObjectName("layoutCard")
        card_layout = QVBoxLayout()
        card_layout.setContentsMargins(8, 8, 8, 8)
        card_layout.setSpacing(6)
        card_layout.addLayout(cabecalho)
        card_layout.addLayout(linha)
        card.setLayout(card_layout)
        layout.addWidget(card)

        return spin

    def _construir_fluxo_geracao(self, layout: QVBoxLayout) -> None:
        self.fluxo_geracao = QWidget()
        self.fluxo_geracao.setObjectName("generationFlow")
        fluxo_layout = QVBoxLayout(self.fluxo_geracao)
        fluxo_layout.setContentsMargins(0, 0, 0, 0)
        fluxo_layout.setSpacing(0)
        self.fluxo_geracao.setVisible(False)
        layout.addWidget(self.fluxo_geracao)

    def _atualizar_fluxo_geracao(self) -> None:
        if not hasattr(self, "progress_geracao") or not hasattr(self, "lbl_etapa"):
            return

        passos = [
            "importar arquivo",
            "confirmar obra",
            "definir destino",
            "gerar projeto",
        ]

        valor = 0
        if self.arquivo:
            valor = max(valor, 1)
        if self.cmb_obra.currentData() or self.cmb_obra.currentText().strip():
            valor = max(valor, 2)
        if os.path.isdir(self.txt_pasta_projeto.text().strip()):
            valor = max(valor, 3)
        if self.btn_ok.isEnabled():
            valor = 4

        etapa_atual = min(valor, len(passos) - 1)
        self.progress_geracao.setValue(valor)
        self.lbl_etapa.setText(f"Etapa {valor + 1}/4: {passos[etapa_atual]}")

        if hasattr(self, "_cards_fluxo"):
            for indice, card in enumerate(self._cards_fluxo):
                if valor >= 4 or indice < valor:
                    estado = "done"
                elif indice == valor:
                    estado = "active"
                else:
                    estado = "pending"

                card.setProperty("state", estado)
                card.style().unpolish(card)
                card.style().polish(card)

                numero = card.findChild(QLabel, "generationStepNumber")
                if numero is not None:
                    numero.setProperty("state", estado)
                    numero.style().unpolish(numero)
                    numero.style().polish(numero)

                titulo = card.findChild(QLabel, "generationStepText")
                if titulo is not None:
                    titulo.setProperty("state", estado)
                    titulo.style().unpolish(titulo)
                    titulo.style().polish(titulo)

    def _construir_botoes(self, layout: QVBoxLayout) -> None:
        botoes = QHBoxLayout()
        botoes.setSpacing(10)

        self.btn_ok = QPushButton("Gerar projeto")
        self.btn_ok.setIcon(criar_icone_estelar("play", "#ffffff"))
        self.btn_ok.setObjectName("btnGerar")
        self.btn_ok.clicked.connect(self.accept)
        botoes.addWidget(self.btn_ok, 2)

        self.btn_reset = QPushButton("Resetar template")
        self.btn_reset.setIcon(criar_icone_estelar("reset", "#ffab8b"))
        self.btn_reset.setObjectName("btnReset")
        self.btn_reset.clicked.connect(self._resetar_template)
        botoes.addWidget(self.btn_reset, 1)

        layout.addLayout(botoes)

    def _alternar_modo_avancado(self, ativado: bool) -> None:
        if hasattr(self, "lbl_sigla_projetista"):
            self.lbl_sigla_projetista.setVisible(ativado)
        if hasattr(self, "lbl_sigla_verificacao"):
            self.lbl_sigla_verificacao.setVisible(ativado)
        if hasattr(self, "txt_sigla_projetista"):
            self.txt_sigla_projetista.setVisible(ativado)
        if hasattr(self, "txt_sigla_verificacao"):
            self.txt_sigla_verificacao.setVisible(ativado)
        if hasattr(self, "cmb_preset"):
            self.cmb_preset.setVisible(not ativado)
        if hasattr(self, "lbl_preset"):
            self.lbl_preset.setVisible(not ativado)
        if hasattr(self, "btn_ok"):
            self._atualizar_estado_botao()

    def _carregar_preset_salvo(self) -> None:
        preset_salvo = self.settings.value("EstelarTemplate/ultimo_preset", "Padrão", type=str)
        if preset_salvo in self._presets:
            self.cmb_preset.setCurrentText(preset_salvo)

    def _salvar_preset(self, nome: str) -> None:
        if nome in self._presets:
            self.settings.setValue("EstelarTemplate/ultimo_preset", nome)

    def _restaurar_estado_formulario(self) -> None:
        self._carregar_preset_salvo()
        self._aplicar_preset(self.cmb_preset.currentText())

        obra = self._variaveis_salvas.get("obra") or self.settings.value(
            "EstelarTemplate/ultima_obra", "", type=str
        )
        if obra:
            indice_obra = self.cmb_obra.findData(obra)
            if indice_obra < 0:
                indice_obra = self.cmb_obra.findText(
                    obra, Qt.MatchFlag.MatchFixedString
                )
            if indice_obra >= 0:
                self.cmb_obra.setCurrentIndex(indice_obra)
            else:
                self.cmb_obra.setEditText(obra)

        tipo = self._variaveis_salvas.get("tipo_projeto") or self.settings.value(
            "EstelarTemplate/ultimo_tipo", "", type=str
        )
        if tipo and self.cmb_tipo.findText(tipo) >= 0:
            self.cmb_tipo.setCurrentText(tipo)

        zona = self._variaveis_salvas.get("zona_utm") or self.settings.value(
            "EstelarTemplate/ultima_zona", "", type=str
        )
        if zona and self.cmb_zona.findText(zona) >= 0:
            self.cmb_zona.setCurrentText(zona)

        sigla_projetista = self._variaveis_salvas.get("sigla_projetista") or self.settings.value(
            "EstelarTemplate/ultima_sigla_projetista", "", type=str
        )
        sigla_verificacao = self._variaveis_salvas.get("sigla_verificacao") or self.settings.value(
            "EstelarTemplate/ultima_sigla_verificacao", "", type=str
        )
        self.txt_sigla_projetista.setText(sigla_projetista)
        self.txt_sigla_verificacao.setText(sigla_verificacao)
        modo_avancado = self.settings.value(
            "EstelarTemplate/modo_avancado", False, type=bool
        )
        self.chk_modo_avancado.setChecked(modo_avancado)
        self._alternar_modo_avancado(modo_avancado)
        self._restaurando_estado = False

    def _salvar_estado_formulario(self, *_args) -> None:
        if self._restaurando_estado:
            return

        obra = self.cmb_obra.currentText().strip()
        if obra:
            self.settings.setValue("EstelarTemplate/ultima_obra", obra)
        else:
            self.settings.remove("EstelarTemplate/ultima_obra")
        self.settings.setValue("EstelarTemplate/ultimo_tipo", self.cmb_tipo.currentText())
        self.settings.setValue("EstelarTemplate/ultima_zona", self.cmb_zona.currentText())
        self.settings.setValue(
            "EstelarTemplate/ultima_sigla_projetista",
            self.txt_sigla_projetista.text().strip(),
        )
        self.settings.setValue(
            "EstelarTemplate/ultima_sigla_verificacao",
            self.txt_sigla_verificacao.text().strip(),
        )
        self.settings.setValue(
            "EstelarTemplate/modo_avancado", self.chk_modo_avancado.isChecked()
        )

    def _aplicar_preset(self, nome: str) -> None:
        if nome not in self._presets:
            return

        if not hasattr(self, "cmb_tipo") or not hasattr(self, "cmb_zona"):
            return

        self._salvar_preset(nome)
        preset = self._presets[nome]
        tipo = preset["tipo"]
        zona = preset["zona"]

        if self.cmb_tipo.findText(tipo) >= 0:
            self.cmb_tipo.setCurrentText(tipo)
        if self.cmb_zona.findText(zona) >= 0:
            self.cmb_zona.setCurrentText(zona)

    def _atualizar_estado_botao(self) -> None:
        projeto_ok = bool(self.cmb_obra.currentText().strip())
        arquivo_ok = bool(self.arquivo)
        destino_ok = os.path.isdir(self.txt_pasta_projeto.text().strip())
        botao_liberado = projeto_ok and arquivo_ok and destino_ok
        pendencias = []
        if not projeto_ok:
            pendencias.append("selecione uma obra")
        if not arquivo_ok:
            pendencias.append("importe um arquivo KML/KMZ")
        if not destino_ok:
            pendencias.append("escolha uma pasta de destino válida")
        self._pendencias_validacao = pendencias

        self._definir_estado_validacao(self.cmb_obra, not projeto_ok)
        self._definir_estado_validacao(self.btn_kml, not arquivo_ok)
        self._definir_estado_validacao(self.txt_pasta_projeto, not destino_ok)
        self.btn_ok.setEnabled(botao_liberado)
        self.btn_ok.setText("Gerar projeto")
        self.btn_ok.setIcon(
            criar_icone_estelar(
                "play" if botao_liberado else "lock",
                "#ffffff" if botao_liberado else "#66818c",
            )
        )
        self.btn_ok.setIconSize(QSize(18, 18))
        self.btn_ok.setToolTip(
            "Projeto pronto para gerar."
            if botao_liberado
            else "Para liberar: " + "; ".join(pendencias) + "."
        )

        if botao_liberado:
            self.lbl_status.setText(f"Pronto para gerar: {helpers.nome_do_arquivo(self.arquivo)}")
        else:
            self.lbl_status.setText("Para liberar a geração: " + "; ".join(pendencias) + ".")

        self._atualizar_fluxo_geracao()
        self._atualizar_resumo_geracao()

    @staticmethod
    def _definir_estado_validacao(widget: QWidget, pendente: bool) -> None:
        estado = "missing" if pendente else ""
        if widget.property("validationState") == estado:
            return
        widget.setProperty("validationState", estado)
        widget.style().unpolish(widget)
        widget.style().polish(widget)

    def _carregar_configuracao_destino(self) -> None:
        pasta_salva = self.settings.value("EstelarTemplate/ultima_pasta", "", type=str)
        if pasta_salva and os.path.isdir(pasta_salva):
            self.txt_pasta_projeto.setText(pasta_salva)
            self._atualizar_estado_botao()

    def _salvar_configuracao_destino(self) -> None:
        pasta = self.txt_pasta_projeto.text().strip()
        if pasta:
            self.settings.setValue("EstelarTemplate/ultima_pasta", pasta)
        else:
            self.settings.remove("EstelarTemplate/ultima_pasta")

    def _atualizar_resumo_geracao(self) -> None:
        if not hasattr(self, "lbl_resumo_geracao"):
            return

        obra = self.cmb_obra.currentText().strip() if hasattr(self, "cmb_obra") else "-"
        tipo = self.cmb_tipo.currentText() if hasattr(self, "cmb_tipo") else "-"
        arquivo = helpers.nome_do_arquivo(self.arquivo) if self.arquivo else "não selecionado"
        pasta = self.txt_pasta_projeto.text().strip() if hasattr(self, "txt_pasta_projeto") else "não selecionada"
        zona = self.cmb_zona.currentText() if hasattr(self, "cmb_zona") else "-"
        texto = (
            "<b>Resumo da geração</b><br>"
            f"Obra: {obra}<br>"
            f"Tipo: {tipo}<br>"
            f"Arquivo de entrada: {arquivo}<br>"
            f"Pasta de destino: {pasta or 'não selecionada'}<br>"
            f"Zona UTM: {zona}"
        )
        self.lbl_resumo_geracao.setText(texto)

    def _adicionar_log(self, mensagem: str) -> None:
        if hasattr(self, "log_geracao"):
            self.log_geracao.append(mensagem)

    def _registrar_projeto_gerado(self, caminho: str) -> None:
        self.ultimo_projeto_gerado = caminho
        self.btn_abrir_projeto.setEnabled(os.path.isfile(caminho))
        self._adicionar_log(f"Projeto disponível em: {caminho}")

    def _copiar_caminho_projeto(self) -> None:
        caminho = self.txt_pasta_projeto.text().strip()
        if not caminho:
            QMessageBox.warning(self, constants.NOME_PLUGIN, "Selecione uma pasta antes de copiar o caminho.")
            return

        clipboard = QApplication.clipboard()
        clipboard.setText(caminho)
        self._adicionar_log(f"Caminho copiado para a área de transferência: {caminho}")

    def _abrir_pasta_projeto(self) -> None:
        pasta = self.txt_pasta_projeto.text().strip()
        if not pasta or not os.path.isdir(pasta):
            QMessageBox.warning(self, constants.NOME_PLUGIN, "Selecione uma pasta válida antes de abrir.")
            return

        try:
            os.startfile(pasta)
            self._adicionar_log(f"Pasta aberta: {pasta}")
            self.btn_abrir_projeto.setEnabled(bool(self.ultimo_projeto_gerado and os.path.isfile(self.ultimo_projeto_gerado)))
        except Exception as erro:
            QMessageBox.critical(self, "Erro ao abrir pasta", str(erro))

    def _abrir_projeto_gerado(self) -> None:
        if not self.ultimo_projeto_gerado or not os.path.isfile(self.ultimo_projeto_gerado):
            QMessageBox.warning(self, constants.NOME_PLUGIN, "Nenhum projeto gerado foi encontrado para abrir.")
            return

        try:
            os.startfile(self.ultimo_projeto_gerado)
            self._adicionar_log(f"Projeto aberto: {self.ultimo_projeto_gerado}")
        except Exception as erro:
            QMessageBox.critical(self, "Erro ao abrir projeto", str(erro))

    def _atualizar_status(self, mensagem: str = None) -> None:
        if mensagem is None:
            mensagem = (
                f"Arquivo carregado: {helpers.nome_do_arquivo(self.arquivo)}"
                if self.arquivo
                else "Nenhum arquivo importado"
            )

        self.lbl_status.setText(mensagem)

    def _construir_rodape(self, layout: QVBoxLayout) -> None:
        linha_rodape = QHBoxLayout()
        linha_rodape.setContentsMargins(0, 0, 0, 0)
        linha_rodape.setSpacing(4)

        rodape = QLabel(constants.RODAPE_TEXTO)
        rodape.setObjectName("footerNote")
        rodape.setAlignment(Qt.AlignmentFlag.AlignRight)
        linha_rodape.addWidget(rodape, 1)

        self._alca_redimensionamento = QSizeGrip(self)
        self._alca_redimensionamento.setObjectName("windowResizeGrip")
        self._alca_redimensionamento.setFixedSize(16, 16)
        self._alca_redimensionamento.setToolTip("Redimensionar janela")
        linha_rodape.addWidget(self._alca_redimensionamento, 0, Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignRight)
        layout.addLayout(linha_rodape)

    # ------------------------------------------------------------------
    # Eventos / delegação para o pacote core
    # ------------------------------------------------------------------
    def _atualizar_preview(self) -> None:
        core_preview.atualizar_preview(self)

    def _normalizar_ordem_layouts(self) -> None:
        if not hasattr(self, "spin_001") or not hasattr(self, "spin_002") or not hasattr(self, "spin_003"):
            return

        valor_001 = self.spin_001.value()
        valor_002 = min(self.spin_002.value(), valor_001)
        valor_003 = min(self.spin_003.value(), valor_002)

        if self.spin_002.value() != valor_002:
            self.spin_002.setValue(valor_002)
        if self.spin_003.value() != valor_003:
            self.spin_003.setValue(valor_003)

    def _desenhar_retangulos(self) -> None:
        self._normalizar_ordem_layouts()
        core_preview.desenhar_retangulos(self)

    def _selecionar_arquivo(self) -> None:
        arquivo, _ = QFileDialog.getOpenFileName(
            self, "Selecione o arquivo", "", "Arquivos Google Earth (*.kml *.kmz)"
        )

        if not arquivo:
            return

        self.arquivo = arquivo
        self.btn_kml.setText(helpers.nome_do_arquivo(arquivo))
        self._atualizar_estado_botao()

        try:
            core_preview.carregar_arquivo_preview(self, arquivo)
        except Exception as erro:
            self._atualizar_status(f"Erro ao carregar: {helpers.nome_do_arquivo(arquivo)}")
            QMessageBox.critical(self, "Erro ao carregar arquivo", str(erro))

    def _selecionar_pasta_projeto(self) -> None:
        pasta = QFileDialog.getExistingDirectory(
            self,
            "Selecione a pasta do projeto",
            self.txt_pasta_projeto.text() or os.path.expanduser("~"),
        )
        if pasta:
            self.txt_pasta_projeto.setText(pasta)
            self._salvar_configuracao_destino()

    def _resetar_template(self) -> None:
        resposta = QMessageBox.question(
            self,
            "Resetar Template",
            "Deseja realmente resetar o STL-TEMPLATE?\n\n"
            "Todas as informações serão apagadas.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if resposta != QMessageBox.StandardButton.Yes:
            return

        try:
            core_projeto.resetar_template(QgsProject.instance())
        except Exception as erro:
            QMessageBox.critical(self, "Erro ao resetar template", str(erro))
            return

        QMessageBox.information(
            self, constants.NOME_PLUGIN,
            "Template resetado com sucesso.\n\nSalve o projeto e abra novamente."
        )
        self.close()

    # ------------------------------------------------------------------
    # Validação antes de aceitar o diálogo (melhoria: a macro original só
    # validava obra/arquivo depois de já ter fechado a janela, retornando
    # silenciosamente sem nenhum aviso ao usuário caso estivessem vazios).
    # ------------------------------------------------------------------
    def accept(self) -> None:
        self._atualizar_estado_botao()
        if not self.btn_ok.isEnabled():
            QMessageBox.warning(
                self,
                constants.NOME_PLUGIN,
                "Para gerar o projeto, " + "; ".join(self._pendencias_validacao) + ".",
            )
            return

        self._salvar_estado_formulario()
        super().accept()
