"""Catalog and lazy launcher registry for Estelar Hub modules."""

import importlib
import json
import sys
from pathlib import Path


class ModuleDefinition:
    def __init__(self, module_id, name, description, icon, category, status,
                 version="1.0.0", entry_point=None, source_path=None):
        self.id = module_id
        self.name = name
        self.description = description
        self.icon = icon
        self.category = category
        self.status = status
        self.version = version
        self.entry_point = entry_point
        self.source_path = source_path

    @property
    def is_active(self):
        return self.status in ("active", "installed")


class ModuleRegistry:
    """Stores module metadata and callbacks without importing module UIs."""

    def __init__(self, modules=()):
        self._modules = {}
        self._launchers = {}
        for module in modules:
            self.register(module)

    def register(self, module, replace=False):
        if module.id in self._modules:
            if not replace:
                raise ValueError(f"Módulo já registrado: {module.id}")
            if self._modules[module.id].is_active:
                raise ValueError(f"Não é permitido substituir módulo ativo integrado: {module.id}")
        self._modules[module.id] = module

    def register_entry_point(self, module_id, entry_point, source_path):
        if module_id not in self._modules:
            raise KeyError(f"Módulo não registrado: {module_id}")
        module_name, separator, callable_name = entry_point.partition(":")
        if not separator or not module_name or not callable_name:
            raise ValueError(f"Entry point inválido: {entry_point}")

        source_path = Path(source_path).resolve()

        def launch(context=None):
            source_path_value = str(source_path)
            if source_path_value not in sys.path:
                sys.path.insert(0, source_path_value)
            imported_module = importlib.import_module(module_name)
            launcher = getattr(imported_module, callable_name)
            return launcher(context)

        self._launchers[module_id] = launch

    def discover_manifests(self, module_roots):
        """Load module manifests; entry-point Python is imported only on launch."""
        errors = []
        for root_value in module_roots:
            root = Path(root_value)
            if not root.is_dir():
                continue
            for manifest_path in sorted(root.rglob("estelar-module.json")):
                try:
                    self._register_manifest(manifest_path)
                except Exception as error:
                    errors.append((str(manifest_path), str(error)))
        return errors

    def _register_manifest(self, manifest_path):
        manifest_path = Path(manifest_path).resolve()
        module_root = manifest_path.parent
        with manifest_path.open("r", encoding="utf-8") as manifest_file:
            manifest = json.load(manifest_file)

        required = ("id", "name", "version", "entry_point")
        missing = [key for key in required if not manifest.get(key)]
        if missing:
            raise ValueError("Campos obrigatórios ausentes: " + ", ".join(missing))
        if int(manifest.get("schema_version", 1)) != 1:
            raise ValueError("schema_version não suportado")

        module_name = manifest["entry_point"].partition(":")[0]
        if not all(part.isidentifier() for part in module_name.split(".")):
            raise ValueError("entry_point deve apontar para um módulo Python relativo à pasta instalada")
        relative_module_path = Path(*module_name.split("."))
        candidates = (
            module_root / relative_module_path.with_suffix(".py"),
            module_root / relative_module_path / "__init__.py",
        )
        if not any(candidate.is_file() for candidate in candidates):
            raise FileNotFoundError(f"Módulo Python do entry point não encontrado: {manifest['entry_point']}")

        module = ModuleDefinition(
            manifest["id"],
            manifest["name"],
            manifest.get("description", "Ferramenta Estelar instalada."),
            manifest.get("icon", "toolbox"),
            manifest.get("category", "Extensões"),
            manifest.get("status", "installed"),
            version=manifest["version"],
            entry_point=manifest["entry_point"],
            source_path=str(module_root),
        )
        self.register(module, replace=True)
        self.register_entry_point(module.id, module.entry_point, module_root)

    def register_launcher(self, module_id, launcher):
        if module_id not in self._modules:
            raise KeyError(f"Módulo não registrado: {module_id}")
        self._launchers[module_id] = launcher

    def get(self, module_id):
        return self._modules[module_id]

    def modules(self):
        return tuple(self._modules.values())

    def can_launch(self, module_id):
        module = self._modules.get(module_id)
        return bool(module and module.is_active and module_id in self._launchers)

    def launch(self, module_id, context=None):
        if not self.can_launch(module_id):
            return False
        return self._launchers[module_id](context)


def criar_catalogo_estelar():
    return ModuleRegistry((
        ModuleDefinition(
            "access-map",
            "Mapa de Acesso",
            "Gere mapas profissionais de acesso para os empreendimentos.",
            "road",
            "Cartografia",
            "active",
        ),
        ModuleDefinition(
            "location-map",
            "Mapa de Localização",
            "Prepare mapas de localização com contexto regional e urbano.",
            "map",
            "Cartografia",
            "upcoming",
        ),
        ModuleDefinition(
            "location-sketch",
            "Croqui de Localização",
            "Monte croquis claros para orientar equipes e clientes.",
            "sketch",
            "Cartografia",
            "upcoming",
        ),
        ModuleDefinition(
            "descriptive-memo",
            "Memorial Descritivo",
            "Estruture memoriais técnicos a partir dos dados do projeto.",
            "document",
            "Documentação",
            "upcoming",
        ),
        ModuleDefinition(
            "coordinate-memo",
            "Memorial de Coordenadas",
            "Gere tabelas e memoriais de coordenadas das estruturas.",
            "coordinates",
            "Documentação",
            "upcoming",
        ),
        ModuleDefinition(
            "coordinate-converter",
            "Conversor de Coordenadas",
            "Converta coordenadas entre formatos e sistemas de referência.",
            "convert",
            "Coordenadas",
            "upcoming",
        ),
        ModuleDefinition(
            "utm-tools",
            "Ferramentas UTM",
            "Consulte zonas, hemisférios e parâmetros de projeção UTM.",
            "globe",
            "Coordenadas",
            "upcoming",
        ),
        ModuleDefinition(
            "pdf-export",
            "Exportação de PDF",
            "Exporte mapas e documentos técnicos em PDF.",
            "pdf",
            "Publicação",
            "upcoming",
        ),
        ModuleDefinition(
            "layout-generator",
            "Gerador de Layouts",
            "Monte layouts cartográficos padronizados para seus projetos.",
            "layout",
            "Publicação",
            "upcoming",
        ),
        ModuleDefinition(
            "future-gis",
            "Futuras Ferramentas GIS",
            "Novos recursos de engenharia e geoprocessamento Estelar.",
            "toolbox",
            "Plataforma",
            "upcoming",
        ),
    ))