#ifndef AppVersion
  #define AppVersion "2.0.0-alpha.1"
#endif
#ifndef NumericVersion
  #define NumericVersion "2.0.0.1"
#endif
#ifndef StageDir
  #define StageDir "..\dist\EstelarHub-stage"
#endif
#ifndef OutputDir
  #define OutputDir "..\dist"
#endif

[Setup]
AppId={{AA53DD8E-1185-48CB-A593-CF47A1CFE48A}
AppName=Estelar Hub
AppVersion={#AppVersion}
AppVerName=Estelar Hub {#AppVersion}
AppPublisher=Estelar Engenharia
AppPublisherURL=https://github.com/caioestelar/EstelarMapTools
AppSupportURL=https://github.com/caioestelar/EstelarMapTools/issues
DefaultDirName={autopf}\Estelar Hub
DefaultGroupName=Estelar Hub
UninstallDisplayIcon={app}\EstelarHub.exe
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64
PrivilegesRequired=admin
OutputDir={#OutputDir}
OutputBaseFilename=EstelarHubSetup
SetupLogging=yes
Compression=lzma2/fast
SolidCompression=no
WizardStyle=modern
CloseApplications=yes
RestartApplications=no
VersionInfoCompany=Estelar Engenharia
VersionInfoDescription=Estelar Hub - Plataforma de Engenharia GIS
VersionInfoProductName=Estelar Hub
VersionInfoProductVersion={#NumericVersion}
VersionInfoVersion={#NumericVersion}
LicenseFile={#StageDir}\THIRD_PARTY_NOTICES.txt

[Tasks]
Name: "desktopicon"; Description: "Criar atalho na área de trabalho"; GroupDescription: "Atalhos adicionais:"; Flags: unchecked

[Dirs]
Name: "{app}\modules"
Name: "{userappdata}\Estelar Engenharia\Estelar Hub\modules"
Name: "{commonappdata}\Estelar Hub\modules"

[Files]
Source: "{#StageDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\Estelar Hub"; Filename: "{app}\EstelarHub.exe"; WorkingDir: "{app}"
Name: "{autodesktop}\Estelar Hub"; Filename: "{app}\EstelarHub.exe"; WorkingDir: "{app}"; Tasks: desktopicon
Name: "{group}\Desinstalar Estelar Hub"; Filename: "{uninstallexe}"

[Run]
Filename: "{app}\EstelarHub.exe"; Description: "Abrir Estelar Hub"; Flags: postinstall nowait skipifsilent