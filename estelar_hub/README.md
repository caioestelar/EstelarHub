# Estelar Hub Standalone

This package is the standalone application layer. It keeps the existing QGIS plugin available while providing a native PyQt entry point that initializes QGIS internally and does not create the QGIS Desktop main window.

## Startup flow

1. `run_estelar_hub.bat` selects a QGIS installation and invokes its `python-qgis.bat` environment.
2. `run_estelar_hub.py` configures QGIS, Qt, Python provider, and native DLL paths before importing PyQGIS.
3. `QgisRuntime` creates one GUI-enabled `QgsApplication`, initializes providers and Processing, and owns shutdown.
4. `application.py` composes settings, project management, Processing services, and the module registry.
5. The existing Estelar Hub dashboard opens. The Mapa de Acesso adapter is imported only when its card is launched.
6. Closing the Hub stops the project refresh timer and calls `exitQgis()`.

## Structure

```text
estelar_hub/
  bootstrap.py             # QGIS install discovery and native environment setup
  runtime.py               # QgsApplication initialization and cleanup
  application.py           # composition root and Qt event loop
  modules/                 # standalone module adapters and future launchers
  services/
    settings.py            # shared application settings
    project_manager.py     # current project, recent list, open, and save
    processing_service.py  # cancellable background Processing tasks
core/
  module_registry.py       # module metadata and lazy launch callbacks
  modules/mapa_acesso.py   # shared adapter around the existing module
ui/
  hub.py                   # shared Estelar Hub dashboard
  janela_projeto.py        # existing Mapa de Acesso UI
run_estelar_hub.py         # standalone Python entry point
run_estelar_hub.bat        # Windows launcher using the QGIS Python runtime
```

## Run on Windows

Install QGIS 4.x (the current Qt 6 UI requires QGIS 4), then run `run_estelar_hub.bat`. The launcher checks the standard QGIS 4 installation path and supports an explicit `ESTELAR_QGIS_ROOT` override. For example:

```bat
set ESTELAR_QGIS_ROOT=C:\Program Files\QGIS 4.0.2
run_estelar_hub.bat
```

## Build the Windows installer

Install QGIS 4.x and Inno Setup 6, then run PowerShell from the repository root:

```powershell
.\packaging\build_release.ps1 `
  -QgisRoot "C:\Program Files\QGIS 4.0.2" `
  -InnoCompiler "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe"
```

The pipeline compiles the application sources with the QGIS Python runtime, stages the shared module code, copies the complete QGIS installation (including Qt, GDAL, PROJ, providers, and bundled licenses), builds the GUI `EstelarHub.exe` launcher, and creates `dist\EstelarHubSetup.exe`. The installer creates Start Menu and optional desktop shortcuts and supports in-place upgrades using a stable AppId. The bundled runtime makes the installer large; keep installer assets on a release/CDN rather than in Git history.

For a production release, build from a clean tagged commit, sign `EstelarHub.exe` and `EstelarHubSetup.exe` with the company code-signing certificate, test install/upgrade/uninstall on a clean Windows VM, then attach `EstelarHubSetup.exe` to the GitHub release for the exact `VERSION` value.

The first deployment model intentionally uses the installed QGIS runtime rather than copying PyQGIS DLLs into a generic Python/PyInstaller bundle. QGIS ships a coupled Qt, GDAL, PROJ, provider, and Python environment; packaging those libraries into a single installer is a separate release-engineering step and must be tested against the QGIS licensing and redistribution requirements.

## Module contract

Built-in catalog entries live in `core/module_registry.py`. Separately installed modules can be discovered from `modules/estelar-module.json` next to the application, `%APPDATA%/Estelar Engenharia/Estelar Hub/modules`, or `%PROGRAMDATA%/Estelar Hub/modules`. Discovery validates the manifest and Python entry point without importing module code; the entry point is imported only when the user launches the module.

Example extension manifest:

```json
{
  "schema_version": 1,
  "id": "coordinate-converter",
  "name": "Conversor de Coordenadas",
  "version": "1.0.0",
  "description": "Converta coordenadas e sistemas de referência.",
  "icon": "convert",
  "category": "Coordenadas",
  "status": "installed",
  "entry_point": "coordinate_converter:launch"
}
```

The entry point receives a `ModuleContext` with the QGIS application, parent widget, shared settings, project manager, Processing service, logger, error service, and update service. The Hub only enables a card when its module is active and has a launch callback.

Long-running Processing algorithms should use `ProcessingService.run_async`. Do not move edits to `QgsProject`, layers, widgets, or canvas objects into worker threads; collect background results and apply QGIS/UI mutations on the main Qt thread.

## Current boundary

The Mapa de Acesso dialog and generation pipeline remain the same. `core/modules/mapa_acesso.py` is only a launcher adapter shared by the plugin and standalone application. Existing operations that depend on mapped engineering network drives continue to require those drives to be available to the signed-in Windows user.

## Versioning and releases

The QGIS plugin keeps its independent `metadata.txt` version. The standalone product uses the root `VERSION` file and semantic versioning: `2.0.0-alpha.N` for internal architecture validation, `2.0.0-beta.N` for user acceptance testing, and `2.x.y` for stable releases. `packaging/build_release.ps1` stages the application and QGIS runtime, compiles the Windows launcher, and produces `EstelarHubSetup.exe`; release automation should attach that installer to the matching GitHub release. Upgrades reuse the same Inno Setup AppId and install directory while keeping user settings and installed user modules under AppData.