"""Vista Dashboard: resumen visual del banquito con tarjetas de métricas."""

from datetime import date
import customtkinter as ctk
from ui import theme as T
from ui.components.cards import StatCard, Panel
from ui.components.tabla import Tabla
from config import settings
from repositories import (socio_repository, prestamo_repository,
                          movimiento_repository)
from services import reporte_service


def _dinero(v):
    return f"{settings.SIMBOLO_MONEDA}{v:,.2f}"


class DashboardView(ctk.CTkFrame):
    def __init__(self, master, app):
        super().__init__(master, fg_color="transparent")
        self.app = app
        self._construir()

    def _construir(self):
        ctk.CTkLabel(self, text="Resumen general", font=T.FONT_H1,
                     text_color=T.TEXT).pack(anchor="w", padx=4, pady=(0, 2))
        ctk.CTkLabel(self, text="Estado actual de la caja en un vistazo",
                     font=T.FONT_SMALL, text_color=T.TEXT_MUTED).pack(
            anchor="w", padx=4, pady=(0, 8))

        # Banner: próxima recaudación según la configuración
        banner = ctk.CTkFrame(self, fg_color=T.BG_PANEL, corner_radius=T.RADIUS_SM,
                              border_width=1, border_color=T.BORDER)
        banner.pack(fill="x", padx=2, pady=(0, 12))
        self.lbl_recaudacion = ctk.CTkLabel(banner, text="", font=T.FONT_SMALL,
                                            text_color=T.TEXT)
        self.lbl_recaudacion.pack(anchor="w", padx=14, pady=8)

        # --- Fila de tarjetas ---
        grid = ctk.CTkFrame(self, fg_color="transparent")
        grid.pack(fill="x")
        for i in range(3):
            grid.grid_columnconfigure(i, weight=1, uniform="cards")

        self.card_caja = StatCard(grid, "Saldo en caja", icono="🏦", color=T.SUCCESS)
        self.card_socios = StatCard(grid, "Socios activos", icono="👥", color=T.ACCENT)
        self.card_prestado = StatCard(grid, "Capital prestado", icono="📤", color=T.INFO)
        self.card_caja.grid(row=0, column=0, padx=(0, 8), pady=8, sticky="ew")
        self.card_socios.grid(row=0, column=1, padx=8, pady=8, sticky="ew")
        self.card_prestado.grid(row=0, column=2, padx=(8, 0), pady=8, sticky="ew")

        self.card_aportes = StatCard(grid, f"Aportes {date.today().year}",
                                     icono="💰", color=T.PURPLE)
        self.card_interes = StatCard(grid, f"Intereses {date.today().year}",
                                     icono="📈", color=T.SUCCESS)
        self.card_mora = StatCard(grid, f"Mora cobrada {date.today().year}",
                                  icono="⏰", color=T.WARNING)
        self.card_aportes.grid(row=1, column=0, padx=(0, 8), pady=8, sticky="ew")
        self.card_interes.grid(row=1, column=1, padx=8, pady=8, sticky="ew")
        self.card_mora.grid(row=1, column=2, padx=(8, 0), pady=8, sticky="ew")

        # --- Actividad reciente ---
        panel = Panel(self, "Actividad reciente")
        panel.pack(fill="both", expand=True, pady=(16, 0))
        self.tabla = Tabla(panel, columnas=("Fecha", "Movimiento", "Socio", "Monto"),
                           anchos=(110, 200, 200, 120), altura=8)
        self.tabla.pack(fill="both", expand=True, padx=14, pady=(0, 14))

    def refrescar(self):
        from services import recaudacion_service
        self.lbl_recaudacion.configure(
            text=f"📅  Próxima recaudación:  {recaudacion_service.descripcion()}")
        anio = date.today().year
        socios = socio_repository.listar(solo_activos=True)
        prestado = sum(p.saldo_capital
                       for p in prestamo_repository.listar_prestamos(solo_activos=True))
        rep = reporte_service.general_anual(anio)

        self.card_caja.set_valor(_dinero(movimiento_repository.saldo_caja()))
        self.card_socios.set_valor(str(len(socios)))
        self.card_prestado.set_valor(_dinero(prestado))
        self.card_aportes.set_valor(_dinero(rep["resumen"]["aportes"]))
        self.card_interes.set_valor(_dinero(rep["resumen"]["intereses_ganados"]))
        self.card_mora.set_valor(_dinero(rep["resumen"]["mora_cobrada"]))

        nombres = {s.id: s.nombre_completo for s in socio_repository.listar()}
        ini, fin = f"{anio}-01-01", f"{anio}-12-31"
        movs = movimiento_repository.listar_por_periodo(ini, fin)
        movs = sorted(movs, key=lambda m: (m.fecha, m.id), reverse=True)[:15]
        etiquetas = {"aporte": "Aporte", "prestamo": "Préstamo otorgado",
                     "pago_capital": "Pago de capital", "interes": "Pago de interés",
                     "mora": "Pago de mora", "gasto": "Gasto"}
        filas = []
        for m in movs:
            signo = "+" if m.tipo == "ingreso" else "−"
            filas.append((m.fecha, etiquetas.get(m.categoria, m.categoria),
                          nombres.get(m.socio_id, "—"),
                          f"{signo} {_dinero(m.monto)}"))
        self.tabla.cargar(filas)
