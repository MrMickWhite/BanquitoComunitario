"""
Generador de PDF de reportes — diseño corporativo/bancario.

Mantiene la MISMA lógica de datos (recibe los dicts de reporte_service) y
expone las mismas funciones públicas:
    generar_reporte_general(datos) -> ruta
    generar_reporte_socio(datos)   -> ruta

Mejoras visuales:
  • Encabezado corporativo con logo y banda de color en cada página.
  • Tarjetas de resumen (KPIs).
  • Tablas modernas (sin apariencia de Excel: líneas finas, filas alternas).
  • Pie de página con numeración "Página X de Y".
  • Marca de agua con el logo Banquito cuando el banco usa su propio logo.
  • El Reporte General tiene estilo ejecutivo (con bloque de firmas) y el
    Estado de Cuenta del socio tiene estilo de extracto bancario.

Para FUTUROS reportes (caja, préstamos, mora, auditoría) usa la función
`construir_documento(...)` con su lista de flowables: ya hereda encabezado,
pie, numeración y marca de agua.
"""

from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.lib.enums import TA_LEFT, TA_RIGHT, TA_CENTER
from reportlab.pdfgen import canvas as _canvas
from reportlab.platypus import (BaseDocTemplate, PageTemplate, Frame, Table,
                                TableStyle, Paragraph, Spacer, KeepTogether)
from config import settings

# --------------------------------------------------------------------------- #
#  Paleta corporativa (combina con el logo verde/dorado)
# --------------------------------------------------------------------------- #
PRIMARY      = colors.HexColor("#2E5D43")   # verde corporativo
PRIMARY_DARK = colors.HexColor("#244A35")
GOLD         = colors.HexColor("#C19A3E")   # dorado (acentos)
GOLD_SOFT    = colors.HexColor("#F3ECD9")   # dorado muy claro (filas/realces)
INK          = colors.HexColor("#2B2B2B")   # texto principal
MUTED        = colors.HexColor("#6B7280")   # texto secundario
LINE         = colors.HexColor("#E3E6E8")   # líneas finas
CARD_BG      = colors.HexColor("#F4F7F4")   # fondo de tarjetas claras
WHITE        = colors.white

PAGE_W, PAGE_H = A4
ML = MR = 1.6 * cm           # márgenes laterales
HEADER_H = 2.6 * cm          # alto de la banda superior
TOP_MARGIN = 3.2 * cm        # el cuerpo empieza debajo de la banda
BOTTOM_MARGIN = 2.0 * cm

# --------------------------------------------------------------------------- #
#  Estilos de texto
# --------------------------------------------------------------------------- #
_ss = getSampleStyleSheet()
S_TITULO = ParagraphStyle("t", parent=_ss["Title"], textColor=PRIMARY_DARK, fontSize=15, spaceAfter=2)
S_SUB    = ParagraphStyle("s", parent=_ss["Normal"], textColor=MUTED, fontSize=9.5)
S_SECC   = ParagraphStyle("sec", parent=_ss["Heading2"], textColor=PRIMARY_DARK, fontSize=11.5, spaceBefore=4, spaceAfter=2)
S_BODY   = ParagraphStyle("b", parent=_ss["Normal"], textColor=INK, fontSize=9, leading=12)
S_CELL   = ParagraphStyle("c", parent=_ss["Normal"], textColor=INK, fontSize=8.2, leading=10)
S_CELLR  = ParagraphStyle("cr", parent=S_CELL, alignment=TA_RIGHT)
S_TH     = ParagraphStyle("th", parent=_ss["Normal"], textColor=WHITE, fontSize=8.4, leading=10, fontName="Helvetica-Bold")
S_THR    = ParagraphStyle("thr", parent=S_TH, alignment=TA_RIGHT)
S_CARD_L = ParagraphStyle("cl", parent=_ss["Normal"], textColor=MUTED, fontSize=8)
S_CARD_V = ParagraphStyle("cv", parent=_ss["Normal"], textColor=PRIMARY_DARK, fontSize=15, fontName="Helvetica-Bold", leading=17)
S_CARD_LW= ParagraphStyle("clw", parent=_ss["Normal"], textColor=colors.HexColor("#DDEEE3"), fontSize=8)
S_CARD_VW= ParagraphStyle("cvw", parent=_ss["Normal"], textColor=WHITE, fontSize=15, fontName="Helvetica-Bold", leading=17)


