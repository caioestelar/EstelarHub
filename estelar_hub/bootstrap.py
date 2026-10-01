"""Prepare the native QGIS runtime before importing any PyQGIS module."""

import os
import sys
from pathlib import Path


_DLL_HANDLES = []


class QgisRuntimeNotFoundError(RuntimeError):
    pass


def _candidate_prefixes():
    prefixes = []
    explicit_prefix = os.environ.get("QGIS_PREFIX_PATH")
    if explicit_prefix:
        prefixes.append(Path(explicit_prefix))

    for variable in ("ESTELAR_QGIS_ROOT", "QGIS_ROOT", "OSGEO4W_ROOT"):
        root = os.environ.get(variable)
        if root:
            root_path = Path(root)
            prefixes.extend((root_path / "apps" / "qgis", root_path))

    if os.name == "nt":
        prefixes.extend((
            Path(r"C:\Program Files\QGIS 4.0.2\apps\qgis"),
            Path(r"C:\OSGeo4W\apps\qgis"),
        ))

    return prefixes


def _is_qgis_prefix(path: Path) -> bool:
    return path.is_dir() and (path / "python").is_dir() and (path / "plugins").is_dir()


def configure_qgis_environment():
    """Resolve QGIS paths, Python providers, Qt plugins, and native DLL search."""
    prefix = next((candidate.resolve() for candidate in _candidate_prefixes() if _is_qgis_prefix(candidate)), None)
    if prefix is None:
        raise QgisRuntimeNotFoundError(
            "Instalação do QGIS não encontrada. Instale QGIS Desktop ou defina "
            "ESTELAR_QGIS_ROOT com o caminho da instalação."
        )

    root = prefix.parent.parent if prefix.name.lower() == "qgis" else prefix.parent
    python_path = prefix / "python"
    plugins_path = python_path / "plugins"

    os.environ["QGIS_PREFIX_PATH"] = str(prefix).replace("\\", "/")
    os.environ.setdefault("QT_PLUGIN_PATH", os.pathsep.join((str(root / "apps" / "qt6" / "plugins"), str(prefix / "qtplugins"))))

    if (root / "apps" / "gdal" / "share" / "gdal").is_dir():
        os.environ.setdefault("GDAL_DATA", str(root / "apps" / "gdal" / "share" / "gdal"))
    if (root / "share" / "proj").is_dir():
        os.environ.setdefault("PROJ_LIB", str(root / "share" / "proj"))
    elif (root / "apps" / "proj" / "share" / "proj").is_dir():
        os.environ.setdefault("PROJ_LIB", str(root / "apps" / "proj" / "share" / "proj"))

    for python_module_path in (python_path, plugins_path):
        path_value = str(python_module_path)
        if python_module_path.is_dir() and path_value not in sys.path:
            sys.path.insert(0, path_value)

    native_paths = (
        root / "bin",
        prefix / "bin",
        root / "apps" / "qt6" / "bin",
        root / "apps" / "Python312",
        root / "apps" / "gdal" / "bin",
    )
    existing_paths = [str(path) for path in native_paths if path.is_dir()]
    if existing_paths:
        current_path = os.environ.get("PATH", "")
        os.environ["PATH"] = os.pathsep.join(existing_paths + [current_path])
        if hasattr(os, "add_dll_directory"):
            for path in existing_paths:
                try:
                    _DLL_HANDLES.append(os.add_dll_directory(path))
                except OSError:
                    pass

    return prefix