@echo off
rem Gera dist\Instalar-HushHush-PTBR.exe (requer Python 3.11+ no PATH)
python -m venv .venv || goto :erro
.venv\Scripts\python -m pip install -r requirements.txt pyinstaller || goto :erro
.venv\Scripts\pyinstaller --noconfirm --clean --onefile --console --name Instalar-HushHush-PTBR ^
  --add-data "dados;dados" --paths . ^
  --collect-all UnityPy --collect-all fmod_toolkit --collect-all texture2ddecoder ^
  --collect-all astc_encoder --collect-all archspec instalar.py || goto :erro
echo.
echo Pronto: dist\Instalar-HushHush-PTBR.exe
exit /b 0
:erro
echo Falhou.
exit /b 1
