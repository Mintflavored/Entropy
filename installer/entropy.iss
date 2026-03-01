; Inno Setup Script for Entropy VPN Dashboard
; Created for v0.33.0+

#define MyAppName "Entropy"
#define MyAppVersion "0.42.5"
#define MyAppPublisher "Mintflavored"
#define MyAppURL "https://github.com/Mintflavored/Entropy"
#define MyAppExeName "Entropy.exe"

[Setup]
; Application info
AppId={{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}/releases

; Installation settings
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog

; Output settings
OutputDir=..\installer_output
OutputBaseFilename=Entropy-Setup-v{#MyAppVersion}
SetupIconFile=..\assets\logo.ico
Compression=lzma2/ultra64
SolidCompression=yes

; Visual settings
WizardStyle=modern
WizardSizePercent=120

; Uninstall settings
UninstallDisplayIcon={app}\{#MyAppExeName}
UninstallDisplayName={#MyAppName}

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "russian"; MessagesFile: "compiler:Languages\Russian.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; Main application files from PyInstaller dist
Source: "..\dist\Entropy\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

; Server scripts
Source: "..\scripts\server\*"; DestDir: "{app}\server"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent
