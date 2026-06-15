"""
Pantalla de configuración inicial (se muestra antes del login la primera vez).

Pregunta el NOMBRE DEL BANCO / ENTIDAD. Con ese nombre se configura la app
(título, barra lateral, login y carpeta de reportes). Una vez guardado, marca
BANCO_CONFIGURADO=1 y ya no vuelve a aparecer (salvo que se reinicie la base).
"""

import tkinter.messagebox as mb
import customtkinter as ctk
from ui import theme as T
from utils.rutas import aplicar_icono
from services import config_service


class SetupWindow(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.guardado = False
        self.title("Configuración inicial")
        self.geometry("460x560")
        self.resizable(False, False)
        self.configure(fg_color=T.BG_APP)
        aplicar_icono(self)
        self._centrar(460, 560)

        card = ctk.CTkFrame(self, fg_color=T.BG_PANEL, corner_radius=T.RADIUS,
                            border_width=1, border_color=T.BORDER)
        card.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.86, relheight=0.82)

        from utils.rutas import cargar_logo
        self._logo = cargar_logo((92, 92))
        if self._logo:
            ctk.CTkLabel(card, image=self._logo, text="").pack(pady=(26, 6))
        else:
            ctk.CTkLabel(card, text="🏦", font=(T.FONT_FAMILY, 44)).pack(pady=(30, 6))
        ctk.CTkLabel(card, text="¡Bienvenido!", font=(T.FONT_FAMILY, 22, "bold"),
                     text_color=T.TEXT).pack()
        ctk.CTkLabel(card, text="¿Cuál es el nombre de tu banco o entidad?",
                     font=T.FONT_SMALL, text_color=T.TEXT_MUTED,
                     wraplength=320, justify="center").pack(pady=(4, 20))

        self.e_nombre = ctk.CTkEntry(card, placeholder_text="Ej: Caja San Miguel",
                                     height=44, corner_radius=T.RADIUS_SM,
                                     fg_color=T.BG_PANEL_2, border_color=T.BORDER,
                                     font=(T.FONT_FAMILY, 14))
        self.e_nombre.pack(fill="x", padx=34)
        actual = config_service.obtener("NOMBRE_BANCO") or ""
        if actual and actual != "Banquito Comunitario":
            self.e_nombre.insert(0, actual)

        ctk.CTkLabel(card, text="Podrás cambiarlo luego en Configuración → General.",
                     font=(T.FONT_FAMILY, 10), text_color=T.TEXT_DIM,
                     wraplength=320, justify="center").pack(pady=(10, 16))

        btn = ctk.CTkButton(card, text="Continuar  →", command=self._guardar,
                            height=46, corner_radius=T.RADIUS_SM, fg_color=T.ACCENT,
                            hover_color=T.ACCENT_HOVER, text_color=T.TEXT_ON_ACCENT,
                            font=(T.FONT_FAMILY, 15, "bold"))
        btn.pack(fill="x", padx=34, pady=(0, 6))
        self.e_nombre.bind("<Return>", lambda _e: self._guardar())

        # Pie con créditos / contacto
        pie = ctk.CTkFrame(self, fg_color="transparent")
        pie.place(relx=0.5, rely=0.97, anchor="s")
        ctk.CTkLabel(pie, text="© Elaborado por MrMickWhite",
                     font=(T.FONT_FAMILY, 11, "bold"), text_color=T.TEXT_MUTED).pack()
        ctk.CTkLabel(pie, text="Soporte: mrmickdesign@gmail.com",
                     font=(T.FONT_FAMILY, 10), text_color=T.TEXT_DIM).pack()

        self.e_nombre.focus()

    def _centrar(self, w, h):
        self.update_idletasks()
        x = (self.winfo_screenwidth() - w) // 2
        y = (self.winfo_screenheight() - h) // 2 - 20
        self.geometry(f"{w}x{h}+{x}+{max(0, y)}")

    def _guardar(self):
        nombre = self.e_nombre.get().strip()
        if len(nombre) < 2:
            return mb.showwarning("Atención", "Escribe el nombre de tu banco o entidad.")
        config_service.guardar("NOMBRE_BANCO", nombre)
        config_service.guardar("BANCO_CONFIGURADO", "1")
        self.guardado = True
        self.destroy()
