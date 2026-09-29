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

from qgis.PyQt.QtCore import Qt, QSettings
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
    QSlider,
    QTextEdit,
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
from qgis.PyQt.QtGui import QPalette, QPixmap


class AbaHover(QTabWidget):
    """QTabWidget que troca de aba ao passar o mouse sobre o título."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMouseTracking(True)
        self.tabBar().setMouseTracking(True)

    def mouseMoveEvent(self, event):
        index = self.tabBar().tabAt(event.pos())
        if index >= 0:
            self.setCurrentIndex(index)
        super().mouseMoveEvent(event)


class JanelaProjeto(QDialog):
    """Diálogo de configuração do template de mapa de localização."""

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

        self.setWindowTitle(constants.NOME_PLUGIN)
        self.setWindowFlags(
            Qt.WindowType.Dialog
            | Qt.WindowType.WindowMinimizeButtonHint
            | Qt.WindowType.WindowCloseButtonHint
        )
        self.resize(760, 760)
        self.setMinimumSize(680, 680)
        self.setMaximumSize(960, 900)

        layout_principal = QVBoxLayout()
        layout_principal.setContentsMargins(14, 12, 14, 12)
        layout_principal.setSpacing(12)

        # Cabeçalho permanece fora das abas
        self._construir_cabecalho(layout_principal)

        # Cria o conjunto de abas
        abas = AbaHover()
        abas.setMinimumHeight(500)

        # ==========================
        # ABA PROJETO
        # ==========================
        aba_projeto = QWidget()
        layout_projeto = QVBoxLayout()
        layout_projeto.setContentsMargins(8, 8, 8, 8)
        layout_projeto.setSpacing(10)

        self._construir_campos_obra(layout_projeto)
        aba_projeto.setLayout(layout_projeto)

        scroll_projeto = QScrollArea()
        scroll_projeto.setWidgetResizable(True)
        scroll_projeto.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_projeto.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_projeto.setWidget(aba_projeto)

        # ==========================
        # ABA LAYOUTS
        # ==========================
        aba_layouts = QWidget()
        layout_layouts = QVBoxLayout()
        layout_layouts.setContentsMargins(8, 8, 8, 8)
        layout_layouts.setSpacing(10)

        self._construir_preview(layout_layouts)
        aba_layouts.setLayout(layout_layouts)

        scroll_layouts = QScrollArea()
        scroll_layouts.setWidgetResizable(True)
        scroll_layouts.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_layouts.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_layouts.setWidget(aba_layouts)

        # ==========================
        # ABA RESUMO
        # ==========================
        aba_config = QWidget()
        layout_config = QVBoxLayout()
        layout_config.setContentsMargins(12, 12, 12, 12)
        layout_config.setSpacing(12)

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

        # ==========================
        # ADICIONA AS ABAS
        # ==========================
        abas.addTab(scroll_projeto, "Projeto")
        abas.addTab(scroll_layouts, "Layouts")
        abas.addTab(aba_config, "Resumo")

        # Adiciona o conjunto de abas
        layout_principal.addWidget(abas)

        self._construir_fluxo_geracao(layout_principal)

        # Botões ficam fora das abas
        self._construir_botoes(layout_principal)
        self._carregar_configuracao_destino()
        self._aplicar_preset("Padrão")
        self._atualizar_estado_botao()

        self._construir_rodape(layout_principal)
        self._atualizar_fluxo_geracao()

        self.setLayout(layout_principal)



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

        logo = QLabel()

        cabecalho = QHBoxLayout()
        cabecalho.setContentsMargins(4, 0, 4, 8)
        cabecalho.setSpacing(12)

        pixmap = QPixmap(caminho_logo)
        if not pixmap.isNull():
            logo.setPixmap(
                pixmap.scaled(
                    72,
                    60,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )
            logo.setFixedSize(78, 64)
            logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
            cabecalho.addWidget(logo)

        textos = QVBoxLayout()
        textos.setSpacing(1)

        titulo = QLabel(constants.NOME_PLUGIN)
        titulo.setObjectName("dialogTitle")

        subtitulo = QLabel("Template de Mapa de Localização")
        subtitulo.setObjectName("dialogSubtitle")

        textos.addWidget(titulo)
        textos.addWidget(subtitulo)
        cabecalho.addLayout(textos)
        cabecalho.addStretch()

        layout.addLayout(cabecalho)

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

        lbl_obra = QLabel("Nome da obra")
        lbl_obra.setObjectName("fieldLabel")
        grupo_layout.addWidget(lbl_obra, 0, 0)

        lbl_preset = QLabel("Perfil rápido")
        lbl_preset.setObjectName("fieldLabel")
        grupo_layout.addWidget(lbl_preset, 0, 1)

        self.cmb_obra = QComboBox()
        self.cmb_obra.setEditable(True)
        self.cmb_obra.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.cmb_obra.setPlaceholderText("Selecione ou digite a obra")
        opcoes_obra = [f"{sigla} - {nome}" for sigla, nome in sorted(constants.OBRAS.items())]
        for texto in opcoes_obra:
            self.cmb_obra.addItem(texto)
        completer_obra = QCompleter(opcoes_obra, self.cmb_obra)
        completer_obra.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        completer_obra.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        self.cmb_obra.setCompleter(completer_obra)
        for indice, (sigla, _nome) in enumerate(sorted(constants.OBRAS.items())):
            self.cmb_obra.setItemData(indice, sigla)
        grupo_layout.addWidget(self.cmb_obra, 1, 0)

        self.cmb_preset = QComboBox()
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
        self.cmb_tipo.addItems(constants.TIPOS_PROJETO)
        grupo_layout.addWidget(self.cmb_tipo, 3, 0)

        self.cmb_zona = QComboBox()
        self.cmb_zona.addItems(constants.ZONAS_UTM)
        self.cmb_zona.setCurrentText(
            self._variaveis_salvas.get("zona_utm") or "AUTOMÁTICO"
        )
        grupo_layout.addWidget(self.cmb_zona, 3, 1)

        self.cmb_obra.currentIndexChanged.connect(self._atualizar_preview)
        self.cmb_obra.currentIndexChanged.connect(self._atualizar_estado_botao)
        self.cmb_tipo.currentIndexChanged.connect(self._atualizar_preview)
        self.cmb_tipo.currentIndexChanged.connect(self._atualizar_estado_botao)

        self.chk_modo_avancado = QCheckBox("Modo avançado")
        self.chk_modo_avancado.toggled.connect(self._alternar_modo_avancado)
        grupo_layout.addWidget(self.chk_modo_avancado, 4, 0, 1, 2)

        lbl_proj = QLabel("Sigla projetista")
        lbl_proj.setObjectName("fieldLabel")
        grupo_layout.addWidget(lbl_proj, 5, 0)

        lbl_verif = QLabel("Sigla verificação")
        lbl_verif.setObjectName("fieldLabel")
        grupo_layout.addWidget(lbl_verif, 5, 1)

        self.txt_sigla_projetista = QLineEdit()
        self.txt_sigla_projetista.setPlaceholderText("Ex.: CCC")
        grupo_layout.addWidget(self.txt_sigla_projetista, 6, 0)

        self.txt_sigla_verificacao = QLineEdit()
        self.txt_sigla_verificacao.setPlaceholderText("Ex.: JRM")
        grupo_layout.addWidget(self.txt_sigla_verificacao, 6, 1)

        self._alternar_modo_avancado(False)

        grupo_projeto.setLayout(grupo_layout)
        layout.addWidget(grupo_projeto)

        grupo_arquivo = QGroupBox("Arquivo de entrada")
        layout_arquivo = QVBoxLayout()
        layout_arquivo.setSpacing(8)

        self.btn_kml = QPushButton("📂 Importar KML/KMZ")
        self.btn_kml.clicked.connect(self._selecionar_arquivo)
        layout_arquivo.addWidget(self.btn_kml)

        self.lbl_status = QLabel("Nenhum arquivo importado")
        self.lbl_status.setObjectName("statusInfo")
        self.lbl_status.setWordWrap(True)
        layout_arquivo.addWidget(self.lbl_status)

        grupo_arquivo.setLayout(layout_arquivo)
        layout.addWidget(grupo_arquivo)

        grupo_destino = QGroupBox("Salvar projeto em")
        layout_destino = QVBoxLayout()
        layout_destino.setSpacing(8)

        linha_destino = QHBoxLayout()
        self.txt_pasta_projeto = QLineEdit()
        self.txt_pasta_projeto.setPlaceholderText("Escolha a pasta de destino")
        self.txt_pasta_projeto.textChanged.connect(self._atualizar_estado_botao)
        linha_destino.addWidget(self.txt_pasta_projeto, 1)

        self.btn_pasta_projeto = QPushButton("Selecionar pasta...")
        self.btn_pasta_projeto.clicked.connect(self._selecionar_pasta_projeto)
        linha_destino.addWidget(self.btn_pasta_projeto)

        self.btn_abrir_pasta_projeto = QPushButton("Abrir pasta")
        self.btn_abrir_pasta_projeto.clicked.connect(self._abrir_pasta_projeto)
        linha_destino.addWidget(self.btn_abrir_pasta_projeto)

        self.btn_copiar_caminho = QPushButton("Copiar caminho")
        self.btn_copiar_caminho.clicked.connect(self._copiar_caminho_projeto)
        linha_destino.addWidget(self.btn_copiar_caminho)

        self.btn_abrir_projeto = QPushButton("Abrir projeto")
        self.btn_abrir_projeto.setEnabled(False)
        self.btn_abrir_projeto.clicked.connect(self._abrir_projeto_gerado)
        linha_destino.addWidget(self.btn_abrir_projeto)

        self.btn_copiar_caminho.setEnabled(bool(self.txt_pasta_projeto.text().strip()))
        self.btn_abrir_projeto.setEnabled(bool(self.ultimo_projeto_gerado and os.path.isfile(self.ultimo_projeto_gerado)))
        layout_destino.addLayout(linha_destino)

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
        self.canvas_preview.setMinimumHeight(360)
        self.canvas_preview.enableAntiAliasing(True)
        self.canvas_preview.setBackgroundRole(QPalette.ColorRole.Window)

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
                "📍 PREVIEW DO EMPREENDIMENTO\n\n"
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

        self.spin_001 = self._criar_slider_escala(escala_layout, "001", "LAYOUT 1 (VERMELHO)", "lbl_001")
        self.spin_002 = self._criar_slider_escala(escala_layout, "002", "LAYOUT 2 (AZUL)", "lbl_002")
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

        self.spin_001.valueChanged.connect(self._desenhar_retangulos)
        self.spin_002.valueChanged.connect(self._desenhar_retangulos)
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

        valor_inicial = 5000
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
        self.btn_ok.setObjectName("btnGerar")
        self.btn_ok.clicked.connect(self.accept)
        botoes.addWidget(self.btn_ok, 2)

        self.btn_reset = QPushButton("Resetar template")
        self.btn_reset.setObjectName("btnReset")
        self.btn_reset.clicked.connect(self._resetar_template)
        botoes.addWidget(self.btn_reset, 1)

        layout.addLayout(botoes)

    def _alternar_modo_avancado(self, ativado: bool) -> None:
        if hasattr(self, "txt_sigla_projetista"):
            self.txt_sigla_projetista.setVisible(ativado)
        if hasattr(self, "txt_sigla_verificacao"):
            self.txt_sigla_verificacao.setVisible(ativado)
        if hasattr(self, "cmb_preset"):
            self.cmb_preset.setVisible(not ativado)
        if hasattr(self, "btn_ok"):
            self._atualizar_estado_botao()

    def _carregar_preset_salvo(self) -> None:
        preset_salvo = self.settings.value("EstelarTemplate/ultimo_preset", "Padrão", type=str)
        if preset_salvo in self._presets:
            self.cmb_preset.setCurrentText(preset_salvo)

    def _salvar_preset(self, nome: str) -> None:
        if nome in self._presets:
            self.settings.setValue("EstelarTemplate/ultimo_preset", nome)

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
        projeto_ok = bool(self.cmb_obra.currentData()) or bool(self.cmb_obra.currentText().strip())
        arquivo_ok = bool(self.arquivo)
        destino_ok = os.path.isdir(self.txt_pasta_projeto.text().strip())
        self.btn_ok.setEnabled(projeto_ok and arquivo_ok and destino_ok)

        if projeto_ok and arquivo_ok and destino_ok:
            self.lbl_status.setText(f"Pronto para gerar: {helpers.nome_do_arquivo(self.arquivo)}")
        elif projeto_ok and arquivo_ok:
            self.lbl_status.setText("Escolha a pasta onde o projeto será salvo")
        elif projeto_ok:
            self.lbl_status.setText("Selecione um arquivo KML/KMZ para continuar")
        elif arquivo_ok:
            self.lbl_status.setText("Selecione a obra antes de gerar o projeto")
        else:
            self.lbl_status.setText("Nenhum arquivo importado")

        self._atualizar_fluxo_geracao()
        self._atualizar_resumo_geracao()

    def _carregar_configuracao_destino(self) -> None:
        pasta_salva = self.settings.value("EstelarTemplate/ultima_pasta", "", type=str)
        if pasta_salva and os.path.isdir(pasta_salva):
            self.txt_pasta_projeto.setText(pasta_salva)
            self._atualizar_estado_botao()

    def _salvar_configuracao_destino(self) -> None:
        pasta = self.txt_pasta_projeto.text().strip()
        if pasta:
            self.settings.setValue("EstelarTemplate/ultima_pasta", pasta)

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
        rodape = QLabel(constants.RODAPE_TEXTO)
        rodape.setAlignment(Qt.AlignmentFlag.AlignRight)
        rodape.setStyleSheet("color: gray; font-size: 8pt;")
        layout.addWidget(rodape)

    # ------------------------------------------------------------------
    # Eventos / delegação para o pacote core
    # ------------------------------------------------------------------
    def _atualizar_preview(self) -> None:
        core_preview.atualizar_preview(self)

    def _desenhar_retangulos(self) -> None:
        core_preview.desenhar_retangulos(self)

    def _selecionar_arquivo(self) -> None:
        arquivo, _ = QFileDialog.getOpenFileName(
            self, "Selecione o arquivo", "", "Arquivos Google Earth (*.kml *.kmz)"
        )

        if not arquivo:
            return

        self.arquivo = arquivo
        self.btn_kml.setText(helpers.nome_do_arquivo(arquivo))
        self._atualizar_status(f"Arquivo carregado: {helpers.nome_do_arquivo(arquivo)}")

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
        obra = self.cmb_obra.currentData() or self.cmb_obra.currentText().strip()
        if not obra:
            QMessageBox.warning(self, constants.NOME_PLUGIN, "Selecione o nome da obra antes de continuar.")
            return

        if not self.arquivo:
            QMessageBox.warning(self, constants.NOME_PLUGIN, "Selecione um arquivo KML/KMZ antes de continuar.")
            return

        if not os.path.isdir(self.txt_pasta_projeto.text().strip()):
            QMessageBox.warning(self, constants.NOME_PLUGIN, "Selecione uma pasta válida para salvar o projeto.")
            return

        super().accept()
