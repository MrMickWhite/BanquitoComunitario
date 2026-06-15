"""Tabla con estilo moderno (ttk.Treeview) y soporte de tema claro/oscuro."""

from tkinter import ttk
import customtkinter as ctk
from ui import theme as T


class Tabla(ctk.CTkFrame):
    # Lista de tablas vivas, para re-estilizarlas al cambiar de tema.
    _instancias = []

    def __init__(self, master, columnas, anchos=None, altura=10, **kwargs):
        super().__init__(master, fg_color=T.BG_PANEL, corner_radius=T.RADIUS, **kwargs)
        self.columnas = columnas

        self._aplicar_estilo()

        self.tree = ttk.Treeview(self, columns=columnas, show="headings",
                                 height=altura, style="Banquito.Treeview")
        for i, col in enumerate(columnas):
            self.tree.heading(col, text=col)
            ancho = anchos[i] if anchos and i < len(anchos) else 120
            self.tree.column(col, width=ancho, anchor="w")

        self._configurar_zebra()

        scroll = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.pack(side="left", fill="both", expand=True, padx=6, pady=6)
        scroll.pack(side="right", fill="y", pady=6)

        Tabla._instancias.append(self)

    # ------------------------------------------------------------- estilo
    @staticmethod
    def _aplicar_estilo():
        """Configura el estilo global de la tabla según el tema actual."""
        style = ttk.Style()
        style.theme_use("default")
        bg = T.pick(T.BG_PANEL)
        style.configure(
            "Banquito.Treeview",
            background=bg, fieldbackground=bg, foreground=T.pick(T.TEXT),
            rowheight=30, borderwidth=0, font=(T.FONT_FAMILY, 10),
        )
        style.configure(
            "Banquito.Treeview.Heading",
            background=T.pick(T.BG_PANEL_2), foreground=T.pick(T.TEXT_MUTED),
            relief="flat", font=(T.FONT_FAMILY, 10, "bold"), padding=(6, 8),
        )
        style.map("Banquito.Treeview.Heading", background=[("active", T.pick(T.BG_HOVER))])
        style.map("Banquito.Treeview",
                  background=[("selected", T.ACCENT)],
                  foreground=[("selected", T.TEXT_ON_ACCENT)])

    def _configurar_zebra(self):
        self.tree.tag_configure("par", background=T.pick(T.BG_PANEL))
        self.tree.tag_configure("impar", background=T.pick(T.ROW_ALT))

    @classmethod
    def reestilizar_todas(cls):
        """Re-aplica el estilo a todas las tablas (al cambiar claro/oscuro)."""
        cls._aplicar_estilo()
        vivas = []
        for inst in cls._instancias:
            try:
                inst._configurar_zebra()
                vivas.append(inst)
            except Exception:
                pass  # tabla destruida
        cls._instancias = vivas

    # ------------------------------------------------------------- datos
    def cargar(self, filas):
        self.tree.delete(*self.tree.get_children())
        for idx, fila in enumerate(filas):
            tag = "par" if idx % 2 == 0 else "impar"
            self.tree.insert("", "end", values=fila, tags=(tag,))

    def id_seleccionado(self):
        sel = self.tree.selection()
        if not sel:
            return None
        valores = self.tree.item(sel[0])["values"]
        return valores[0] if valores else None

    def on_seleccion(self, callback):
        self.tree.bind("<<TreeviewSelect>>", lambda e: callback())
