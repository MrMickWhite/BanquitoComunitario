"""
Servicio de Movimientos varios y Recaudación del día.

- Ingresos / egresos varios: dinero que entra o sale por conceptos que no son
  aportes ni préstamos (donaciones, multas, compra de útiles, etc.).
- Recaudación del día: registra de una sola vez la cuota configurada para todos
  los socios activos que aún no aportaron ese día.
"""

from datetime import date
from models.entidades import Movimiento
from repositories import movimiento_repository, socio_repository, aporte_repository
from services import config_service, aporte_service


def registrar_vario(tipo: str, monto: float, fecha: str = None,
                    descripcion: str = "", genera_interes: bool = False,
                    tasa_interes=None) -> int:
    """
    tipo: 'ingreso' o 'egreso'. Registra un movimiento manual en la caja.
    genera_interes: si True, este movimiento acumula interés.
    tasa_interes: tasa MENSUAL individual en fracción (ej 0.03 = 3%). Si es None
                  y genera_interes=True, se usa la tasa GENERAL de configuración.
    """
    if tipo not in ("ingreso", "egreso"):
        raise ValueError("El tipo debe ser 'ingreso' o 'egreso'.")
    if monto <= 0:
        raise ValueError("El monto debe ser mayor a 0.")
    if fecha is None:
        fecha = date.today().isoformat()
    categoria = "ingreso_vario" if tipo == "ingreso" else "egreso_vario"
    return movimiento_repository.registrar(Movimiento(
        fecha=fecha, tipo=tipo, categoria=categoria, monto=monto,
        socio_id=None, referencia="vario",
        descripcion=descripcion or ("Ingreso vario" if tipo == "ingreso" else "Egreso vario"),
        genera_interes=1 if genera_interes else 0,
        tasa_interes=tasa_interes,
    ))


def interes_de_movimiento(mov, fecha=None) -> dict:
    """
    Calcula el interés acumulado de un movimiento hasta 'fecha'.
    Devuelve {activo, tasa, origen, interes}:
      - activo: si el movimiento genera interés.
      - tasa: tasa mensual aplicada (individual o general).
      - origen: 'individual' | 'general' | '—'.
      - interes: monto de interés acumulado a la fecha.
    Usa la tasa individual del movimiento si la tiene; si no, la GENERAL
    (Configuración → Intereses: tasa de préstamo mensual).
    """
    from services import interes_service, config_service
    if fecha is None:
        fecha = date.today().isoformat()
    if not getattr(mov, "genera_interes", 0):
        return {"activo": False, "tasa": 0.0, "origen": "—", "interes": 0.0}
    if mov.tasa_interes is not None:
        tasa = float(mov.tasa_interes)
        origen = "individual"
    else:
        tasa = config_service.obtener_float("TASA_INTERES_PRESTAMO_MENSUAL")
        origen = "general"
    interes = interes_service.interes_acumulado(mov.monto, tasa, mov.fecha, fecha)
    return {"activo": True, "tasa": tasa, "origen": origen, "interes": interes}


def listar_varios(limite: int = 100):
    return movimiento_repository.listar_varios_recientes(limite)


def eliminar_vario(mov_id: int) -> None:
    movimiento_repository.eliminar(mov_id)


def registrar_recaudacion_del_dia(fecha: str = None) -> dict:
    """
    Registra la cuota configurada para todos los socios activos que NO hayan
    aportado en esa fecha. Devuelve un resumen con cuántos se cobraron y la lista
    de los que ya habían aportado (omitidos).
    """
    if fecha is None:
        fecha = date.today().isoformat()
    cuota = config_service.obtener_float("CUOTA_RECAUDACION")
    if cuota <= 0:
        raise ValueError("No hay una cuota configurada (Configuración → Recaudación).")

    cobrados, omitidos = [], []
    for s in socio_repository.listar(solo_activos=True):
        ya = any(a.fecha == fecha for a in aporte_repository.listar_por_socio(s.id))
        if ya:
            omitidos.append(s.nombre_completo)
            continue
        aporte_service.registrar_aporte(s.id, cuota, fecha, tipo="aporte",
                                        descripcion="Recaudación del día")
        cobrados.append(s.nombre_completo)
    return {"cuota": cuota, "fecha": fecha, "cobrados": cobrados, "omitidos": omitidos}


# --------------------------- Cuadre de caja / Caja chica ---------------------
def resumen_caja_total() -> dict:
    """Resumen para el Cuadre de caja: saldo, ingresos, egresos y desglose."""
    saldo = movimiento_repository.saldo_caja()
    ingresos, egresos = movimiento_repository.totales_globales()
    cats = movimiento_repository.totales_por_categoria("0001-01-01", "9999-12-31")
    return {"saldo": saldo, "ingresos": ingresos, "egresos": egresos,
            "categorias": cats}


def registrar_ajuste(diferencia: float, fecha: str = None) -> int:
    """
    Registra un ajuste de arqueo. diferencia = efectivo_contado - saldo_sistema.
      > 0  -> sobrante: ingreso de ajuste.
      < 0  -> faltante: egreso de ajuste.
    """
    if abs(diferencia) < 0.005:
        raise ValueError("No hay diferencia para ajustar.")
    if diferencia > 0:
        return registrar_vario("ingreso", round(diferencia, 2), fecha,
                               "Ajuste de arqueo (sobrante)")
    return registrar_vario("egreso", round(-diferencia, 2), fecha,
                           "Ajuste de arqueo (faltante)")


def registrar_gasto_caja_chica(monto: float, fecha: str = None,
                               descripcion: str = "") -> int:
    """Registra un gasto pagado con la caja chica (egreso marcado)."""
    desc = f"[Caja chica] {descripcion}".strip()
    return registrar_vario("egreso", monto, fecha, desc)


def estado_caja_chica() -> dict:
    """Fondo asignado, gastado y disponible de la caja chica."""
    from services import config_service
    fondo = config_service.obtener_float("CAJA_CHICA_FONDO")
    gastado = movimiento_repository.total_caja_chica()
    return {"fondo": fondo, "gastado": gastado,
            "disponible": round(fondo - gastado, 2)}
