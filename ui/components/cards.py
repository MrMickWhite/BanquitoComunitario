"""Tarjetas reutilizables para el dashboard y paneles con título."""

import customtkinter as ctk
from ui import theme as T


class StatCard(ctk.CTkFrame):
    """Tarjeta de métrica: ícono, valor grande y etiqueta."""

    def __init__(self, master, titulo, valor="—", icono="", color=T.ACCENT, **kwargs):
        super().__init__(master, fg_color=T.BG_PANEL, corner_radius=T.RADIUS,
                         border_width=1, border_color=T.BORDER, **kwargs)

        # franja de color a la izquierda
        franja = ctk.CTkFrame(self, fg_color=color, width=5, corner_radius=T.RADIUS)
        franja.pack(side="left", fill="y", padx=(0, 0), pady=0)

        cont = ctk.CTkFrame(self, fg_color="transparent")
        cont.pack(side="left", fill="both", expand=True, padx=16, pady=14)

        fila = ctk.CTkFrame(cont, fg_color="transparent")
        fila.pack(fill="x")
        ctk.CTkLabel(fila, text=icono, font=(T.FONT_FAMILY, 18),
                     text_color=color).pack(side="left")
        ctk.CTkLabel(fila, text=titulo, font=T.FONT_SMALL,
                     text_color=T.TEXT_MUTED).pack(side="left", padx=8)

        self.lbl_valor = ctk.CTkLabel(cont, text=valor, font=T.FONT_STAT,
                                      text_color=T.TEXT)
        self.lbl_valor.pack(anchor="w", pady=(6, 0))

    def set_valor(self, valor):
        self.lbl_valor.configure(text=valor)


class Panel(ctk.CTkFrame):
    """Panel con título, para agrupar formularios o tablas."""

    def __init__(self, master, titulo="", **kwargs):
        super().__init__(master, fg_color=T.BG_PANEL, corner_radius=T.RADIUS,
                         border_width=1, border_color=T.BORDER, **kwargs)
        if titulo:
            ctk.CTkLabel(self, text=titulo, font=T.FONT_H2,
                         text_color=T.TEXT).pack(anchor="w", padx=18, pady=(14, 4))


def campo(master, etiqueta, ancho=200, valor_inicial=""):
    """Crea un campo etiqueta + entry con estilo. Devuelve (contenedor, entry)."""
    cont = ctk.CTkFrame(master, fg_color="transparent")
    ctk.CTkLabel(cont, text=etiqueta, font=T.FONT_LABEL,
                 text_color=T.TEXT_MUTED).pack(anchor="w", pady=(0, 3))
    entry = ctk.CTkEntry(cont, width=ancho, height=36, corner_radius=T.RADIUS_SM,
                         fg_color=T.BG_PANEL_2, border_color=T.BORDER,
                         text_color=T.TEXT)
    if valor_inicial:
        entry.insert(0, valor_inicial)
    entry.pack()
    return cont, entry


def boton(master, texto, comando, color=T.ACCENT, hover=T.ACCENT_HOVER,
          ancho=160, text_color=T.TEXT_ON_ACCENT):
    return ctk.CTkButton(master, text=texto, command=comando, width=ancho, height=38,
                         corner_radius=T.RADIUS_SM, fg_color=color, hover_color=hover,
                         font=T.FONT_LABEL, text_color=text_color)
