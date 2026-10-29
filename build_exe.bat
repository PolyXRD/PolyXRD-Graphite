@echo off
chcp 65001 >nul
REM ============================================================
REM 打包 PolyXRD Graphite 内部评估版
REM (依赖: PySide6 + numpy, 已含于 PolyXRD venv)
REM
REM 内部评估版 = 打入 packaging\internal_eval.marker,
REM   运行时 BUILD_VARIANT = "internal": 无注册机制, 状态栏
REM   显示「内部评估版本」。
REM   对外发布的【安装版】(含注册机制) 请用 build_installer.bat。
REM
REM 默认产物(FOLDER 版, 推荐):
REM   dist\PolyXRD-Graphite-vX.Y.Z-internal\PolyXRD-Graphite-vX.Y.Z-internal.exe
REM
REM 为什么不再默认单文件:
REM   --onefile 每次启动都要把 ~58 MB 解包到 %TEMP%\_MEIxxxx, 若该机
REM   %TEMP% 不可写/被安全软件拦截, 启动即弹
REM   「Error: Could not create temporary directory!」直接退出。
REM   FOLDER 版不解包, 启动更快, 也不依赖 %TEMP%。
REM   确需单文件(便携介质、目标机环境正常)时: build_exe.bat onefile
REM   单文件产物: dist\PolyXRD-Graphite-vX.Y.Z-internal.exe (+ 固定名副本)
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

if /i "%~1"=="onefile" goto :onefile

echo [folder] Building PolyXRD Graphite v%VER% (internal eval) ...
"%VENV%" -m PyInstaller --noconfirm --clean --onedir --windowed ^
  --name "PolyXRD-Graphite-v%VER%-internal" ^
  --specpath "%SPEC%" ^
  --icon "%ROOT%resources\app-icon.ico" ^
  --add-data "%ROOT%resources;resources" ^
  --add-data "%ROOT%packaging\internal_eval.marker;." ^
  "%ROOT%graphite_app.py"
if errorlevel 1 goto :err
echo.
echo 完成(整目录拷贝/压缩分发, 不要只拿 exe):
echo   dist\PolyXRD-Graphite-v%VER%-internal\
echo   dist\PolyXRD-Graphite-v%VER%-internal\PolyXRD-Graphite-v%VER%-internal.exe
goto :eof

:onefile
echo [onefile] Building PolyXRD Graphite v%VER% (internal eval) ...
"%VENV%" -m PyInstaller --noconfirm --clean --onefile --windowed ^
  --name "PolyXRD-Graphite-v%VER%-internal" ^
  --specpath "%SPEC%" ^
  --icon "%ROOT%resources\app-icon.ico" ^
  --add-data "%ROOT%resources;resources" ^
  --add-data "%ROOT%packaging\internal_eval.marker;." ^
  "%ROOT%graphite_app.py"
if errorlevel 1 goto :err
copy /Y "dist\PolyXRD-Graphite-v%VER%-internal.exe" "dist\PolyXRD-Graphite-internal.exe" >nul
echo.
echo 完成:
echo   dist\PolyXRD-Graphite-v%VER%-internal.exe
echo   dist\PolyXRD-Graphite-internal.exe
echo   注意: 若目标机 %TEMP% 不可写, 单文件版会报
echo         「Could not create temporary directory!」, 请改用 folder 版。
goto :eof

:err
echo.
echo 构建失败，请检查上面的错误信息。
exit /b 1
