"""
Ventana principal con barra lateral de navegación (estilo dashboard moderno).

Para agregar una nueva sección en el futuro:
  1) Crea una vista en ui/views/ (clase que herede de ctk.CTkFrame).
  2) Regístrala en self._defs.  El resto del sistema no cambia.
"""

import tkinter as tk
import customtkinter as ctk
from config import settings
from ui import theme as T
from utils.rutas import aplicar_icono
from repositories import movimiento_repository
from services import config_service
from ui.components.tabla import Tabla
from ui.views.dashboard_view import DashboardView
from ui.views.socios_view import SociosView
from ui.views.aportes_view import AportesView
from ui.views.prestamos_view import PrestamosView
from ui.views.movimientos_view import MovimientosView
from ui.views.cuadre_view import CuadreCajaView
from ui.views.reportes_view import ReportesView
from ui.views.config_view import ConfigView
from ui.views.licencia_view import LicenciaView


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        # Apariencia guardada (claro / oscuro)
        ctk.set_appearance_mode(config_service.obtener("APARIENCIA") or "dark")

        self.title(f"{config_service.obtener('NOMBRE_BANCO')} — Gestión")
        # Tamaño que se adapta a la pantalla (para que NADA se corte sin pantalla
        # completa). Toma como base 1180x760 pero nunca más del 92% de la pantalla.
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        ancho = min(1180, int(sw * 0.92))
        alto = min(760, int(sh * 0.90))
        x = max(0, (sw - ancho) // 2)
        y = max(0, (sh - alto) // 2 - 20)
        self.geometry(f"{ancho}x{alto}+{x}+{y}")
        self.minsize(min(1000, ancho), min(620, alto))
        self.configure(fg_color=T.BG_APP)
        aplicar_icono(self)
        self.protocol("WM_DELETE_WINDOW", self._confirmar_salida)

        # Registro de secciones: (nombre, ícono, clase)
        self._defs = [
            ("Dashboard", "📊", DashboardView),
            ("Socios",    "👥", SociosView),
            ("Aportes",   "💰", AportesView),
            ("Préstamos", "🏦", PrestamosView),
            ("Movimientos", "💵", MovimientosView),
            ("Cuadre de caja", "🧮", CuadreCajaView),
            ("Reportes",  "📄", ReportesView),
            ("Licencia", "🔑", LicenciaView),
            ("Configuración", "⚙️", ConfigView),
        ]

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._construir_sidebar()
        self._construir_contenido()
        self.mostrar_vista("Dashboard")
        self.actualizar_saldo()

    # ------------------------------------------------------------- sidebar
    def _construir_sidebar(self):
        side = ctk.CTkFrame(self, width=220, corner_radius=0, fg_color=T.BG_SIDEBAR)
        side.grid(row=0, column=0, sticky="nsew")
        side.grid_propagate(False)

        # Logo / marca
        logo = ctk.CTkFrame(side, fg_color="transparent")
        logo.pack(fill="x", padx=20, pady=(26, 30))
        from utils.rutas import cargar_logo
        self._logo_side = cargar_logo((40, 40))
        if self._logo_side:
            ctk.CTkLabel(logo, image=self._logo_side, text="").pack(side="left")
        else:
            ctk.CTkLabel(logo, text="🏦", font=(T.FONT_FAMILY, 30)).pack(side="left")
        marca = ctk.CTkFrame(logo, fg_color="transparent")
        marca.pack(side="left", padx=10)
        ctk.CTkLabel(marca, text=(config_service.obtener("NOMBRE_BANCO") or settings.NOMBRE_APP),
                     font=(T.FONT_FAMILY, 17, "bold"),
                     text_color=T.TEXT).pack(anchor="w")
        ctk.CTkLabel(marca, text="Gestión de caja", font=(T.FONT_FAMILY, 10),
                     text_color=T.TEXT_MUTED).pack(anchor="w")

        # Botones de navegación
        self.nav_botones = {}
        for nombre, icono, _ in self._defs:
            b = ctk.CTkButton(
                side, text=f"   {icono}   {nombre}", anchor="w",
                font=(T.FONT_FAMILY, 13), height=44, corner_radius=T.RADIUS_SM,
                fg_color="transparent", hover_color=T.BG_HOVER,
                text_color=T.TEXT_MUTED,
                command=lambda n=nombre: self.mostrar_vista(n),
            )
            b.pack(fill="x", padx=14, pady=3)
            self.nav_botones[nombre] = b

        # Pie de la barra lateral
        pie = ctk.CTkLabel(side, text=f"{settings.MONEDA}  ·  {settings.VERSION_APP}",
                           font=(T.FONT_FAMILY, 10), text_color=T.TEXT_DIM)
        pie.pack(side="bottom", pady=(2, 14))
        contacto = ctk.CTkLabel(side, text=f"📧 {settings.CORREO_SOPORTE}",
                                font=(T.FONT_FAMILY, 10), text_color=T.TEXT_MUTED)
        contacto.pack(side="bottom", pady=(0, 0))
        ctk.CTkLabel(side, text="Soporte y contacto:", font=(T.FONT_FAMILY, 9),
                     text_color=T.TEXT_DIM).pack(side="bottom")

    # ------------------------------------------------------------- contenido
    def _construir_contenido(self):
        derecha = ctk.CTkFrame(self, fg_color="transparent")
        derecha.grid(row=0, column=1, sticky="nsew")
        derecha.grid_rowconfigure(1, weight=1)
        derecha.grid_columnconfigure(0, weight=1)

        # Barra superior con saldo
        topbar = ctk.CTkFrame(derecha, fg_color="transparent", height=64)
        topbar.grid(row=0, column=0, sticky="ew", padx=26, pady=(20, 6))
        self.lbl_titulo = ctk.CTkLabel(topbar, text="", font=T.FONT_TITLE,
                                       text_color=T.TEXT)
        self.lbl_titulo.pack(side="left")

        saldo_card = ctk.CTkFrame(topbar, fg_color=T.BG_PANEL, corner_radius=T.RADIUS,
                                  border_width=1, border_color=T.BORDER)
        saldo_card.pack(side="right")
        ctk.CTkLabel(saldo_card, text="Saldo en caja", font=T.FONT_SMALL,
                     text_color=T.TEXT_MUTED).pack(side="left", padx=(16, 8), pady=12)
        self.lbl_saldo = ctk.CTkLabel(saldo_card, text="—", font=T.FONT_H1,
                                      text_color=T.SUCCESS)
        self.lbl_saldo.pack(side="left", padx=(0, 16), pady=12)

        # Contenedor de vistas con scroll VERTICAL y HORIZONTAL (para que ningún
        # ícono, logo o botón quede cortado en pantallas pequeñas).
        outer = ctk.CTkFrame(derecha, fg_color="transparent")
        outer.grid(row=1, column=0, sticky="nsew", padx=20, pady=(6, 12))
        outer.grid_rowconfigure(0, weight=1)
        outer.grid_columnconfigure(0, weight=1)

        bg = self._apply_appearance_mode(T.BG_APP)
        self._canvas = tk.Canvas(outer, highlightthickness=0, bd=0, bg=bg)
        vbar = ctk.CTkScrollbar(outer, command=self._canvas.yview)
        hbar = ctk.CTkScrollbar(outer, orientation="horizontal", command=self._canvas.xview)
        self._canvas.configure(yscrollcommand=vbar.set, xscrollcommand=hbar.set)
        self._canvas.grid(row=0, column=0, sticky="nsew")
        vbar.grid(row=0, column=1, sticky="ns")
        hbar.grid(row=1, column=0, sticky="ew")

        # Frame interno donde van las vistas. Con color EXPLÍCITO (no "transparent")
        # para que CustomTkinter lo recolore solo al cambiar entre claro/oscuro
        # (los frames transparentes dentro de un Canvas de tkinter no se recolorean).
        self.contenido = ctk.CTkFrame(self._canvas, fg_color=T.BG_APP)
        self._win = self._canvas.create_window((0, 0), window=self.contenido, anchor="nw")

        def _ajustar_scroll(_e=None):
            self._canvas.configure(scrollregion=self._canvas.bbox("all"))
        self.contenido.bind("<Configure>", _ajustar_scroll)

        def _ajustar_ancho(e):
            # El contenido nunca es más angosto que el canvas; si es más ancho,
            # aparece la barra horizontal.
            ancho = max(e.width, self.contenido.winfo_reqwidth())
            self._canvas.itemconfigure(self._win, width=ancho)
        self._canvas.bind("<Configure>", _ajustar_ancho)

        # Rueda del mouse (vertical; con Shift, horizontal)
        def _rueda(e):
            self._canvas.yview_scroll(int(-1 * (e.delta / 120)), "units")
        def _rueda_h(e):
            self._canvas.xview_scroll(int(-1 * (e.delta / 120)), "units")
        self._canvas.bind("<Enter>", lambda _e: (
            self._canvas.bind_all("<MouseWheel>", _rueda),
            self._canvas.bind_all("<Shift-MouseWheel>", _rueda_h)))
        self._canvas.bind("<Leave>", lambda _e: (
            self._canvas.unbind_all("<MouseWheel>"),
            self._canvas.unbind_all("<Shift-MouseWheel>")))

        self.vistas = {}
        for nombre, _, clase in self._defs:
            vista = clase(self.contenido, self)
            self.vistas[nombre] = vista

    # ------------------------------------------------------------- navegación
    def mostrar_vista(self, nombre):
        for v in self.vistas.values():
            v.pack_forget()
        self.vistas[nombre].pack(fill="both", expand=True)
        self.lbl_titulo.configure(text=nombre)

        # resaltar botón activo
        for n, b in self.nav_botones.items():
            if n == nombre:
                b.configure(fg_color=T.ACCENT, text_color=T.TEXT_ON_ACCENT)
            else:
                b.configure(fg_color="transparent", text_color=T.TEXT_MUTED)

        # refrescar la vista al entrar (datos siempre actuales)
        if hasattr(self.vistas[nombre], "refrescar"):
            self.vistas[nombre].refrescar()
        self.actualizar_saldo()
        # Volver el scroll al inicio al cambiar de sección
        if hasattr(self, "_canvas"):
            self.update_idletasks()
            self._canvas.yview_moveto(0)
            self._canvas.xview_moveto(0)
            self._canvas.configure(scrollregion=self._canvas.bbox("all"))

    def notificar_cambio_socios(self):
        """Refresca combos/tablas dependientes de la lista de socios."""
        for nombre, vista in self.vistas.items():
            if hasattr(vista, "refrescar_socios"):
                vista.refrescar_socios()
            elif hasattr(vista, "refrescar"):
                vista.refrescar()
        self.actualizar_saldo()

    def actualizar_saldo(self):
        saldo = movimiento_repository.saldo_caja()
        self.lbl_saldo.configure(
            text=f"{settings.SIMBOLO_MONEDA}{saldo:,.2f}")

    def actualizar_titulo(self):
        """Se llama al cambiar el nombre del banco en Configuración."""
        self.title(f"{config_service.obtener('NOMBRE_BANCO')} — Gestión")

    def _confirmar_salida(self):
        import tkinter.messagebox as mb
        if mb.askyesno("Salir", "¿Seguro que quieres salir del programa?"):
            self.destroy()

    def cambiar_apariencia(self, modo: str):
        """Cambia entre 'dark' y 'light', lo guarda y re-estiliza las tablas."""
        ctk.set_appearance_mode(modo)
        config_service.guardar("APARIENCIA", modo)
        if hasattr(self, "_canvas"):
            self._canvas.configure(bg=self._apply_appearance_mode(T.BG_APP))
        # Las tablas ttk no cambian solas: las re-estilizamos y recargamos.
        Tabla.reestilizar_todas()
        for vista in self.vistas.values():
            if hasattr(vista, "refrescar"):
                vista.refrescar()
