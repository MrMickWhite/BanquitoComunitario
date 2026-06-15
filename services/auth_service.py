"""
Servicio de Autenticación — 100% local (sin internet).

Flujo:
  - Al instalar existen dos usuarios:
      * usuario / usuario   -> al entrar la primera vez OBLIGA a cambiar
                               nombre de usuario y contraseña.
      * mrmick / 123456     -> administrador.
  - Recuperación: si el cliente olvida su contraseña, se contacta por correo
    con el proveedor y se le da el CÓDIGO DE RECUPERACIÓN (fijo, en settings).
    Con ese código puede cambiar SOLO su contraseña dentro de la app.

La contraseña nunca se guarda en texto plano (PBKDF2-HMAC-SHA256 + salt).
"""

import os
import hashlib
import binascii
from datetime import date
from database.connection import obtener_conexion
from config import settings


def _hash_password(password: str, salt: bytes = None):
    if salt is None:
        salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100_000)
    return binascii.hexlify(salt).decode(), binascii.hexlify(dk).decode()


def usuario_existe(usuario: str) -> bool:
    with obtener_conexion() as conn:
        r = conn.execute("SELECT 1 FROM usuarios WHERE usuario=?",
                         ((usuario or "").strip(),)).fetchone()
        return r is not None


def _crear(conn, usuario, password, admin=False, debe_cambiar=False):
    salt_hex, hash_hex = _hash_password(password)
    conn.execute(
        """INSERT INTO usuarios
           (usuario, email, telefono, password_hash, salt, confirmado,
            codigo_confirmacion, debe_cambiar, es_admin, fecha_creacion)
           VALUES (?, '', '', ?, ?, 1, NULL, ?, ?, ?)""",
        (usuario, hash_hex, salt_hex, 1 if debe_cambiar else 0,
         1 if admin else 0, date.today().isoformat()),
    )


def sembrar_usuarios_iniciales():
    """Crea el usuario inicial y el admin si no existen. Se llama al iniciar la BD.
    Usa valores seguros por defecto para que la app funcione aunque las claves
    en settings estén vacías (p. ej. en un clon público sin local_secrets)."""
    u_ini = getattr(settings, "USUARIO_INICIAL", "") or "usuario"
    p_ini = getattr(settings, "PASS_INICIAL", "") or "usuario"
    adm = getattr(settings, "DEMO_ADMIN_USER", "") or "mrmick"
    adm_pass = getattr(settings, "DEMO_ADMIN_PASS", "") or "123456"
    with obtener_conexion() as conn:
        ya = conn.execute("SELECT 1 FROM usuarios WHERE usuario=?", (u_ini,)).fetchone()
        if not ya:
            _crear(conn, u_ini, p_ini, admin=False, debe_cambiar=True)
        if getattr(settings, "DEMO_ADMIN_ENABLED", True):
            ya_adm = conn.execute("SELECT 1 FROM usuarios WHERE usuario=?", (adm,)).fetchone()
            if not ya_adm:
                _crear(conn, adm, adm_pass, admin=True, debe_cambiar=False)


def verificar_login(usuario: str, password: str):
    """Devuelve (ok, mensaje, debe_cambiar)."""
    with obtener_conexion() as conn:
        fila = conn.execute("SELECT * FROM usuarios WHERE usuario=?",
                           ((usuario or "").strip(),)).fetchone()
    if fila is None:
        return False, "Usuario o contraseña incorrectos.", False
    salt = binascii.unhexlify(fila["salt"])
    _, hash_calc = _hash_password(password, salt)
    if hash_calc != fila["password_hash"]:
        return False, "Usuario o contraseña incorrectos.", False
    debe = bool(fila["debe_cambiar"]) if "debe_cambiar" in fila.keys() else False
    return True, "Acceso correcto.", debe


def cambiar_credenciales(usuario_actual: str, nuevo_usuario: str, nueva_password: str):
    """Cambio FORZADO del primer ingreso: usuario Y contraseña. (ok, msg, usuario_final)."""
    nuevo_usuario = (nuevo_usuario or "").strip()
    if len(nuevo_usuario) < 3:
        return False, "El usuario debe tener al menos 3 caracteres.", usuario_actual
    if len(nueva_password or "") < 4:
        return False, "La contraseña debe tener al menos 4 caracteres.", usuario_actual
    if nuevo_usuario != usuario_actual and usuario_existe(nuevo_usuario):
        return False, "Ese nombre de usuario ya está en uso.", usuario_actual
    salt_hex, hash_hex = _hash_password(nueva_password)
    with obtener_conexion() as conn:
        conn.execute(
            "UPDATE usuarios SET usuario=?, password_hash=?, salt=?, debe_cambiar=0 "
            "WHERE usuario=?",
            (nuevo_usuario, hash_hex, salt_hex, usuario_actual))
    return True, "Datos actualizados. Usa tus nuevos datos para entrar.", nuevo_usuario


def cambiar_password(usuario: str, nueva_password: str):
    """Cambia solo la contraseña de un usuario. (ok, mensaje)."""
    if len(nueva_password or "") < 4:
        return False, "La contraseña debe tener al menos 4 caracteres."
    if not usuario_existe(usuario):
        return False, "No existe ese usuario."
    salt_hex, hash_hex = _hash_password(nueva_password)
    with obtener_conexion() as conn:
        conn.execute("UPDATE usuarios SET password_hash=?, salt=?, debe_cambiar=0 "
                     "WHERE usuario=?", (hash_hex, salt_hex, (usuario or "").strip()))
    return True, "Contraseña actualizada."


def recuperar_con_codigo(usuario: str, codigo: str, nueva_password: str):
    """Recuperación con el CÓDIGO FIJO (definido en local_secrets). (ok, mensaje)."""
    codigo_ok = getattr(settings, "CODIGO_RECUPERACION", "") or ""
    if not codigo_ok:
        return False, "La recuperación no está disponible en esta instalación."
    if (codigo or "").strip() != codigo_ok:
        return False, "Código de recuperación incorrecto."
    if not usuario_existe(usuario):
        return False, "No existe ese usuario."
    return cambiar_password(usuario, nueva_password)
