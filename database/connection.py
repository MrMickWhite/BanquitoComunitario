"""
Gestor de la conexión a SQLite.

¿Por qué SQLite?
 - Es GRATIS y no necesita servidor.
 - Es UN SOLO ARCHIVO (data/banquito.db). El cliente no configura nada.
 - Está incluido en Python (módulo sqlite3), no instalas nada.

Toda la app pide conexiones aquí. Si el día de mañana migras a PostgreSQL,
solo cambias este archivo y los repositorios siguen funcionando casi igual.
"""

import sqlite3
from contextlib import contextmanager
from config import settings


def _crear_conexion() -> sqlite3.Connection:
    """Abre una conexión y activa buenas prácticas de SQLite."""
    conn = sqlite3.connect(settings.DB_PATH)
    # Devuelve filas como diccionarios (row["nombres"] en vez de row[0])
    conn.row_factory = sqlite3.Row
    # Activa las llaves foráneas (por defecto SQLite las ignora)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


@contextmanager
def obtener_conexion():
    """
    Context manager: usa 'with obtener_conexion() as conn:' y se encarga
    de hacer commit si todo salió bien, o rollback si hubo error, y de
    cerrar la conexión siempre.
    """
    conn = _crear_conexion()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _migrar(conn):
    """
    Migraciones suaves para bases ya existentes: agrega columnas nuevas si faltan
    (CREATE TABLE IF NOT EXISTS no altera tablas que ya existían).
    """
    cols = {f["name"] for f in conn.execute("PRAGMA table_info(movimientos)").fetchall()}
    if "genera_interes" not in cols:
        conn.execute("ALTER TABLE movimientos ADD COLUMN genera_interes INTEGER NOT NULL DEFAULT 0")
    if "tasa_interes" not in cols:
        conn.execute("ALTER TABLE movimientos ADD COLUMN tasa_interes REAL")
    ucols = {f["name"] for f in conn.execute("PRAGMA table_info(usuarios)").fetchall()}
    if "debe_cambiar" not in ucols:
        conn.execute("ALTER TABLE usuarios ADD COLUMN debe_cambiar INTEGER NOT NULL DEFAULT 0")
    if "es_admin" not in ucols:
        conn.execute("ALTER TABLE usuarios ADD COLUMN es_admin INTEGER NOT NULL DEFAULT 0")


def inicializar_base_de_datos():
    """Crea las tablas si no existen. Se llama una vez al arrancar la app."""
    schema_path = settings.BASE_DIR / "database" / "schema.sql"
    with open(schema_path, "r", encoding="utf-8") as f:
        schema_sql = f.read()
    with obtener_conexion() as conn:
        conn.executescript(schema_sql)
        _migrar(conn)
    # Crear usuarios iniciales locales (usuario/usuario y admin mrmick/123456)
    from services import auth_service
    auth_service.sembrar_usuarios_iniciales()


def reiniciar_base_de_datos():
    """
    BORRA TODA la base de datos y la vuelve a crear desde cero (tablas vacías,
    100 códigos nuevos y el admin de demostración). Se usa para 'iniciar de nuevo'.
    """
    import os
    try:
        if os.path.exists(settings.DB_PATH):
            os.remove(settings.DB_PATH)
    except Exception as e:
        raise RuntimeError(f"No se pudo borrar la base de datos: {e}")
    inicializar_base_de_datos()
