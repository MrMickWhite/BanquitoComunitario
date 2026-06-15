"""Vista de Préstamos: otorgar, consultar deuda y registrar pagos (con fecha)."""

from datetime import date
import tkinter.messagebox as mb
import customtkinter as ctk
from ui import theme as T
from ui.components.cards import Panel, campo, boton
from ui.components.tabla import Tabla
from ui.components.selector_fecha import SelectorFecha
from config import settings
from services import prestamo_service, socio_service, config_service
from repositories import prestamo_repository


def _dinero(v):
    return f"{settings.SIMBOLO_MONEDA}{v:,.2f}"


class PrestamosView(ctk.CTkFrame):
    def __init__(self, master, app):
        super().__init__(master, fg_color="transparent")
        self.app = app
        self._socios = []
        self._construir()
        self.refrescar_socios()

    def _combo(self, master, etiqueta, valores, ancho=200):
        cont = ctk.CTkFrame(master, fg_color="transparent")
        ctk.CTkLabel(cont, text=etiqueta, font=T.FONT_LABEL,
                     text_color=T.TEXT_MUTED).pack(anchor="w", pady=(0, 3))
        combo = ctk.CTkComboBox(cont, values=valores, width=ancho, height=36,
                                corner_radius=T.RADIUS_SM, fg_color=T.BG_PANEL_2,
                                border_color=T.BORDER, button_color=T.ACCENT,
                                button_hover_color=T.ACCENT_HOVER)
        combo.pack()
        return cont, combo

    def _construir(self):
        # --- Otorgar ---
        form = Panel(self, "Otorgar préstamo")
        form.pack(fill="x")
        fila = ctk.CTkFrame(form, fg_color="transparent")
        fila.pack(fill="x", padx=18, pady=(0, 14))
        c1, self.combo_socio = self._combo(fila, "Socio", ["—"], 220)
        c2, self.e_monto = campo(fila, "Monto", 110)
        c3, self.e_plazo = campo(fila, "Plazo (meses)", 100, "3")
        self.selector_fecha = SelectorFecha(fila, "Fecha")
        for i, c in enumerate((c1, c2, c3)):
            c.grid(row=0, column=i, padx=(0, 12), pady=4, sticky="w")
        self.selector_fecha.grid(row=0, column=3, padx=(0, 12), pady=4, sticky="w")
        boton(fila, "🏦  Otorgar", self._otorgar, color=T.ACCENT, hover=T.ACCENT_HOVER,
              ancho=140).grid(row=0, column=4, padx=(6, 0), pady=(18, 0))

        # Interés sí/no + tasa individual del préstamo
        fila_int = ctk.CTkFrame(form, fg_color="transparent")
        fila_int.pack(fill="x", padx=18, pady=(0, 10))
        self.sw_interes = ctk.CTkSwitch(
            fila_int, text="¿Cobra interés?", command=self._toggle_interes,
            progress_color=T.ACCENT, font=T.FONT_LABEL, text_color=T.TEXT)
        self.sw_interes.select()  # por defecto SÍ cobra interés
        self.sw_interes.grid(row=0, column=0, padx=(0, 16), pady=(4, 0), sticky="w")
        self.cont_tasa, self.e_tasa = campo(fila_int, "Tasa mensual % (vacío = general)", 220)
        self.cont_tasa.grid(row=0, column=1, sticky="w")
        self.lbl_int_info = ctk.CTkLabel(fila_int, text="", font=T.FONT_SMALL,
                                         text_color=T.TEXT_DIM)
        self.lbl_int_info.grid(row=0, column=2, padx=(16, 0), pady=(4, 0), sticky="w")
        self._toggle_interes()

        # --- Tabla ---
        panel = Panel(self, "Préstamos")
        panel.pack(fill="both", expand=True, pady=(14, 0))
        self.tabla = Tabla(panel, columnas=("ID", "Socio", "Monto", "Saldo",
                                            "Tasa", "Estado", "Otorgado", "Próx. pago"),
                           anchos=(35, 160, 90, 90, 55, 80, 100, 100), altura=9)
        self.tabla.pack(fill="both", expand=True, padx=14, pady=(0, 8))

        # --- Acciones sobre el préstamo seleccionado (corregir errores) ---
        acc = ctk.CTkFrame(panel, fg_color="transparent")
        acc.pack(fill="x", padx=14, pady=(0, 6))
        boton(acc, "↩ Deshacer último pago", self._deshacer_pago,
              color=T.WARNING, hover="#d97706", ancho=200).pack(side="left")
        boton(acc, "🗑 Eliminar préstamo", self._eliminar_prestamo,
              color=T.DANGER, hover=T.DANGER_HOVER, ancho=180,
              text_color=T.TEXT_LIGHT).pack(side="left", padx=(10, 0))

        # --- Pagos ---
        pago = ctk.CTkFrame(panel, fg_color=T.BG_PANEL_2, corner_radius=T.RADIUS_SM)
        pago.pack(fill="x", padx=14, pady=(0, 14))
        cont = ctk.CTkFrame(pago, fg_color="transparent")
        cont.pack(fill="x", padx=12, pady=12)
        c5, self.e_pago = campo(cont, "Monto del pago", 120)
        self.selector_pago = SelectorFecha(cont, "Fecha del pago")
        c5.grid(row=0, column=0, padx=(0, 12)); self.selector_pago.grid(row=0, column=1, padx=(0, 12))
        boton(cont, "🔎 Ver deuda", self._ver_deuda, color=T.BG_PANEL,
              hover=T.BG_HOVER, ancho=130, text_color=T.TEXT).grid(
            row=0, column=2, padx=6, pady=(18, 0))
        boton(cont, "✅ Registrar pago", self._pagar, color=T.SUCCESS,
              hover=T.SUCCESS_HOVER, ancho=160).grid(row=0, column=3, padx=6, pady=(18, 0))

    def refrescar_socios(self):
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
        general = config_service.obtener_float("TASA_INTERES_PRESTAMO_MENSUAL") * 100
        if self.sw_interes.get():
            self.cont_tasa.grid()
            self.lbl_int_info.configure(text=f"Vacío = tasa general: {general:g}%/mes")
        else:
            self.cont_tasa.grid_remove()
            self.lbl_int_info.configure(text="Este préstamo NO cobrará interés (0%).")

    def _otorgar(self):
        sid = self._socio_id()
        if sid is None:
            return mb.showwarning("Atención", "Selecciona un socio.")
        try:
            monto = float(self.e_monto.get())
            plazo = int(self.e_plazo.get())
            if not self.sw_interes.get():
                tasa = 0.0
            elif self.e_tasa.get().strip():
                tasa = float(self.e_tasa.get()) / 100.0
            else:
                tasa = None  # usa la general en el servicio
            prestamo_service.otorgar_prestamo(sid, monto, plazo, tasa_mensual=tasa,
                                              fecha=self.selector_fecha.get())
            self.e_monto.delete(0, "end")
            self.e_tasa.delete(0, "end")
            self.refrescar_tabla()
            self.app.actualizar_saldo()
            mb.showinfo("Listo", "Préstamo otorgado.")
        except Exception as ex:
            mb.showerror("Error", str(ex))

    def _ver_deuda(self):
        pid = self.tabla.id_seleccionado()
        if not pid:
            return mb.showwarning("Atención", "Selecciona un préstamo en la tabla.")
        d = prestamo_service.calcular_deuda_actual(int(pid), self.selector_pago.get())
        mb.showinfo("Deuda actual",
                    f"Capital:  {_dinero(d['capital'])}\n"
                    f"Interés:  {_dinero(d['interes'])}\n"
                    f"Mora:     {_dinero(d['mora'])}\n"
                    f"────────────────\nTOTAL:   {_dinero(d['total'])}")

    def _pagar(self):
        pid = self.tabla.id_seleccionado()
        if not pid:
            return mb.showwarning("Atención", "Selecciona un préstamo en la tabla.")
        try:
            monto = float(self.e_pago.get())
            r = prestamo_service.registrar_pago(int(pid), monto, self.selector_pago.get())
            self.e_pago.delete(0, "end")
            self.refrescar_tabla()
            self.app.actualizar_saldo()
            mb.showinfo("Pago registrado",
                        f"Mora: {_dinero(r['mora'])}  |  Interés: {_dinero(r['interes'])}  |  "
                        f"Capital: {_dinero(r['capital'])}\n"
                        f"Saldo restante: {_dinero(r['saldo_restante'])}  ({r['estado']})")
        except Exception as ex:
            mb.showerror("Error", str(ex))

    def _deshacer_pago(self):
        pid = self.tabla.id_seleccionado()
        if not pid:
            return mb.showwarning("Atención", "Selecciona un préstamo en la tabla.")
        if not mb.askyesno("Confirmar", "¿Deshacer el último pago de este préstamo?"):
            return
        try:
            r = prestamo_service.deshacer_ultimo_pago(int(pid))
            self.refrescar_tabla()
            self.app.actualizar_saldo()
            mb.showinfo("Pago deshecho",
                        f"Se revirtió un pago de {_dinero(r['monto_pago'])}.\n"
                        f"Capital devuelto al saldo: {_dinero(r['capital_devuelto'])}\n"
                        f"Saldo actual del préstamo: {_dinero(r['saldo_actual'])}")
        except ValueError as ex:
            mb.showerror("Error", str(ex))

    def _eliminar_prestamo(self):
        pid = self.tabla.id_seleccionado()
        if not pid:
            return mb.showwarning("Atención", "Selecciona un préstamo en la tabla.")
        if mb.askyesno("Confirmar",
                       "Esto eliminará el préstamo y TODOS sus pagos.\n"
                       "El saldo de caja se recalculará. ¿Continuar?"):
            prestamo_service.eliminar_prestamo(int(pid))
            self.refrescar_tabla()
            self.app.actualizar_saldo()

    def refrescar_tabla(self):
        nombres = {s.id: s.nombre_completo for s in socio_service.listar_socios()}
        filas = []
        for p in prestamo_repository.listar_prestamos():
            filas.append((p.id, nombres.get(p.socio_id, "?"), _dinero(p.monto),
                          _dinero(p.saldo_capital), f"{p.tasa_mensual*100:.1f}%",
                          p.estado, p.fecha_otorgado, p.fecha_vencimiento or "—"))
        self.tabla.cargar(filas)
