#define MyAppName "DiagNova Connector"
#define MyAppVersion "0.24.0"
#define MyAppPublisher "DiagNova"
#define MyAppExeName "DiagNova.Connector.exe"
; UNSIGNED test installer – no fake signatures. Code-signing: BLK-CERT / operator.

#ifndef PublishDir
  #define PublishDir "..\publish\win-x64"
#endif

[Setup]
AppId={{A7C3E9D1-23B4-4F5A-9C8E-DIAGNOVA0230}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\DiagNova\Connector
DefaultGroupName=DiagNova
DisableProgramGroupPage=yes
OutputDir=..\publish\installer
OutputBaseFilename=DiagNovaConnectorSetup-{#MyAppVersion}-unsigned
Compression=lzma
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
UninstallDisplayIcon={app}\{#MyAppExeName}
SetupLogging=yes
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
; No SignTool – unsigned test artifact only

[Languages]
Name: "german"; MessagesFile: "compiler:Languages\German.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "{#PublishDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\Uninstall {#MyAppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Connector starten"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{app}\logs"
