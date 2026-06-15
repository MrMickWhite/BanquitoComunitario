"""
Vista de Cuadre de caja.

Reúne tres herramientas de control del dinero:
  1) Resumen: saldo en sistema, total ingresos y egresos.
  2) Arqueo (cuadre): cuentas el efectivo real y lo comparas con el sistema;
     si hay diferencia, registras un ajuste para que cuadren.
  3) Caja chica: fondo fijo para gastos pequeños, con su disponible.
"""

import tkinter.messagebox as mb
import customtkinter as ctk
from ui import theme as T
from ui.components.cards import StatCard, Panel, campo, boton
from ui.components.tabla import Tabla
from ui.components.selector_fecha import SelectorFecha
from config import settings
from services import movimiento_service, config_service

# Etiquetas legibles para el desglose por categoría
_CATS = {
    "aporte_ingreso": "Aportes",
    "pago_capital_ingreso": "Capital recuperado",
    "interes_ingreso": "Intereses",
    "mora_ingreso": "Mora",
    "ingreso_vario_ingreso": "Ingresos varios",
    "prestamo_egreso": "Préstamos otorgados",
    "egreso_vario_egreso": "Egresos varios",
    "gasto_egreso": "Gastos",
}


def _dinero(v):
    return f"{settings.SIMBOLO_MONEDA}{v:,.2f}"


