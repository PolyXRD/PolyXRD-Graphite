@echo off
chcp 65001 >nul
REM ============================================================
REM 构建【安装版】: PyInstaller onedir + Inno Setup 安装包
REM (依赖: PySide6 + numpy 已含于 PolyXRD venv; Inno Setup 6)
REM
REM 安装版 = setup 变体（不打 internal_eval.marker），含注册机制:
REM   - 未注册时每次启动弹版权提示（确定后仍可正常使用）
REM   - 帮助菜单「输入注册码」; 注册后状态栏右侧显示注册的单位部门名称
REM 安装向导默认装到 Program Files，可自由指定安装位置。
REM
REM 产物: dist\PolyXRD-Graphite-Setup-vX.Y.Z.exe
REM
REM 注意: 请在 cmd.exe 中运行 (Git Bash 经 cmd //c 调用会因编码跑挂)。
REM ============================================================
cd /d %~dp0
set VENV=..\PolyXRD\venv\Scripts\python.exe
if not exist "%VENV%" set VENV=venv\Scripts\python.exe
set ISCC="%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
if not exist %ISCC% set ISCC="%ProgramFiles%\Inno Setup 6\ISCC.exe"

REM 从源码读取版本号 (避免人工改两处)
for /f "delims=" %%v in ('"%VENV%" -c "import re,io;print(re.search(r'APP_VERSION\s*=\s*\"([^\"]+)\"', io.open('graphite_app.py',encoding='utf-8').read()).group(1))"') do set VER=%%v

echo [1/2] Building onedir (setup variant) v%VER% ...
"%VENV%" -m PyInstaller --noconfirm --clean --onedir --windowed --name "PolyXRD-Graphite" ^
  --icon resources\app-icon.ico ^
  --add-data "resources;resources" ^
  graphite_app.py
if errorlevel 1 exit /b 1

echo [2/2] Building installer with Inno Setup ...
if not exist %ISCC% (
  echo 未找到 Inno Setup 6 的 ISCC.exe，请先安装 Inno Setup 6。
  exit /b 1
)
%ISCC% /DMyAppVersion=%VER% packaging\installer.iss
if errorlevel 1 exit /b 1

echo.
echo 完成:
echo   dist\PolyXRD-Graphite-Setup-v%VER%.exe
