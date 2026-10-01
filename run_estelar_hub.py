"""Standalone entry point; environment setup precedes all PyQGIS imports."""

import sys
from importlib import import_module
from pathlib import Path


LAUNCHER_DIRECTORY = Path(__file__).resolve().parent
if (LAUNCHER_DIRECTORY / "__init__.py").is_file():
    PACKAGE_ROOT = LAUNCHER_DIRECTORY
elif (LAUNCHER_DIRECTORY / "EstelarMapTools" / "__init__.py").is_file():
    PACKAGE_ROOT = LAUNCHER_DIRECTORY / "EstelarMapTools"
else:
    raise RuntimeError("Pacote Python EstelarMapTools não encontrado ao lado do launcher.")

PACKAGE_PARENT = PACKAGE_ROOT.parent
if str(PACKAGE_PARENT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_PARENT))

def main():
    package_name = PACKAGE_ROOT.name
    bootstrap = import_module(f"{package_name}.estelar_hub.bootstrap")
    prefix_path = bootstrap.configure_qgis_environment()
    application = import_module(f"{package_name}.estelar_hub.application")

    return application.main(prefix_path)


if __name__ == "__main__":
    raise SystemExit(main())