def _money(v) -> str:
    try:
        return f"{settings.SIMBOLO_MONEDA}{float(v):,.2f}"
    except Exception:
        return str(v)


def _p(texto, style=S_CELL):
    return Paragraph(str(texto if texto is not None else ""), style)


# --------------------------------------------------------------------------- #
#  Logos / marca de agua
# --------------------------------------------------------------------------- #
def _logo_encabezado() -> str:
    """Logo a usar en el encabezado: el propio del banco si lo configuró, si no
    el de Banquito."""
    try:
        from services import config_service
        propio = (config_service.obtener("LOGO_BANCO") or "").strip()
        from pathlib import Path
        if propio and Path(propio).exists():
            return propio
    except Exception:
        pass
    return str(settings.LOGO_PNG) if settings.LOGO_PNG.exists() else None


def _usa_logo_propio() -> bool:
    try:
        from services import config_service
        from pathlib import Path
        propio = (config_service.obtener("LOGO_BANCO") or "").strip()
        return bool(propio and Path(propio).exists())
    except Exception:
        return False


def _watermark_path():
    """Genera (una vez) una versión tenue del logo Banquito para marca de agua."""
    try:
        from PIL import Image
        if not settings.LOGO_PNG.exists():
            return None
        wm = settings.DATA_DIR / "_wm_banquito.png"
        if not wm.exists():
            img = Image.open(settings.LOGO_PNG).convert("RGBA")
            alpha = img.split()[3].point(lambda a: int(a * 0.06))
            img.putalpha(alpha)
            img.save(wm)
        return str(wm)
    except Exception:
        return None


# --------------------------------------------------------------------------- #
#  Canvas con encabezado, pie y numeración "Página X de Y"
# --------------------------------------------------------------------------- #
class _ReportCanvas(_canvas.Canvas):
    meta = {}  # {"banco":..., "titulo":..., "logo":..., "watermark":...}

    def __init__(self, *a, **k):
        super().__init__(*a, **k)
        self._saved = []

    def showPage(self):
        self._saved.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        total = len(self._saved)
        for st in self._saved:
            self.__dict__.update(st)
            self._dibujar_adornos(total)
            super().showPage()
        super().save()

    def _dibujar_adornos(self, total):
        m = _ReportCanvas.meta
        # ---- Marca de agua (solo si el banco usa logo propio) ----
        wm = m.get("watermark")
        if wm:
            try:
                self.drawImage(wm, PAGE_W/2 - 6*cm, PAGE_H/2 - 6*cm, 12*cm, 12*cm,
                               mask="auto", preserveAspectRatio=True)
            except Exception:
                pass
        # ---- Banda superior ----
        self.setFillColor(PRIMARY)
        self.rect(0, PAGE_H - HEADER_H, PAGE_W, HEADER_H, fill=1, stroke=0)
        self.setFillColor(GOLD)
        self.rect(0, PAGE_H - HEADER_H - 0.10*cm, PAGE_W, 0.10*cm, fill=1, stroke=0)
        # Logo dentro de un recuadro blanco para que se vea limpio
        logo = m.get("logo")
        tx = ML
        if logo:
            try:
                s = 1.7*cm
                ly = PAGE_H - HEADER_H + (HEADER_H - s)/2
                self.setFillColor(WHITE)
                self.roundRect(ML, ly, s, s, 4, fill=1, stroke=0)
                self.drawImage(logo, ML+1.5, ly+1.5, s-3, s-3,
                               mask="auto", preserveAspectRatio=True)
                tx = ML + s + 0.4*cm
            except Exception:
                tx = ML
        # Nombre del banco + título del reporte
        self.setFillColor(WHITE)
        self.setFont("Helvetica-Bold", 14)
        self.drawString(tx, PAGE_H - HEADER_H + 1.45*cm, m.get("banco", "")[:46])
        self.setFont("Helvetica", 9.5)
        self.setFillColor(GOLD_SOFT)
        self.drawString(tx, PAGE_H - HEADER_H + 0.85*cm, m.get("titulo", ""))
        # Fecha de generación (derecha)
        self.setFont("Helvetica", 8)
        self.setFillColor(GOLD_SOFT)
        gen = datetime.now().strftime("Generado: %d/%m/%Y %H:%M")
        self.drawRightString(PAGE_W - MR, PAGE_H - HEADER_H + 0.65*cm, gen)
        # ---- Pie de página ----
        self.setStrokeColor(LINE)
        self.setLineWidth(0.5)
        self.line(ML, 1.5*cm, PAGE_W - MR, 1.5*cm)
        self.setFont("Helvetica", 7.5)
        self.setFillColor(MUTED)
        self.drawString(ML, 1.05*cm, f"{m.get('banco','')} · Documento generado por el sistema")
        self.drawCentredString(PAGE_W/2, 1.05*cm, f"Página {self._pageNumber} de {total}")
        self.drawRightString(PAGE_W - MR, 1.05*cm, "Elaborado por MrMickWhite")


