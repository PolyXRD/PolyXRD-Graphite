@echo off
chcp 65001 >nul
REM ============================================================
REM 打包 PolyXRD Graphite 为【单文件】内部评估版 exe
REM (依赖: PySide6 + numpy, 已含于 PolyXRD venv)
REM
REM 单文件版 = 内部评估版: 打入 packaging\internal_eval.marker,
REM   运行时 BUILD_VARIANT = "internal": 无注册机制, 状态栏最右侧
REM   显示「内部评估版本」。
REM   对外发布的【安装版】(含注册机制) 请用 build_installer.bat。
REM
REM 产物(单文件, 拷贝即用):
REM   dist\PolyXRD-Graphite-vX.Y.Z-internal.exe   <- 版本化归档副本
REM   dist\PolyXRD-Graphite-internal.exe          <- 最新版固定名副本
REM
REM 注意: 请在 cmd.exe 中运行 (Git Bash 经 cmd //c 调用会因编码跑挂)。
REM ============================================================
cd /d %~dp0
set ROOT=%~dp0
set VENV=..\PolyXRD\venv\Scripts\python.exe
if not exist "%VENV%" set VENV=venv\Scripts\python.exe

REM 从源码读取版本号 (避免人工改两处)
for /f "delims=" %%v in ('"%VENV%" -c "import re,io;print(re.search(r'APP_VERSION\s*=\s*\"([^\"]+)\"', io.open('graphite_app.py',encoding='utf-8').read()).group(1))"') do set VER=%%v

REM 受控环境下 Python 只能写「它自己新建」的目录, 因此 spec 放到 build 下的
REM 专用子目录; --add-data / --icon / 入口脚本一律用绝对路径,
REM 否则相对路径会按 --specpath 解析而找不到 build\spec\resources。
set SPEC=%ROOT%build\pyi_spec
if not exist "%SPEC%" mkdir "%SPEC%"

echo Building PolyXRD Graphite v%VER% (internal eval) ...
"%VENV%" -m PyInstaller --noconfirm --clean --onefile --windowed ^
  --name "PolyXRD-Graphite-v%VER%-internal" ^
  --specpath "%SPEC%" ^
  --icon "%ROOT%resources\app-icon.ico" ^
  --add-data "%ROOT%resources;resources" ^
  --add-data "%ROOT%packaging\internal_eval.marker;." ^
  "%ROOT%graphite_app.py"
if errorlevel 1 goto :err

REM 复制一份最新版固定名副本
copy /Y "dist\PolyXRD-Graphite-v%VER%-internal.exe" "dist\PolyXRD-Graphite-internal.exe" >nul
echo.
echo 完成:
echo   dist\PolyXRD-Graphite-v%VER%-internal.exe
echo   dist\PolyXRD-Graphite-internal.exe
goto :eof

:err
echo.
echo 构建失败，请检查上面的错误信息。
exit /b 1
