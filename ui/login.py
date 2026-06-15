"""
Ventana de inicio de sesión — 100% local (sin internet).

Flujo:
  • Iniciar sesión (usuario + contraseña).
  • Primer ingreso con usuario/usuario -> obliga a cambiar usuario y contraseña.
  • "¿Olvidaste tu contraseña?" -> recuperación con el código que entrega el
    proveedor por correo (cambia solo la contraseña).
"""

import tkinter.messagebox as mb
import customtkinter as ctk
from ui import theme as T
from utils.rutas import aplicar_icono, cargar_logo
from services import auth_service, config_service
from config import settings


class LoginWindow(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.exito = False
        self.usuario = None

        nombre = config_service.obtener("NOMBRE_BANCO") or settings.NOMBRE_APP
        self.title(f"{nombre} — Acceso")
        self.geometry("460x640")
        self.resizable(False, False)
        self.configure(fg_color=T.BG_APP)
        aplicar_icono(self)
        self._centrar(460, 640)

        self.card = ctk.CTkFrame(self, fg_color=T.BG_PANEL, corner_radius=T.RADIUS,
                                 border_width=1, border_color=T.BORDER)
        self.card.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.86, relheight=0.84)

        self._logo = cargar_logo((84, 84))
        if self._logo:
            ctk.CTkLabel(self.card, image=self._logo, text="").pack(pady=(22, 4))
        else:
            ctk.CTkLabel(self.card, text="🏦", font=(T.FONT_FAMILY, 40)).pack(pady=(24, 4))
        ctk.CTkLabel(self.card, text=nombre, font=(T.FONT_FAMILY, 22, "bold"),
                     text_color=T.TEXT).pack()
        self.lbl_sub = ctk.CTkLabel(self.card, text="Inicia sesión para continuar",
                                    font=T.FONT_SMALL, text_color=T.TEXT_MUTED)
        self.lbl_sub.pack(pady=(2, 14))

        self.cuerpo = ctk.CTkFrame(self.card, fg_color="transparent")
        self.cuerpo.pack(fill="both", expand=True, padx=30)

        pie = ctk.CTkFrame(self, fg_color="transparent")
        pie.place(relx=0.5, rely=0.975, anchor="s")
        ctk.CTkLabel(pie, text="© Elaborado por MrMickWhite",
                     font=(T.FONT_FAMILY, 11, "bold"), text_color=T.TEXT_MUTED).pack()
        ctk.CTkLabel(pie, text="Para información o soporte, escríbenos a:\n"
                              "mrmickdesign@gmail.com",
                     font=(T.FONT_FAMILY, 10), text_color=T.TEXT_DIM,
                     justify="center").pack()

        self._mostrar_login()

    # --------------------------------------------------------------- utilidades
    def _centrar(self, w, h):
        self.update_idletasks()
        x = (self.winfo_screenwidth() - w) // 2
        y = (self.winfo_screenheight() - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")

    def _limpiar(self):
        for w in self.cuerpo.winfo_children():
            w.destroy()

    def _entry(self, placeholder, show=None):
        e = ctk.CTkEntry(self.cuerpo, placeholder_text=placeholder, height=44,
                         corner_radius=T.RADIUS_SM, fg_color=T.BG_PANEL_2,
                         border_color=T.BORDER, font=(T.FONT_FAMILY, 13),
                         show=show or "")
        e.pack(fill="x", pady=6)
        return e

    def _boton(self, texto, cmd, primario=True):
        b = ctk.CTkButton(
            self.cuerpo, text=texto, command=cmd, height=46, corner_radius=T.RADIUS_SM,
            fg_color=(T.ACCENT if primario else T.BG_PANEL_2),
            hover_color=(T.ACCENT_HOVER if primario else T.BG_HOVER),
            text_color=(T.TEXT_ON_ACCENT if primario else T.TEXT),
            font=(T.FONT_FAMILY, 14, "bold"))
        b.pack(fill="x", pady=(10, 4))
        return b

    def _link(self, texto, cmd):
        l = ctk.CTkLabel(self.cuerpo, text=texto, font=(T.FONT_FAMILY, 11, "underline"),
                         text_color=T.ACCENT, cursor="hand2")
        l.pack(pady=(6, 0))
        l.bind("<Button-1>", lambda _e: cmd())
        return l

    # ------------------------------------------------------------------- LOGIN
    def _mostrar_login(self):
        self._limpiar()
        self.lbl_sub.configure(text="Inicia sesión para continuar")
        self.e_user = self._entry("Usuario")
        self.e_pass = self._entry("Contraseña", show="•")
        self.e_pass.bind("<Return>", lambda _e: self._ingresar())
        self._boton("Ingresar", self._ingresar)
        self._link("¿Olvidaste tu contraseña?", self._mostrar_recuperar)

    def _ingresar(self):
        u = self.e_user.get().strip()
        p = self.e_pass.get()
        ok, msg, debe = auth_service.verificar_login(u, p)
        if not ok:
            return mb.showerror("Acceso", msg)
        if debe:
            self._mostrar_cambio_forzado(u)
        else:
            self.usuario = u
            self.exito = True
            self.destroy()

    # ----------------------------------------------- CAMBIO FORZADO (1er ingreso)
    def _mostrar_cambio_forzado(self, usuario_actual):
        self._limpiar()
        self._usuario_actual = usuario_actual
        self.lbl_sub.configure(text="Primer ingreso: define tus datos")
        ctk.CTkLabel(self.cuerpo,
                     text="Por seguridad, crea tu propio usuario y contraseña.",
                     font=T.FONT_SMALL, text_color=T.TEXT_MUTED,
                     wraplength=320, justify="center").pack(pady=(0, 6))
        self.e_nuevo_user = self._entry("Nuevo usuario")
        self.e_nuevo_pass = self._entry("Nueva contraseña", show="•")
        self.e_nuevo_pass2 = self._entry("Repite la contraseña", show="•")
        self._boton("Guardar y continuar", self._guardar_cambio_forzado)

    def _guardar_cambio_forzado(self):
        nu = self.e_nuevo_user.get().strip()
        p1 = self.e_nuevo_pass.get()
        p2 = self.e_nuevo_pass2.get()
        if p1 != p2:
            return mb.showerror("Atención", "Las contraseñas no coinciden.")
        ok, msg, _ = auth_service.cambiar_credenciales(self._usuario_actual, nu, p1)
        if not ok:
            return mb.showerror("Atención", msg)
        mb.showinfo("Listo", "Datos guardados. Inicia sesión con tus nuevos datos.")
        self._mostrar_login()

    # ------------------------------------------------------------- RECUPERACIÓN
    def _mostrar_recuperar(self):
        self._limpiar()
        self.lbl_sub.configure(text="Recuperar contraseña")
        ctk.CTkLabel(self.cuerpo,
                     text="Escríbenos a mrmickdesign@gmail.com para obtener "
                          "tu código de recuperación, e ingrésalo aquí.",
                     font=T.FONT_SMALL, text_color=T.TEXT_MUTED,
                     wraplength=320, justify="center").pack(pady=(0, 8))
        self.e_rec_user = self._entry("Tu usuario")
        self.e_rec_cod = self._entry("Código de recuperación")
        self.e_rec_pass = self._entry("Nueva contraseña", show="•")
        self._boton("Cambiar contraseña", self._guardar_recuperacion)
        self._link("← Volver al inicio de sesión", self._mostrar_login)

    def _guardar_recuperacion(self):
        u = self.e_rec_user.get().strip()
        cod = self.e_rec_cod.get().strip()
        p = self.e_rec_pass.get()
        ok, msg = auth_service.recuperar_con_codigo(u, cod, p)
        if not ok:
            return mb.showerror("Recuperación", msg)
        mb.showinfo("Listo", "Contraseña actualizada. Ya puedes iniciar sesión.")
        self._mostrar_login()