def construir_documento(ruta, titulo_reporte, flowables):
    """Arma el PDF con encabezado, pie, numeración y marca de agua comunes."""
    from services import config_service
    banco = config_service.obtener("NOMBRE_BANCO") or settings.NOMBRE_ORGANIZACION
    _ReportCanvas.meta = {
        "banco": banco,
        "titulo": titulo_reporte,
        "logo": _logo_encabezado(),
        "watermark": _watermark_path() if _usa_logo_propio() else None,
    }
    doc = BaseDocTemplate(
        str(ruta), pagesize=A4, leftMargin=ML, rightMargin=MR,
        topMargin=TOP_MARGIN, bottomMargin=BOTTOM_MARGIN,
        title=titulo_reporte, author="MrMickWhite")
    frame = Frame(ML, BOTTOM_MARGIN, PAGE_W - ML - MR,
                  PAGE_H - TOP_MARGIN - BOTTOM_MARGIN, id="cuerpo")
    doc.addPageTemplates([PageTemplate(id="principal", frames=[frame])])
    doc.build(flowables, canvasmaker=_ReportCanvas)
    return str(ruta)


# --------------------------------------------------------------------------- #
#  Componentes reutilizables
# --------------------------------------------------------------------------- #
def _seccion(titulo):
    """Título de sección con barra dorada a la izquierda."""
    barra = Table([[ "", _p(titulo, S_SECC)]], colWidths=[0.16*cm, None])
    barra.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, 0), GOLD),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (1, 0), (1, 0), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
    ]))
    return barra


def _card(label, value, resaltado=False):
    """Una tarjeta KPI (tabla de una celda con esquinas redondeadas)."""
    if resaltado:
        cont = [[_p(label, S_CARD_LW)], [_p(value, S_CARD_VW)]]
        bg = PRIMARY
    else:
        cont = [[_p(label, S_CARD_L)], [_p(value, S_CARD_V)]]
        bg = CARD_BG
    t = Table(cont, colWidths=[None])
    estilo = [
        ("BACKGROUND", (0, 0), (-1, -1), bg),
        ("LEFTPADDING", (0, 0), (-1, -1), 9),
        ("RIGHTPADDING", (0, 0), (-1, -1), 9),
        ("TOPPADDING", (0, 0), (0, 0), 8),
        ("BOTTOMPADDING", (0, -1), (-1, -1), 8),
        ("TOPPADDING", (0, 1), (-1, 1), 0),
    ]
    if not resaltado:
        estilo.append(("LINEBELOW", (0, 0), (-1, 0), 0, bg))
        estilo.append(("BOX", (0, 0), (-1, -1), 0.5, LINE))
    try:
        estilo.append(("ROUNDEDCORNERS", [5, 5, 5, 5]))
    except Exception:
        pass
    t.setStyle(TableStyle(estilo))
    return t


def _fila_cards(cards):
    """Coloca varias tarjetas en una fila con separación entre ellas."""
    celdas, anchos = [], []
    ancho_util = PAGE_W - ML - MR
    gap = 0.3 * cm
    n = len(cards)
    card_w = (ancho_util - gap * (n - 1)) / n
    for i, c in enumerate(cards):
        celdas.append(c)
        anchos.append(card_w)
        if i < n - 1:
            celdas.append("")
            anchos.append(gap)
    t = Table([celdas], colWidths=anchos)
    t.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))
    return t


