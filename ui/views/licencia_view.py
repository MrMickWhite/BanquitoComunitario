"""
Vista de Licencia (dentro de la app).

Muestra el estado actual (prueba / activa / por vencer), el código de equipo,
los planes y precios, el botón de correo y un campo para activar con la clave.
"""

import urllib.parse
import webbrowser
import tkinter.messagebox as mb
import customtkinter as ctk

from config import settings
from services import licencia_service as L, config_service
from ui import theme as T


class LicenciaView(ctk.CTkFrame):
    def __init__(self, master, app=None):
        super().__init__(master, fg_color="transparent")
        self.app = app
        self._construir()

    def _construir(self):
        for w in self.winfo_children():
            w.destroy()
        info = L.estado_licencia()

        ctk.CTkLabel(self, text="Licencia", font=T.FONT_H1,
                     text_color=T.TEXT).pack(anchor="w", pady=(0, 2))
        ctk.CTkLabel(self, text="Estado de tu licencia, planes y activación",
                     font=T.FONT_SMALL, text_color=T.TEXT_MUTED).pack(anchor="w", pady=(0, 12))

        # Tarjeta de estado
        estado_txt, color = self._estado_texto(info)
        card = ctk.CTkFrame(self, fg_color=T.BG_PANEL, corner_radius=T.RADIUS,
                            border_width=1, border_color=T.BORDER)
        card.pack(fill="x", pady=(0, 12))
        ctk.CTkLabel(card, text=estado_txt, font=(T.FONT_FAMILY, 16, "bold"),
                     text_color=color).pack(anchor="w", padx=16, pady=(12, 2))
        if info.get("vence"):
            ctk.CTkLabel(card, text=f"Vence el {info['vence'].strftime('%d/%m/%Y')}",
                         font=T.FONT_SMALL, text_color=T.TEXT_MUTED).pack(anchor="w", padx=16)
        # Código de equipo
        f = ctk.CTkFrame(card, fg_color="transparent")
        f.pack(fill="x", padx=16, pady=(8, 12))
        ctk.CTkLabel(f, text="Código de equipo:", font=T.FONT_SMALL,
                     text_color=T.TEXT_MUTED).pack(side="left")
        ctk.CTkLabel(f, text=info["codigo"], font=(T.FONT_FAMILY, 14, "bold"),
                     text_color=T.ACCENT).pack(side="left", padx=8)
        ctk.CTkButton(f, text="📋 Copiar", width=80, command=lambda: self._copiar(info["codigo"]),
                      fg_color=T.BG_PANEL_2, hover_color=T.BG_HOVER,
                      text_color=T.TEXT).pack(side="left")

        # Planes
        fila = ctk.CTkFrame(self, fg_color="transparent")
        fila.pack(fill="x", pady=4)
        self._tarjeta(fila, "mensual", False)
        self._tarjeta(fila, "semestral", False)
        self._tarjeta(fila, "anual", True)

        # Correo
        ctk.CTkButton(self, text="✉️  Contactar por correo para activar / renovar",
                      command=lambda: self._correo(info["codigo"]), height=46,
                      fg_color=T.ACCENT, hover_color=T.ACCENT_HOVER,
                      text_color=T.TEXT_ON_ACCENT,
                      font=(T.FONT_FAMILY, 14, "bold")).pack(fill="x", pady=(14, 6))

        # Activar
        act = ctk.CTkFrame(self, fg_color=T.BG_PANEL, corner_radius=T.RADIUS,
                           border_width=1, border_color=T.BORDER)
        act.pack(fill="x", pady=6)
        ctk.CTkLabel(act, text="¿Ya tienes tu clave? Pégala aquí:", font=T.FONT_SMALL,
                     text_color=T.TEXT_MUTED).pack(anchor="w", padx=16, pady=(12, 2))
        fa = ctk.CTkFrame(act, fg_color="transparent")
        fa.pack(fill="x", padx=16, pady=(0, 12))
        self.e_clave = ctk.CTkEntry(fa, height=40, fg_color=T.BG_PANEL_2,
                                    border_color=T.BORDER,
                                    placeholder_text="XXXX-XXXX-XXXX-XXXX-XXXX-X")
        self.e_clave.pack(side="left", fill="x", expand=True)
        ctk.CTkButton(fa, text="Activar", width=110, command=self._activar, height=40,
                      fg_color=T.SUCCESS, hover_color=T.SUCCESS_HOVER,
                      text_color=T.TEXT_ON_ACCENT,
                      font=(T.FONT_FAMILY, 13, "bold")).pack(side="left", padx=(10, 0))

    def _estado_texto(self, info):
        e = info["estado"]
        if e == "activo":
            return f"✅ Licencia activa — Plan {settings.PLANES.get(info.get('plan'),{}).get('nombre','')}", T.SUCCESS
        if e == "por_vencer":
            return f"⚠️ Tu licencia vence en {info['dias']} día(s)", T.WARNING
        if e == "prueba":
            return f"🕒 Periodo de prueba — te quedan {info['dias']} día(s)", T.ACCENT
        return "🔒 Sin licencia activa", T.DANGER

    def _tarjeta(self, parent, plan_key, destacado):
        p = settings.PLANES[plan_key]
        bg = T.ACCENT if destacado else T.BG_PANEL
        card = ctk.CTkFrame(parent, fg_color=bg, corner_radius=T.RADIUS,
                            border_width=2 if destacado else 1,
                            border_color=T.ACCENT if destacado else T.BORDER, width=210)
        card.pack(side="left", padx=6)
        card.pack_propagate(False)
        card.configure(height=150)
        tcol = T.TEXT_ON_ACCENT if destacado else T.TEXT
        ctk.CTkLabel(card, text=("★ " if destacado else "") + p["nombre"],
                     font=(T.FONT_FAMILY, 14, "bold"), text_color=tcol).pack(pady=(14, 0))
        ctk.CTkLabel(card, text=f"${p['precio']}", font=(T.FONT_FAMILY, 28, "bold"),
                     text_color=tcol).pack()
        extra = {"mensual": "Pago mensual", "semestral": "Ahorras $7",
                 "anual": "¡3 meses gratis!"}[plan_key]
        ctk.CTkLabel(card, text=extra, font=(T.FONT_FAMILY, 11, "bold"),
                     text_color=tcol).pack(pady=(6, 12))

    def _copiar(self, txt):
        self.clipboard_clear(); self.clipboard_append(txt)
        mb.showinfo("Copiado", "Código de equipo copiado.")

    def _correo(self, codigo):
        nombre = config_service.obtener("NOMBRE_BANCO") or "mi banco"
        asunto = f"Activar/Renovar Banquito - {nombre}"
        cuerpo = (f"Hola, quiero activar/renovar MMWBank para {nombre}.\n"
                  f"Mi código de equipo es: {codigo}")
        url = (f"mailto:{settings.CORREO_SOPORTE}"
               f"?subject={urllib.parse.quote(asunto)}&body={urllib.parse.quote(cuerpo)}")
        try:
            webbrowser.open(url)
        except Exception:
            mb.showinfo("Correo", f"Escríbenos a {settings.CORREO_SOPORTE} con tu código: {codigo}")

    def _activar(self):
        ok, msg = L.activar(self.e_clave.get())
        if ok:
            mb.showinfo("Licencia", msg)
            self._construir()
        else:
            mb.showerror("Licencia", msg)

    def refrescar(self):
        self._construir()
