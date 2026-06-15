"""Vista de Aportes: registrar aportes (con fecha) y ver el historial del socio."""

from datetime import date
import tkinter.messagebox as mb
import customtkinter as ctk
from ui import theme as T
from ui.components.cards import Panel, campo, boton
from ui.components.tabla import Tabla
from ui.components.selector_fecha import SelectorFecha
from config import settings
from services import aporte_service, socio_service, movimiento_service
from repositories import aporte_repository


def _dinero(v):
    return f"{settings.SIMBOLO_MONEDA}{v:,.2f}"


class AportesView(ctk.CTkFrame):
    def __init__(self, master, app):
        super().__init__(master, fg_color="transparent")
        self.app = app
        self._socios = []
        self._construir()
        self.refrescar_socios()

    def _combo(self, master, etiqueta, valores, ancho=220, command=None):
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
        form = Panel(self, "Registrar aporte")
        form.pack(fill="x")
        fila = ctk.CTkFrame(form, fg_color="transparent")
        fila.pack(fill="x", padx=18, pady=(0, 14))

        c1, self.combo_socio = self._combo(fila, "Socio", ["—"], 220,
                                           command=lambda _: self.refrescar_tabla())
        c2, self.e_monto = campo(fila, "Monto", 110)
        self.selector_fecha = SelectorFecha(fila, "Fecha")
        c4, self.e_desc = campo(fila, "Descripción", 180)
        c1.grid(row=0, column=0, padx=(0, 12), pady=4, sticky="w")
        c2.grid(row=0, column=1, padx=(0, 12), pady=4, sticky="w")
        self.selector_fecha.grid(row=0, column=2, padx=(0, 12), pady=4, sticky="w")
        c4.grid(row=0, column=3, padx=(0, 12), pady=4, sticky="w")
        boton(fila, "💰  Registrar", self._registrar, color=T.SUCCESS,
              hover=T.SUCCESS_HOVER, ancho=130).grid(
            row=0, column=4, padx=(6, 0), pady=(18, 0))

        # Interés sí/no + tasa individual (igual que en Movimientos)
        fila_int = ctk.CTkFrame(form, fg_color="transparent")
        fila_int.pack(fill="x", padx=18, pady=(0, 8))
        self.sw_interes = ctk.CTkSwitch(
            fila_int, text="¿Genera interés?", command=self._toggle_interes,
            progress_color=T.ACCENT, font=T.FONT_LABEL, text_color=T.TEXT)
        self.sw_interes.grid(row=0, column=0, padx=(0, 16), pady=(4, 0), sticky="w")
        self.cont_tasa, self.e_tasa = campo(fila_int, "Tasa mensual % (vacío = general)", 220)
        self.cont_tasa.grid(row=0, column=1, sticky="w")
        self.cont_tasa.grid_remove()
        self.lbl_int_info = ctk.CTkLabel(fila_int, text="", font=T.FONT_SMALL,
                                         text_color=T.TEXT_DIM)
        self.lbl_int_info.grid(row=0, column=2, padx=(16, 0), pady=(4, 0), sticky="w")
        self._toggle_interes()

        # Pista de recaudación + botón "Registrar recaudación del día"
        barra = ctk.CTkFrame(form, fg_color="transparent")
        barra.pack(fill="x", padx=18, pady=(0, 12))
        self.lbl_recaudacion = ctk.CTkLabel(barra, text="", font=T.FONT_SMALL,
                                            text_color=T.TEXT_MUTED)
        self.lbl_recaudacion.pack(side="left")
        boton(barra, "📅  Registrar recaudación del día", self._recaudacion_dia,
              ancho=250).pack(side="right")

        panel = Panel(self, "Historial de aportes del socio")
        panel.pack(fill="both", expand=True, pady=(14, 0))
        self.tabla = Tabla(panel, columnas=("ID", "Fecha", "Monto", "Tipo", "Descripción"),
                           anchos=(40, 120, 120, 110, 320), altura=12)
        self.tabla.pack(fill="both", expand=True, padx=14, pady=(0, 8))
        boton(panel, "🗑 Eliminar aporte seleccionado", self._eliminar,
              color=T.DANGER, hover=T.DANGER_HOVER, ancho=240,
              text_color=T.TEXT_LIGHT).pack(anchor="w", padx=14, pady=(0, 14))

    def _eliminar(self):
        aid = self.tabla.id_seleccionado()
        if not aid:
            return mb.showwarning("Atención", "Selecciona un aporte de la tabla.")
        if mb.askyesno("Confirmar", "¿Eliminar este aporte? El saldo de caja se "
                                    "recalculará."):
            aporte_service.eliminar_aporte(int(aid))
            self.refrescar_tabla()
            self.app.actualizar_saldo()

    def refrescar_socios(self):
        from services import recaudacion_service
        self.lbl_recaudacion.configure(
            text=f"📅 Próxima recaudación: {recaudacion_service.descripcion()}")
        self._socios = socio_service.listar_socios(solo_activos=True)
        valores = [s.nombre_completo for s in self._socios] or ["—"]
        self.combo_socio.configure(values=valores)
        self.combo_socio.set(valores[0])
        self.refrescar_tabla()

    def _socio_id(self):
        valores = list(self.combo_socio.cget("values"))
        if self.combo_socio.get() in valores and self._socios:
            return self._socios[valores.index(self.combo_socio.get())].id
        return None

    def _toggle_interes(self):
        if self.sw_interes.get():
            self.cont_tasa.grid()
            general = config_service.obtener_float("TASA_INTERES_PRESTAMO_MENSUAL") * 100
            self.lbl_int_info.configure(
                text=f"Vacío = tasa general: {general:g}%/mes")
        else:
            self.cont_tasa.grid_remove()
            self.lbl_int_info.configure(text="")

    def _registrar(self):
        sid = self._socio_id()
        if sid is None:
            return mb.showwarning("Atención", "Agrega y selecciona un socio primero.")
        try:
            monto = float(self.e_monto.get())
            genera = bool(self.sw_interes.get())
            tasa = None
            if genera and self.e_tasa.get().strip():
                tasa = float(self.e_tasa.get()) / 100.0
            aporte_service.registrar_aporte(sid, monto, self.selector_fecha.get(),
                                            descripcion=self.e_desc.get(),
                                            genera_interes=genera, tasa_interes=tasa)
            self.e_monto.delete(0, "end")
            self.e_desc.delete(0, "end")
            self.e_tasa.delete(0, "end")
            self.sw_interes.deselect()
            self._toggle_interes()
            self.refrescar_tabla()
            self.app.actualizar_saldo()
            mb.showinfo("Listo", "Aporte registrado.")
        except ValueError as ex:
            mb.showerror("Error", str(ex))
        except Exception:
            mb.showerror("Error", "Monto inválido. Usa números, ej: 50.00")

    def _recaudacion_dia(self):
        try:
            r = movimiento_service.registrar_recaudacion_del_dia()
        except ValueError as ex:
            return mb.showerror("Recaudación", str(ex))
        self.refrescar_tabla()
        self.app.actualizar_saldo()
        cobrados = "\n".join(f"  • {n}" for n in r["cobrados"]) or "  (ninguno)"
        omitidos = ", ".join(r["omitidos"]) or "ninguno"
        mb.showinfo(
            "Recaudación del día",
            f"Fecha: {r['fecha']}  ·  Cuota: {_dinero(r['cuota'])}\n\n"
            f"Cobrados ({len(r['cobrados'])}):\n{cobrados}\n\n"
            f"Ya habían aportado hoy: {omitidos}")

    def refrescar_tabla(self):
        sid = self._socio_id()
        if sid is None:
            return self.tabla.cargar([])
        filas = [(a.id, a.fecha, _dinero(a.monto), a.tipo, a.descripcion or "")
                 for a in aporte_repository.listar_por_socio(sid)]
        self.tabla.cargar(filas)
