"""Launcher adapter for the existing Mapa de Acesso module."""

from qgis.core import QgsProject

from .. import projeto as core_projeto
from ..carregar_bases import carregar_bases_estelar


def abrir(parent=None) -> bool:
    """Run the established Mapa de Acesso form and generation workflow."""
    carregar_bases_estelar()
    projeto = QgsProject.instance()

    if core_projeto.obra_ja_configurada(projeto):
        if not core_projeto.confirmar_reconfiguracao(parent):
            return False

    from ...ui.janela_projeto import JanelaProjeto

    dialogo = JanelaProjeto(parent)
    if not dialogo.exec():
        return False

    return core_projeto.gerar_projeto(dialogo)