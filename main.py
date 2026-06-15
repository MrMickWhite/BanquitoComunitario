"""
Punto de entrada del programa.

Ejecuta:  python main.py

1) Inicializa la base de datos (crea las tablas si no existen).
2) Muestra la ventana de LOGIN. Si el acceso es correcto, abre la app.
"""

import customtkinter as ctk
from database.connection import inicializar_base_de_datos
from services import config_service, licencia_service
from ui.setup import SetupWindow
from ui.login import LoginWindow
from ui.precios import PreciosWindow
from ui.app import App


def _licencia_bloqueo():
    """Antes del login: si está bloqueado/manipulado, exige activar.
    Devuelve True si se puede continuar; False si hay que cerrar."""
    info = licencia_service.estado_licencia()
    if info["estado"] in ("bloqueado", "manipulado"):
        win = PreciosWindow(bloqueo=True, info=info)
        win.mainloop()
        if getattr(win, "activado", False):
            return licencia_service.puede_entrar()
        return False
    return True


def _aviso_licencia():
    """Después del login (al entrar): muestra la propaganda/aviso cuando el
    usuario está en versión de PRUEBA o cuando la licencia está por vencer
    (15 días o menos). Es informativo: se puede cerrar y seguir usando."""
    info = licencia_service.estado_licencia()
    if info["estado"] in ("prueba", "por_vencer"):
        win = PreciosWindow(bloqueo=False, info=info)
        win.mainloop()


def main():
    inicializar_base_de_datos()
    ctk.set_appearance_mode(config_service.obtener("APARIENCIA") or "dark")

    # 1) Primera vez: pedir el nombre del banco/entidad
    if config_service.obtener("BANCO_CONFIGURADO") != "1":
        setup = SetupWindow()
        setup.mainloop()
        if not getattr(setup, "guardado", False):
            return  # cerró sin configurar

    # 2) Si la licencia está vencida/bloqueada, exigir activación antes de entrar
    if not _licencia_bloqueo():
        return

    # 3) Login
    login = LoginWindow()
    login.mainloop()
    if not getattr(login, "exito", False):
        return

    # 4) Ya dentro: mostrar el aviso/propaganda si está en prueba o por vencer
    _aviso_licencia()

    # 5) Abrir la aplicación
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
