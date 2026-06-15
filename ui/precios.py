"""
Ventana de Precios / Activación de licencia.

Diseño llamativo: FONDO BLANCO con BORDES ROJOS para que resalte.

Aparece cuando:
  • Versión de prueba o licencia por vencer (modo aviso, se puede cerrar).
  • Prueba terminada o licencia vencida (modo bloqueo, hay que activar).

Muestra los 3 planes (Anual resaltado), el código de equipo, un botón para
CONTACTAR POR CORREO y un campo para PEGAR LA CLAVE y activar.
"""

import urllib.parse
import webbrowser
import tkinter.messagebox as mb
import customtkinter as ctk

from config import settings
from services import licencia_service as L, config_service
from ui import theme as T
from utils.rutas import aplicar_icono, cargar_logo

# Paleta fija (no depende del tema, para que siempre resalte)
BLANCO   = "#FFFFFF"
ROJO     = "#D32F2F"
ROJO_OSC = "#B71C1C"
TINTA    = "#1F2937"
GRIS     = "#6B7280"
GRIS_BG  = "#F7F7F8"
ORO      = "#E0A91B"
ORO_OSC  = "#C8910F"
VERDE    = "#2E7D32"
VERDE_OSC= "#1B5E20"


class PreciosWindow(ctk.CTk):
    def __init__(self, bloqueo=True, info=None):
        super().__init__()
        self.activado = False
        self.bloqueo = bloqueo
        self.info = info or L.estado_licencia()

        nombre = config_service.obtener("NOMBRE_BANCO") or settings.NOMBRE_APP
        self.title(f"{nombre} — Licencia")
        self.configure(fg_color=ROJO)          # el borde rojo se ve alrededor
        aplicar_icono(self)
        # Pantalla completa (maximizada, conservando controles)
        self.update_idletasks()
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        self.geometry(f"{sw}x{sh}+0+0")
        try:
            self.state("zoomed")          # maximizada en Windows
        except Exception:
            pass
        if bloqueo:
            self.protocol("WM_DELETE_WINDOW", self._cerrar_bloqueo)

        # Marco blanco con borde rojo FINO
        marco = ctk.CTkFrame(self, fg_color=BLANCO, corner_radius=0,
                             border_width=1, border_color=ROJO)
        marco.pack(fill="both", expand=True)

        cont = ctk.CTkScrollableFrame(marco, fg_color=BLANCO)
        cont.pack(fill="both", expand=True, padx=16, pady=12)

        self._logo = cargar_logo((64, 64))
        if self._logo:
            ctk.CTkLabel(cont, image=self._logo, text="").pack(pady=(4, 6))
        ctk.CTkLabel(cont, text=self._titulo(), font=(T.FONT_FAMILY, 24, "bold"),
                     text_color=ROJO_OSC).pack()
        ctk.CTkLabel(cont, text=self._subtitulo(), font=(T.FONT_FAMILY, 12),
                     text_color=GRIS, wraplength=740, justify="center").pack(pady=(2, 14))

        # Tarjetas de planes
        fila = ctk.CTkFrame(cont, fg_color=BLANCO)
        fila.pack(pady=4)
        self._tarjeta(fila, "mensual", destacado=False)
        self._tarjeta(fila, "semestral", destacado=False)
        self._tarjeta(fila, "anual", destacado=True)

        # Código de equipo
        codcard = ctk.CTkFrame(cont, fg_color=GRIS_BG, corner_radius=10,
                               border_width=2, border_color=ROJO)
        codcard.pack(fill="x", pady=(18, 8))
        ctk.CTkLabel(codcard, text="Tu código de equipo (envíalo al activar):",
                     font=(T.FONT_FAMILY, 12), text_color=GRIS).pack(anchor="w", padx=16, pady=(10, 0))
        finner = ctk.CTkFrame(codcard, fg_color=GRIS_BG)
        finner.pack(fill="x", padx=16, pady=(2, 12))
        ctk.CTkLabel(finner, text=self.info["codigo"], font=(T.FONT_FAMILY, 18, "bold"),
                     text_color=ROJO_OSC).pack(side="left")
        ctk.CTkButton(finner, text="📋 Copiar", width=90, command=self._copiar_codigo,
                      fg_color=TINTA, hover_color="#374151", text_color=BLANCO).pack(side="left", padx=10)

        # Botón Correo (principal, ROJO para llamar la atención)
        ctk.CTkButton(cont, text="✉️  Contactar por correo para activar",
                      command=self._correo, height=50, fg_color=ROJO,
                      hover_color=ROJO_OSC, text_color=BLANCO,
                      font=(T.FONT_FAMILY, 15, "bold")).pack(fill="x", pady=(10, 4))

        # Campo para pegar la clave
        actcard = ctk.CTkFrame(cont, fg_color=GRIS_BG, corner_radius=10,
                               border_width=2, border_color=ROJO)
        actcard.pack(fill="x", pady=(10, 8))
        ctk.CTkLabel(actcard, text="¿Ya tienes tu clave? Pégala aquí:",
                     font=(T.FONT_FAMILY, 12), text_color=GRIS).pack(anchor="w", padx=16, pady=(12, 2))
        fa = ctk.CTkFrame(actcard, fg_color=GRIS_BG)
        fa.pack(fill="x", padx=16, pady=(0, 12))
        self.e_clave = ctk.CTkEntry(fa, height=42, fg_color=BLANCO, text_color=TINTA,
                                    border_color=ROJO, border_width=2,
                                    placeholder_text="XXXX-XXXX-XXXX-XXXX-XXXX-X")
        self.e_clave.pack(side="left", fill="x", expand=True)
        self.e_clave.bind("<Return>", lambda _e: self._activar())
        ctk.CTkButton(fa, text="Activar", width=120, command=self._activar, height=42,
                      fg_color=VERDE, hover_color=VERDE_OSC, text_color=BLANCO,
                      font=(T.FONT_FAMILY, 14, "bold")).pack(side="left", padx=(10, 0))

        if not bloqueo:
            ctk.CTkButton(cont, text="Saltar  ⏭", command=self.destroy, height=42,
                          fg_color=VERDE, hover_color=VERDE_OSC, text_color=BLANCO,
                          font=(T.FONT_FAMILY, 14, "bold")).pack(pady=(8, 2))

        ctk.CTkLabel(cont, text=f"📧 Contacto y soporte:  {settings.CORREO_SOPORTE}",
                     font=(T.FONT_FAMILY, 13, "bold"), text_color=ROJO_OSC).pack(pady=(14, 2))
        ctk.CTkLabel(cont, text="© Elaborado por MrMickWhite",
                     font=(T.FONT_FAMILY, 10), text_color=GRIS).pack(pady=(0, 4))

    # ----------------------------------------------------------------- textos
    def _titulo(self):
        est = self.info["estado"]
        if est == "manipulado":
            return "Fecha del sistema incorrecta"
        if self.bloqueo:
            return "Activa tu licencia para continuar"
        return "Planes y precios"

    def _subtitulo(self):
        est = self.info["estado"]
        if est == "manipulado":
            return ("Detectamos que la fecha de la computadora fue cambiada. Ajusta la "
                    "fecha y hora correctas del equipo para poder continuar.")
        if est == "prueba":
            return f"Estás en periodo de prueba. Te quedan {self.info['dias']} día(s). " \
                   "Elige un plan y actívalo cuando quieras."
        if est == "por_vencer":
            return f"Tu licencia vence en {self.info['dias']} día(s). Renueva para no " \
                   "perder el acceso."
        if est == "bloqueado" and self.info.get("motivo") == "vencida":
            return "Tu licencia venció. Renueva un plan para seguir usando el programa."
        return "Tu prueba terminó. Elige un plan para seguir usando el programa. " \
               "Tus datos están guardados y a salvo."

    # --------------------------------------------------------------- tarjetas
    def _tarjeta(self, parent, plan_key, destacado):
        p = settings.PLANES[plan_key]
        if destacado:
            bg, borde, tcol, scol = ORO, ORO_OSC, TINTA, "#5b4500"
        else:
            bg, borde, tcol, scol = BLANCO, ROJO, TINTA, GRIS
        card = ctk.CTkFrame(parent, fg_color=bg, corner_radius=12,
                            border_width=2, border_color=borde, width=205)
        card.pack(side="left", padx=6, pady=6)
        card.pack_propagate(False)
        card.configure(height=185)
        if destacado:
            ctk.CTkLabel(card, text="★ RECOMENDADO", font=(T.FONT_FAMILY, 11, "bold"),
                         text_color=ROJO_OSC).pack(pady=(12, 0))
        else:
            ctk.CTkLabel(card, text=" ", font=(T.FONT_FAMILY, 11)).pack(pady=(12, 0))
        ctk.CTkLabel(card, text=p["nombre"], font=(T.FONT_FAMILY, 17, "bold"),
                     text_color=tcol).pack(pady=(6, 0))
        ctk.CTkLabel(card, text=f"${p['precio']}", font=(T.FONT_FAMILY, 34, "bold"),
                     text_color=tcol).pack()
        por_mes = p["precio"] / p["meses"]
        ctk.CTkLabel(card, text=f"${por_mes:.2f} / mes", font=(T.FONT_FAMILY, 12),
                     text_color=scol).pack()
        extra = {"mensual": "Pago cada mes", "semestral": "Ahorras $7",
                 "anual": "¡3 meses gratis!"}[plan_key]
        ctk.CTkLabel(card, text=extra, font=(T.FONT_FAMILY, 12, "bold"),
                     text_color=tcol).pack(pady=(8, 12))

    # ---------------------------------------------------------------- acciones
    def _copiar_codigo(self):
        self.clipboard_clear(); self.clipboard_append(self.info["codigo"])
        mb.showinfo("Copiado", "Código de equipo copiado.")

    def _correo(self):
        nombre = config_service.obtener("NOMBRE_BANCO") or "mi banco"
        asunto = f"Activar Banquito - {nombre}"
        cuerpo = (f"Hola, quiero activar MMWBank para {nombre}.\n"
                  f"Mi código de equipo es: {self.info['codigo']}\n\n"
                  f"Plan que me interesa: (Mensual $7 / Semestral $35 / Anual $63)")
        url = (f"mailto:{settings.CORREO_SOPORTE}"
               f"?subject={urllib.parse.quote(asunto)}&body={urllib.parse.quote(cuerpo)}")
        try:
            webbrowser.open(url)
        except Exception:
            mb.showinfo("Correo", f"Escríbenos a {settings.CORREO_SOPORTE} con tu código:\n{self.info['codigo']}")

    def _activar(self):
        ok, msg = L.activar(self.e_clave.get())
        if ok:
            self.activado = True
            mb.showinfo("Licencia", msg)
            self.destroy()
        else:
            mb.showerror("Licencia", msg)

    def _cerrar_bloqueo(self):
        self.destroy()
