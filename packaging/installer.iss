; ============================================================================
; PolyXRD Graphite 安装包脚本 (Inno Setup 6)
; ----------------------------------------------------------------------------
; 先运行 build_installer.bat (或手动 PyInstaller --onedir) 得到
;   dist\PolyXRD-Graphite\             <- onedir 输出（setup 变体）
; 再用 ISCC 编译本脚本得到
;   dist\PolyXRD-Graphite-Setup-v<版本>.exe
;
; 版本号从 graphite_app.py 读出后经 /DMyAppVersion=... 传入 (见 build_installer.bat)；
; 直接双击编译时使用下面的缺省版本号。
;
; 安装版 = setup 变体（不含 internal_eval.marker）→ 含注册机制：
;   未注册时每次启动弹版权提示（确定后仍可正常使用）；
;   帮助菜单「输入注册码」；注册后状态栏右侧显示注册的单位部门名称。
; ============================================================================

#define MyAppName "PolyXRD Graphite"
#define MyAppExeName "PolyXRD-Graphite.exe"

#ifndef MyAppVersion
  #define MyAppVersion "1.1.1"
#endif

[Setup]
; AppId 固定: 同一 AppId 覆盖安装/升级, 不产生并行条目
AppId={{8F3C2A61-5D74-4B19-9E82-7A4C1D0B6F35}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} v{#MyAppVersion}
AppPublisher=PolyXRD Team
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
UninstallDisplayIcon={app}\{#MyAppExeName}
SetupIconFile=..\resources\app-icon.ico
OutputDir=..\dist
OutputBaseFilename=PolyXRD-Graphite-Setup-v{#MyAppVersion}
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
; 安装位置默认 Program Files, 向导中可自由修改
PrivilegesRequired=admin
ArchitecturesInstallIn64BitMode=x64compatible

[Languages]
Name: "chinese"; MessagesFile: "ChineseSimplified.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "japanese"; MessagesFile: "compiler:Languages\Japanese.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: checkedonce

[Files]
; onedir 全量内容 (exe + _internal\), 安装版 = setup 变体, 含注册机制
Source: "..\dist\PolyXRD-Graphite\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#MyAppName}}"; Flags: nowait postinstall skipifsilent
