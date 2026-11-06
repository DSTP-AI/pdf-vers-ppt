#!/bin/bash
# Construit "PDF vers PPT.app" pour Mac Apple Silicon (M1/M2/M3...)
# Usage : ouvrir le Terminal dans ce dossier puis : bash build_mac.sh
set -e
cd "$(dirname "$0")"
PY=${PYTHON:-python3}
rm -rf .venv-build
"$PY" -m venv .venv-build
source .venv-build/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
rm -rf build dist
APP="dist/PDF vers PPT.app"
pyinstaller --noconfirm --windowed --name "PDF vers PPT" \
  --target-arch "${ARCH:-arm64}" \
  --icon assets/icon.icns \
  --add-data "assets:assets" \
  --osx-bundle-identifier fr.dstp.pdfversppt \
  app.py
# L'app accepte les PDF glissés sur son icône (Dock / Finder)
PL="$APP/Contents/Info.plist"
/usr/libexec/PlistBuddy -c "Delete :CFBundleDocumentTypes" "$PL" 2>/dev/null || true
/usr/libexec/PlistBuddy \
  -c "Add :CFBundleDocumentTypes array" \
  -c "Add :CFBundleDocumentTypes:0 dict" \
  -c "Add :CFBundleDocumentTypes:0:CFBundleTypeName string PDF" \
  -c "Add :CFBundleDocumentTypes:0:CFBundleTypeRole string Viewer" \
  -c "Add :CFBundleDocumentTypes:0:LSHandlerRank string Alternate" \
  -c "Add :CFBundleDocumentTypes:0:LSItemContentTypes array" \
  -c "Add :CFBundleDocumentTypes:0:LSItemContentTypes:0 string com.adobe.pdf" \
  "$PL"
/usr/libexec/PlistBuddy -c "Set :CFBundleShortVersionString 2.0" "$PL" 2>/dev/null || true
# signature ad hoc (nécessaire sur Apple Silicon) + retrait de la quarantaine
codesign --force --deep --sign - "$APP"
xattr -cr "$APP"
cd dist && ditto -c -k --keepParent "PDF vers PPT.app" "PDF-vers-PPT-mac-${ARCH:-arm64}.zip"
echo "OK : dist/PDF vers PPT.app"
