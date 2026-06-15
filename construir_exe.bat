@echo off
REM ============================================================
REM  Compila el Banquito a un .exe (Windows).
REM  Doble clic para ejecutar. Necesita Python instalado.
REM ============================================================
echo Instalando dependencias...
pip install -r requirements.txt
pip install pyinstaller pillow

echo.
echo Compilando el .exe...
pyinstaller banquito.spec --noconfirm

echo.
echo ============================================================
echo  Listo. El programa esta en:  dist\MMWBank\MMWBank.exe
echo.
echo  PARA CREAR EL INSTALADOR (icono + escritorio + Archivos de
echo  Programa): instala Inno Setup (gratis) desde
echo     https://jrsoftware.org/isdl.php
echo  y luego abre el archivo  instalador.iss  y dale Compile.
echo  Se generara  Salida\Instalador-MMWBank.exe
echo ============================================================
pause
