"""Standalone Estelar Hub startup and application composition root."""

from pathlib import Path
import sys

from ..core.module_registry import criar_catalogo_estelar
from ..core.modules.mapa_acesso import abrir as abrir_mapa_acesso
from ..core.projeto import criar_timer_atualizacao
from ..ui.hub import EstelarHubDialog
from .module_manager import ModuleManager
from .runtime import QgisRuntime
from .services.error_service import ErrorService
from .services.logging_service import configurar_logger
from .services.project_manager import ProjectManager
from .services.processing_service import ProcessingService
from .services.settings import SettingsService
from .services.update_service import UpdateService


def main(prefix_path):
    runtime = QgisRuntime(prefix_path)
    application = None
    refresh_timer = None
    hub = None
    error_service = None
    try:
        application = runtime.start()
        logger = configurar_logger()
        error_service = ErrorService(logger)
        error_service.install()
        settings = SettingsService()
        project_manager = ProjectManager(settings)
        processing_service = ProcessingService()
        update_service = UpdateService(parent=application)
        module_manager = ModuleManager(
            criar_catalogo_estelar(),
            ModuleManager.default_module_roots(Path(sys.argv[0]).resolve().parent),
            logger,
        )
        module_manager.discover()
        module_manager.register_launcher(
            "access-map",
            lambda context: abrir_mapa_acesso(context.parent),
        )
        hub = EstelarHubDialog(
            module_manager,
            project_manager=project_manager,
            settings=settings,
            processing_service=processing_service,
            logger=logger,
            error_service=error_service,
            update_service=update_service,
        )

        refresh_timer = criar_timer_atualizacao()
        refresh_timer.start()
        hub.show()
        return application.exec()
    finally:
        if refresh_timer is not None:
            refresh_timer.stop()
        if hub is not None:
            hub.close()
        if error_service is not None:
            error_service.restore()
        runtime.stop()