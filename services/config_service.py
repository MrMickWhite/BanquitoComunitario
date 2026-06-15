"""
Servicio de Configuración.

Lee y guarda parámetros en la base de datos (tabla 'parametros'). Si un
parámetro no existe en la BD, usa el valor por defecto definido en DEFAULTS
(que a su vez vienen de config/settings.py). Así se editan las tasas y el
tema desde la interfaz SIN tocar el código.

Las tasas se guardan como FRACCIÓN (ej: 0.02 = 2%).
"""

from repositories import parametros_repository
from config import settings

# Valores por defecto (clave -> valor). Las claves van en MAYÚSCULAS.
DEFAULTS = {
    "TASA_INTERES_PRESTAMO_MENSUAL": settings.TASA_INTERES_PRESTAMO_MENSUAL,
    "TASA_MORA_DIARIA":              settings.TASA_MORA_DIARIA,
    "TASA_INTERES_AHORRO_ANUAL":     settings.TASA_INTERES_AHORRO_ANUAL,
    "APORTE_MINIMO":                 settings.APORTE_MINIMO,
    "DIAS_GRACIA_MORA":              settings.DIAS_GRACIA_MORA,
    "APARIENCIA":                    "dark",
    # --- Identidad (afecta los PDF y la carpeta de reportes del escritorio) ---
    "NOMBRE_BANCO":                  settings.NOMBRE_ORGANIZACION,
    # --- Método de recaudación (acumulación de dinero) ---
    "FRECUENCIA_RECAUDACION":        "mensual",  # semanal | mensual
    "DIA_RECAUDACION_SEMANA":        0,           # 0=Lunes ... 6=Domingo
    "DIA_RECAUDACION_MES":           1,           # día del mes (1..31)
    "CUOTA_RECAUDACION":             0.0,         # 0 = aporte libre
    "CAJA_CHICA_FONDO":              0.0,         # fondo fijo de caja chica
    "NOMBRE_CARPETA_REPORTES":       "",          # vacío = "Reportes <NOMBRE_BANCO>"
    "BANCO_CONFIGURADO":             "",          # "1" cuando ya se nombró el banco
    "LOGO_BANCO":                    "",          # ruta a logo propio del banco (PDF)
    # --- Reglas financieras (cada caja las ajusta a su gusto) ---
    "TIPO_INTERES_PRESTAMO":         "saldo",     # saldo | fijo
    "TIPO_MORA":                     "diaria",    # diaria | fija
    "MORA_FIJA_MONTO":               1.0,         # monto fijo de mora por mes de atraso
    "MODO_FIN_ANIO":                 "fondo",     # fondo | reparto
    "INCLUIR_INTERES_ESTIMADO":      "",          # "1" = sumar intereses estimados a la utilidad
}


def obtener(clave: str):
    """Devuelve el valor (string) guardado, o el default. None si no hay default."""
    v = parametros_repository.obtener(clave)
    if v is not None:
        return v
    d = DEFAULTS.get(clave)
    return str(d) if d is not None else None


def obtener_float(clave: str) -> float:
    v = parametros_repository.obtener(clave)
    if v is None:
        return float(DEFAULTS.get(clave, 0.0))
    try:
        return float(v)
    except (TypeError, ValueError):
        return float(DEFAULTS.get(clave, 0.0))


def obtener_int(clave: str) -> int:
    v = parametros_repository.obtener(clave)
    if v is None:
        return int(DEFAULTS.get(clave, 0))
    try:
        return int(float(v))
    except (TypeError, ValueError):
        return int(DEFAULTS.get(clave, 0))


def guardar(clave: str, valor) -> None:
    parametros_repository.guardar(clave, str(valor))
