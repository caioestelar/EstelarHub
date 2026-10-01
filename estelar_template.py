# -*- coding: utf-8 -*-
"""
/***************************************************************************
 EstelarTemplate
                                 A QGIS plugin
 Este plugin automatiza processos para padronizar os desenhos da Estelar

        begin                : 2026-09-23
        copyright            : (C) 2026 by CaioChiarello/ESTELAR ENGENHARIA ASSOCIADOS
        email                : caio@estelarengenharia.com.br
 ***************************************************************************/

Classe principal do plugin. Substitui por completo o uso da macro de
projeto `openProject` / `saveProject` / `closeProject`: toda a lógica agora
roda sob demanda, disparada pelo usuário através do ícone/menu do plugin
(método `run`), e não mais automaticamente ao abrir o projeto.
"""

import os.path

from qgis.PyQt.QtCore import QCoreApplication, QLocale, QTranslator
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction
from qgis.core import QgsSettings

from .core import projeto as core_projeto
from .core.modules.mapa_acesso import abrir as abrir_mapa_acesso
from .core.module_registry import criar_catalogo_estelar
from .ui.hub import EstelarHubDialog

class EstelarTemplate:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        self.iface = iface
        self.plugin_dir = os.path.dirname(__file__)

        # Internacionalização (mantido igual ao scaffold original).
        locale = QgsSettings().value("locale/userLocale", QLocale().name())[0:2]
        locale_path = os.path.join(self.plugin_dir, "i18n", f"EstelarTemplate_{locale}.qm")

        self.translator = None
        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)
            QCoreApplication.installTranslator(self.translator)

        self.actions = []
        self.menu = self.tr("&Estelar Hub")
        self.toolbar = self.iface.addToolBar("EstelarTemplate")
        self.toolbar.setObjectName("EstelarTemplate")

        self.first_start = None

        # Timer de atualização periódica (tabela de coordenadas + layouts).
        # Substitui o timer que, na macro original, era criado dentro do
        # gatilho `closeProject()` e nunca era interrompido.
        self.timer = None
        self.module_registry = criar_catalogo_estelar()
        self.module_registry.register_launcher(
            "access-map",
            lambda context=None: self._abrir_mapa_acesso(
                context.parent if context is not None else self.iface.mainWindow()
            ),
        )

    # ------------------------------------------------------------------
    def tr(self, message):
        return QCoreApplication.translate("EstelarTemplate", message)

    # ------------------------------------------------------------------
    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None,
    ):
        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            self.toolbar.addAction(action)

        if add_to_menu:
            self.iface.addPluginToMenu(self.menu, action)

        self.actions.append(action)

        return action

    # ------------------------------------------------------------------
    def initGui(self):
        icon_path = os.path.join(self.plugin_dir, "icon.png")

        self.add_action(
            icon_path,
            text="Estelar Hub",
            callback=self.run,
            status_tip=self.tr("Abrir o workspace de ferramentas Estelar"),
            parent=self.iface.mainWindow(),
        )

        self.first_start = True

        # Inicia o timer assim que o plugin é carregado: passa a manter a
        # tabela de coordenadas e os layouts atualizados durante toda a
        # sessão do QGIS, e não apenas de forma acidental ao fechar o
        # projeto (comportamento da macro original).
        self.timer = core_projeto.criar_timer_atualizacao()
        self.timer.start()

    def unload(self):
        for action in self.actions:
            self.iface.removePluginMenu(self.menu, action)
            self.iface.removeToolBarIcon(action)

        del self.toolbar

        if self.timer is not None:
            self.timer.stop()
            self.timer = None

    # ------------------------------------------------------------------
    def run(self):
        """Abre o Hub central de ferramentas Estelar."""
        dlg = EstelarHubDialog(self.module_registry, self.iface.mainWindow())
        dlg.exec()

    def _abrir_mapa_acesso(self, parent=None):
        """Carrega sob demanda o módulo Mapa de Acesso já existente."""
        abrir_mapa_acesso(parent or self.iface.mainWindow())
