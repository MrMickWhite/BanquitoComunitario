"""Repositorio de Aportes (ahorros/contribuciones de los socios)."""

from typing import List
from database.connection import obtener_conexion
from models.entidades import Aporte


def _fila_a_aporte(f) -> Aporte:
    return Aporte(id=f["id"], socio_id=f["socio_id"], monto=f["monto"],
                  fecha=f["fecha"], tipo=f["tipo"], descripcion=f["descripcion"])


def crear(aporte: Aporte) -> int:
    with obtener_conexion() as conn:
        cur = conn.execute(
            """INSERT INTO aportes (socio_id, monto, fecha, tipo, descripcion)
               VALUES (?, ?, ?, ?, ?)""",
            (aporte.socio_id, aporte.monto, aporte.fecha, aporte.tipo, aporte.descripcion),
        )
        return cur.lastrowid


def eliminar(aporte_id: int) -> None:
    with obtener_conexion() as conn:
        conn.execute("DELETE FROM aportes WHERE id=?", (aporte_id,))


def listar_por_socio(socio_id: int) -> List[Aporte]:
    with obtener_conexion() as conn:
        filas = conn.execute(
            "SELECT * FROM aportes WHERE socio_id=? ORDER BY fecha", (socio_id,)
        ).fetchall()
        return [_fila_a_aporte(f) for f in filas]


def total_por_socio(socio_id: int) -> float:
    with obtener_conexion() as conn:
        r = conn.execute(
            "SELECT COALESCE(SUM(monto),0) AS t FROM aportes WHERE socio_id=?", (socio_id,)
        ).fetchone()
        return float(r["t"])


def listar_por_periodo(fecha_inicio: str, fecha_fin: str) -> List[Aporte]:
    with obtener_conexion() as conn:
        filas = conn.execute(
            "SELECT * FROM aportes WHERE fecha BETWEEN ? AND ? ORDER BY fecha",
            (fecha_inicio, fecha_fin),
        ).fetchall()
        return [_fila_a_aporte(f) for f in filas]
