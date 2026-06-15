"""
Servicio de Socios: agrega validaciones de negocio sobre el repositorio.
"""

from datetime import date
from models.entidades import Socio
from repositories import socio_repository


def agregar_socio(nombres: str, apellidos: str, documento: str = "",
                  telefono: str = "", email: str = "", notas: str = "") -> int:
    if not nombres.strip() or not apellidos.strip():
        raise ValueError("Nombres y apellidos son obligatorios.")
    socio = Socio(
        nombres=nombres.strip(),
        apellidos=apellidos.strip(),
        documento=documento.strip() or None,
        telefono=telefono.strip() or None,
        email=email.strip() or None,
        fecha_ingreso=date.today().isoformat(),
        activo=1,
        notas=notas.strip() or None,
    )
    return socio_repository.crear(socio)


def eliminar_socio(socio_id: int, borrar_historial: bool = False) -> None:
    """
    Por defecto solo DESACTIVA al socio (conserva su historial, recomendado).
    Si borrar_historial=True, elimina al socio y todos sus registros.
    """
    if borrar_historial:
        socio_repository.eliminar(socio_id)
    else:
        socio_repository.desactivar(socio_id)


def listar_socios(solo_activos: bool = False):
    return socio_repository.listar(solo_activos=solo_activos)
