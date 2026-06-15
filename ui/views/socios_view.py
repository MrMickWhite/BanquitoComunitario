"""Vista de Socios: alta, baja y, al seleccionar, su HISTORIAL fechado."""

import tkinter.messagebox as mb
import customtkinter as ctk
from ui import theme as T
from ui.components.cards import Panel, campo, boton
from ui.components.tabla import Tabla
from config import settings
from services import socio_service, reporte_service
from repositories import aporte_repository, prestamo_repository


def _dinero(v):
    return f"{settings.SIMBOLO_MONEDA}{v:,.2f}"


class SociosView(ctk.CTkFrame):
    def __init__(self, master, app):
        super().__init__(master, fg_color="transparent")
        self.app = app
        self._construir()
        self.refrescar()

    def _construir(self):
        # --- Formulario de alta (una fila compacta) ---
        form = Panel(self, "Agregar socio")
        form.pack(fill="x")
        fila = ctk.CTkFrame(form, fg_color="transparent")
        fila.pack(fill="x", padx=18, pady=(0, 14))

        c1, self.e_nombres = campo(fila, "Nombres", 150)
        c2, self.e_apellidos = campo(fila, "Apellidos", 150)
        c3, self.e_documento = campo(fila, "C.I. / DNI", 130)
        c4, self.e_telefono = campo(fila, "Teléfono", 120)
        c5, self.e_email = campo(fila, "Email", 160)
        for i, c in enumerate((c1, c2, c3, c4, c5)):
            c.grid(row=0, column=i, padx=(0, 10), pady=4, sticky="w")
        boton(fila, "➕  Agregar", self._agregar, ancho=130).grid(
            row=0, column=5, padx=(6, 0), pady=(18, 0))

        # --- Cuerpo: tabla socios (izq) + historial (der) ---
        cuerpo = ctk.CTkFrame(self, fg_color="transparent")
        cuerpo.pack(fill="both", expand=True, pady=(14, 0))
        cuerpo.grid_columnconfigure(0, weight=3, uniform="b")
        cuerpo.grid_columnconfigure(1, weight=2, uniform="b")
        cuerpo.grid_rowconfigure(0, weight=1)

        izq = Panel(cuerpo, "Lista de socios")
        izq.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        self.tabla = Tabla(izq, columnas=("ID", "Nombre", "C.I. / DNI",
                                          "Aportado", "Deuda", "Ingreso", "Activo"),
                           anchos=(35, 150, 100, 90, 90, 95, 55), altura=12)
        self.tabla.pack(fill="both", expand=True, padx=14, pady=(0, 8))
        self.tabla.on_seleccion(self._mostrar_historial)

        acciones = ctk.CTkFrame(izq, fg_color="transparent")
        acciones.pack(fill="x", padx=14, pady=(0, 14))
        boton(acciones, "🚫 Desactivar", self._desactivar,
              color=T.WARNING, hover="#d97706", ancho=130).pack(side="left", padx=(0, 8))
        boton(acciones, "🗑 Eliminar", self._eliminar,
              color=T.DANGER, hover=T.DANGER_HOVER, ancho=120,
              text_color=T.TEXT_LIGHT).pack(side="left")
        boton(acciones, "📄 Reporte", self._ir_reporte,
              color=T.BG_PANEL_2, hover=T.BG_HOVER, ancho=110,
              text_color=T.TEXT).pack(side="right")

        der = Panel(cuerpo, "Historial del socio")
        der.grid(row=0, column=1, sticky="nsew", padx=(8, 0))
        self.lbl_socio = ctk.CTkLabel(der, text="Selecciona un socio para ver "
                                      "sus procesos con fecha",
                                      font=T.FONT_SMALL, text_color=T.TEXT_MUTED)
        self.lbl_socio.pack(anchor="w", padx=18, pady=(0, 6))
        self.tabla_hist = Tabla(der, columnas=("Fecha", "Proceso", "Monto"),
                                anchos=(100, 150, 110), altura=14)
        self.tabla_hist.pack(fill="both", expand=True, padx=14, pady=(0, 14))

    # ----------------------------------------------------------------- acciones
    def _agregar(self):
        try:
            socio_service.agregar_socio(
                self.e_nombres.get(), self.e_apellidos.get(), self.e_documento.get(),
                self.e_telefono.get(), self.e_email.get())
            for e in (self.e_nombres, self.e_apellidos, self.e_documento,
                      self.e_telefono, self.e_email):
                e.delete(0, "end")
            self.app.notificar_cambio_socios()
            mb.showinfo("Listo", "Socio agregado correctamente.")
        except Exception as ex:
            mb.showerror("Error", str(ex))

    def _desactivar(self):
        sid = self.tabla.id_seleccionado()
        if not sid:
            return mb.showwarning("Atención", "Selecciona un socio.")
        socio_service.eliminar_socio(int(sid), borrar_historial=False)
        self.app.notificar_cambio_socios()

    def _eliminar(self):
        sid = self.tabla.id_seleccionado()
        if not sid:
            return mb.showwarning("Atención", "Selecciona un socio.")
        if mb.askyesno("Confirmar", "Esto borrará al socio y TODO su historial.\n¿Continuar?"):
            socio_service.eliminar_socio(int(sid), borrar_historial=True)
            self.app.notificar_cambio_socios()

    def _ir_reporte(self):
        self.app.mostrar_vista("Reportes")

    # --------------------------------------------------------------- historial
    def _mostrar_historial(self):
        sid = self.tabla.id_seleccionado()
        if not sid:
            return
        from repositories import socio_repository
        s = socio_repository.obtener_por_id(int(sid))
        self.lbl_socio.configure(text=f"{s.nombre_completo}  ·  ingresó {s.fecha_ingreso}")
        historial = reporte_service.historial_socio(int(sid))
        filas = []
        for h in historial:
            signo = "+" if h["tipo"] == "ingreso" else "−"
            filas.append((h["fecha"], h["proceso"], f"{signo} {_dinero(h['monto'])}"))
        self.tabla_hist.cargar(filas)

    # --------------------------------------------------------------- refrescar
    def refrescar(self):
        filas = []
        for s in socio_service.listar_socios():
            aportado = aporte_repository.total_por_socio(s.id)
            deuda = sum(p.saldo_capital
                        for p in prestamo_repository.listar_prestamos_por_socio(s.id))
            filas.append((s.id, s.nombre_completo, s.documento or "",
                          _dinero(aportado), _dinero(deuda), s.fecha_ingreso,
                          "Sí" if s.activo else "No"))
        self.tabla.cargar(filas)
