"""
Vista de Configuración, organizada en SUB-PESTAÑAS:

  🏦 General      -> nombre del banco (afecta PDF y carpeta de reportes)
  💵 Intereses    -> tasas de préstamo, mora, ahorro, aporte mínimo, gracia
  📅 Recaudación  -> método de acumulación: semanal/mensual, día y cuota
  🎨 Apariencia   -> tema claro / oscuro
"""

import tkinter.messagebox as mb
import customtkinter as ctk
from ui import theme as T
from ui.components.cards import campo, boton
from services import config_service, recaudacion_service
from utils.rutas import carpeta_reportes


class ConfigView(ctk.CTkFrame):
    def __init__(self, master, app):
        super().__init__(master, fg_color="transparent")
        self.app = app
        self._construir()
        self.refrescar()

    # ------------------------------------------------------------- construir
    def _construir(self):
        self.tabs = ctk.CTkTabview(
            self, fg_color=T.BG_PANEL, corner_radius=T.RADIUS,
            border_width=1, border_color=T.BORDER,
            segmented_button_fg_color=T.BG_PANEL_2,
            segmented_button_selected_color=T.ACCENT,
            segmented_button_selected_hover_color=T.ACCENT_HOVER,
            segmented_button_unselected_color=T.BG_PANEL_2,
            segmented_button_unselected_hover_color=T.BG_HOVER,
            text_color=T.TEXT,
        )
        self.tabs.pack(fill="both", expand=True)
        for nombre in ("🏦 General", "💵 Intereses", "⚖️ Reglas", "📅 Recaudación",
                       "🎨 Apariencia"):
            self.tabs.add(nombre)

        self._tab_general(self.tabs.tab("🏦 General"))
        self._tab_intereses(self.tabs.tab("💵 Intereses"))
        self._tab_reglas(self.tabs.tab("⚖️ Reglas"))
        self._tab_recaudacion(self.tabs.tab("📅 Recaudación"))
        self._tab_apariencia(self.tabs.tab("🎨 Apariencia"))

    def _nota(self, master, texto):
        ctk.CTkLabel(master, text=texto, font=T.FONT_SMALL, text_color=T.TEXT_DIM,
                     wraplength=760, justify="left").pack(anchor="w", padx=18, pady=(4, 12))

    # ------------------------------------------------------------ TAB General
    def _tab_general(self, tab):
        cont = ctk.CTkFrame(tab, fg_color="transparent")
        cont.pack(fill="x", padx=18, pady=(16, 6))
        c1, self.e_nombre_banco = campo(cont, "Nombre del banco / caja", 320)
        c1.grid(row=0, column=0, padx=(0, 16), sticky="w")
        boton(cont, "💾  Guardar", self._guardar_general, ancho=140).grid(
            row=0, column=1, padx=(6, 0), pady=(18, 0))

        cont2 = ctk.CTkFrame(tab, fg_color="transparent")
        cont2.pack(fill="x", padx=18, pady=(0, 6))
        c2, self.e_carpeta = campo(cont2, "Nombre de la carpeta de reportes "
                                          "(vacío = automático)", 320)
        c2.grid(row=0, column=0, padx=(0, 16), sticky="w")
        boton(cont2, "💾  Guardar carpeta", self._guardar_carpeta, ancho=160).grid(
            row=0, column=1, padx=(6, 0), pady=(18, 0))

        self.lbl_carpeta = ctk.CTkLabel(tab, text="", font=T.FONT_SMALL,
                                        text_color=T.TEXT_MUTED, wraplength=760,
                                        justify="left")
        self.lbl_carpeta.pack(anchor="w", padx=18, pady=(2, 4))

        # --- Logo del banco para los PDF ---
        cont3 = ctk.CTkFrame(tab, fg_color="transparent")
        cont3.pack(fill="x", padx=18, pady=(6, 4))
        boton(cont3, "🖼  Elegir logo del banco", self._elegir_logo, ancho=210).pack(side="left")
        boton(cont3, "Quitar logo", self._quitar_logo, color=T.BG_PANEL_2,
              hover=T.BG_HOVER, ancho=120, text_color=T.TEXT).pack(side="left", padx=(10, 0))
        self.lbl_logo = ctk.CTkLabel(tab, text="", font=T.FONT_SMALL,
                                     text_color=T.TEXT_MUTED, wraplength=760, justify="left")
        self.lbl_logo.pack(anchor="w", padx=18, pady=(2, 4))

        self._nota(tab, "El nombre del banco aparece en el título, el login y los PDF. "
                        "La carpeta de reportes se crea en el Escritorio con el nombre "
                        "que pongas. Si eliges un logo propio, aparecerá en el encabezado "
                        "de los reportes y el logo de Banquito se usará como marca de agua.")

        # --- Zona de peligro: borrar todo ---
        peligro = ctk.CTkFrame(tab, fg_color="transparent")
        peligro.pack(fill="x", padx=18, pady=(18, 6))
        ctk.CTkLabel(peligro, text="⚠️ Zona de peligro", font=T.FONT_LABEL,
                     text_color=T.DANGER).pack(anchor="w", pady=(0, 4))
        boton(peligro, "🗑 Borrar TODO e iniciar de nuevo", self._borrar_todo,
              color=T.DANGER, hover=T.DANGER_HOVER, ancho=280,
              text_color=T.TEXT_LIGHT).pack(anchor="w")
        ctk.CTkLabel(peligro, text="Elimina socios, aportes, préstamos, movimientos, "
                     "usuarios y configuración. No se puede deshacer.",
                     font=T.FONT_SMALL, text_color=T.TEXT_DIM,
                     wraplength=760, justify="left").pack(anchor="w", pady=(4, 0))

    def _elegir_logo(self):
        from tkinter import filedialog
        import shutil
        from config import settings
        ruta = filedialog.askopenfilename(
            title="Elige el logo del banco",
            filetypes=[("Imágenes", "*.png *.jpg *.jpeg")])
        if not ruta:
            return
        try:
            ext = "." + ruta.rsplit(".", 1)[-1].lower()
            destino = settings.DATA_DIR / ("logo_banco" + ext)
            shutil.copyfile(ruta, str(destino))
            config_service.guardar("LOGO_BANCO", str(destino))
            self._actualizar_logo_lbl()
            mb.showinfo("Logo", "Logo del banco actualizado. Aparecerá en los reportes PDF.")
        except Exception as ex:
            mb.showerror("Error", f"No se pudo usar esa imagen: {ex}")

    def _quitar_logo(self):
        config_service.guardar("LOGO_BANCO", "")
        self._actualizar_logo_lbl()
        mb.showinfo("Logo", "Se quitó el logo propio. Los reportes usarán el logo Banquito.")

    def _actualizar_logo_lbl(self):
        from pathlib import Path
        ruta = (config_service.obtener("LOGO_BANCO") or "").strip()
        if ruta and Path(ruta).exists():
            self.lbl_logo.configure(text=f"Logo propio: {Path(ruta).name}  (Banquito quedará como marca de agua)")
        else:
            self.lbl_logo.configure(text="Sin logo propio: los reportes usan el logo Banquito.")

    def _guardar_carpeta(self):
        config_service.guardar("NOMBRE_CARPETA_REPORTES", self.e_carpeta.get().strip())
        self._actualizar_carpeta_lbl()
        mb.showinfo("Guardado", "Nombre de la carpeta de reportes actualizado.")

    def _borrar_todo(self):
        if not mb.askyesno("Confirmar",
                           "¿Seguro que quieres BORRAR TODA la base de datos?\n"
                           "Se perderán socios, aportes, préstamos, movimientos y "
                           "usuarios. Esta acción NO se puede deshacer."):
            return
        if not mb.askyesno("Última confirmación",
                           "Esto es definitivo. ¿Continuar y empezar de cero?"):
            return
        from database.connection import reiniciar_base_de_datos
        try:
            reiniciar_base_de_datos()
        except Exception as ex:
            return mb.showerror("Error", str(ex))
        mb.showinfo("Listo", "La base de datos se borró. La aplicación se cerrará; "
                             "vuelve a abrirla para empezar de nuevo.")
        self.app.destroy()

    def _guardar_general(self):
        nombre = self.e_nombre_banco.get().strip()
        if not nombre:
            return mb.showerror("Error", "El nombre no puede estar vacío.")
        config_service.guardar("NOMBRE_BANCO", nombre)
        self._actualizar_carpeta_lbl()
        if hasattr(self.app, "actualizar_titulo"):
            self.app.actualizar_titulo()
        mb.showinfo("Guardado", "Nombre actualizado.")

    def _actualizar_carpeta_lbl(self):
        self.lbl_carpeta.configure(
            text=f"📁 Los PDF se guardan en:  {carpeta_reportes()}")

    # ---------------------------------------------------------- TAB Intereses
    def _tab_intereses(self, tab):
        cont = ctk.CTkFrame(tab, fg_color="transparent")
        cont.pack(fill="x", padx=18, pady=16)
        c1, self.e_interes = campo(cont, "Interés préstamo mensual (%)", 200)
        c2, self.e_mora = campo(cont, "Mora por día de atraso (%)", 200)
        c3, self.e_ahorro = campo(cont, "Interés ahorro anual (%)", 200)
        c4, self.e_minimo = campo(cont, "Aporte mínimo", 160)
        c5, self.e_gracia = campo(cont, "Días de gracia (mora)", 160)
        for i, c in enumerate((c1, c2, c3)):
            c.grid(row=0, column=i, padx=(0, 16), pady=6, sticky="w")
        c4.grid(row=1, column=0, padx=(0, 16), pady=6, sticky="w")
        c5.grid(row=1, column=1, padx=(0, 16), pady=6, sticky="w")
        boton(tab, "💾  Guardar intereses", self._guardar_intereses, ancho=200).pack(
            anchor="w", padx=18, pady=(2, 0))
        self._nota(tab, "Los porcentajes se ingresan como número (ej: 2 = 2%). "
                        "Aplican a los nuevos préstamos y a los cálculos de mora.")

    def _guardar_intereses(self):
        try:
            config_service.guardar("TASA_INTERES_PRESTAMO_MENSUAL",
                                   float(self.e_interes.get()) / 100.0)
            config_service.guardar("TASA_MORA_DIARIA",
                                   float(self.e_mora.get()) / 100.0)
            config_service.guardar("TASA_INTERES_AHORRO_ANUAL",
                                   float(self.e_ahorro.get()) / 100.0)
            config_service.guardar("APORTE_MINIMO", float(self.e_minimo.get()))
            config_service.guardar("DIAS_GRACIA_MORA", int(self.e_gracia.get()))
            mb.showinfo("Guardado", "Intereses actualizados correctamente.")
        except ValueError:
            mb.showerror("Error", "Revisa que los valores sean numéricos.")

    # -------------------------------------------------------------- TAB Reglas
    def _tab_reglas(self, tab):
        def _seg(master, etiqueta, valores):
            cont = ctk.CTkFrame(master, fg_color="transparent")
            ctk.CTkLabel(cont, text=etiqueta, font=T.FONT_LABEL,
                         text_color=T.TEXT_MUTED).pack(anchor="w", pady=(0, 3))
            seg = ctk.CTkSegmentedButton(
                cont, values=valores, selected_color=T.ACCENT,
                selected_hover_color=T.ACCENT_HOVER, unselected_color=T.BG_PANEL_2,
                unselected_hover_color=T.BG_HOVER, text_color=T.TEXT,
                fg_color=T.BG_PANEL_2, height=36)
            seg.pack(anchor="w")
            return cont, seg

        cont = ctk.CTkFrame(tab, fg_color="transparent")
        cont.pack(fill="x", padx=18, pady=(16, 6))
        c1, self.seg_tipo_int = _seg(cont, "Interés del préstamo",
                                     ["Sobre saldo", "Fijo sobre monto"])
        c1.grid(row=0, column=0, padx=(0, 24), pady=(0, 10), sticky="w")
        c2, self.seg_tipo_mora = _seg(cont, "Mora", ["Por día", "Fija por mes"])
        c2.grid(row=0, column=1, pady=(0, 10), sticky="w")
        c3, self.e_mora_fija = campo(cont, "Monto de mora fija (por mes)", 200)
        c3.grid(row=1, column=0, padx=(0, 24), pady=(0, 10), sticky="w")
        c4, self.seg_fin = _seg(cont, "Fin de año",
                                ["Queda en fondo", "Reparto entre socios"])
        c4.grid(row=1, column=1, pady=(0, 10), sticky="w")
        self.sw_int_est = ctk.CTkSwitch(
            cont, text="Sumar intereses estimados de movimientos a la utilidad",
            progress_color=T.ACCENT, font=T.FONT_LABEL, text_color=T.TEXT)
        self.sw_int_est.grid(row=2, column=0, columnspan=2, pady=(4, 0), sticky="w")
        boton(tab, "💾  Guardar reglas", self._guardar_reglas, ancho=190).pack(
            anchor="w", padx=18, pady=(2, 0))
        self._nota(tab,
                   "• Interés sobre saldo: se cobra solo sobre lo que aún se debe (más "
                   "justo). Fijo: sobre el monto original.\n"
                   "• Mora por día: proporcional al atraso. Fija: un monto por cada mes "
                   "de atraso.\n"
                   "• Reparto de fin de año: el reporte general anual propone repartir la "
                   "utilidad entre socios según lo aportado (no mueve dinero solo).\n"
                   "• Intereses estimados: actívalo solo si quieres verlos sumados en la "
                   "utilidad de los reportes.")

    def _guardar_reglas(self):
        config_service.guardar("TIPO_INTERES_PRESTAMO",
                               "fijo" if self.seg_tipo_int.get() == "Fijo sobre monto" else "saldo")
        config_service.guardar("TIPO_MORA",
                               "fija" if self.seg_tipo_mora.get() == "Fija por mes" else "diaria")
        try:
            config_service.guardar("MORA_FIJA_MONTO", float(self.e_mora_fija.get() or 0))
        except ValueError:
            return mb.showerror("Error", "El monto de mora fija debe ser numérico.")
        config_service.guardar("MODO_FIN_ANIO",
                               "reparto" if self.seg_fin.get() == "Reparto entre socios" else "fondo")
        config_service.guardar("INCLUIR_INTERES_ESTIMADO",
                               "1" if self.sw_int_est.get() else "")
        mb.showinfo("Guardado", "Reglas financieras actualizadas.")

    # -------------------------------------------------------- TAB Recaudación
    def _tab_recaudacion(self, tab):
        fila1 = ctk.CTkFrame(tab, fg_color="transparent")
        fila1.pack(fill="x", padx=18, pady=(16, 4))
        ctk.CTkLabel(fila1, text="Frecuencia de recaudación", font=T.FONT_LABEL,
                     text_color=T.TEXT_MUTED).pack(anchor="w", pady=(0, 4))
        self.seg_frec = ctk.CTkSegmentedButton(
            fila1, values=["Semanal", "Mensual"], command=self._toggle_frecuencia,
            selected_color=T.ACCENT, selected_hover_color=T.ACCENT_HOVER,
            unselected_color=T.BG_PANEL_2, unselected_hover_color=T.BG_HOVER,
            text_color=T.TEXT, fg_color=T.BG_PANEL_2, height=38)
        self.seg_frec.pack(anchor="w")

        fila2 = ctk.CTkFrame(tab, fg_color="transparent")
        fila2.pack(fill="x", padx=18, pady=10)

        # Día de la semana (modo semanal)
        self.cont_semana = ctk.CTkFrame(fila2, fg_color="transparent")
        ctk.CTkLabel(self.cont_semana, text="Día de la semana", font=T.FONT_LABEL,
                     text_color=T.TEXT_MUTED).pack(anchor="w", pady=(0, 3))
        self.combo_dia_semana = ctk.CTkComboBox(
            self.cont_semana, values=recaudacion_service.DIAS_SEMANA, width=160,
            height=36, corner_radius=T.RADIUS_SM, fg_color=T.BG_PANEL_2,
            border_color=T.BORDER, button_color=T.ACCENT,
            button_hover_color=T.ACCENT_HOVER)
        self.combo_dia_semana.pack()

        # Día del mes (modo mensual)
        self.cont_mes, self.e_dia_mes = campo(fila2, "Día del mes (1-31)", 140)

        # Cuota
        cont_cuota, self.e_cuota = campo(fila2, "Cuota por socio (0 = libre)", 180)
        cont_cuota.grid(row=0, column=1, padx=(16, 0), sticky="w")

        boton(tab, "💾  Guardar recaudación", self._guardar_recaudacion,
              ancho=210).pack(anchor="w", padx=18, pady=(2, 0))
        self.lbl_proxima = ctk.CTkLabel(tab, text="", font=T.FONT_SMALL,
                                        text_color=T.TEXT_MUTED)
        self.lbl_proxima.pack(anchor="w", padx=18, pady=(10, 0))
        self._nota(tab, "Define cada cuánto y qué día se acumula el dinero "
                        "(ej: todos los lunes, o el día 5 de cada mes). La cuota "
                        "es el monto esperado por socio en cada recaudación; "
                        "déjala en 0 si el aporte es libre.")

    def _toggle_frecuencia(self, valor=None):
        if (valor or self.seg_frec.get()) == "Semanal":
            self.cont_mes.grid_forget()
            self.cont_semana.grid(row=0, column=0, padx=(0, 0), sticky="w")
        else:
            self.cont_semana.grid_forget()
            self.cont_mes.grid(row=0, column=0, padx=(0, 0), sticky="w")

    def _guardar_recaudacion(self):
        try:
            frecuencia = "semanal" if self.seg_frec.get() == "Semanal" else "mensual"
            config_service.guardar("FRECUENCIA_RECAUDACION", frecuencia)
            config_service.guardar(
                "DIA_RECAUDACION_SEMANA",
                recaudacion_service.DIAS_SEMANA.index(self.combo_dia_semana.get()))
            dia_mes = int(self.e_dia_mes.get() or 1)
            if not (1 <= dia_mes <= 31):
                raise ValueError
            config_service.guardar("DIA_RECAUDACION_MES", dia_mes)
            cuota = float(self.e_cuota.get() or 0)
            if cuota < 0:
                raise ValueError
            config_service.guardar("CUOTA_RECAUDACION", cuota)
            self._actualizar_proxima_lbl()
            mb.showinfo("Guardado", "Método de recaudación actualizado.")
        except ValueError:
            mb.showerror("Error", "Revisa los valores (día 1-31, cuota numérica ≥ 0).")

    def _actualizar_proxima_lbl(self):
        self.lbl_proxima.configure(
            text=f"📅 Próxima recaudación: {recaudacion_service.descripcion()}")

    # --------------------------------------------------------- TAB Apariencia
    def _tab_apariencia(self, tab):
        fila = ctk.CTkFrame(tab, fg_color="transparent")
        fila.pack(fill="x", padx=18, pady=16)
        ctk.CTkLabel(fila, text="Tema de la aplicación", font=T.FONT_LABEL,
                     text_color=T.TEXT_MUTED).pack(side="left", padx=(0, 16))
        self.seg_tema = ctk.CTkSegmentedButton(
            fila, values=["Oscuro", "Claro"], command=self._cambiar_tema,
            selected_color=T.ACCENT, selected_hover_color=T.ACCENT_HOVER,
            unselected_color=T.BG_PANEL_2, unselected_hover_color=T.BG_HOVER,
            text_color=T.TEXT, fg_color=T.BG_PANEL_2, height=38)
        self.seg_tema.pack(side="left")
        self._nota(tab, "El tema se guarda y se aplica también en la pantalla "
                        "de inicio de sesión.")

    def _cambiar_tema(self, valor):
        self.app.cambiar_apariencia("light" if valor == "Claro" else "dark")

    # --------------------------------------------------------------- refrescar
    def refrescar(self):
        # General
        self.e_nombre_banco.delete(0, "end")
        self.e_nombre_banco.insert(0, config_service.obtener("NOMBRE_BANCO") or "")
        self.e_carpeta.delete(0, "end")
        self.e_carpeta.insert(0, config_service.obtener("NOMBRE_CARPETA_REPORTES") or "")
        self._actualizar_carpeta_lbl()
        self._actualizar_logo_lbl()
        # Intereses
        pares = [
            (self.e_interes, f"{config_service.obtener_float('TASA_INTERES_PRESTAMO_MENSUAL')*100:g}"),
            (self.e_mora,    f"{config_service.obtener_float('TASA_MORA_DIARIA')*100:g}"),
            (self.e_ahorro,  f"{config_service.obtener_float('TASA_INTERES_AHORRO_ANUAL')*100:g}"),
            (self.e_minimo,  f"{config_service.obtener_float('APORTE_MINIMO'):g}"),
            (self.e_gracia,  str(config_service.obtener_int('DIAS_GRACIA_MORA'))),
        ]
        for entry, valor in pares:
            entry.delete(0, "end")
            entry.insert(0, valor)
        # Recaudación
        frecuencia = config_service.obtener("FRECUENCIA_RECAUDACION") or "mensual"
        self.seg_frec.set("Semanal" if frecuencia == "semanal" else "Mensual")
        self.combo_dia_semana.set(
            recaudacion_service.DIAS_SEMANA[
                config_service.obtener_int("DIA_RECAUDACION_SEMANA") % 7])
        self.e_dia_mes.delete(0, "end")
        self.e_dia_mes.insert(0, str(config_service.obtener_int("DIA_RECAUDACION_MES")))
        self.e_cuota.delete(0, "end")
        self.e_cuota.insert(0, f"{config_service.obtener_float('CUOTA_RECAUDACION'):g}")
        self._toggle_frecuencia()
        self._actualizar_proxima_lbl()
        # Apariencia
        self.seg_tema.set("Claro" if config_service.obtener("APARIENCIA") == "light"
                          else "Oscuro")
        # Reglas financieras
        self.seg_tipo_int.set("Fijo sobre monto"
                              if config_service.obtener("TIPO_INTERES_PRESTAMO") == "fijo"
                              else "Sobre saldo")
        self.seg_tipo_mora.set("Fija por mes"
                               if config_service.obtener("TIPO_MORA") == "fija"
                               else "Por día")
        self.e_mora_fija.delete(0, "end")
        self.e_mora_fija.insert(0, f"{config_service.obtener_float('MORA_FIJA_MONTO'):g}")
        self.seg_fin.set("Reparto entre socios"
                         if config_service.obtener("MODO_FIN_ANIO") == "reparto"
                         else "Queda en fondo")
        if config_service.obtener("INCLUIR_INTERES_ESTIMADO") == "1":
            self.sw_int_est.select()
        else:
            self.sw_int_est.deselect()