def _tabla(headers, filas, col_widths, alineaciones=None):
    """Tabla moderna: cabecera verde, filas alternas suaves, líneas finas."""
    head = []
    for i, h in enumerate(headers):
        izq = not alineaciones or alineaciones[i] == "L"
        head.append(_p(h, S_TH if izq else S_THR))
    data = [head]
    for fila in filas:
        celdas = []
        for i, val in enumerate(fila):
            izq = not alineaciones or alineaciones[i] == "L"
            if hasattr(val, "wrapOn"):       # ya es Paragraph
                celdas.append(val)
            else:
                celdas.append(_p(val, S_CELL if izq else S_CELLR))
        data.append(celdas)
    t = Table(data, colWidths=col_widths, repeatRows=1)
    estilo = [
        ("BACKGROUND", (0, 0), (-1, 0), PRIMARY),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, CARD_BG]),
        ("LINEBELOW", (0, 0), (-1, 0), 0.6, PRIMARY_DARK),
        ("LINEBELOW", (0, 1), (-1, -1), 0.3, LINE),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
    ]
    t.setStyle(TableStyle(estilo))
    return t


def _firmas():
    """Bloque de firmas para el reporte ejecutivo."""
    linea = "_______________________"
    fila = [[_p(linea, S_BODY), "", _p(linea, S_BODY), "", _p(linea, S_BODY)],
            [_p("Elaborado por", S_SUB), "", _p("Revisado por", S_SUB), "",
             _p("Aprobado por", S_SUB)]]
    t = Table(fila, colWidths=[5*cm, 0.6*cm, 5*cm, 0.6*cm, 5*cm])
    t.setStyle(TableStyle([
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("TOPPADDING", (0, 0), (-1, 0), 10),
        ("TOPPADDING", (0, 1), (-1, 1), 2),
    ]))
    return t


