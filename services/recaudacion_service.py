"""
Servicio de Recaudación (método de acumulación de dinero).

El banquito recauda en fechas establecidas: cada semana (un día fijo, p. ej.
los lunes) o cada mes (un día fijo, p. ej. el día 5). Esto se configura en
Configuración → Recaudación, junto con una cuota opcional.

Este servicio calcula la PRÓXIMA fecha de recaudación según esa configuración,
para mostrarla en el Dashboard y en Aportes.
"""

import calendar
from datetime import date, timedelta
from services import config_service

DIAS_SEMANA = ["Lunes", "Martes", "Miércoles", "Jueves",
               "Viernes", "Sábado", "Domingo"]


def proxima_fecha(desde: date = None) -> date:
    """Próxima fecha de recaudación (incluye hoy si hoy toca recaudar)."""
    if desde is None:
        desde = date.today()
    frecuencia = config_service.obtener("FRECUENCIA_RECAUDACION") or "mensual"

    if frecuencia == "semanal":
        objetivo = config_service.obtener_int("DIA_RECAUDACION_SEMANA")  # 0=Lunes
        delta = (objetivo - desde.weekday()) % 7
        return desde + timedelta(days=delta)

    # Mensual: día fijo del mes (si el mes es más corto, usa el último día)
    dia = max(1, min(31, config_service.obtener_int("DIA_RECAUDACION_MES")))
    ultimo = calendar.monthrange(desde.year, desde.month)[1]
    dia_mes = min(dia, ultimo)
    if desde.day <= dia_mes:
        return date(desde.year, desde.month, dia_mes)
    anio = desde.year + (1 if desde.month == 12 else 0)
    mes = 1 if desde.month == 12 else desde.month + 1
    ultimo = calendar.monthrange(anio, mes)[1]
    return date(anio, mes, min(dia, ultimo))


def descripcion(desde: date = None) -> str:
    """Texto legible: 'lunes 2026-06-15 (semanal) · Cuota: $10.00'."""
    from config import settings
    f = proxima_fecha(desde)
    frecuencia = config_service.obtener("FRECUENCIA_RECAUDACION") or "mensual"
    dia_nombre = DIAS_SEMANA[f.weekday()]
    texto = f"{dia_nombre} {f.isoformat()}  ({frecuencia})"
    cuota = config_service.obtener_float("CUOTA_RECAUDACION")
    if cuota > 0:
        texto += f"  ·  Cuota: {settings.SIMBOLO_MONEDA}{cuota:,.2f}"
    else:
        texto += "  ·  Aporte libre"
    return texto
