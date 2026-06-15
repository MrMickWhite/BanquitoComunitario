"""
Servicio de Reportes.

Consolida la información en estructuras de datos listas para mostrar en pantalla
o enviar al generador de PDF. NO genera el PDF aquí (eso lo hace reports/),
para mantener separada la lógica de los datos del formato de salida.
"""

from repositories import (socio_repository, aporte_repository,
                          prestamo_repository, movimiento_repository)
from utils.fechas import rango_mes, rango_anio, rango_semana, NOMBRES_MESES
from services import config_service


def _resumen_caja(fecha_inicio: str, fecha_fin: str) -> dict:
    """Totales de ingresos/egresos por categoría en un periodo."""
    cats = movimiento_repository.totales_por_categoria(fecha_inicio, fecha_fin)
    return {
        "aportes":        cats.get("aporte_ingreso", 0.0),
        "prestamos_dados": cats.get("prestamo_egreso", 0.0),
        "capital_recuperado": cats.get("pago_capital_ingreso", 0.0),
        "intereses_ganados": cats.get("interes_ingreso", 0.0),
        "mora_cobrada":   cats.get("mora_ingreso", 0.0),
        "ingresos_varios": cats.get("ingreso_vario_ingreso", 0.0),
        "gastos":         cats.get("gasto_egreso", 0.0) + cats.get("egreso_vario_egreso", 0.0),
    }


def reporte_general(fecha_inicio: str, fecha_fin: str, titulo_periodo: str) -> dict:
    """Reporte consolidado de TODO el banquito en un periodo."""
    resumen = _resumen_caja(fecha_inicio, fecha_fin)
    utilidad = round(resumen["intereses_ganados"] + resumen["mora_cobrada"]
                     + resumen["ingresos_varios"] - resumen["gastos"], 2)

    # Opcional: sumar el interés ESTIMADO de los movimientos que generan interés
    interes_estimado = 0.0
    if config_service.obtener("INCLUIR_INTERES_ESTIMADO") == "1":
        from services import movimiento_service
        for m in movimiento_repository.listar_varios_periodo(fecha_inicio, fecha_fin):
            info = movimiento_service.interes_de_movimiento(m, fecha_fin)
            if info["activo"]:
                interes_estimado += info["interes"]
        interes_estimado = round(interes_estimado, 2)
        utilidad = round(utilidad + interes_estimado, 2)

    socios = socio_repository.listar()
    detalle_socios = []
    socios_full = []
    for s in socios:
        total_aportado = aporte_repository.total_por_socio(s.id)
        prestamos = prestamo_repository.listar_prestamos_por_socio(s.id)
        deuda = sum(p.saldo_capital for p in prestamos)
        detalle_socios.append({
            "socio": s.nombre_completo,
            "documento": s.documento or "",
            "aportado": round(total_aportado, 2),
            "deuda_actual": round(deuda, 2),
            "activo": "Sí" if s.activo else "No",
        })
        # Detalle por socio dentro del periodo (con descripciones)
        aportes_p = [a for a in aporte_repository.listar_por_socio(s.id)
                     if fecha_inicio <= a.fecha <= fecha_fin]
        prest_p = []
        for p in prestamos:
            if fecha_inicio <= p.fecha_otorgado <= fecha_fin:
                prest_p.append({"fecha": p.fecha_otorgado, "monto": p.monto,
                                "saldo": p.saldo_capital, "estado": p.estado,
                                "tasa": p.tasa_mensual,
                                "descripcion": p.descripcion or ""})
        if aportes_p or prest_p:
            socios_full.append({
                "socio": s.nombre_completo,
                "documento": s.documento or "",
                "aportes": [{"fecha": a.fecha, "monto": a.monto,
                             "descripcion": a.descripcion or ""} for a in aportes_p],
                "prestamos": prest_p,
            })

    # Movimientos varios del periodo (con descripciones guardadas)
    varios_detalle = [{"fecha": m.fecha, "tipo": m.tipo, "monto": m.monto,
                       "descripcion": m.descripcion or ""}
                      for m in movimiento_repository.listar_varios_periodo(
                          fecha_inicio, fecha_fin)]

    # Reparto de fin de año (propuesta): si el modo es 'reparto', se calcula la
    # parte de cada socio proporcional a lo que aportó.
    modo_fin = config_service.obtener("MODO_FIN_ANIO") or "fondo"
    reparto = []
    if modo_fin == "reparto" and utilidad > 0:
        total_aportado = sum(d["aportado"] for d in detalle_socios) or 0
        if total_aportado > 0:
            for d in detalle_socios:
                parte = round(utilidad * (d["aportado"] / total_aportado), 2)
                if parte > 0:
                    reparto.append({"socio": d["socio"], "aportado": d["aportado"],
                                    "parte": parte})

    return {
        "tipo": "general",
        "periodo": titulo_periodo,
        "fecha_inicio": fecha_inicio,
        "fecha_fin": fecha_fin,
        "resumen": resumen,
        "utilidad": utilidad,
        "interes_estimado": interes_estimado,
        "modo_fin_anio": modo_fin,
        "reparto": reparto,
        "saldo_caja": movimiento_repository.saldo_caja(),
        "socios": detalle_socios,
        "socios_detalle": socios_full,
        "varios_detalle": varios_detalle,
        "total_socios": len(socios),
    }


