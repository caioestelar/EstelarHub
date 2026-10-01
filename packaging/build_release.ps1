param(
    [string]$QgisRoot = $env:ESTELAR_QGIS_ROOT,
    [string]$InnoCompiler = (Join-Path $env:LOCALAPPDATA "Programs\Inno Setup 6\ISCC.exe"),
    [string]$OutputDirectory = (Join-Path $PSScriptRoot "..\dist"),
    [switch]$ReuseStage,
    [switch]$SkipInstaller
)

$ErrorActionPreference = "Stop"
$RepositoryRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$Version = (Get-Content (Join-Path $RepositoryRoot "VERSION") -Raw).Trim()
$PluginVersion = ((Select-String -Path (Join-Path $RepositoryRoot "metadata.txt") -Pattern '^version=').Line -split '=', 2)[1]
if (-not $Version -or -not $PluginVersion) { throw "Application or plugin version is missing." }
$NumericVersion = ($Version -replace "-.*$", ".0")

if (-not $QgisRoot) {
    $Candidates = @(
        "C:\Program Files\QGIS 4.0.2",
        "C:\Program Files\QGIS 4.0.1",
        "C:\Program Files\QGIS 4.0.0"
    )
    $QgisRoot = $Candidates | Where-Object { Test-Path (Join-Path $_ "bin\python-qgis.bat") } | Select-Object -First 1
}
if (-not $QgisRoot -or -not (Test-Path (Join-Path $QgisRoot "bin\python-qgis.bat"))) {
    throw "QGIS 4 runtime not found. Pass -QgisRoot or set ESTELAR_QGIS_ROOT."
}

$OutputDirectory = [System.IO.Path]::GetFullPath($OutputDirectory)
$StageDirectory = Join-Path $OutputDirectory "EstelarHub-stage"
if ((Test-Path $StageDirectory) -and -not $ReuseStage) {
    throw "Stage directory already exists. Move it aside before rebuilding: $StageDirectory"
}
if (-not (Test-Path $StageDirectory)) {
    New-Item -ItemType Directory -Path $StageDirectory -Force | Out-Null
}

