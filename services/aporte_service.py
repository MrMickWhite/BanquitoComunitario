"""
Servicio de Aportes.

Coordina: cuando un socio aporta, se guarda el aporte Y se registra el
movimiento de ingreso en la caja. Así el saldo de caja siempre cuadra.
"""

from datetime import date
from models.entidades import Aporte, Movimiento
from repositories import aporte_repository, movimiento_repository
from services import config_service
from config import settings


def registrar_aporte(socio_id: int, monto: float, fecha: str = None,
                     tipo: str = "aporte", descripcion: str = "",
                     genera_interes: bool = False, tasa_interes=None) -> int:
    minimo = config_service.obtener_float("APORTE_MINIMO")
    if monto < minimo:
        raise ValueError(f"El aporte mínimo es {settings.SIMBOLO_MONEDA}{minimo:.2f}")
    if fecha is None:
        fecha = date.today().isoformat()

    aporte = Aporte(socio_id=socio_id, monto=monto, fecha=fecha,
                    tipo=tipo, descripcion=descripcion)
    aporte_id = aporte_repository.crear(aporte)

    movimiento_repository.registrar(Movimiento(
        fecha=fecha, tipo="ingreso", categoria="aporte", monto=monto,
        socio_id=socio_id, referencia=f"aporte:{aporte_id}",
        descripcion=descripcion or "Aporte de socio",
        genera_interes=1 if genera_interes else 0,
        tasa_interes=tasa_interes,
    ))
    return aporte_id


def eliminar_aporte(aporte_id: int) -> None:
    """Borra un aporte y su movimiento de caja asociado (el saldo se recalcula)."""
    aporte_repository.eliminar(aporte_id)
    movimiento_repository.eliminar_por_referencia(f"aporte:{aporte_id}")