class CuadreCajaView(ctk.CTkFrame):
    def __init__(self, master, app):
        super().__init__(master, fg_color="transparent")
        self.app = app
        self._construir()
        self.refrescar()

    def _construir(self):
        # --- Tarjetas de resumen ---
        tarjetas = ctk.CTkFrame(self, fg_color="transparent")
        tarjetas.pack(fill="x")
        self.card_saldo = StatCard(tarjetas, "Saldo en sistema", "—", "💰")
        self.card_ing = StatCard(tarjetas, "Total ingresos", "—", "⬆️")
        self.card_egr = StatCard(tarjetas, "Total egresos", "—", "⬇️")
        for i, c in enumerate((self.card_saldo, self.card_ing, self.card_egr)):
            c.grid(row=0, column=i, padx=(0 if i == 0 else 12, 0), sticky="ew")
            tarjetas.grid_columnconfigure(i, weight=1)

        # --- Arqueo de caja ---
        arqueo = Panel(self, "🧮  Arqueo de caja (cuadre)")
        arqueo.pack(fill="x", pady=(14, 0))
        fila = ctk.CTkFrame(arqueo, fg_color="transparent")
        fila.pack(fill="x", padx=18, pady=(0, 4))
        c1, self.e_contado = campo(fila, "Efectivo contado", 150)
        self.selector_fecha = SelectorFecha(fila, "Fecha del arqueo")
        c1.grid(row=0, column=0, padx=(0, 14), sticky="w")
        self.selector_fecha.grid(row=0, column=1, padx=(0, 14), sticky="w")
        # Botones en su propia fila para que nunca se corten
        fila_btn = ctk.CTkFrame(arqueo, fg_color="transparent")
        fila_btn.pack(fill="x", padx=18, pady=(0, 4))
        boton(fila_btn, "🔎  Comparar", self._comparar, color=T.BG_PANEL_2,
              hover=T.BG_HOVER, ancho=150, text_color=T.TEXT).pack(side="left")
        self.btn_ajuste = boton(fila_btn, "✔ Registrar ajuste", self._ajustar,
                                color=T.WARNING, hover="#d97706", ancho=180)
        self.btn_ajuste.pack(side="left", padx=(10, 0))
        self.lbl_dif = ctk.CTkLabel(arqueo, text="", font=T.FONT_LABEL,
                                    text_color=T.TEXT_MUTED)
        self.lbl_dif.pack(anchor="w", padx=18, pady=(2, 14))
        self._diferencia = 0.0

        # --- Desglose por categoría ---
        desg = Panel(self, "📂  Desglose por categoría (histórico)")
        desg.pack(fill="both", expand=True, pady=(14, 0))
        self.tabla = Tabla(desg, columnas=("Categoría", "Tipo", "Monto"),
                           anchos=(280, 120, 160), altura=8)
        self.tabla.pack(fill="both", expand=True, padx=14, pady=(0, 14))

        # --- Caja chica ---
        chica = Panel(self, "🪙  Caja chica")
        chica.pack(fill="x", pady=(14, 0))
        f2 = ctk.CTkFrame(chica, fg_color="transparent")
        f2.pack(fill="x", padx=18, pady=(0, 6))
        c3, self.e_fondo = campo(f2, "Fondo de caja chica", 150)
        boton(f2, "💾 Guardar fondo", self._guardar_fondo, ancho=150).grid(
            row=0, column=1, padx=(10, 0), pady=(18, 0))
        c3.grid(row=0, column=0, padx=(0, 0), sticky="w")
        self.lbl_chica = ctk.CTkLabel(chica, text="", font=T.FONT_LABEL,
                                      text_color=T.TEXT)
        self.lbl_chica.pack(anchor="w", padx=18, pady=(2, 6))

        f3 = ctk.CTkFrame(chica, fg_color="transparent")
        f3.pack(fill="x", padx=18, pady=(0, 14))
        c4, self.e_gasto = campo(f3, "Gasto de caja chica", 130)
        c5, self.e_gasto_desc = campo(f3, "Descripción", 240)
        self.selector_gasto = SelectorFecha(f3, "Fecha")
        c4.grid(row=0, column=0, padx=(0, 12), sticky="w")
        c5.grid(row=0, column=1, padx=(0, 12), sticky="w")
        self.selector_gasto.grid(row=0, column=2, padx=(0, 12), sticky="w")
        boton(f3, "➖ Registrar gasto", self._gasto_chica, color=T.DANGER,
              hover=T.DANGER_HOVER, ancho=170, text_color=T.TEXT_LIGHT).grid(
            row=0, column=3, padx=(0, 0), pady=(18, 0))

    # --------------------------------------------------------------- acciones
    def _comparar(self):
        try:
            contado = float(self.e_contado.get())
        except ValueError:
            return mb.showerror("Error", "Escribe el efectivo contado (número).")
        saldo = movimiento_service.resumen_caja_total()["saldo"]
        self._diferencia = round(contado - saldo, 2)
        if abs(self._diferencia) < 0.005:
            self.lbl_dif.configure(text=f"✅ Cuadra exacto. Sistema {_dinero(saldo)} = "
                                        f"contado {_dinero(contado)}.",
                                   text_color=T.SUCCESS)
        elif self._diferencia > 0:
            self.lbl_dif.configure(
                text=f"⚠️ SOBRANTE de {_dinero(self._diferencia)} "
                     f"(contado {_dinero(contado)} > sistema {_dinero(saldo)}).",
                text_color=T.WARNING)
        else:
            self.lbl_dif.configure(
                text=f"⚠️ FALTANTE de {_dinero(-self._diferencia)} "
                     f"(contado {_dinero(contado)} < sistema {_dinero(saldo)}).",
                text_color=T.DANGER)

    def _ajustar(self):
        if abs(self._diferencia) < 0.005:
            return mb.showinfo("Arqueo", "Primero compara; no hay diferencia que ajustar.")
        if not mb.askyesno("Confirmar",
                           f"Se registrará un ajuste de {_dinero(abs(self._diferencia))} "
                           "para que el sistema cuadre con el efectivo contado. ¿Continuar?"):
            return
        movimiento_service.registrar_ajuste(self._diferencia, self.selector_fecha.get())
        self._diferencia = 0.0
        self.lbl_dif.configure(text="Ajuste registrado. La caja quedó cuadrada.",
                               text_color=T.SUCCESS)
        self.e_contado.delete(0, "end")
        self.refrescar()
        self.app.actualizar_saldo()

    def _guardar_fondo(self):
        try:
            config_service.guardar("CAJA_CHICA_FONDO", float(self.e_fondo.get() or 0))
            self.refrescar()
            mb.showinfo("Guardado", "Fondo de caja chica actualizado.")
        except ValueError:
            mb.showerror("Error", "Escribe un número válido.")

    def _gasto_chica(self):
        try:
            monto = float(self.e_gasto.get())
            movimiento_service.registrar_gasto_caja_chica(
                monto, self.selector_gasto.get(), self.e_gasto_desc.get())
            self.e_gasto.delete(0, "end")
            self.e_gasto_desc.delete(0, "end")
            self.refrescar()
            self.app.actualizar_saldo()
            mb.showinfo("Listo", "Gasto de caja chica registrado.")
        except ValueError as ex:
            mb.showerror("Error", str(ex) if str(ex) else "Monto inválido.")

    # --------------------------------------------------------------- refrescar
    def refrescar(self):
        r = movimiento_service.resumen_caja_total()
        self.card_saldo.set_valor(_dinero(r["saldo"]))
        self.card_ing.set_valor(_dinero(r["ingresos"]))
        self.card_egr.set_valor(_dinero(r["egresos"]))

        filas = []
        for clave, monto in sorted(r["categorias"].items()):
            etiqueta = _CATS.get(clave, clave)
            tipo = "Ingreso" if clave.endswith("_ingreso") else "Egreso"
            filas.append((etiqueta, tipo, _dinero(monto)))
        self.tabla.cargar(filas)

        ch = movimiento_service.estado_caja_chica()
        self.e_fondo.delete(0, "end")
        self.e_fondo.insert(0, f"{ch['fondo']:g}")
        self.lbl_chica.configure(
            text=f"Fondo: {_dinero(ch['fondo'])}   ·   Gastado: {_dinero(ch['gastado'])}"
                 f"   ·   Disponible: {_dinero(ch['disponible'])}")
