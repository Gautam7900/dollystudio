[Setup]
AppName=Dolly Photo Studio
AppVersion=1.0
DefaultDirName={pf}\Dolly Photo Studio
DefaultGroupName=Dolly Photo Studio
OutputDir=output
OutputBaseFilename=DollyStudioSetup
Compression=lzma
SolidCompression=yes

[Files]
Source: "dist\DollyStudio.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "dist\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\Dolly Photo Studio"; Filename: "{app}\DollyStudio.exe"
Name: "{commondesktop}\Dolly Photo Studio"; Filename: "{app}\DollyStudio.exe"

[Run]
Filename: "{app}\DollyStudio.exe"; Description: "Launch Dolly Photo Studio"; Flags: nowait postinstall skipifsilent