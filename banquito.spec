# -*- mode: python ; coding: utf-8 -*-
"""
Spec de PyInstaller para compilar el MMWBank a un .exe (Windows).

Compilar:
    pip install pyinstaller
    pyinstaller banquito.spec

El .exe queda en  dist/MMWBank/MMWBank.exe
Copia toda la carpeta dist/MMWBank a la PC destino. La base de datos y los
reportes se crean solos en una carpeta escribible del usuario (no requiere
permisos de administrador).
"""

from PyInstaller.utils.hooks import collect_all

datas = [("database/schema.sql", "database"), ("assets/banquito.ico", "assets"),
         ("assets/banquito.png", "assets")]
binaries = []
hiddenimports = ["config.local_secrets"]

# Incluir archivos de datos de estas librerías (temas, fuentes, etc.)
for paquete in ("customtkinter", "reportlab"):
    d, b, h = collect_all(paquete)
    datas += d
    binaries += b
    hiddenimports += h

a = Analysis(
    ["main.py"],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz, a.scripts, [], exclude_binaries=True,
    name="MMWBank",
    console=False,          # sin ventana de consola
    icon="assets/banquito.ico",
)
coll = COLLECT(
    exe, a.binaries, a.datas,
    strip=False, upx=True, name="MMWBank",
)
