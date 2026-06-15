"""Repositorio de Préstamos y Pagos."""

from typing import List, Optional
from database.connection import obtener_conexion
from models.entidades import Prestamo, Pago


def _fila_a_prestamo(f) -> Prestamo:
    return Prestamo(
        id=f["id"], socio_id=f["socio_id"], monto=f["monto"],
        tasa_mensual=f["tasa_mensual"], fecha_otorgado=f["fecha_otorgado"],
        plazo_meses=f["plazo_meses"], fecha_vencimiento=f["fecha_vencimiento"],
        estado=f["estado"], saldo_capital=f["saldo_capital"], descripcion=f["descripcion"],
    )


def _fila_a_pago(f) -> Pago:
    return Pago(id=f["id"], prestamo_id=f["prestamo_id"], fecha=f["fecha"],
                monto_total=f["monto_total"], capital=f["capital"], interes=f["interes"],
                mora=f["mora"], descripcion=f["descripcion"])


# ----------------------------- Préstamos -----------------------------------
def crear_prestamo(p: Prestamo) -> int:
    with obtener_conexion() as conn:
        cur = conn.execute(
            """INSERT INTO prestamos
               (socio_id, monto, tasa_mensual, fecha_otorgado, plazo_meses,
                fecha_vencimiento, estado, saldo_capital, descripcion)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (p.socio_id, p.monto, p.tasa_mensual, p.fecha_otorgado, p.plazo_meses,
             p.fecha_vencimiento, p.estado, p.saldo_capital, p.descripcion),
        )
        return cur.lastrowid


def actualizar_prestamo(p: Prestamo) -> None:
    with obtener_conexion() as conn:
        conn.execute(
            """UPDATE prestamos SET
               estado=?, saldo_capital=?, fecha_vencimiento=?
               WHERE id=?""",
            (p.estado, p.saldo_capital, p.fecha_vencimiento, p.id),
        )


def obtener_prestamo(prestamo_id: int) -> Optional[Prestamo]:
    with obtener_conexion() as conn:
        f = conn.execute("SELECT * FROM prestamos WHERE id=?", (prestamo_id,)).fetchone()
        return _fila_a_prestamo(f) if f else None


def listar_prestamos(solo_activos: bool = False) -> List[Prestamo]:
    sql = "SELECT * FROM prestamos"
    if solo_activos:
        sql += " WHERE estado != 'pagado'"
    sql += " ORDER BY fecha_otorgado DESC"
    with obtener_conexion() as conn:
        return [_fila_a_prestamo(f) for f in conn.execute(sql).fetchall()]


def listar_prestamos_por_socio(socio_id: int) -> List[Prestamo]:
    with obtener_conexion() as conn:
        filas = conn.execute(
            "SELECT * FROM prestamos WHERE socio_id=? ORDER BY fecha_otorgado DESC",
            (socio_id,),
        ).fetchall()
        return [_fila_a_prestamo(f) for f in filas]


# ------------------------------- Pagos -------------------------------------
def crear_pago(pago: Pago) -> int:
    with obtener_conexion() as conn:
        cur = conn.execute(
            """INSERT INTO pagos
               (prestamo_id, fecha, monto_total, capital, interes, mora, descripcion)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (pago.prestamo_id, pago.fecha, pago.monto_total, pago.capital,
             pago.interes, pago.mora, pago.descripcion),
        )
        return cur.lastrowid


def listar_pagos_por_prestamo(prestamo_id: int) -> List[Pago]:
    with obtener_conexion() as conn:
        filas = conn.execute(
            "SELECT * FROM pagos WHERE prestamo_id=? ORDER BY fecha", (prestamo_id,)
        ).fetchall()
        return [_fila_a_pago(f) for f in filas]
