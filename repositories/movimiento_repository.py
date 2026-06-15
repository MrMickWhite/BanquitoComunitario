"""Repositorio de Movimientos: el libro general de caja."""

from typing import List, Dict
from database.connection import obtener_conexion
from models.entidades import Movimiento


def _fila_a_mov(f) -> Movimiento:
    cols = f.keys()
    return Movimiento(
        id=f["id"], fecha=f["fecha"], tipo=f["tipo"], categoria=f["categoria"],
        monto=f["monto"], socio_id=f["socio_id"], referencia=f["referencia"],
        descripcion=f["descripcion"],
        genera_interes=(f["genera_interes"] if "genera_interes" in cols else 0),
        tasa_interes=(f["tasa_interes"] if "tasa_interes" in cols else None),
    )


def registrar(mov: Movimiento) -> int:
    with obtener_conexion() as conn:
        cur = conn.execute(
            """INSERT INTO movimientos
               (fecha, tipo, categoria, monto, socio_id, referencia, descripcion,
                genera_interes, tasa_interes)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (mov.fecha, mov.tipo, mov.categoria, mov.monto, mov.socio_id,
             mov.referencia, mov.descripcion, mov.genera_interes, mov.tasa_interes),
        )
        return cur.lastrowid


def saldo_caja() -> float:
    """Dinero disponible = ingresos - egresos en todo el historial."""
    with obtener_conexion() as conn:
        r = conn.execute(
            """SELECT
                 COALESCE(SUM(CASE WHEN tipo='ingreso' THEN monto ELSE 0 END),0) -
                 COALESCE(SUM(CASE WHEN tipo='egreso'  THEN monto ELSE 0 END),0) AS saldo
               FROM movimientos"""
        ).fetchone()
        return float(r["saldo"])


def listar_por_periodo(fecha_inicio: str, fecha_fin: str) -> List[Movimiento]:
    with obtener_conexion() as conn:
        filas = conn.execute(            "SELECT * FROM movimientos WHERE fecha BETWEEN ? AND ? ORDER BY fecha",
            (fecha_inicio, fecha_fin),
        ).fetchall()
        return [_fila_a_mov(f) for f in filas]


def listar_por_socio(socio_id: int) -> List[Movimiento]:
    """Historial completo y fechado de un socio (aportes, préstamos, pagos...)."""
    with obtener_conexion() as conn:
        filas = conn.execute(
            "SELECT * FROM movimientos WHERE socio_id=? ORDER BY fecha DESC, id DESC",
            (socio_id,),
        ).fetchall()
        return [_fila_a_mov(f) for f in filas]


def totales_por_categoria(fecha_inicio: str, fecha_fin: str) -> Dict[str, float]:
    """Suma agrupada por categoría dentro de un periodo (para reportes)."""
    with obtener_conexion() as conn:
        filas = conn.execute(
            """SELECT categoria, tipo, COALESCE(SUM(monto),0) AS total
               FROM movimientos
               WHERE fecha BETWEEN ? AND ?
               GROUP BY categoria, tipo""",
            (fecha_inicio, fecha_fin),
        ).fetchall()
        return {f"{f['categoria']}_{f['tipo']}": float(f["total"]) for f in filas}


def listar_varios_recientes(limite: int = 100) -> List[Movimiento]:
    """Movimientos manuales de ingresos/egresos varios (categoría 'otro' o 'gasto')."""
    with obtener_conexion() as conn:
        filas = conn.execute(
            """SELECT * FROM movimientos
               WHERE categoria IN ('otro', 'gasto', 'ingreso_vario', 'egreso_vario')
               ORDER BY fecha DESC, id DESC LIMIT ?""",
            (limite,),
        ).fetchall()
        return [_fila_a_mov(f) for f in filas]


def eliminar(mov_id: int) -> None:
    with obtener_conexion() as conn:
        conn.execute("DELETE FROM movimientos WHERE id=?", (mov_id,))


def eliminar_por_referencia(referencia: str) -> None:
    """Borra todos los movimientos con una referencia dada (ej 'aporte:5', 'pago:3')."""
    with obtener_conexion() as conn:
        conn.execute("DELETE FROM movimientos WHERE referencia=?", (referencia,))


def listar_varios_periodo(fecha_inicio: str, fecha_fin: str) -> List[Movimiento]:
    """Ingresos/egresos varios dentro de un periodo (con su descripción)."""
    with obtener_conexion() as conn:
        filas = conn.execute(
            """SELECT * FROM movimientos
               WHERE categoria IN ('ingreso_vario','egreso_vario','otro','gasto')
                 AND fecha BETWEEN ? AND ?
               ORDER BY fecha ASC, id ASC""",
            (fecha_inicio, fecha_fin),
        ).fetchall()
        return [_fila_a_mov(f) for f in filas]


def totales_globales():
    """Devuelve (total_ingresos, total_egresos) de todo el historial."""
    with obtener_conexion() as conn:
        r = conn.execute(
            """SELECT
                 COALESCE(SUM(CASE WHEN tipo='ingreso' THEN monto END),0) AS ing,
                 COALESCE(SUM(CASE WHEN tipo='egreso'  THEN monto END),0) AS egr
               FROM movimientos""").fetchone()
        return round(r["ing"], 2), round(r["egr"], 2)


def total_caja_chica() -> float:
    """Suma de egresos marcados como caja chica (descripción '[Caja chica] ...')."""
    with obtener_conexion() as conn:
        r = conn.execute(
            "SELECT COALESCE(SUM(monto),0) AS s FROM movimientos "
            "WHERE tipo='egreso' AND descripcion LIKE '[Caja chica]%'").fetchone()
        return round(r["s"], 2)
