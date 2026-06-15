"""
Repositorio de Socios.

Un "repositorio" encapsula TODO el acceso a la base de datos para una entidad.
La interfaz y los servicios nunca escriben SQL directo: llaman a estos métodos.
Ventaja: si cambias de SQLite a PostgreSQL, solo tocas esta capa.
"""

from typing import List, Optional
from database.connection import obtener_conexion
from models.entidades import Socio


def _fila_a_socio(fila) -> Socio:
    return Socio(
        id=fila["id"],
        nombres=fila["nombres"],
        apellidos=fila["apellidos"],
        documento=fila["documento"],
        telefono=fila["telefono"],
        email=fila["email"],
        fecha_ingreso=fila["fecha_ingreso"],
        activo=fila["activo"],
        notas=fila["notas"],
    )


def crear(socio: Socio) -> int:
    """Inserta un socio y devuelve su id."""
    with obtener_conexion() as conn:
        cur = conn.execute(
            """INSERT INTO socios
               (nombres, apellidos, documento, telefono, email, fecha_ingreso, activo, notas)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (socio.nombres, socio.apellidos, socio.documento, socio.telefono,
             socio.email, socio.fecha_ingreso, socio.activo, socio.notas),
        )
        return cur.lastrowid


def actualizar(socio: Socio) -> None:
    with obtener_conexion() as conn:
        conn.execute(
            """UPDATE socios SET
               nombres=?, apellidos=?, documento=?, telefono=?, email=?,
               fecha_ingreso=?, activo=?, notas=?
               WHERE id=?""",
            (socio.nombres, socio.apellidos, socio.documento, socio.telefono,
             socio.email, socio.fecha_ingreso, socio.activo, socio.notas, socio.id),
        )


def eliminar(socio_id: int) -> None:
    """
    Elimina un socio. Gracias a ON DELETE CASCADE en el esquema, también se
    borran sus aportes, préstamos y pagos. Si prefieres NO borrar el historial,
    usa 'desactivar' en lugar de este método.
    """
    with obtener_conexion() as conn:
        conn.execute("DELETE FROM socios WHERE id=?", (socio_id,))


def desactivar(socio_id: int) -> None:
    """Marca al socio como inactivo sin borrar su historial (recomendado)."""
    with obtener_conexion() as conn:
        conn.execute("UPDATE socios SET activo=0 WHERE id=?", (socio_id,))


def obtener_por_id(socio_id: int) -> Optional[Socio]:
    with obtener_conexion() as conn:
        fila = conn.execute("SELECT * FROM socios WHERE id=?", (socio_id,)).fetchone()
        return _fila_a_socio(fila) if fila else None


def listar(solo_activos: bool = False) -> List[Socio]:
    sql = "SELECT * FROM socios"
    if solo_activos:
        sql += " WHERE activo=1"
    sql += " ORDER BY apellidos, nombres"
    with obtener_conexion() as conn:
        filas = conn.execute(sql).fetchall()
        return [_fila_a_socio(f) for f in filas]
