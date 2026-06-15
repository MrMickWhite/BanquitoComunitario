"""
Rutas de salida de los reportes.

Los PDF NO se guardan dentro de las carpetas del programa: se crea una carpeta
en el ESCRITORIO del usuario llamada "Reportes <Nombre del banco>" y ahí se
guardan todos los reportes. Si el equipo no tiene carpeta de escritorio
(idiomas/instalaciones raras), se usa la carpeta personal del usuario.
"""

from pathlib import Path
from services import config_service


def obtener_escritorio() -> Path:
    """Devuelve la carpeta Escritorio del usuario (multi-idioma y multi-SO)."""
    home = Path.home()

    # Windows: intentar leer la ruta real del registro (soporta OneDrive)
    try:
        import winreg  # solo existe en Windows
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders",
        ) as k:
            valor, _ = winreg.QueryValueEx(k, "Desktop")
            p = Path(str(valor).replace("%USERPROFILE%", str(home)))
            if p.is_dir():
                return p
    except Exception:
        pass

    # Linux / macOS / Windows estándar
    for nombre in ("Desktop", "Escritorio", "Área de Trabalho", "Bureau"):
        p = home / nombre
        if p.is_dir():
            return p
    return home  # último recurso: carpeta personal


def carpeta_reportes() -> Path:
    """Crea (si no existe) y devuelve la carpeta de reportes en el escritorio.
    Usa el nombre configurado en NOMBRE_CARPETA_REPORTES; si está vacío, usa
    'Reportes <Nombre del banco>'."""
    personalizado = (config_service.obtener("NOMBRE_CARPETA_REPORTES") or "").strip()
    if personalizado:
        nombre = personalizado
    else:
        nombre_banco = config_service.obtener("NOMBRE_BANCO") or "MMWBank"
        nombre = f"Reportes {nombre_banco}"
    carpeta = obtener_escritorio() / nombre
    carpeta.mkdir(parents=True, exist_ok=True)
    return carpeta


def aplicar_icono(ventana):
    """Pone el icono de la app a una ventana Tk de la forma más confiable."""
    from config import settings
    # 1) iconbitmap (.ico) para la barra de título en Windows
    try:
        if settings.ICONO_ICO.exists():
            ventana.iconbitmap(default=str(settings.ICONO_ICO))
    except Exception:
        pass
    # 2) iconphoto con el PNG: es lo que mejor funciona para la barra de tareas
    #    (Tkinter no siempre dibuja los .ico con PNG embebido).
    try:
        import tkinter as tk
        if settings.LOGO_PNG.exists():
            img = tk.PhotoImage(file=str(settings.LOGO_PNG))
            ventana.iconphoto(True, img)
            ventana._icono_ref = img  # mantener referencia para que no se borre
    except Exception:
        pass


def cargar_logo(size=(72, 72)):
    """Devuelve un CTkImage con el logo de la app (o None si no se puede)."""
    try:
        import customtkinter as ctk
        from PIL import Image
        from config import settings
        if settings.LOGO_PNG.exists():
            img = Image.open(settings.LOGO_PNG).convert("RGBA")
            return ctk.CTkImage(light_image=img, dark_image=img, size=size)
    except Exception:
        pass
    return None
