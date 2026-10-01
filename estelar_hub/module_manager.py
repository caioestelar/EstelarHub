"""Discoverable module installation and lazy launch management."""

import logging
import os
from pathlib import Path

from qgis.PyQt.QtCore import QStandardPaths


class ModuleManager:
    def __init__(self, registry, module_roots=(), logger=None):
        self.registry = registry
        self.module_roots = [Path(root) for root in module_roots]
        self.logger = logger or logging.getLogger("EstelarHub.modules")
        self.discovery_errors = []

    def discover(self):
        self.discovery_errors = self.registry.discover_manifests(self.module_roots)
        for path, message in self.discovery_errors:
            self.logger.error("Invalid Hub module manifest %s: %s", path, message)
        return tuple(self.discovery_errors)

    def modules(self):
        return self.registry.modules()

    def get(self, module_id):
        return self.registry.get(module_id)

    def can_launch(self, module_id):
        return self.registry.can_launch(module_id)

    def register_launcher(self, module_id, launcher):
        self.registry.register_launcher(module_id, launcher)

    def launch(self, module_id, context=None):
        return self.registry.launch(module_id, context)

    @staticmethod
    def default_module_roots(application_directory=None):
        roots = []
        if application_directory:
            roots.append(Path(application_directory) / "modules")

        user_data = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppDataLocation)
        if user_data:
            roots.append(Path(user_data) / "modules")

        program_data = os.environ.get("PROGRAMDATA")
        if program_data:
            roots.append(Path(program_data) / "Estelar Hub" / "modules")

        return tuple(dict.fromkeys(roots))