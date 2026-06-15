"""Vista de Movimientos: registrar ingresos / egresos varios de la caja."""

import tkinter.messagebox as mb
import customtkinter as ctk
from ui import theme as T
from ui.components.cards import Panel, campo, boton
from ui.components.tabla import Tabla
from ui.components.selector_fecha import SelectorFecha
from config import settings
from services import movimiento_service, config_service


def _dinero(v):
    return f"{settings.SIMBOLO_MONEDA}{v:,.2f}"


class MovimientosView(ctk.CTkFrame):
    def __init__(self, master, app):
        super().__init__(master, fg_color="transparent")
        self.app = app
        self._construir()
        self.refrescar()

    def _construir(self):
        form = Panel(self, "Registrar ingreso / egreso vario")
        form.pack(fill="x")
        fila = ctk.CTkFrame(form, fg_color="transparent")
        fila.pack(fill="x", padx=18, pady=(0, 8))

        # Tipo (ingreso/egreso)
        cont_tipo = ctk.CTkFrame(fila, fg_color="transparent")
        ctk.CTkLabel(cont_tipo, text="Tipo", font=T.FONT_LABEL,
                     text_color=T.TEXT_MUTED).pack(anchor="w", pady=(0, 3))
        self.seg_tipo = ctk.CTkSegmentedButton(
            cont_tipo, values=["Ingreso", "Egreso"],
            selected_color=T.ACCENT, selected_hover_color=T.ACCENT_HOVER,
            unselected_color=T.BG_PANEL_2, unselected_hover_color=T.BG_HOVER,
            text_color=T.TEXT, fg_color=T.BG_PANEL_2, height=36)
        self.seg_tipo.set("Ingreso")
        self.seg_tipo.pack()

        c_monto, self.e_monto = campo(fila, "Monto", 120)
        self.selector_fecha = SelectorFecha(fila, "Fecha")
        c_desc, self.e_desc = campo(fila, "Descripción", 200)

        cont_tipo.grid(row=0, column=0, padx=(0, 14), sticky="w")
        c_monto.grid(row=0, column=1, padx=(0, 14), sticky="w")
        self.selector_fecha.grid(row=0, column=2, padx=(0, 14), sticky="w")
        c_desc.grid(row=0, column=3, padx=(0, 14), sticky="w")
        boton(fila, "➕  Registrar", self._registrar, ancho=140).grid(
            row=0, column=4, padx=(6, 0), pady=(18, 0))

        # --- Fila de interés (sí/no + tasa individual) ---
        fila2 = ctk.CTkFrame(form, fg_color="transparent")
        fila2.pack(fill="x", padx=18, pady=(0, 14))
        self.sw_interes = ctk.CTkSwitch(
            fila2, text="¿Genera interés?", command=self._toggle_interes,
            progress_color=T.ACCENT, font=T.FONT_LABEL, text_color=T.TEXT)
        self.sw_interes.grid(row=0, column=0, padx=(0, 16), pady=(6, 0), sticky="w")
        self.cont_tasa, self.e_tasa = campo(fila2, "Tasa mensual % (vacío = general)", 220)
        self.cont_tasa.grid(row=0, column=1, sticky="w")
        self.cont_tasa.grid_remove()  # oculto hasta activar el switch
        self.lbl_interes_info = ctk.CTkLabel(
            fila2, text="", font=T.FONT_SMALL, text_color=T.TEXT_DIM)
        self.lbl_interes_info.grid(row=0, column=2, padx=(16, 0), pady=(6, 0), sticky="w")
        self._toggle_interes()

        panel = Panel(self, "Movimientos varios recientes")
        panel.pack(fill="both", expand=True, pady=(14, 0))
        self.tabla = Tabla(panel, columnas=("ID", "Fecha", "Tipo", "Monto",
                                            "Interés", "Descripción"),
                           anchos=(40, 110, 90, 110, 170, 250), altura=12)
        self.tabla.pack(fill="both", expand=True, padx=14, pady=(0, 8))
        boton(panel, "🗑 Eliminar seleccionado", self._eliminar, color=T.DANGER,
              hover=T.DANGER_HOVER, ancho=190, text_color=T.TEXT_LIGHT).pack(
            anchor="w", padx=14, pady=(0, 14))

    def _toggle_interes(self):
        if self.sw_interes.get():
            self.cont_tasa.grid()
            general = config_service.obtener_float("TASA_INTERES_PRESTAMO_MENSUAL") * 100
            self.lbl_interes_info.configure(
                text=f"Si dejas la tasa vacía se usa la general: {general:g}%/mes")
        else:
            self.cont_tasa.grid_remove()
            self.lbl_interes_info.configure(text="")

    def _registrar(self):
        try:
            tipo = "ingreso" if self.seg_tipo.get() == "Ingreso" else "egreso"
            monto = float(self.e_monto.get())
            genera = bool(self.sw_interes.get())
            tasa = None
            if genera and self.e_tasa.get().strip():
                tasa = float(self.e_tasa.get()) / 100.0  # % -> fracción
            movimiento_service.registrar_vario(
                tipo, monto, self.selector_fecha.get(), self.e_desc.get(),
                genera_interes=genera, tasa_interes=tasa)
            self.e_monto.delete(0, "end")
            self.e_desc.delete(0, "end")
            self.e_tasa.delete(0, "end")
            self.sw_interes.deselect()
            self._toggle_interes()
            self.refrescar()
            self.app.actualizar_saldo()
            mb.showinfo("Listo", "Movimiento registrado.")
        except ValueError as ex:
            mb.showerror("Error", str(ex) if str(ex) else "Monto o tasa inválidos.")

    def _eliminar(self):
        mid = self.tabla.id_seleccionado()
        if not mid:
            return mb.showwarning("Atención", "Selecciona un movimiento.")
        if mb.askyesno("Confirmar", "¿Eliminar este movimiento de la caja?"):
            movimiento_service.eliminar_vario(int(mid))
            self.refrescar()
            self.app.actualizar_saldo()

    def refrescar(self):
        filas = []
        for m in movimiento_service.listar_varios():
            etiqueta = "Ingreso" if m.tipo == "ingreso" else "Egreso"
            signo = "+" if m.tipo == "ingreso" else "−"
            info = movimiento_service.interes_de_movimiento(m)
            if info["activo"]:
                interes_txt = (f"{info['tasa']*100:g}%/mes ({info['origen']}) "
                               f"→ {_dinero(info['interes'])}")
            else:
                interes_txt = "—"
            filas.append((m.id, m.fecha, etiqueta, f"{signo} {_dinero(m.monto)}",
                          interes_txt, m.descripcion or ""))
        self.tabla.cargar(filas)
