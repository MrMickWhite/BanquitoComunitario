"""
Servicio de Préstamos.

Coordina toda la lógica de un préstamo:
 - Otorgar (entrega dinero -> egreso de caja).
 - Registrar pago, desglosando automáticamente cuánto va a MORA, INTERÉS y CAPITAL.
 - Mantener el saldo de capital y el estado (activo / pagado / mora).

Orden de imputación del pago (estándar): primero MORA, luego INTERÉS, luego CAPITAL.
"""

from datetime import date
from utils.fechas import sumar_meses  # helper local (sin dependencias externas)
from models.entidades import Prestamo, Pago, Movimiento
from repositories import prestamo_repository, movimiento_repository
from services import interes_service
from services import config_service
from config import settings


def otorgar_prestamo(socio_id: int, monto: float, plazo_meses: int = 1,
                     tasa_mensual: float = None, fecha: str = None,
                     descripcion: str = "") -> int:
    """Crea el préstamo y registra el egreso de dinero de la caja."""
    if monto <= 0:
        raise ValueError("El monto del préstamo debe ser mayor a 0.")
    if tasa_mensual is None:
        tasa_mensual = config_service.obtener_float("TASA_INTERES_PRESTAMO_MENSUAL")
    if fecha is None:
        fecha = date.today().isoformat()

    fecha_venc = sumar_meses(fecha, 1)  # primer pago esperado en 1 mes

    prestamo = Prestamo(
        socio_id=socio_id, monto=monto, tasa_mensual=tasa_mensual,
        fecha_otorgado=fecha, plazo_meses=plazo_meses,
        fecha_vencimiento=fecha_venc, estado="activo",
        saldo_capital=monto, descripcion=descripcion,
    )
    prestamo_id = prestamo_repository.crear_prestamo(prestamo)

    movimiento_repository.registrar(Movimiento(
        fecha=fecha, tipo="egreso", categoria="prestamo", monto=monto,
        socio_id=socio_id, referencia=f"prestamo:{prestamo_id}",
        descripcion=descripcion or "Préstamo otorgado",
    ))
    return prestamo_id


def calcular_deuda_actual(prestamo_id: int, fecha=None) -> dict:
    """
    Calcula a una fecha dada cuánto debe el socio:
    capital pendiente + interés acumulado desde el último pago + mora si está atrasado.
    """
    if fecha is None:
        fecha = date.today().isoformat()
    prestamo = prestamo_repository.obtener_prestamo(prestamo_id)
    if prestamo is None:
        raise ValueError("Préstamo no encontrado.")

    pagos = prestamo_repository.listar_pagos_por_prestamo(prestamo_id)
    fecha_base = pagos[-1].fecha if pagos else prestamo.fecha_otorgado

    # Interés sobre saldo (decreciente) o fijo sobre el monto original
    tipo_int = config_service.obtener("TIPO_INTERES_PRESTAMO") or "saldo"
    base_interes = prestamo.monto if tipo_int == "fijo" else prestamo.saldo_capital
    interes = interes_service.interes_acumulado(
        base_interes, prestamo.tasa_mensual, fecha_base, fecha
    )
    mora = 0.0
    if prestamo.fecha_vencimiento:
        mora = interes_service.calcular_mora(
            prestamo.saldo_capital, prestamo.fecha_vencimiento, fecha
        )
    total = round(prestamo.saldo_capital + interes + mora, 2)
    return {
        "capital": prestamo.saldo_capital,
        "interes": interes,
        "mora": mora,
        "total": total,
    }


