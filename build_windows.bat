@echo off
REM Construit "PDF vers PPT.exe" pour Windows 10 / 11 (64 bits)
REM Prerequis : Python 3.11+ de python.org (cocher "Add to PATH")
cd /d "%~dp0"
py -3 -m venv .venv-build || python -m venv .venv-build
call .venv-build\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt
rmdir /s /q build dist 2>nul
pyinstaller --noconfirm --onefile --windowed --name "PDF vers PPT" app.py
echo OK : dist\PDF vers PPT.exe
pause
