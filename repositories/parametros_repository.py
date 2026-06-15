"""Repositorio de parámetros (almacén clave-valor para la configuración)."""

from typing import Optional, Dict
from database.connection import obtener_conexion


def obtener(clave: str) -> Optional[str]:
    with obtener_conexion() as conn:
        f = conn.execute("SELECT valor FROM parametros WHERE clave=?", (clave,)).fetchone()
        return f["valor"] if f else None


def guardar(clave: str, valor: str) -> None:
    with obtener_conexion() as conn:
        conn.execute(
            """INSERT INTO parametros (clave, valor) VALUES (?, ?)
               ON CONFLICT(clave) DO UPDATE SET valor=excluded.valor""",
            (clave, str(valor)),
        )


def todos() -> Dict[str, str]:
    with obtener_conexion() as conn:
        filas = conn.execute("SELECT clave, valor FROM parametros").fetchall()
        return {f["clave"]: f["valor"] for f in filas}
