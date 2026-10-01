"""Shared QGIS project and recent-project management."""

import os

from qgis.core import QgsProject


class ProjectManager:
    RECENTS_KEY = "EstelarHub/recentProjects"
    MAX_RECENTS = 8

    def __init__(self, settings):
        self.settings = settings

    def current_path(self):
        return QgsProject.instance().fileName()

    def recent_projects(self):
        stored = self.settings.value(self.RECENTS_KEY, [], list)
        if isinstance(stored, str):
            stored = [stored]
        return [path for path in stored if isinstance(path, str) and os.path.isfile(path)][:self.MAX_RECENTS]

    def remember(self, path):
        if not path or not os.path.isfile(path):
            return
        projects = [path] + [item for item in self.recent_projects() if item != path]
        self.settings.set_value(self.RECENTS_KEY, projects[:self.MAX_RECENTS])

    def open_project(self, path):
        project_path = os.path.abspath(os.path.expanduser(path))
        if not os.path.isfile(project_path):
            raise FileNotFoundError(f"Projeto QGIS não encontrado: {project_path}")
        if not QgsProject.instance().read(project_path):
            raise RuntimeError(f"Não foi possível abrir o projeto: {project_path}")
        self.remember(project_path)
        return project_path

    def save_project(self, path=None):
        project = QgsProject.instance()
        project_path = os.path.abspath(path or project.fileName()) if (path or project.fileName()) else ""
        if not project_path:
            raise ValueError("Informe o caminho para salvar o projeto QGIS.")
        os.makedirs(os.path.dirname(project_path), exist_ok=True)
        if not project.write(project_path):
            raise OSError(f"Não foi possível salvar o projeto: {project_path}")
        self.remember(project_path)
        return project_path