$PackageDirectory = Join-Path $StageDirectory "EstelarMapTools"
if (-not $ReuseStage) {
    Write-Host "Staging Estelar Hub $Version..."
    New-Item -ItemType Directory -Path $PackageDirectory -Force | Out-Null
    foreach ($Item in @("core", "ui", "utils", "estelar_hub")) {
        Copy-Item -Path (Join-Path $RepositoryRoot $Item) -Destination $PackageDirectory -Recurse
    }
    foreach ($Item in @("__init__.py", "metadata.txt", "icon.png", "VERSION")) {
        Copy-Item -Path (Join-Path $RepositoryRoot $Item) -Destination $PackageDirectory
    }
    Copy-Item (Join-Path $RepositoryRoot "run_estelar_hub.py") -Destination $StageDirectory
    Copy-Item (Join-Path $RepositoryRoot "THIRD_PARTY_NOTICES.txt") -Destination $StageDirectory
    if (Test-Path (Join-Path $RepositoryRoot "modules")) {
        Copy-Item (Join-Path $RepositoryRoot "modules") -Destination $StageDirectory -Recurse
    }

    Get-ChildItem $StageDirectory -Directory -Filter "__pycache__" -Recurse | Remove-Item -Recurse -Force
    Get-ChildItem $StageDirectory -File -Filter "*.pyc" -Recurse | Remove-Item -Force

    Write-Host "Compiling staged Python sources with the selected QGIS runtime..."
    & (Join-Path $QgisRoot "bin\python-qgis.bat") -m compileall -q $PackageDirectory
    if ($LASTEXITCODE -ne 0) { throw "QGIS Python compileall failed with exit code $LASTEXITCODE" }

    $RuntimeDestination = Join-Path $StageDirectory "runtime\qgis"
    New-Item -ItemType Directory -Path $RuntimeDestination -Force | Out-Null
    Write-Host "Copying the complete QGIS runtime; this can require several gigabytes and take minutes..."
    & robocopy $QgisRoot $RuntimeDestination /E /COPY:DAT /DCOPY:DAT /R:1 /W:1 /XJ
    if ($LASTEXITCODE -ge 8) { throw "Robocopy failed with exit code $LASTEXITCODE" }
} elseif (-not (Test-Path (Join-Path $StageDirectory "runtime\qgis\bin\python-qgis.bat"))) {
    throw "ReuseStage requested, but the staged QGIS runtime is incomplete: $StageDirectory"
} elseif (-not (Test-Path (Join-Path $StageDirectory "EstelarHub.exe"))) {
    Write-Host "Reusing the staged QGIS runtime; refreshing Python modules and launcher..."
    foreach ($Item in @("core", "ui", "utils", "estelar_hub")) {
        $destination = Join-Path $PackageDirectory $Item
        if (Test-Path $destination) { Remove-Item $destination -Recurse -Force }
        Copy-Item -Path (Join-Path $RepositoryRoot $Item) -Destination $PackageDirectory -Recurse
    }
    foreach ($Item in @("__init__.py", "metadata.txt", "icon.png", "VERSION")) {
        Copy-Item -Path (Join-Path $RepositoryRoot $Item) -Destination $PackageDirectory -Force
    }
    Copy-Item (Join-Path $RepositoryRoot "run_estelar_hub.py") -Destination $StageDirectory -Force
    Copy-Item (Join-Path $RepositoryRoot "THIRD_PARTY_NOTICES.txt") -Destination $StageDirectory -Force
    Get-ChildItem $StageDirectory -Directory -Filter "__pycache__" -Recurse | Remove-Item -Recurse -Force
    Get-ChildItem $StageDirectory -File -Filter "*.pyc" -Recurse | Remove-Item -Force
    & (Join-Path $QgisRoot "bin\python-qgis.bat") -m compileall -q $PackageDirectory
    if ($LASTEXITCODE -ne 0) { throw "QGIS Python compileall failed with exit code $LASTEXITCODE" }
} else {
    Write-Host "Reusing the existing staged application and QGIS runtime."
}

$CSharpCompiler = Join-Path $env:WINDIR "Microsoft.NET\Framework64\v4.0.30319\csc.exe"
if (-not (Test-Path $CSharpCompiler)) { throw "C# compiler not found: $CSharpCompiler" }
$LauncherSource = Join-Path $PSScriptRoot "launcher\EstelarHubLauncher.cs"
$LauncherOutput = Join-Path $StageDirectory "EstelarHub.exe"
& $CSharpCompiler /nologo /target:winexe /platform:x64 /reference:System.Windows.Forms.dll "/out:$LauncherOutput" $LauncherSource
if ($LASTEXITCODE -ne 0) { throw "Launcher compilation failed with exit code $LASTEXITCODE" }

if (-not $SkipInstaller) {
    if (-not (Test-Path $InnoCompiler)) { throw "Inno Setup compiler not found: $InnoCompiler. Install Inno Setup 6 or pass -InnoCompiler." }
    New-Item -ItemType Directory -Path $OutputDirectory -Force | Out-Null
    $InstallerScript = Join-Path $PSScriptRoot "EstelarHubSetup.iss"
    & $InnoCompiler "/DAppVersion=$Version" "/DNumericVersion=$NumericVersion" "/DStageDir=$StageDirectory" "/DOutputDir=$OutputDirectory" $InstallerScript
    if ($LASTEXITCODE -ne 0) { throw "Inno Setup failed with exit code $LASTEXITCODE" }
    Write-Host "Installer created: $(Join-Path $OutputDirectory 'EstelarHubSetup.exe')"
} else {
    Write-Host "Staged application and EstelarHub.exe created at: $StageDirectory"
}