"""
Servicio de cálculo de INTERESES y MORA.

Aquí vive la matemática financiera. La separamos en su propio módulo para
que sea fácil de revisar, probar y ajustar a las reglas reales de tu banquito.

SUPUESTOS (ajústalos en config/settings.py):
 - Interés del préstamo: mensual y simple, sobre el SALDO de capital pendiente.
     interes_mensual = saldo_capital * tasa_mensual
   Para un periodo de N días: se prorratea (N/30).
 - Mora: por día de atraso sobre el monto vencido.
     mora = monto_vencido * tasa_mora_diaria * dias_atraso
"""

from datetime import date
from config import settings
from services import config_service


def _a_fecha(valor) -> date:
    """Acepta un date o un string 'YYYY-MM-DD' y devuelve un date."""
    if isinstance(valor, date):
        return valor
    return date.fromisoformat(valor)


def interes_acumulado(saldo_capital: float, tasa_mensual: float,
                      fecha_desde, fecha_hasta) -> float:
    """
    Interés generado por un préstamo entre dos fechas, prorrateado por días.
    Ejemplo: saldo 100, tasa 2% mensual, 30 días -> 2.00
    """
    d0 = _a_fecha(fecha_desde)
    d1 = _a_fecha(fecha_hasta)
    dias = max((d1 - d0).days, 0)
    interes_mes = saldo_capital * tasa_mensual
    return round(interes_mes * (dias / 30.0), 2)


def calcular_mora(monto_vencido: float, fecha_vencimiento, fecha_pago,
                  tasa_diaria: float = None, dias_gracia: int = None) -> float:
    """
    Mora por pagar tarde. Devuelve 0 si paga a tiempo o dentro de los días de gracia.
    """
    if tasa_diaria is None:
        tasa_diaria = config_service.obtener_float("TASA_MORA_DIARIA")
    if dias_gracia is None:
        dias_gracia = config_service.obtener_int("DIAS_GRACIA_MORA")

    venc = _a_fecha(fecha_vencimiento)
    pago = _a_fecha(fecha_pago)
    dias_atraso = (pago - venc).days - dias_gracia
    if dias_atraso <= 0:
        return 0.0

    tipo = config_service.obtener("TIPO_MORA") or "diaria"
    if tipo == "fija":
        # Monto fijo por cada mes (o fracción) de atraso
        monto_fijo = config_service.obtener_float("MORA_FIJA_MONTO")
        meses_atraso = max(1, (dias_atraso + 29) // 30)
        return round(monto_fijo * meses_atraso, 2)
    # Mora diaria proporcional al monto vencido
    return round(monto_vencido * tasa_diaria * dias_atraso, 2)


def rendimiento_ahorro_anual(saldo_promedio: float, tasa_anual: float = None) -> float:
    """
    Rendimiento que el banquito reconoce a los ahorros de un socio al cerrar el año.
    Útil para el reparto de utilidades. (Modelo simple sobre saldo promedio.)
    """
    if tasa_anual is None:
        tasa_anual = config_service.obtener_float("TASA_INTERES_AHORRO_ANUAL")
    return round(saldo_promedio * tasa_anual, 2)
