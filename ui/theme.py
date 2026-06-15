"""
Tema visual central de la aplicación.

👉 ESTE ES EL ÚNICO ARCHIVO QUE DEBES EDITAR PARA CAMBIAR LOS COLORES.

Cada color de FONDO/TEXTO es un par  (claro, oscuro):  CustomTkinter elige
automáticamente según el modo activo. Los ACENTOS (amarillos) son un solo
valor porque se ven bien en ambos modos.

Paleta: BLANCOS, AMARILLOS y GRISES OSCUROS.
"""

import customtkinter as ctk

# =====================================================================
#  FONDOS            (claro,      oscuro)
# =====================================================================
BG_APP      = ("#f4f4f5", "#1c1c1e")   # fondo general
BG_SIDEBAR  = ("#e9e9ec", "#161618")   # barra lateral
BG_PANEL    = ("#ffffff", "#262629")   # tarjetas y paneles
BG_PANEL_2  = ("#eef0f2", "#2f2f33")   # inputs / paneles secundarios
BG_HOVER    = ("#e2e2e6", "#3a3a3f")   # hover
ROW_ALT     = ("#f3f4f6", "#1f1f22")   # fila alterna de las tablas (zebra)

# =====================================================================
#  ACENTOS (amarillos) — un solo valor para ambos modos
# =====================================================================
ACCENT       = "#f5c518"   # amarillo principal
ACCENT_HOVER = "#d4a510"
SUCCESS      = "#f5c518"
SUCCESS_HOVER= "#d4a510"
WARNING      = "#eab308"
DANGER       = "#a16207"   # ámbar oscuro (eliminar)
DANGER_HOVER = "#854d0e"
INFO         = ("#52525b", "#e8e8ea")  # gris (acento neutro)
PURPLE       = "#eab308"

# =====================================================================
#  TEXTO             (claro,      oscuro)
# =====================================================================
TEXT        = ("#1c1c1e", "#f5f5f5")   # texto principal
TEXT_MUTED  = ("#52525b", "#a1a1aa")   # etiquetas / subtítulos
TEXT_DIM    = ("#71717a", "#6b7280")   # notas tenues
BORDER      = ("#d4d4d8", "#3a3a3f")   # bordes

TEXT_ON_ACCENT = "#1c1c1e"   # texto OSCURO sobre botones amarillos
TEXT_LIGHT     = "#f5f5f5"   # texto CLARO sobre botones oscuros (ej. eliminar)

# =====================================================================
#  TIPOGRAFÍAS
# =====================================================================
FONT_FAMILY = "Segoe UI"
FONT_TITLE  = (FONT_FAMILY, 22, "bold")
FONT_H1     = (FONT_FAMILY, 18, "bold")
FONT_H2     = (FONT_FAMILY, 14, "bold")
FONT_BODY   = (FONT_FAMILY, 12)
FONT_SMALL  = (FONT_FAMILY, 11)
FONT_STAT   = (FONT_FAMILY, 26, "bold")
FONT_LABEL  = (FONT_FAMILY, 11, "bold")

RADIUS = 14
RADIUS_SM = 10


def pick(color):
    """
    Resuelve un par (claro, oscuro) al color de un solo valor según el modo
    actual. Útil para ttk (la tabla), que no entiende los pares de CustomTkinter.
    """
    if isinstance(color, (tuple, list)):
        return color[0] if ctk.get_appearance_mode() == "Light" else color[1]
    return color
