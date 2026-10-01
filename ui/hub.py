"""Estelar Hub home screen and modular tool launcher."""

import os

from qgis.PyQt.QtCore import QEasingCurve, QPropertyAnimation, QSize, Qt, QTimer, QUrl
from qgis.PyQt.QtGui import QColor, QDesktopServices, QIcon, QPainter, QPainterPath, QPen, QPixmap
from qgis.PyQt.QtWidgets import (
    QApplication,
    QDialog,
    QFrame,
    QGraphicsOpacityEffect,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizeGrip,
    QToolButton,
    QVBoxLayout,
    QWidget,
)
from qgis.core import QgsApplication
from ..core.module_registry import ModuleRegistry
from ..estelar_hub.services.project_manager import ProjectManager
from ..estelar_hub.services.settings import SettingsService
from ..estelar_hub.module_context import ModuleContext


def _caminho_icone(pontos, fechar=False):
    caminho = QPainterPath()
    caminho.moveTo(*pontos[0])
    for ponto in pontos[1:]:
        caminho.lineTo(*ponto)
    if fechar:
        caminho.closeSubpath()
    return caminho


def criar_icone_hub(nome: str, cor: str = "#3b82f6", tamanho: int = 24) -> QIcon:
    """Desenha ícones vetoriais locais para manter a identidade do Hub sem emojis."""
    pixmap = QPixmap(tamanho, tamanho)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    escala = tamanho / 32.0
    painter.scale(escala, escala)
    painter.setPen(QPen(QColor(cor), 1.8, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
    painter.setBrush(Qt.BrushStyle.NoBrush)

    if nome == "road":
        esquerda = QPainterPath()
        esquerda.moveTo(7, 29)
        esquerda.cubicTo(11, 22, 9, 15, 13, 4)
        direita = QPainterPath()
        direita.moveTo(25, 29)
        direita.cubicTo(21, 22, 23, 15, 19, 4)
        painter.drawPath(esquerda)
        painter.drawPath(direita)
        painter.drawLine(16, 7, 16, 11)
        painter.drawLine(16, 15, 16, 19)
        painter.drawLine(16, 23, 16, 27)
    elif nome == "map":
        painter.drawPath(_caminho_icone([(4, 7), (12, 4), (20, 7), (28, 4), (28, 25), (20, 28), (12, 25), (4, 28), (4, 7)]))
        painter.drawLine(12, 4, 12, 25)
        painter.drawLine(20, 7, 20, 28)
        painter.drawEllipse(13, 11, 6, 6)
    elif nome == "sketch":
        painter.drawPath(_caminho_icone([(5, 25), (11, 17), (16, 20), (24, 8), (28, 12)]))
        painter.drawEllipse(20, 4, 9, 9)
        painter.drawEllipse(23, 7, 3, 3)
    elif nome == "document":
        painter.drawRoundedRect(7, 3, 18, 26, 2, 2)
        painter.drawLine(11, 11, 21, 11)
        painter.drawLine(11, 16, 21, 16)
        painter.drawLine(11, 21, 19, 21)
    elif nome == "coordinates":
        painter.drawRect(5, 5, 22, 22)
        painter.drawLine(16, 2, 16, 30)
        painter.drawLine(2, 16, 30, 16)
        painter.drawEllipse(13, 13, 6, 6)
    elif nome == "convert":
        painter.drawLine(5, 11, 26, 11)
        painter.drawLine(22, 7, 26, 11)
        painter.drawLine(26, 11, 22, 15)
        painter.drawLine(27, 21, 6, 21)
        painter.drawLine(10, 17, 6, 21)
        painter.drawLine(6, 21, 10, 25)
    elif nome == "globe":
        painter.drawEllipse(4, 4, 24, 24)
        painter.drawEllipse(11, 4, 10, 24)
        painter.drawLine(5, 12, 27, 12)
        painter.drawLine(5, 20, 27, 20)
    elif nome == "pdf":
        painter.drawPath(_caminho_icone([(8, 3), (20, 3), (25, 8), (25, 29), (8, 29), (8, 3)]))
        painter.drawLine(20, 3, 20, 8)
        painter.drawLine(20, 8, 25, 8)
        painter.drawLine(11, 17, 22, 17)
        painter.drawLine(11, 21, 22, 21)
    elif nome == "layout":
        painter.drawRect(4, 5, 24, 22)
        painter.drawLine(4, 12, 28, 12)
        painter.drawLine(15, 12, 15, 27)
        painter.drawLine(20, 17, 25, 17)
        painter.drawLine(20, 21, 25, 21)
    elif nome == "toolbox":
        painter.drawRoundedRect(5, 10, 22, 17, 3, 3)
        painter.drawPath(_caminho_icone([(11, 10), (11, 6), (21, 6), (21, 10)]))
        painter.drawLine(5, 16, 27, 16)
        painter.drawLine(14, 15, 14, 18)
        painter.drawLine(18, 15, 18, 18)
    elif nome == "search":
        painter.drawEllipse(4, 4, 17, 17)
        painter.drawLine(18, 18, 28, 28)
    elif nome == "star":
        painter.drawPath(_caminho_icone([(16, 3), (20, 12), (29, 13), (22, 19), (24, 28), (16, 23), (8, 28), (10, 19), (3, 13), (12, 12)], True))
    elif nome == "home":
        painter.drawPath(_caminho_icone([(4, 14), (16, 4), (28, 14), (25, 14), (25, 28), (18, 28), (18, 20), (13, 20), (13, 28), (7, 28), (7, 14), (4, 14)]))
    elif nome == "clock":
        painter.drawEllipse(4, 4, 24, 24)
        painter.drawLine(16, 8, 16, 16)
        painter.drawLine(16, 16, 22, 19)
    elif nome == "folder":
        painter.drawPath(_caminho_icone([(4, 8), (13, 8), (16, 11), (28, 11), (28, 25), (4, 25), (4, 8)]))
    elif nome == "minus":
        painter.drawLine(7, 16, 25, 16)
    elif nome == "close":
        painter.drawLine(8, 8, 24, 24)
        painter.drawLine(24, 8, 8, 24)

    painter.end()
    return QIcon(pixmap)


class HubTitleBar(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._drag_offset = None

    @staticmethod
    def _global_position(event):
        if hasattr(event, "globalPosition"):
            return event.globalPosition().toPoint()
        return event.globalPos()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_offset = self._global_position(event) - self.window().frameGeometry().topLeft()
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._drag_offset is not None and event.buttons() & Qt.MouseButton.LeftButton:
            self.window().move(self._global_position(event) - self._drag_offset)
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_offset = None
        super().mouseReleaseEvent(event)


class HubToolCard(QFrame):
    def __init__(self, module, favorite, launch, toggle_favorite, can_launch=True, parent=None):
        super().__init__(parent)
        self.module = module
        self.can_launch = bool(module.is_active and can_launch)
        self.setObjectName("hubToolCard")
        self.setProperty("moduleStatus", module.status)
        self.setCursor(Qt.CursorShape.PointingHandCursor if self.can_launch else Qt.CursorShape.ArrowCursor)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 13, 14, 12)
        layout.setSpacing(9)

        top = QHBoxLayout()
        top.setSpacing(10)
        icon_tile = QFrame()
        icon_tile.setObjectName("hubToolIconTile")
        icon_tile.setProperty("moduleStatus", module.status)
        icon_tile.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        icon_layout = QVBoxLayout(icon_tile)
        icon_layout.setContentsMargins(0, 0, 0, 0)
        icon = QLabel()
        icon.setPixmap(criar_icone_hub(module.icon, "#3b82f6", 25).pixmap(QSize(25, 25)))
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        icon_layout.addWidget(icon)
        top.addWidget(icon_tile)

        heading = QVBoxLayout()
        heading.setSpacing(4)
        title = QLabel(module.name)
        title.setObjectName("hubCardTitle")
        title.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        heading.addWidget(title)
        badge = QLabel("ATIVO" if module.is_active else "EM PREPARAÇÃO")
        badge.setObjectName("hubStatusBadge")
        badge.setProperty("moduleStatus", module.status)
        badge.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        heading.addWidget(badge, 0, Qt.AlignmentFlag.AlignLeft)
        top.addLayout(heading, 1)

        self.favorite_button = QToolButton()
        self.favorite_button.setObjectName("hubFavoriteButton")
        self.favorite_button.setCheckable(True)
        self.favorite_button.setChecked(favorite)
        self.favorite_button.setIcon(criar_icone_hub("star", "#3b82f6" if favorite else "#77777b", 17))
        self.favorite_button.setIconSize(QSize(17, 17))
        self.favorite_button.setToolTip("Remover dos favoritos" if favorite else "Adicionar aos favoritos")
        self.favorite_button.setAccessibleName(self.favorite_button.toolTip())
        self.favorite_button.clicked.connect(lambda: toggle_favorite(module.id))
        top.addWidget(self.favorite_button, 0, Qt.AlignmentFlag.AlignTop)
        layout.addLayout(top)

        description = QLabel(module.description)
        description.setObjectName("hubCardDescription")
        description.setWordWrap(True)
        description.setMinimumHeight(34)
        description.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        layout.addWidget(description, 1)

        footer = QHBoxLayout()
        category = QLabel(module.category)
        category.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        footer.addWidget(category)
        footer.addStretch()
        self.launch_button = QPushButton(f"Abrir {module.name}" if self.can_launch else "Indisponível")
        self.launch_button.setObjectName("hubLaunchButton" if self.can_launch else "hubUpcomingButton")
        self.launch_button.setIcon(criar_icone_hub(module.icon if self.can_launch else "clock", "#ffffff" if self.can_launch else "#8b8b90", 16))
        self.launch_button.setIconSize(QSize(16, 16))
        self.launch_button.setEnabled(self.can_launch)
        self.launch_button.setToolTip(f"Abrir {module.name}" if self.can_launch else "Este módulo não está disponível para abertura")
        self.launch_button.clicked.connect(lambda: launch(module.id))
        footer.addWidget(self.launch_button)
        layout.addLayout(footer)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.can_launch:
            self.launch_button.click()
            event.accept()
            return
        super().mouseReleaseEvent(event)


class EstelarHubDialog(QDialog):
    def __init__(self, registry: ModuleRegistry, parent=None, project_manager=None,
                 settings=None, processing_service=None, logger=None,
                 error_service=None, update_service=None):
        super().__init__(parent)
        self.registry = registry
        self.settings = settings or SettingsService()
        self.project_manager = project_manager or ProjectManager(self.settings)
        self.processing_service = processing_service
        self.logger = logger
        self.error_service = error_service
        self.update_service = update_service
        self._filter = "all"
        self._cards = {}
        self._groups = {}
        self._favorite_ids = set(self.settings.value("EstelarHub/favorites", [], type=list))
        self._recent_projects = self._load_recent_projects()
        self._current_project_path = self.project_manager.current_path()
        self._remember_project(self._current_project_path)

        if self.update_service is not None:
            self.update_service.update_available.connect(self._update_available)
            self.update_service.up_to_date.connect(self._up_to_date)
            self.update_service.check_failed.connect(self._update_check_failed)
            self.update_service.installer_downloaded.connect(self._installer_downloaded)

        self.setObjectName("estelarHubDialog")
        self.setWindowTitle("Estelar Hub")
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        self._set_initial_size()
        self._load_styles()
        self._build_ui()

    def _set_initial_size(self):
        screen = QApplication.primaryScreen()
        if screen is None:
            self.resize(1280, 800)
            self.setMinimumSize(940, 620)
            return
        available = screen.availableGeometry()
        self.resize(min(1460, max(1020, available.width() - 48)), min(900, max(680, available.height() - 56)))
        self.setMinimumSize(940, 620)
        self.setMaximumSize(1800, 1100)

    def _load_styles(self):
        style_path = os.path.join(os.path.dirname(__file__), "styles.qss")
        try:
            with open(style_path, "r", encoding="utf-8") as style_file:
                self.setStyleSheet(style_file.read())
        except OSError:
            pass

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.addWidget(self._build_header())

        workspace = QWidget()
        workspace.setObjectName("hubWorkspace")
        workspace_layout = QHBoxLayout(workspace)
        workspace_layout.setContentsMargins(0, 0, 0, 0)
        workspace_layout.setSpacing(0)

        self.sidebar = self._build_sidebar()
        workspace_layout.addWidget(self.sidebar)
        self.main_scroll = self._build_main_content()
        workspace_layout.addWidget(self.main_scroll, 1)
        workspace_layout.addWidget(self._build_status_panel())
        root.addWidget(workspace, 1)
        root.addWidget(self._build_footer())

        effect = QGraphicsOpacityEffect(workspace)
        effect.setOpacity(0.55)
        workspace.setGraphicsEffect(effect)
        self._entry_animation = QPropertyAnimation(effect, b"opacity", self)
        self._entry_animation.setDuration(240)
        self._entry_animation.setStartValue(0.55)
        self._entry_animation.setEndValue(1.0)
        self._entry_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        QTimer.singleShot(0, self._entry_animation.start)

    def _build_header(self):
        header = HubTitleBar(self)
        header.setObjectName("hubHeader")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(20, 8, 16, 8)
        header_layout.setSpacing(11)

        logo = QLabel()
        logo_path = os.path.join(os.path.dirname(__file__), "assets", "logo.png")
        pixmap = QPixmap(logo_path)
        if not pixmap.isNull():
            logo.setPixmap(pixmap.scaled(38, 38, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        logo.setFixedSize(40, 40)
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        header_layout.addWidget(logo)

        brand = QVBoxLayout()
        brand.setSpacing(2)
        title = QLabel("Estelar Hub")
        title.setObjectName("hubBrandTitle")
        subtitle = QLabel("Workspace de engenharia GIS")
        subtitle.setObjectName("hubBrandSubtitle")
        title.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        subtitle.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        brand.addWidget(title)
        brand.addWidget(subtitle)
        header_layout.addLayout(brand)
        header_layout.addStretch()

        project_name = os.path.basename(self._current_project_path) if self._current_project_path else "Projeto não salvo"
        status = QLabel(project_name)
        status.setObjectName("hubHeaderProject")
        status.setToolTip(self._current_project_path or "O projeto atual do QGIS ainda não foi salvo")
        status.setMaximumWidth(300)
        status.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        header_layout.addWidget(status)
        self.header_project_label = status

        minimize = QToolButton()
        minimize.setObjectName("btnMinimize")
        minimize.setIcon(criar_icone_hub("minus", "#c8c8ca", 16))
        minimize.setIconSize(QSize(16, 16))
        minimize.setToolTip("Minimizar janela")
        minimize.clicked.connect(self.showMinimized)
        header_layout.addWidget(minimize)

        close = QToolButton()
        close.setObjectName("btnClose")
        close.setIcon(criar_icone_hub("close", "#c8c8ca", 16))
        close.setIconSize(QSize(16, 16))
        close.setToolTip("Fechar Hub")
        close.clicked.connect(self.reject)
        header_layout.addWidget(close)
        return header

    def _build_sidebar(self):
        sidebar = QFrame()
        sidebar.setObjectName("hubSidebar")
        sidebar.setFixedWidth(196)
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(14, 18, 12, 14)
        layout.setSpacing(5)

        heading = QLabel("WORKSPACE")
        heading.setObjectName("hubNavHeading")
        layout.addWidget(heading)

        self._navigation = {}
        for key, text, icon in (
            ("home", "Início", "home"),
            ("tools", "Ferramentas", "toolbox"),
            ("favorites", "Favoritos", "star"),
            ("recent", "Projetos recentes", "clock"),
        ):
            button = QPushButton(text)
            button.setObjectName("hubNavButton")
            button.setIcon(criar_icone_hub(icon, "#8b8b90", 18))
            button.setIconSize(QSize(18, 18))
            button.setCheckable(True)
            button.setChecked(key == "home")
            button.clicked.connect(lambda _checked=False, nav_key=key: self._navigate(nav_key))
            layout.addWidget(button)
            self._navigation[key] = button

        layout.addSpacing(18)
        category_heading = QLabel("CATEGORIAS")
        category_heading.setObjectName("hubNavHeading")
        layout.addWidget(category_heading)
        for category, icon in (("Cartografia", "map"), ("Documentação", "document"), ("Coordenadas", "coordinates"), ("Publicação", "pdf")):
            button = QPushButton(category)
            button.setObjectName("hubCategoryButton")
            button.setIcon(criar_icone_hub(icon, "#77777b", 16))
            button.setIconSize(QSize(16, 16))
            button.clicked.connect(lambda _checked=False, value=category: self._filter_category(value))
            layout.addWidget(button)

        layout.addStretch()
        note = QLabel("Ferramentas integradas ao seu fluxo de trabalho no QGIS.")
        note.setObjectName("hubSidebarNote")
        note.setWordWrap(True)
        layout.addWidget(note)
        return sidebar

    def _build_main_content(self):
        scroll = QScrollArea()
        scroll.setObjectName("hubMainScroll")
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        content = QWidget()
        content.setObjectName("hubMainContent")
        layout = QVBoxLayout(content)
        layout.setContentsMargins(25, 22, 25, 24)
        layout.setSpacing(18)

        layout.addWidget(self._build_current_project_section())

        self.recent_section = self._build_recent_section()
        layout.addWidget(self.recent_section)

        self.favorites_section = QWidget()
        favorites_layout = QVBoxLayout(self.favorites_section)
        favorites_layout.setContentsMargins(0, 0, 0, 0)
        favorites_layout.setSpacing(9)
        favorites_layout.addWidget(self._section_heading("Favoritos", "Ferramentas fixadas para acesso rápido"))
        self._favorites_content = QHBoxLayout()
        self._favorites_content.setSpacing(8)
        favorites_layout.addLayout(self._favorites_content)
        self._favorites_empty = QLabel("Use a estrela de uma ferramenta para fixá-la aqui.")
        self._favorites_empty.setObjectName("hubEmptyHint")
        favorites_layout.addWidget(self._favorites_empty)
        layout.addWidget(self.favorites_section)

        self.search = QLineEdit()
        self.search.setObjectName("hubSearch")
        self.search.setPlaceholderText("Buscar módulos por nome, descrição ou categoria")
        self.search.setAccessibleName("Buscar ferramentas")
        self.search.setToolTip("Filtra ferramentas disponíveis e em preparação; projetos recentes não são pesquisados.")
        self.search.setClearButtonEnabled(True)
        self.search.addAction(criar_icone_hub("search", "#858589", 18), QLineEdit.ActionPosition.LeadingPosition)
        self.search.textChanged.connect(self._apply_filter)
        layout.addWidget(self.search)

        self.active_section, self._active_grid = self._build_tool_section(
            "Ferramentas disponíveis",
            "Módulos que podem ser abertos nesta instalação",
        )
        layout.addWidget(self.active_section)

        self.upcoming_section = self._build_upcoming_section()
        layout.addWidget(self.upcoming_section)
        layout.addStretch(1)

        self._add_module_cards()
        self._render_favorites()
        self._render_recent_projects()
        scroll.setWidget(content)
        self._main_content = content
        return scroll

    def _section_heading(self, title_text, subtitle_text=None):
        section = QWidget()
        row = QHBoxLayout(section)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(10)
        text = QVBoxLayout()
        text.setSpacing(3)
        title = QLabel(title_text)
        title.setObjectName("hubSectionTitle")
        text.addWidget(title)
        if subtitle_text:
            subtitle = QLabel(subtitle_text)
            subtitle.setObjectName("hubSectionSubtitle")
            text.addWidget(subtitle)
        row.addLayout(text)
        row.addStretch()
        return section

    def _build_quick_actions(self, parent_layout):
        row = QHBoxLayout()
        row.setSpacing(9)
        launch = QPushButton("Abrir Mapa de Acesso")
        launch.setObjectName("hubPrimaryAction")
        launch.setIcon(criar_icone_hub("road", "#ffffff", 17))
        launch.setIconSize(QSize(17, 17))
        launch.clicked.connect(lambda: self._launch_module("access-map"))
        row.addWidget(launch)

        open_folder = QPushButton("Pasta do projeto")
        open_folder.setObjectName("hubSecondaryAction")
        open_folder.setIcon(criar_icone_hub("folder", "#a6a6aa", 17))
        open_folder.setIconSize(QSize(17, 17))
        open_folder.setEnabled(bool(self._current_project_path and os.path.isfile(self._current_project_path)))
        open_folder.setToolTip("Abrir a pasta do projeto atual no Explorador de Arquivos")
        open_folder.clicked.connect(self._open_current_project_folder)
        row.addWidget(open_folder)
        self.open_folder_button = open_folder
        row.addStretch(1)
        parent_layout.addLayout(row)

    def _build_tool_section(self, title_text, subtitle_text):
        section = QWidget()
        layout = QVBoxLayout(section)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        layout.addWidget(self._section_heading(title_text, subtitle_text))
        grid = QGridLayout()
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(10)
        grid.setVerticalSpacing(10)
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)
        layout.addLayout(grid)
        return section, grid

    def _build_recent_section(self):
        section = QWidget()
        layout = QVBoxLayout(section)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(9)
        layout.addWidget(self._section_heading("Projetos recentes", "Projetos abertos nesta sessão do Hub"))
        self._recent_content = QVBoxLayout()
        self._recent_content.setSpacing(7)
        layout.addLayout(self._recent_content)
        return section

    def _build_status_panel(self):
        panel = QFrame()
        panel.setObjectName("hubStatusPanel")
        panel.setFixedWidth(270)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(16, 20, 16, 16)
        layout.setSpacing(12)

        heading = QLabel("Workspace")
        heading.setObjectName("hubSideHeading")
        layout.addWidget(heading)

        project_box = QFrame()
        project_box.setObjectName("hubContextBlock")
        project_layout = QVBoxLayout(project_box)
        project_layout.setContentsMargins(12, 12, 12, 12)
        project_layout.setSpacing(7)
        project_state = QLabel("PROJETO ATUAL")
        project_state.setObjectName("hubEyebrow")
        project_layout.addWidget(project_state)
        project_name = os.path.basename(self._current_project_path) if self._current_project_path else "Projeto não salvo"
        self.project_name_label = QLabel(project_name)
        self.project_name_label.setObjectName("hubContextTitle")
        self.project_name_label.setWordWrap(True)
        project_layout.addWidget(self.project_name_label)
        project_detail = self._current_project_path or "Salve o projeto no QGIS para registrá-lo nos recentes."
        self.project_detail_label = QLabel(project_detail)
        self.project_detail_label.setObjectName("hubContextDetail")
        self.project_detail_label.setWordWrap(True)
        project_layout.addWidget(self.project_detail_label)
        layout.addWidget(project_box)

        layout.addWidget(self._divider())
        counts_heading = QLabel("FERRAMENTAS")
        counts_heading.setObjectName("hubEyebrow")
        layout.addWidget(counts_heading)
        active_count = sum(1 for module in self.registry.modules() if module.is_active)
        upcoming_count = len(self.registry.modules()) - active_count
        counts = QHBoxLayout()
        counts.addWidget(self._stat_block(str(active_count), "Ativa"))
        counts.addWidget(self._stat_block(str(upcoming_count), "Em preparação"))
        layout.addLayout(counts)

        layout.addWidget(self._divider())
        qgis_status = QLabel("SESSÃO QGIS")
        qgis_status.setObjectName("hubEyebrow")
        layout.addWidget(qgis_status)
        status_row = QHBoxLayout()
        indicator = QLabel()
        indicator.setObjectName("hubOnlineIndicator")
        indicator.setFixedSize(8, 8)
        status_row.addWidget(indicator, 0, Qt.AlignmentFlag.AlignVCenter)
        status_text = QLabel("Conectado ao QGIS")
        status_text.setObjectName("hubContextTitle")
        status_row.addWidget(status_text)
        status_row.addStretch()
        layout.addLayout(status_row)
        status_detail = QLabel("O Hub compartilha o projeto, as camadas e o ambiente GIS atual.")
        status_detail.setObjectName("hubContextDetail")
        status_detail.setWordWrap(True)
        layout.addWidget(status_detail)

        layout.addStretch(1)
        version = self._read_plugin_version()
        version_label = QLabel(f"Estelar Hub · versão {version}")
        version_label.setObjectName("hubVersionLabel")
        layout.addWidget(version_label)
        self.update_button = QPushButton("Verificar atualizações")
        self.update_button.setObjectName("hubUpdateButton")
        self.update_button.setVisible(self.update_service is not None)
        self.update_button.clicked.connect(self._check_updates)
        layout.addWidget(self.update_button)
        return panel

    def _build_footer(self):
        footer = QFrame()
        footer.setObjectName("hubFooter")
        layout = QHBoxLayout(footer)
        layout.setContentsMargins(18, 5, 10, 5)
        layout.setSpacing(8)
        status = QLabel("ESTELAR ENGENHARIA · AMBIENTE DE TRABALHO GIS")
        status.setObjectName("hubFooterText")
        layout.addWidget(status)
        layout.addStretch()
        grip = QSizeGrip(self)
        grip.setObjectName("windowResizeGrip")
        grip.setFixedSize(14, 14)
        layout.addWidget(grip)
        return footer

    @staticmethod
    def _divider():
        line = QFrame()
        line.setObjectName("hubDivider")
        line.setFrameShape(QFrame.Shape.HLine)
        return line

    @staticmethod
    def _stat_block(value, label):
        block = QFrame()
        block.setObjectName("hubStatBlock")
        layout = QVBoxLayout(block)
        layout.setContentsMargins(10, 9, 10, 9)
        layout.setSpacing(3)
        value_label = QLabel(value)
        value_label.setObjectName("hubStatValue")
        layout.addWidget(value_label)
        caption = QLabel(label)
        caption.setObjectName("hubStatCaption")
        layout.addWidget(caption)
        return block

    def _load_recent_projects(self):
        return self.project_manager.recent_projects()

    def _remember_project(self, path):
        self.project_manager.remember(path)
        self._recent_projects = self.project_manager.recent_projects()

    @staticmethod
    def _read_plugin_version():
        application_root = os.path.dirname(os.path.dirname(__file__))
        version_path = os.path.join(application_root, "VERSION")
        metadata_path = os.path.join(application_root, "metadata.txt")
        try:
            with open(version_path, "r", encoding="utf-8") as version_file:
                return version_file.read().strip()
        except OSError:
            try:
                with open(metadata_path, "r", encoding="utf-8") as metadata_file:
                    for line in metadata_file:
                        if line.startswith("version="):
                            return line.partition("=")[2].strip()
            except OSError:
                pass
        return "—"

    def _render_recent_projects(self):
        while self._recent_content.count():
            item = self._recent_content.takeAt(0)
            if item.widget() is not None:
                item.widget().deleteLater()

        if not self._recent_projects:
            empty = QLabel("Nenhum projeto recente salvo. Abra ou salve um projeto no QGIS para vê-lo aqui.")
            empty.setObjectName("hubEmptyHint")
            empty.setWordWrap(True)
            self._recent_content.addWidget(empty)
            return

        for path in self._recent_projects:
            row = QFrame()
            row.setObjectName("hubRecentRow")
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(10, 8, 10, 8)
            row_layout.setSpacing(9)
            icon = QLabel()
            icon.setPixmap(criar_icone_hub("document", "#858589", 18).pixmap(QSize(18, 18)))
            row_layout.addWidget(icon)
            text = QVBoxLayout()
            text.setSpacing(2)
            name = QLabel(os.path.basename(path))
            name.setObjectName("hubRecentName")
            detail = QLabel(os.path.dirname(path))
            detail.setObjectName("hubRecentPath")
            detail.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            text.addWidget(name)
            text.addWidget(detail)
            row_layout.addLayout(text, 1)
            open_folder = QToolButton()
            open_folder.setObjectName("hubSmallAction")
            open_folder.setIcon(criar_icone_hub("document", "#858589", 16))
            open_folder.setIconSize(QSize(16, 16))
            open_folder.setToolTip("Abrir este projeto no Estelar Hub")
            open_folder.clicked.connect(lambda _checked=False, project_path=path: self._open_recent_project(project_path))
            row_layout.addWidget(open_folder)

            show_folder = QToolButton()
            show_folder.setObjectName("hubSmallAction")
            show_folder.setIcon(criar_icone_hub("folder", "#858589", 16))
            show_folder.setIconSize(QSize(16, 16))
            show_folder.setToolTip("Mostrar a pasta do projeto")
            show_folder.clicked.connect(lambda _checked=False, folder=os.path.dirname(path): self._open_folder(folder))
            row_layout.addWidget(show_folder)
            self._recent_content.addWidget(row)

    def _add_module_cards(self):
        active_modules = [module for module in self.registry.modules() if module.is_active]
        upcoming_modules = [module for module in self.registry.modules() if not module.is_active]

        for index, module in enumerate(active_modules):
            card = HubToolCard(
                module,
                module.id in self._favorite_ids,
                self._launch_module,
                self._toggle_favorite,
            )
            self._cards[module.id] = card
            self._active_grid.addWidget(card, index, 0, 1, 2)

        for index, module in enumerate(upcoming_modules):
            card = HubToolCard(
                module,
                module.id in self._favorite_ids,
                self._launch_module,
                self._toggle_favorite,
            )
            self._cards[module.id] = card
            row, column = divmod(index, 2)
            self._upcoming_grid.addWidget(card, row, column)

        self._apply_filter()

    def _render_favorites(self):
        while self._favorites_content.count():
            item = self._favorites_content.takeAt(0)
            if item.widget() is not None:
                item.widget().deleteLater()

        favorites = [module for module in self.registry.modules() if module.id in self._favorite_ids]
        self._favorites_empty.setVisible(not favorites)
        for module in favorites:
            shortcut = QPushButton(module.name)
            shortcut.setObjectName("hubFavoriteShortcut")
            shortcut.setIcon(criar_icone_hub(module.icon, "#3b82f6" if module.is_active else "#77777b", 17))
            shortcut.setIconSize(QSize(17, 17))
            shortcut.setEnabled(module.is_active and self.registry.can_launch(module.id))
            shortcut.clicked.connect(lambda _checked=False, module_id=module.id: self._launch_module(module_id))
            self._favorites_content.addWidget(shortcut)
        self._favorites_content.addStretch(1)

    def _toggle_favorite(self, module_id):
        if module_id in self._favorite_ids:
            self._favorite_ids.remove(module_id)
        else:
            self._favorite_ids.add(module_id)
        self.settings.setValue("EstelarHub/favorites", sorted(self._favorite_ids))
        card = self._cards.get(module_id)
        if card is not None:
            is_favorite = module_id in self._favorite_ids
            card.favorite_button.setChecked(is_favorite)
            card.favorite_button.setIcon(criar_icone_hub("star", "#3b82f6" if is_favorite else "#77777b", 17))
            card.favorite_button.setToolTip("Remover dos favoritos" if is_favorite else "Adicionar aos favoritos")
            card.favorite_button.setAccessibleName(card.favorite_button.toolTip())
        self._render_favorites()
        if self._filter == "favorites":
            self._apply_filter()

    def _apply_filter(self, *_args):
        query = self.search.text().strip().casefold()
        visible_active = 0
        visible_upcoming = 0
        for module in self.registry.modules():
            card = self._cards[module.id]
            searchable = f"{module.name} {module.description} {module.category}".casefold()
            matches_search = not query or query in searchable
            matches_filter = self._filter != "favorites" or module.id in self._favorite_ids
            visible = matches_search and matches_filter
            card.setVisible(visible)
            if visible:
                if module.is_active:
                    visible_active += 1
                else:
                    visible_upcoming += 1

        self.active_section.setVisible(visible_active > 0)
        self.upcoming_section.setVisible(visible_upcoming > 0)

    def _navigate(self, key):
        self._filter = "favorites" if key == "favorites" else "all"
        for nav_key, button in self._navigation.items():
            button.setChecked(nav_key == key)
        self._apply_filter()

        if key == "home":
            self.main_scroll.verticalScrollBar().setValue(0)
        elif key == "tools":
            self.main_scroll.ensureWidgetVisible(self.active_section, 0, 20)
        elif key == "favorites":
            self.main_scroll.ensureWidgetVisible(self.favorites_section, 0, 20)
        elif key == "recent":
            self.main_scroll.ensureWidgetVisible(self.recent_section, 0, 20)

    def _filter_category(self, category):
        self._filter = "all"
        for nav_key, button in self._navigation.items():
            button.setChecked(nav_key == "tools")
        self.search.setText(category)
        self._apply_filter()
        self.main_scroll.ensureWidgetVisible(self.active_section, 0, 20)

    def _launch_module(self, module_id):
        if not self.registry.can_launch(module_id):
            return
        self.hide()
        try:
            context = ModuleContext(
                application=QgsApplication.instance(),
                parent=self,
                settings=self.settings,
                project_manager=self.project_manager,
                processing_service=self.processing_service,
                logger=self.logger,
                error_service=self.error_service,
                update_service=self.update_service,
            )
            self.registry.launch(module_id, context)
        except Exception as error:
            if self.error_service is not None:
                self.error_service.report(self, "Falha ao abrir ferramenta", str(error), error)
            else:
                QMessageBox.critical(self, "Falha ao abrir ferramenta", str(error))
        finally:
            self._refresh_project_context()
            self.show()
            self.raise_()
            self.activateWindow()

    def _refresh_project_context(self):
        self._current_project_path = self.project_manager.current_path()
        self._remember_project(self._current_project_path)
        project_name = os.path.basename(self._current_project_path) if self._current_project_path else "Projeto não salvo"
        self.header_project_label.setText(project_name)
        self.header_project_label.setToolTip(self._current_project_path or "O projeto atual do QGIS ainda não foi salvo")
        self.project_name_label.setText(project_name)
        self.project_detail_label.setText(
            self._current_project_path or "Salve o projeto no QGIS para registrá-lo nos recentes."
        )
        self.open_folder_button.setEnabled(
            bool(self._current_project_path and os.path.isfile(self._current_project_path))
        )
        self._render_recent_projects()

    def _open_recent_project(self, path):
        try:
            self.project_manager.open_project(path)
        except Exception as error:
            QMessageBox.warning(self, "Não foi possível abrir o projeto", str(error))
            return
        self._refresh_project_context()

    def _check_updates(self):
        if self.update_service is None:
            return
        self.update_button.setEnabled(False)
        self.update_button.setText("Verificando…")
        self.update_service.check_for_updates(self._read_plugin_version())

    def _update_available(self, release):
        self.update_button.setEnabled(True)
        self.update_button.setText("Verificar atualizações")
        resposta = QMessageBox.question(
            self,
            "Atualização disponível",
            f"Estelar Hub {release['version']} está disponível.\n\nBaixar o instalador e iniciar a atualização?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if resposta == QMessageBox.StandardButton.Yes:
            self.update_button.setEnabled(False)
            self.update_button.setText("Baixando instalador…")
            self.update_service.download_installer(release)

    def _installer_downloaded(self, installer_path):
        resposta = QMessageBox.question(
            self,
            "Instalador pronto",
            "O instalador foi baixado. Fechar o Estelar Hub e iniciar a atualização?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        self.update_button.setEnabled(True)
        self.update_button.setText("Verificar atualizações")
        if resposta == QMessageBox.StandardButton.Yes:
            QDesktopServices.openUrl(QUrl.fromLocalFile(installer_path))
            QTimer.singleShot(250, self.close)

    def _up_to_date(self, _release):
        self.update_button.setEnabled(True)
        self.update_button.setText("Verificar atualizações")
        QMessageBox.information(self, "Estelar Hub atualizado", "Você já está usando a versão mais recente.")

    def _update_check_failed(self, message):
        self.update_button.setEnabled(True)
        self.update_button.setText("Verificar atualizações")
        if self.logger is not None:
            self.logger.warning("Update check failed: %s", message)
        QMessageBox.warning(self, "Não foi possível verificar atualizações", message)

    def _open_current_project_folder(self):
        if self._current_project_path and os.path.isfile(self._current_project_path):
            self._open_folder(os.path.dirname(self._current_project_path))

    @staticmethod
    def _open_folder(path):
        if path and os.path.isdir(path):
            QDesktopServices.openUrl(QUrl.fromLocalFile(path))
