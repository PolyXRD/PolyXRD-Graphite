#!/usr/bin/env bash
# 生成品牌资源（Git Bash 版）。Python 进程被禁止写文件时，走 --emit + base64 -d 落盘。
set -euo pipefail
cd "$(dirname "$0")/.."
PY="../PolyXRD/venv/Scripts/python.exe"
[ -x "$PY" ] || PY="python"
for n in app-icon.png app-icon.ico splash-screen.png logo-horizontal.png; do
  "$PY" tools/make_assets.py --emit "$n" | base64 -d > "resources/$n"
  echo "resources/$n  $(stat -c%s "resources/$n") bytes"
done
