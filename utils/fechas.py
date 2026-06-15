"""
Utilidades de fechas (sin librerías externas, solo la estándar de Python).
"""

import calendar
from datetime import date


def _a_fecha(valor) -> date:
    if isinstance(valor, date):
        return valor
    return date.fromisoformat(valor)


def sumar_meses(fecha, meses: int) -> str:
    """Suma 'meses' a una fecha y devuelve 'YYYY-MM-DD'. Maneja fin de mes."""
    d = _a_fecha(fecha)
    mes_total = d.month - 1 + meses
    anio = d.year + mes_total // 12
    mes = mes_total % 12 + 1
    ultimo_dia = calendar.monthrange(anio, mes)[1]
    dia = min(d.day, ultimo_dia)
    return date(anio, mes, dia).isoformat()


def rango_mes(anio: int, mes: int):
    """Devuelve (primer_dia, ultimo_dia) del mes como strings ISO."""
    ultimo = calendar.monthrange(anio, mes)[1]
    return date(anio, mes, 1).isoformat(), date(anio, mes, ultimo).isoformat()


def rango_anio(anio: int):
    """Devuelve (1 de enero, 31 de diciembre) del año como strings ISO."""
    return date(anio, 1, 1).isoformat(), date(anio, 12, 31).isoformat()


def rango_semana(fecha):
    """Devuelve (lunes, domingo) de la semana que contiene 'fecha', como ISO."""
    from datetime import timedelta
    d = _a_fecha(fecha)
    lunes = d - timedelta(days=d.weekday())
    domingo = lunes + timedelta(days=6)
    return lunes.isoformat(), domingo.isoformat()


NOMBRES_MESES = [
    "", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
    "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre",
]