# --------------------------------------------------------------------------- #
#  REPORTE GENERAL (estilo ejecutivo)
# --------------------------------------------------------------------------- #
def generar_reporte_general(datos: dict) -> str:
    from utils.rutas import carpeta_reportes
    ruta = carpeta_reportes() / f"reporte_general_{datos['fecha_inicio']}_a_{datos['fecha_fin']}.pdf"

    r = datos["resumen"]
    el = []
    el.append(_p("Reporte General Ejecutivo", S_TITULO))
    el.append(_p(f"Periodo: {datos['periodo']}", S_SUB))
    el.append(Spacer(1, 0.35*cm))

    # KPIs principales
    el.append(_fila_cards([
        _card("Saldo en caja", _money(datos["saldo_caja"]), resaltado=True),
        _card("Utilidad del periodo", _money(datos["utilidad"]), resaltado=True),
        _card("Socios", str(datos["total_socios"])),
    ]))
    el.append(Spacer(1, 0.3*cm))
    el.append(_fila_cards([
        _card("Aportes recibidos", _money(r["aportes"])),
        _card("Capital recuperado", _money(r["capital_recuperado"])),
        _card("Intereses ganados", _money(r["intereses_ganados"])),
        _card("Mora cobrada", _money(r["mora_cobrada"])),
    ]))
    el.append(Spacer(1, 0.5*cm))

    # Detalle financiero
    el.append(_seccion("Resumen financiero del periodo"))
    el.append(Spacer(1, 0.15*cm))
    filas = [
        ["Aportes recibidos", _money(r["aportes"])],
        ["Préstamos otorgados", _money(r["prestamos_dados"])],
        ["Capital recuperado", _money(r["capital_recuperado"])],
        ["Intereses ganados", _money(r["intereses_ganados"])],
        ["Mora cobrada", _money(r["mora_cobrada"])],
        ["Ingresos varios", _money(r.get("ingresos_varios", 0.0))],
        ["Gastos", _money(r["gastos"])],
        ["Utilidad del periodo", _money(datos["utilidad"])],
        ["Saldo en caja", _money(datos["saldo_caja"])],
    ]
    tt = _tabla(["Concepto", "Monto"], filas, [None, 4.5*cm], ["L", "R"])
    tt.setStyle(TableStyle([
        ("BACKGROUND", (0, len(filas)-1), (-1, len(filas)), GOLD_SOFT),
        ("FONTNAME", (0, len(filas)-1), (-1, len(filas)), "Helvetica-Bold"),
    ]))
    el.append(tt)
    el.append(Spacer(1, 0.5*cm))

    # Socios
    el.append(_seccion(f"Socios ({datos['total_socios']})"))
    el.append(Spacer(1, 0.15*cm))
    filas = [[s["socio"], s["documento"], _money(s["aportado"]),
              _money(s["deuda_actual"]), s["activo"]] for s in datos["socios"]]
    el.append(_tabla(["Socio", "C.I. / DNI", "Aportado", "Deuda", "Activo"], filas,
                     [None, 3*cm, 2.6*cm, 2.6*cm, 1.6*cm], ["L", "L", "R", "R", "L"]))

    # Movimientos varios
    varios = datos.get("varios_detalle", [])
    if varios:
        el.append(Spacer(1, 0.5*cm))
        el.append(_seccion("Ingresos / egresos varios"))
        el.append(Spacer(1, 0.15*cm))
        filas = [[m["fecha"], "Ingreso" if m["tipo"] == "ingreso" else "Egreso",
                  _money(m["monto"]), _p(m["descripcion"])] for m in varios]
        el.append(_tabla(["Fecha", "Tipo", "Monto", "Descripción"], filas,
                         [2.5*cm, 2*cm, 2.6*cm, None], ["L", "L", "R", "L"]))

    # Detalle por socio
    sf = datos.get("socios_detalle", [])
    if sf:
        el.append(Spacer(1, 0.5*cm))
        el.append(_seccion("Detalle por socio"))
        for sd in sf:
            el.append(Spacer(1, 0.2*cm))
            cab = sd["socio"] + (f"   ·   C.I./DNI: {sd['documento']}" if sd["documento"] else "")
            el.append(_p(cab, ParagraphStyle("h", parent=S_BODY,
                       fontName="Helvetica-Bold", fontSize=10, textColor=PRIMARY_DARK)))
            if sd["aportes"]:
                el.append(Spacer(1, 0.1*cm))
                fa = [[a["fecha"], _money(a["monto"]), _p(a["descripcion"])] for a in sd["aportes"]]
                el.append(_tabla(["Aporte · Fecha", "Monto", "Descripción"], fa,
                                 [3*cm, 2.6*cm, None], ["L", "R", "L"]))
            if sd["prestamos"]:
                el.append(Spacer(1, 0.1*cm))
                fp = [[p["fecha"], _money(p["monto"]), _money(p["saldo"]),
                       f"{p['tasa']*100:g}%", p["estado"], _p(p["descripcion"])]
                      for p in sd["prestamos"]]
                el.append(_tabla(["Préstamo · Fecha", "Monto", "Saldo", "Tasa", "Estado", "Descripción"],
                                 fp, [2.6*cm, 2*cm, 2*cm, 1.3*cm, 1.8*cm, None],
                                 ["L", "R", "R", "R", "L", "L"]))

    # Reparto de fin de año
    reparto = datos.get("reparto", [])
    if reparto:
        el.append(Spacer(1, 0.5*cm))
        el.append(_seccion("Reparto de utilidades (propuesta)"))
        el.append(_p("Distribución proporcional a lo aportado por cada socio. Es una "
                     "propuesta para que la directiva la apruebe; no mueve dinero por "
                     "sí sola.", S_BODY))
        el.append(Spacer(1, 0.15*cm))
        fr = [[x["socio"], _money(x["aportado"]), _money(x["parte"])] for x in reparto]
        el.append(_tabla(["Socio", "Aportado", "Parte propuesta"], fr,
                         [None, 3.5*cm, 3.5*cm], ["L", "R", "R"]))

    # Firmas
    el.append(Spacer(1, 1.0*cm))
    el.append(_firmas())

    return construir_documento(ruta, "Reporte General", el)


