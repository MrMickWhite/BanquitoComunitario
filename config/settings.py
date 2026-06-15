"""
Configuración central del sistema.

IMPORTANTE: Todos los parámetros financieros viven aquí (o en la tabla
'parametros' de la BD para poder editarlos desde la interfaz sin tocar código).
Así, si tu banquito cambia las tasas, solo cambias un valor.

Estos son los SUPUESTOS por defecto. Ajústalos a las reglas reales de tu caja.
"""

import os
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Rutas del proyecto  (compatibles con ejecución normal y con .exe PyInstaller)
# ---------------------------------------------------------------------------
if getattr(sys, "frozen", False):
    # Empaquetado como .exe: los archivos incluidos (schema.sql) están en _MEIPASS,
    # y los datos (BD, etc.) se guardan en una carpeta ESCRIBIBLE del usuario.
    BASE_DIR = Path(getattr(sys, "_MEIPASS", Path(sys.executable).resolve().parent))
    _WRITABLE = Path(os.environ.get("LOCALAPPDATA") or Path.home()) / "MMWBank"
else:
    BASE_DIR = Path(__file__).resolve().parent.parent
    _WRITABLE = BASE_DIR

DATA_DIR = _WRITABLE / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Ruta del archivo de base de datos SQLite (un solo archivo, cero configuración)
DB_PATH = DATA_DIR / "banquito.db"

# Carpeta donde se guardan los PDF generados
REPORTS_OUTPUT_DIR = DATA_DIR / "reportes"
REPORTS_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Recursos visuales (icono y logo). Funciona en desarrollo y dentro del .exe.
ASSETS_DIR = BASE_DIR / "assets"
ICONO_ICO = ASSETS_DIR / "banquito.ico"
LOGO_PNG = ASSETS_DIR / "banquito.png"

# ---------------------------------------------------------------------------
# Datos de la organización (salen en los reportes / PDF)
# ---------------------------------------------------------------------------
NOMBRE_ORGANIZACION = "Banquito Comunitario"
MONEDA = "USD"
SIMBOLO_MONEDA = "$"

# ---------------------------------------------------------------------------
# Parámetros financieros (valores por defecto)
# ---------------------------------------------------------------------------
# Interés que se cobra sobre los PRÉSTAMOS (mensual, sobre saldo pendiente)
# 0.02 = 2% mensual
TASA_INTERES_PRESTAMO_MENSUAL = 0.02

# Mora por atraso. Se cobra sobre la cuota/monto vencido.
# Puede ser diaria o mensual; aquí usamos diaria.
# 0.001 = 0.1% por día de atraso
TASA_MORA_DIARIA = 0.001

# Interés que el banquito RECONOCE a los ahorros de los socios (anual).
# Sirve para el reparto/rendimiento de fin de año. 0.05 = 5% anual.
TASA_INTERES_AHORRO_ANUAL = 0.05

# Aporte mínimo permitido (validación de la interfaz)
APORTE_MINIMO = 1.00

# Días de gracia antes de empezar a cobrar mora
DIAS_GRACIA_MORA = 0

# ---------------------------------------------------------------------------
# Usuario ADMIN
# ---------------------------------------------------------------------------
# Se crea automáticamente en cada instalación. Los valores reales viven en
# config/local_secrets.py (no se sube a GitHub). Si están vacíos, la app usa
# valores seguros por defecto (usuario/usuario y mrmick/123456).
DEMO_ADMIN_ENABLED = True
DEMO_ADMIN_USER = ""
DEMO_ADMIN_PASS = ""

# Usuario inicial que se crea al instalar (obliga a cambiar usuario/clave al entrar)
USUARIO_INICIAL = ""
PASS_INICIAL = ""

# Código FIJO de recuperación de contraseña (se entrega al cliente por correo).
# El valor real va en config/local_secrets.py (privado).
CODIGO_RECUPERACION = ""

# Frase secreta para validar las licencias. El valor real va en local_secrets.py.
LICENCIA_SECRETO = ""

# Correo de soporte/ventas (sale en las pantallas de ayuda y precios)
CORREO_SOPORTE = "mrmickdesign@gmail.com"

# Nombre y versión del programa (la marca; el nombre que pone el cliente es aparte)
NOMBRE_APP = "MMWBank"
VERSION_APP = "v2.5.13"

# Precios de los planes (USD)
PLANES = {
    "mensual":   {"nombre": "Mensual",   "precio": 7,  "meses": 1},
    "semestral": {"nombre": "Semestral", "precio": 35, "meses": 6},
    "anual":     {"nombre": "Anual",     "precio": 63, "meses": 12},
}

# ---------------------------------------------------------------------------
# Claves PRIVADAS (no se suben a GitHub).
# Los valores reales viven en  config/local_secrets.py  (excluido por .gitignore).
# Si ese archivo existe, sus valores reemplazan a los de arriba. Así el
# repositorio público muestra las claves vacías, pero tu .exe compilado funciona.
# ---------------------------------------------------------------------------
try:
    from config.local_secrets import *  # noqa: F401,F403
except Exception:
    pass