def reporte_por_socio(socio_id: int, fecha_inicio: str, fecha_fin: str,
                      titulo_periodo: str) -> dict:
    """Reporte individual de un socio en un periodo."""
    socio = socio_repository.obtener_por_id(socio_id)
    if socio is None:
        raise ValueError("Socio no encontrado.")

    aportes = [a for a in aporte_repository.listar_por_socio(socio_id)
               if fecha_inicio <= a.fecha <= fecha_fin]
    total_aportes_periodo = round(sum(a.monto for a in aportes), 2)
    total_aportes_historico = aporte_repository.total_por_socio(socio_id)

    prestamos = prestamo_repository.listar_prestamos_por_socio(socio_id)
    detalle_prestamos = []
    pagos_detalle = []
    total_interes_pagado = 0.0
    total_mora_pagada = 0.0
    for p in prestamos:
        pagos = prestamo_repository.listar_pagos_por_prestamo(p.id)
        interes_pagado = sum(pg.interes for pg in pagos)
        mora_pagada = sum(pg.mora for pg in pagos)
        total_interes_pagado += interes_pagado
        total_mora_pagada += mora_pagada
        detalle_prestamos.append({
            "fecha": p.fecha_otorgado,
            "monto": p.monto,
            "saldo": p.saldo_capital,
            "estado": p.estado,
            "tasa": p.tasa_mensual,
            "descripcion": p.descripcion or "",
            "interes_pagado": round(interes_pagado, 2),
            "mora_pagada": round(mora_pagada, 2),
        })
        for pg in pagos:
            if fecha_inicio <= pg.fecha <= fecha_fin:
                pagos_detalle.append({
                    "fecha": pg.fecha, "total": pg.monto_total,
                    "capital": pg.capital, "interes": pg.interes, "mora": pg.mora,
                    "descripcion": pg.descripcion or "",
                })

    return {
        "tipo": "socio",
        "periodo": titulo_periodo,
        "socio": socio.nombre_completo,
        "documento": socio.documento or "",
        "fecha_ingreso": socio.fecha_ingreso,
        "aportes_periodo": total_aportes_periodo,
        "aportes_historico": round(total_aportes_historico, 2),
        "num_aportes": len(aportes),
        "aportes_detalle": [{"fecha": a.fecha, "monto": a.monto,
                             "descripcion": a.descripcion or ""} for a in aportes],
        "prestamos": detalle_prestamos,
        "pagos_detalle": pagos_detalle,
        "deuda_actual": round(sum(p.saldo_capital for p in prestamos), 2),
        "interes_pagado": round(total_interes_pagado, 2),
        "mora_pagada": round(total_mora_pagada, 2),
    }


# --------- Atajos para periodos mensuales y anuales -------------------------
def general_mensual(anio: int, mes: int) -> dict:
    ini, fin = rango_mes(anio, mes)
    return reporte_general(ini, fin, f"{NOMBRES_MESES[mes]} {anio}")


def general_anual(anio: int) -> dict:
    ini, fin = rango_anio(anio)
    return reporte_general(ini, fin, f"Año {anio}")


def socio_mensual(socio_id: int, anio: int, mes: int) -> dict:
    ini, fin = rango_mes(anio, mes)
    return reporte_por_socio(socio_id, ini, fin, f"{NOMBRES_MESES[mes]} {anio}")


def socio_anual(socio_id: int, anio: int) -> dict:
    ini, fin = rango_anio(anio)
    return reporte_por_socio(socio_id, ini, fin, f"Año {anio}")


# Etiquetas legibles para cada categoría de movimiento
_ETIQUETAS = {
    "aporte": "Aporte",
    "prestamo": "Préstamo otorgado",
    "pago_capital": "Pago de capital",
    "interes": "Pago de interés",
    "mora": "Pago de mora",
    "gasto": "Gasto",
    "otro": "Otro",
}


def historial_socio(socio_id: int) -> list:
    """
    Devuelve la lista FECHADA de cada proceso del socio (lo más reciente primero):
    [{fecha, proceso, monto, tipo, descripcion}, ...]
    """
    movimientos = movimiento_repository.listar_por_socio(socio_id)
    historial = []
    for m in movimientos:
        historial.append({
            "fecha": m.fecha,
            "proceso": _ETIQUETAS.get(m.categoria, m.categoria),
            "monto": m.monto,
            "tipo": m.tipo,  # ingreso | egreso
            "descripcion": m.descripcion or "",
        })
    return historial


def general_semanal(fecha) -> dict:
    ini, fin = rango_semana(fecha)
    return reporte_general(ini, fin, f"Semana {ini} a {fin}")


def socio_semanal(socio_id: int, fecha) -> dict:
    ini, fin = rango_semana(fecha)
    return reporte_por_socio(socio_id, ini, fin, f"Semana {ini} a {fin}")
