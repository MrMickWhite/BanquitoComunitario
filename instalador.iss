; ============================================================================
;  Instalador de MMWBank  (Inno Setup)
;
;  QUE HACE:
;   - Instala la app en  C:\Program Files\MMWBank
;   - Crea acceso directo en el ESCRITORIO y en el MENU INICIO
;   - Usa el icono banquito.ico
;   - Genera  Instalador-MMWBank.exe  (un solo archivo para dar a los clientes)
;
;  COMO USARLO (en tu PC con Windows):
;   1) Compila primero el .exe:   pyinstaller banquito.spec
;      (esto crea la carpeta  dist\MMWBank  con MMWBank.exe dentro)
;   2) Instala Inno Setup (gratis):  https://jrsoftware.org/isdl.php
;   3) Abre ESTE archivo (instalador.iss) con Inno Setup
;   4) Menu  Build -> Compile  (o el boton de play)
;   5) Se genera  Salida\Instalador-MMWBank.exe   <-- esto das a los clientes
;
;  Los datos de cada cliente (base de datos, reportes) NO se guardan en
;  Program Files; se guardan en su carpeta de usuario, asi que no hay
;  problemas de permisos ni se borran al desinstalar.
; ============================================================================

#define MiApp        "MMWBank"
#define MiVersion    "1.0.0"
#define MiAutor      "MrMickWhite"
#define MiExe        "MMWBank.exe"

[Setup]
AppId={{B4NQU1T0-MRMW-2026-0001-BANQUITOAPP}}
AppName={#MiApp}
AppVersion={#MiVersion}
AppPublisher={#MiAutor}
DefaultDirName={autopf}\{#MiApp}
DefaultGroupName={#MiApp}
DisableProgramGroupPage=yes
OutputDir=Salida
OutputBaseFilename=Instalador-MMWBank
SetupIconFile=assets\banquito.ico
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
; Instala para todos los usuarios (requiere admin). Para instalar sin admin,
; cambia a:  PrivilegesRequired=lowest   y  DefaultDirName={localappdata}\{#MiApp}
PrivilegesRequired=admin
ArchitecturesInstallIn64BitMode=x64compatible

[Languages]
Name: "es"; MessagesFile: "compiler:Languages\Spanish.isl"

[Tasks]
Name: "desktopicon"; Description: "Crear un acceso directo en el escritorio"; GroupDescription: "Accesos directos:"; Flags: checkedonce

[Files]
; Copia TODO el contenido de la carpeta compilada por PyInstaller.
Source: "dist\MMWBank\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs ignoreversion

[Icons]
; Menu inicio (el icono se toma del propio .exe, que ya lo lleva incrustado)
Name: "{group}\{#MiApp}"; Filename: "{app}\{#MiExe}"; IconFilename: "{app}\{#MiExe}"; IconIndex: 0
Name: "{group}\Desinstalar {#MiApp}"; Filename: "{uninstallexe}"
; Escritorio (segun la casilla marcada)
Name: "{autodesktop}\{#MiApp}"; Filename: "{app}\{#MiExe}"; IconFilename: "{app}\{#MiExe}"; IconIndex: 0; Tasks: desktopicon

[Run]
; Refrescar la cache de iconos de Windows para que el acceso directo no salga en blanco
Filename: "{cmd}"; Parameters: "/c ie4uinit.exe -show"; Flags: runhidden skipifdoesntexist
; Ofrecer abrir la app al terminar de instalar
Filename: "{app}\{#MiExe}"; Description: "Abrir {#MiApp} ahora"; Flags: nowait postinstall skipifsilent
