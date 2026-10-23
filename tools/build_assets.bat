@echo off
chcp 65001 >nul
REM ============================================================
REM 生成品牌资源（app-icon.png/.ico、splash-screen.png、logo-horizontal.png）
REM
REM 直接运行 tools\make_assets.py 即可；若运行环境禁止 Python 写文件，
REM 脚本会改为输出 *.b64，本批处理再用 PowerShell 解码落盘。
REM 需在 cmd.exe 中运行（Git Bash 请用 bash tools/build_assets.sh）。
REM ============================================================
cd /d %~dp0\..
set VENV=..\PolyXRD\venv\Scripts\python.exe
if not exist "%VENV%" set VENV=venv\Scripts\python.exe

"%VENV%" tools\make_assets.py
if errorlevel 1 goto :err

for %%f in (resources\*.b64) do (
    echo 解码 %%~nf
    powershell -NoProfile -Command "$b=[Convert]::FromBase64String((Get-Content -Raw '%%f')); [IO.File]::WriteAllBytes('resources\%%~nf', $b)"
    if not errorlevel 1 del "%%f"
)
echo.
echo 完成，产物在 resources\
goto :eof

:err
echo 生成失败，请检查上面的错误信息。
exit /b 1
