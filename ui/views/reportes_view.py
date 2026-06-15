"""
Vista de Reportes.

Estructura solicitada:
  • Reporte GENERAL del banquito  -> ANUAL.
  • Reporte por SOCIO             -> MENSUAL y ANUAL.
"""

import os
import sys
import subprocess
from datetime import date
import tkinter.messagebox as mb
import customtkinter as ctk
from ui import theme as T
from ui.components.cards import Panel, campo, boton
from ui.components.selector_fecha import SelectorFecha
from services import reporte_service, socio_service
from reports import pdf_generator
from utils.fechas import NOMBRES_MESES


class ReportesView(ctk.CTkFrame):
    def __init__(self, master, app):
        super().__init__(master, fg_color="transparent")
        self.app = app
        self._socios = []
        self._construir()
        self.refrescar_socios()

    def _combo(self, master, etiqueta, valores, ancho=160, command=None):
        cont = ctk.CTkFrame(master, fg_color="transparent")
        ctk.CTkLabel(cont, text=etiqueta, font=T.FONT_LABEL,
                     text_color=T.TEXT_MUTED).pack(anchor="w", pady=(0, 3))
        combo = ctk.CTkComboBox(cont, values=valores, width=ancho, height=36,
                                corner_radius=T.RADIUS_SM, fg_color=T.BG_PANEL_2,
                                border_color=T.BORDER, button_color=T.ACCENT,
                                button_hover_color=T.ACCENT_HOVER, command=command)
        combo.pack()
        return cont, combo

    def _construir(self):
        # ---------------- General: semanal / mensual / anual ----------------
        gen = Panel(self, "📊  Reporte general del banquito  ·  SEMANAL · MENSUAL · ANUAL")
        gen.pack(fill="x")
        fg = ctk.CTkFrame(gen, fg_color="transparent")
        fg.pack(fill="x", padx=18, pady=(0, 16))
        c0, self.combo_periodo_gen = self._combo(fg, "Periodo",
                                                 ["Semanal", "Mensual", "Anual", "Rango"], 130,
                                                 command=lambda _: self._toggle_periodo_gen())
        c1, self.e_anio_gen = campo(fg, "Año", 90, str(date.today().year))
        c2, self.combo_mes_gen = self._combo(fg, "Mes", NOMBRES_MESES[1:], 140)
        self.selector_semana_gen = SelectorFecha(fg, "Día de la semana")
        self.sel_desde_gen = SelectorFecha(fg, "Desde")
        self.sel_hasta_gen = SelectorFecha(fg, "Hasta")
        self.combo_periodo_gen.set("Anual")
        self.combo_mes_gen.set(NOMBRES_MESES[date.today().month])
        c0.grid(row=0, column=0, padx=(0, 12), sticky="w")
        c1.grid(row=0, column=1, padx=(0, 12), sticky="w")
        c2.grid(row=0, column=2, padx=(0, 12), sticky="w")
        self.selector_semana_gen.grid(row=0, column=2, padx=(0, 12), sticky="w")
        self.sel_desde_gen.grid(row=0, column=2, padx=(0, 12), sticky="w")
        self.sel_hasta_gen.grid(row=0, column=3, padx=(0, 12), sticky="w")
        self._mes_gen_cont = c2
        boton(fg, "📄  Generar PDF", self._reporte_general, ancho=160).grid(
            row=0, column=4, padx=6, pady=(18, 0))
        ctk.CTkLabel(gen, text="Incluye: resumen financiero, detalle de socios, "
                     "ingresos/egresos varios y el detalle por socio, todo con sus "
                     "descripciones.",
                     font=T.FONT_SMALL, text_color=T.TEXT_DIM,
                     wraplength=820, justify="left").pack(anchor="w", padx=18, pady=(0, 14))
        self._toggle_periodo_gen()

        # ---------------- Por socio semanal/mensual/anual ----------------
        soc = Panel(self, "👤  Reporte por socio  ·  SEMANAL · MENSUAL · ANUAL")
        soc.pack(fill="x", pady=(16, 0))
        fs = ctk.CTkFrame(soc, fg_color="transparent")
        fs.pack(fill="x", padx=18, pady=(0, 16))

        c2, self.combo_socio = self._combo(fs, "Socio", ["—"], 220)
        c3, self.combo_periodo = self._combo(fs, "Periodo",
                                             ["Semanal", "Mensual", "Anual", "Rango"], 130,
                                             command=lambda _: self._toggle_periodo())
        c4, self.e_anio_soc = campo(fs, "Año", 90, str(date.today().year))
        c5, self.combo_mes = self._combo(fs, "Mes", NOMBRES_MESES[1:], 140)
        self.selector_semana = SelectorFecha(fs, "Día de la semana")
        self.sel_desde_soc = SelectorFecha(fs, "Desde")
        self.sel_hasta_soc = SelectorFecha(fs, "Hasta")
        self.combo_periodo.set("Mensual")
        self.combo_mes.set(NOMBRES_MESES[date.today().month])
        c2.grid(row=0, column=0, padx=(0, 12), sticky="w")
        c3.grid(row=0, column=1, padx=(0, 12), sticky="w")
        c4.grid(row=0, column=2, padx=(0, 12), sticky="w")
        c5.grid(row=0, column=3, padx=(0, 12), sticky="w")
        self.selector_semana.grid(row=0, column=3, padx=(0, 12), sticky="w")
        self.sel_desde_soc.grid(row=0, column=3, padx=(0, 12), sticky="w")
        self.sel_hasta_soc.grid(row=0, column=4, padx=(0, 12), sticky="w")
        self._mes_cont = c5
        boton(fs, "📄  Generar PDF", self._reporte_socio, color=T.SUCCESS,
              hover=T.SUCCESS_HOVER, ancho=150).grid(
            row=0, column=4, padx=(6, 0), pady=(18, 0))
        self._toggle_periodo()

        self.lbl_estado = ctk.CTkLabel(self, text="", font=T.FONT_SMALL,
                                       text_color=T.SUCCESS, wraplength=820,
                                       justify="left")
        self.lbl_estado.pack(anchor="w", padx=6, pady=(18, 0))

    def _toggle_periodo(self):
        periodo = self.combo_periodo.get()
        self._mes_cont.grid_remove()
        self.selector_semana.grid_remove()
        self.sel_desde_soc.grid_remove()
        self.sel_hasta_soc.grid_remove()
        if periodo == "Mensual":
            self._mes_cont.grid(row=0, column=3, padx=(0, 12), sticky="w")
        elif periodo == "Semanal":
            self.selector_semana.grid(row=0, column=3, padx=(0, 12), sticky="w")
        elif periodo == "Rango":
            self.sel_desde_soc.grid(row=0, column=3, padx=(0, 12), sticky="w")
            self.sel_hasta_soc.grid(row=0, column=4, padx=(0, 12), sticky="w")

    def refrescar_socios(self):
        self._socios = socio_service.listar_socios()
        valores = [s.nombre_completo for s in self._socios] or ["—"]
        self.combo_socio.configure(values=valores)
        self.combo_socio.set(valores[0])

    # ----------------------------------------------------------------- generar
    def _toggle_periodo_gen(self):
        periodo = self.combo_periodo_gen.get()
        self._mes_gen_cont.grid_remove()
        self.selector_semana_gen.grid_remove()
        self.sel_desde_gen.grid_remove()
        self.sel_hasta_gen.grid_remove()
        self.e_anio_gen.master.grid()  # año visible por defecto
        if periodo == "Mensual":
            self._mes_gen_cont.grid(row=0, column=2, padx=(0, 12), sticky="w")
        elif periodo == "Semanal":
            self.selector_semana_gen.grid(row=0, column=2, padx=(0, 12), sticky="w")
        elif periodo == "Rango":
            self.sel_desde_gen.grid(row=0, column=2, padx=(0, 12), sticky="w")
            self.sel_hasta_gen.grid(row=0, column=3, padx=(0, 12), sticky="w")

    def _reporte_general(self):
        try:
            periodo = self.combo_periodo_gen.get()
            if periodo == "Semanal":
                datos = reporte_service.general_semanal(self.selector_semana_gen.get())
            elif periodo == "Mensual":
                anio = int(self.e_anio_gen.get())
                mes = NOMBRES_MESES.index(self.combo_mes_gen.get())
                datos = reporte_service.general_mensual(anio, mes)
            elif periodo == "Rango":
                ini, fin = self.sel_desde_gen.get(), self.sel_hasta_gen.get()
                if ini > fin:
                    return mb.showerror("Error", "La fecha 'Desde' no puede ser mayor que 'Hasta'.")
                datos = reporte_service.reporte_general(ini, fin, f"Del {ini} al {fin}")
            else:
                anio = int(self.e_anio_gen.get())
                datos = reporte_service.general_anual(anio)
            ruta = pdf_generator.generar_reporte_general(datos)
            self._exito(ruta)
        except Exception as ex:
            mb.showerror("Error", str(ex))

    def _reporte_socio(self):
        try:
            valores = list(self.combo_socio.cget("values"))
            if self.combo_socio.get() not in valores or not self._socios:
                return mb.showwarning("Atención", "Selecciona un socio.")
            sid = self._socios[valores.index(self.combo_socio.get())].id
            periodo = self.combo_periodo.get()
            if periodo == "Semanal":
                datos = reporte_service.socio_semanal(sid, self.selector_semana.get())
            elif periodo == "Mensual":
                anio = int(self.e_anio_soc.get())
                mes = NOMBRES_MESES.index(self.combo_mes.get())
                datos = reporte_service.socio_mensual(sid, anio, mes)
            elif periodo == "Rango":
                ini, fin = self.sel_desde_soc.get(), self.sel_hasta_soc.get()
                if ini > fin:
                    return mb.showerror("Error", "La fecha 'Desde' no puede ser mayor que 'Hasta'.")
                datos = reporte_service.reporte_por_socio(sid, ini, fin, f"Del {ini} al {fin}")
            else:
                anio = int(self.e_anio_soc.get())
                datos = reporte_service.socio_anual(sid, anio)
            ruta = pdf_generator.generar_reporte_socio(datos)
            self._exito(ruta)
        except Exception as ex:
            mb.showerror("Error", str(ex))

    def _exito(self, ruta):
        self.lbl_estado.configure(text=f"✅  PDF generado:  {ruta}")
        if mb.askyesno("Reporte generado", f"PDF creado en:\n{ruta}\n\n¿Abrirlo ahora?"):
            self._abrir(ruta)

    @staticmethod
    def _abrir(ruta):
        try:
            if sys.platform.startswith("win"):
                os.startfile(ruta)  # type: ignore[attr-defined]
            elif sys.platform == "darwin":
                subprocess.run(["open", ruta])
            else:
                subprocess.run(["xdg-open", ruta])
        except Exception:
            pass

    def refrescar(self):
        self.refrescar_socios()
