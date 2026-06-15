"""
Selector de fecha con desplegables (día / mes / año), para no tener que escribir.

Rango de años: del 2025 hasta 2025 + 10 (configurable). Devuelve la fecha en
formato ISO 'YYYY-MM-DD' con get(). Ajusta automáticamente los días válidos
según el mes y el año (ej: febrero, años bisiestos).
"""

import calendar
from datetime import date
import customtkinter as ctk
from ui import theme as T

ANIO_INICIO = 2025
ANIOS = 10  # 2025 .. 2035
MESES = ["Ene", "Feb", "Mar", "Abr", "May", "Jun",
         "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]


class SelectorFecha(ctk.CTkFrame):
    def __init__(self, master, etiqueta="Fecha", valor=None, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        if valor is None:
            valor = date.today()
        elif isinstance(valor, str):
            valor = date.fromisoformat(valor)

        if etiqueta:
            ctk.CTkLabel(self, text=etiqueta, font=T.FONT_LABEL,
                         text_color=T.TEXT_MUTED).pack(anchor="w", pady=(0, 3))

        fila = ctk.CTkFrame(self, fg_color="transparent")
        fila.pack(anchor="w")

        anios = [str(ANIO_INICIO + i) for i in range(ANIOS + 1)]
        self.cb_dia = self._combo(fila, [f"{d:02d}" for d in range(1, 32)], 70)
        self.cb_mes = self._combo(fila, MESES, 80, command=self._ajustar_dias)
        self.cb_anio = self._combo(fila, anios, 90, command=self._ajustar_dias)
        self.cb_dia.pack(side="left", padx=(0, 6))
        self.cb_mes.pack(side="left", padx=(0, 6))
        self.cb_anio.pack(side="left")

        # Valor inicial (acotado al rango de años disponible)
        anio = min(max(valor.year, ANIO_INICIO), ANIO_INICIO + ANIOS)
        self.cb_anio.set(str(anio))
        self.cb_mes.set(MESES[valor.month - 1])
        self._ajustar_dias()
        self.cb_dia.set(f"{valor.day:02d}")

    def _combo(self, master, valores, ancho, command=None):
        return ctk.CTkComboBox(master, values=valores, width=ancho, height=36,
                               corner_radius=T.RADIUS_SM, fg_color=T.BG_PANEL_2,
                               border_color=T.BORDER, button_color=T.ACCENT,
                               button_hover_color=T.ACCENT_HOVER, state="readonly",
                               command=command)

    def _ajustar_dias(self, _=None):
        mes = MESES.index(self.cb_mes.get()) + 1
        anio = int(self.cb_anio.get())
        ultimo = calendar.monthrange(anio, mes)[1]
        valores = [f"{d:02d}" for d in range(1, ultimo + 1)]
        actual = self.cb_dia.get()
        self.cb_dia.configure(values=valores)
        if actual not in valores:
            self.cb_dia.set(valores[-1])  # ej: si estaba en 31 y el mes tiene 30

    def get(self) -> str:
        """Devuelve la fecha seleccionada como 'YYYY-MM-DD'."""
        dia = int(self.cb_dia.get())
        mes = MESES.index(self.cb_mes.get()) + 1
        anio = int(self.cb_anio.get())
        return date(anio, mes, dia).isoformat()

    def set(self, valor):
        if isinstance(valor, str):
            valor = date.fromisoformat(valor)
        self.cb_anio.set(str(min(max(valor.year, ANIO_INICIO), ANIO_INICIO + ANIOS)))
        self.cb_mes.set(MESES[valor.month - 1])
        self._ajustar_dias()
        self.cb_dia.set(f"{valor.day:02d}")