def registrar_pago(prestamo_id: int, monto: float, fecha: str = None,
                   descripcion: str = "") -> dict:
    """
    Registra un pago y lo reparte: primero mora, luego interés, luego capital.
    Actualiza el saldo y el estado del préstamo, y registra el ingreso a caja.
    """
    if monto <= 0:
        raise ValueError("El monto del pago debe ser mayor a 0.")
    if fecha is None:
        fecha = date.today().isoformat()

    prestamo = prestamo_repository.obtener_prestamo(prestamo_id)
    if prestamo is None:
        raise ValueError("Préstamo no encontrado.")

    deuda = calcular_deuda_actual(prestamo_id, fecha)
    restante = monto

    # 1) Mora
    pago_mora = min(restante, deuda["mora"])
    restante -= pago_mora
    # 2) Interés
    pago_interes = min(restante, deuda["interes"])
    restante -= pago_interes
    # 3) Capital (lo que sobre)
    pago_capital = min(restante, prestamo.saldo_capital)
    restante -= pago_capital

    # Guardar el pago
    pago_id = prestamo_repository.crear_pago(Pago(
        prestamo_id=prestamo_id, fecha=fecha, monto_total=monto,
        capital=pago_capital, interes=pago_interes, mora=pago_mora,
        descripcion=descripcion,
    ))

    # Actualizar saldo y estado del préstamo
    prestamo.saldo_capital = round(prestamo.saldo_capital - pago_capital, 2)
    if prestamo.saldo_capital <= 0.001:
        prestamo.saldo_capital = 0.0
        prestamo.estado = "pagado"
    else:
        prestamo.estado = "activo"
        prestamo.fecha_vencimiento = sumar_meses(fecha, 1)
    prestamo_repository.actualizar_prestamo(prestamo)

    # Registrar ingresos a caja por cada componente (referencia al PAGO para
    # poder deshacerlo limpiamente luego).
    for categoria, valor in (("pago_capital", pago_capital),
                             ("interes", pago_interes),
                             ("mora", pago_mora)):
        if valor > 0:
            movimiento_repository.registrar(Movimiento(
                fecha=fecha, tipo="ingreso", categoria=categoria, monto=valor,
                socio_id=prestamo.socio_id, referencia=f"pago:{pago_id}",
                descripcion=descripcion or f"Pago de préstamo ({categoria})",
            ))

    return {
        "capital": pago_capital, "interes": pago_interes, "mora": pago_mora,
        "sobrante": round(restante, 2), "saldo_restante": prestamo.saldo_capital,
        "estado": prestamo.estado,
    }


def eliminar_prestamo(prestamo_id: int) -> None:
    """
    Elimina un préstamo completo: sus pagos (por CASCADE) y TODOS los movimientos
    de caja asociados (el desembolso y los pagos). El saldo de caja se recalcula.
    """
    prestamo = prestamo_repository.obtener_prestamo(prestamo_id)
    if prestamo is None:
        raise ValueError("Préstamo no encontrado.")
    # Borrar movimientos de cada pago y del desembolso del préstamo
    for p in prestamo_repository.listar_pagos_por_prestamo(prestamo_id):
        movimiento_repository.eliminar_por_referencia(f"pago:{p.id}")
    movimiento_repository.eliminar_por_referencia(f"prestamo:{prestamo_id}")
    # Borrar el préstamo (CASCADE borra sus pagos)
    from database.connection import obtener_conexion
    with obtener_conexion() as conn:
        conn.execute("DELETE FROM prestamos WHERE id=?", (prestamo_id,))


def deshacer_ultimo_pago(prestamo_id: int) -> dict:
    """
    Revierte el ÚLTIMO pago de un préstamo: devuelve el capital al saldo, borra
    los movimientos de ese pago y reactiva el préstamo. Devuelve un resumen.
    """
    prestamo = prestamo_repository.obtener_prestamo(prestamo_id)
    if prestamo is None:
        raise ValueError("Préstamo no encontrado.")
    pagos = prestamo_repository.listar_pagos_por_prestamo(prestamo_id)
    if not pagos:
        raise ValueError("Este préstamo no tiene pagos para deshacer.")
    ultimo = pagos[-1]

    # Devolver el capital abonado al saldo y reactivar
    prestamo.saldo_capital = round(prestamo.saldo_capital + ultimo.capital, 2)
    prestamo.estado = "activo"
    prestamo_repository.actualizar_prestamo(prestamo)

    # Borrar los movimientos del pago y el pago en sí
    movimiento_repository.eliminar_por_referencia(f"pago:{ultimo.id}")
    from database.connection import obtener_conexion
    with obtener_conexion() as conn:
        conn.execute("DELETE FROM pagos WHERE id=?", (ultimo.id,))

    return {"capital_devuelto": ultimo.capital, "monto_pago": ultimo.monto_total,
            "saldo_actual": prestamo.saldo_capital}
