#!/bin/bash
# Construit "PDF vers PPT.app" pour Mac Apple Silicon (M1/M2/M3...)
# Usage : ouvrir le Terminal dans ce dossier puis : bash build_mac.sh
set -e
cd "$(dirname "$0")"
PY=${PYTHON:-python3}
"$PY" -c "import tkinter" || { echo "Python sans Tkinter : installez Python depuis python.org (ou 'brew install python-tk')"; exit 1; }
"$PY" -m venv .venv-build
source .venv-build/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
rm -rf build dist
pyinstaller --noconfirm --windowed --name "PDF vers PPT" \
  --target-arch arm64 \
  --osx-bundle-identifier fr.dstp.pdfversppt \
  app.py
# signature ad hoc (nécessaire sur Apple Silicon) + retrait de la quarantaine
codesign --force --deep --sign - "dist/PDF vers PPT.app"
xattr -cr "dist/PDF vers PPT.app"
cd dist && ditto -c -k --keepParent "PDF vers PPT.app" "PDF-vers-PPT-mac-arm64.zip"
echo "OK : dist/PDF vers PPT.app"
