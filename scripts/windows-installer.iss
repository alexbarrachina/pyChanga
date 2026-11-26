; Copyright (C) 2026 Alex Barrachina
; SPDX-License-Identifier: GPL-3.0-only
;
; Inno Setup script for the Windows x64 installer. Do not compile it directly:
; `node scripts/make_windows_installer.mjs` passes the version from
; package.json and the application folder that `npm run make` packaged.

#ifndef AppVersion
  #error Define AppVersion: run node scripts/make_windows_installer.mjs
#endif
#ifndef AppDir
  #error Define AppDir: run node scripts/make_windows_installer.mjs
#endif
#define AppName "pyChangaIDE"
#define AppExe "pyChangaIDE.exe"

[Setup]
; AppId links upgrades and the uninstaller to earlier installs. Never change it.
AppId={{D6DF84E2-66F7-4666-97F3-92B739D06A90}
AppName={#AppName}
AppVersion={#AppVersion}
AppVerName={#AppName} {#AppVersion}
AppPublisher=Alex Barrachina
AppPublisherURL=https://github.com/alexbarrachina/pyChanga
AppComments=Python live coding for musicians
; Installs for the current user without an administrator prompt; the first
; page offers an all-users install in Program Files instead.
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog commandline
DefaultDirName={autopf}\{#AppName}
DisableProgramGroupPage=yes
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=10.0
OutputBaseFilename={#AppName}-{#AppVersion}-win-x64-setup
UninstallDisplayIcon={app}\{#AppExe}
UninstallDisplayName={#AppName}
WizardStyle=modern
ShowLanguageDialog=auto
Compression=lzma2/max
SolidCompression=yes
LZMAUseSeparateProcess=yes
LZMANumBlockThreads=4
#ifdef Sign
SignTool=signtool
SignedUninstaller=yes
#endif

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"
Name: "catalan"; MessagesFile: "compiler:Languages\Catalan.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[InstallDelete]
; An upgrade replaces the bundled Python runtime instead of mixing versions.
Type: filesandordirs; Name: "{app}\resources\runtime"

[Files]
#ifdef Sign
Source: "{#AppDir}\{#AppExe}"; DestDir: "{app}"; Flags: ignoreversion signonce
Source: "{#AppDir}\*"; Excludes: "\{#AppExe}"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
#else
Source: "{#AppDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
#endif

[Icons]
Name: "{autoprograms}\{#AppName}"; Filename: "{app}\{#AppExe}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExe}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#AppExe}"; Description: "{cm:LaunchProgram,{#AppName}}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Python writes bytecode caches into the runtime after installation.
Type: filesandordirs; Name: "{app}\resources\runtime"
