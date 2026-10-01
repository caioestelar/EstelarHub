@echo off
setlocal

set "QGIS_ROOT=%ESTELAR_QGIS_ROOT%"
if not defined QGIS_ROOT if exist "C:\Program Files\QGIS 4.0.2\bin\python-qgis.bat" set "QGIS_ROOT=C:\Program Files\QGIS 4.0.2"

if not defined QGIS_ROOT (
    echo QGIS was not found. Set ESTELAR_QGIS_ROOT to the QGIS installation directory.
    pause
    exit /b 1
)

if not exist "%QGIS_ROOT%\bin\python-qgis.bat" (
    echo PyQGIS launcher not found: %QGIS_ROOT%\bin\python-qgis.bat
    pause
    exit /b 1
)

call "%QGIS_ROOT%\bin\python-qgis.bat" "%~dp0run_estelar_hub.py" %*
set "EXIT_CODE=%ERRORLEVEL%"
if not "%EXIT_CODE%"=="0" pause
exit /b %EXIT_CODE%