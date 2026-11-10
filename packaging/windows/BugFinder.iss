#define AppName "BugFinder"
#define AppVersion "0.1.0"

[Setup]
AppId={{D6C2D4E4-3B9C-4D41-8F36-2C9D6B7F4010}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher=BugFinder contributors
DefaultDirName={autopf}\BugFinder
DefaultGroupName=BugFinder
OutputDir=..\..\dist\installer
OutputBaseFilename=BugFinder-Setup
ArchitecturesInstallIn64BitMode=x64
ArchitecturesAllowed=x64
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
UninstallDisplayIcon={app}\BugFinder.exe
PrivilegesRequired=admin
ShowLanguageDialog=yes

[Languages]
Name: "german"; MessagesFile: "compiler:Languages\German.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "..\..\dist\BugFinder.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\BugFinder"; Filename: "{app}\BugFinder.exe"
Name: "{autodesktop}\BugFinder"; Filename: "{app}\BugFinder.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\BugFinder.exe"; Description: "{cm:LaunchProgram,BugFinder}"; Flags: postinstall nowait skipifsilent