# --------------------------------------------------------------------------- #
#  ESTADO DE CUENTA DEL SOCIO (estilo extracto bancario)
# --------------------------------------------------------------------------- #
def generar_reporte_socio(datos: dict) -> str:
    from utils.rutas import carpeta_reportes
    safe = "".join(c for c in datos["socio"] if c.isalnum() or c in " _-").strip().replace(" ", "_")
    ruta = carpeta_reportes() / f"estado_cuenta_{safe}_{datos['periodo'].replace(' ', '_')}.pdf"

    el = []
    el.append(_p("Estado de Cuenta", S_TITULO))
    el.append(_p(f"Periodo: {datos['periodo']}", S_SUB))
    el.append(Spacer(1, 0.35*cm))

    # Bloque de titular (estilo extracto)
    info = [
        [_p("Socio", S_CARD_L), _p(datos["socio"], ParagraphStyle("v", parent=S_BODY, fontName="Helvetica-Bold")),
         _p("C.I. / DNI", S_CARD_L), _p(datos["documento"] or "—", S_BODY)],
        [_p("Fecha de ingreso", S_CARD_L), _p(datos["fecha_ingreso"], S_BODY),
         _p("Aportes (histórico)", S_CARD_L), _p(_money(datos["aportes_historico"]), S_BODY)],
    ]
    ti = Table(info, colWidths=[3.2*cm, None, 3.2*cm, 4*cm])
    ti.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), CARD_BG),
        ("BOX", (0, 0), (-1, -1), 0.5, LINE),
        ("INNERGRID", (0, 0), (-1, -1), 0.3, LINE),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
    ]))
    el.append(ti)
    el.append(Spacer(1, 0.4*cm))

    # KPIs del socio
    el.append(_fila_cards([
        _card("Aportes del periodo", _money(datos["aportes_periodo"]), resaltado=True),
        _card("Deuda actual", _money(datos["deuda_actual"]), resaltado=True),
        _card("Interés pagado", _money(datos["interes_pagado"])),
        _card("Mora pagada", _money(datos["mora_pagada"])),
    ]))
    el.append(Spacer(1, 0.5*cm))

    # Aportes
    el.append(_seccion("Aportes del periodo"))
    el.append(Spacer(1, 0.15*cm))
    ad = datos.get("aportes_detalle", [])
    if ad:
        fa = [[a["fecha"], _money(a["monto"]), _p(a["descripcion"])] for a in ad]
        el.append(_tabla(["Fecha", "Monto", "Descripción"], fa,
                         [3*cm, 2.6*cm, None], ["L", "R", "L"]))
    else:
        el.append(_p("Sin aportes en el periodo.", S_BODY))
    el.append(Spacer(1, 0.45*cm))

    # Préstamos
    if datos["prestamos"]:
        el.append(_seccion("Préstamos"))
        el.append(Spacer(1, 0.15*cm))
        fp = [[p["fecha"], _money(p["monto"]), _money(p["saldo"]),
               f"{p.get('tasa', 0)*100:g}%", p["estado"],
               _money(p["interes_pagado"]), _money(p["mora_pagada"])]
              for p in datos["prestamos"]]
        el.append(_tabla(["Fecha", "Monto", "Saldo", "Tasa", "Estado", "Int. pag.", "Mora pag."],
                         fp, [2.1*cm, 2*cm, 2*cm, 1.3*cm, 1.7*cm, 2*cm, 2*cm],
                         ["L", "R", "R", "R", "L", "R", "R"]))
    else:
        el.append(_seccion("Préstamos"))
        el.append(Spacer(1, 0.1*cm))
        el.append(_p("Sin préstamos en el historial.", S_BODY))

    # Pagos
    pd = datos.get("pagos_detalle", [])
    if pd:
        el.append(Spacer(1, 0.45*cm))
        el.append(_seccion("Pagos del periodo"))
        el.append(Spacer(1, 0.15*cm))
        fpg = [[pg["fecha"], _money(pg["total"]), _money(pg["capital"]),
                _money(pg["interes"]), _money(pg["mora"]), _p(pg["descripcion"])]
               for pg in pd]
        el.append(_tabla(["Fecha", "Total", "Capital", "Interés", "Mora", "Descripción"],
                         fpg, [2.1*cm, 2*cm, 2*cm, 1.8*cm, 1.8*cm, None],
                         ["L", "R", "R", "R", "R", "L"]))

    el.append(Spacer(1, 0.8*cm))
    el.append(_p("Este documento es un extracto informativo de su cuenta. Para cualquier "
                 "aclaración, contacte con la directiva de la entidad.", S_SUB))

    return construir_documento(ruta, "Estado de Cuenta de Socio", el)
