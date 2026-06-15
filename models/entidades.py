"""
Modelos de datos.

Usamos dataclasses: clases simples que representan una fila de cada tabla.
Esto hace el código más legible (socio.nombres) y fácil de mantener.
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Socio:
    id: Optional[int] = None
    nombres: str = ""
    apellidos: str = ""
    documento: Optional[str] = None
    telefono: Optional[str] = None
    email: Optional[str] = None
    fecha_ingreso: str = ""
    activo: int = 1
    notas: Optional[str] = None

    @property
    def nombre_completo(self) -> str:
        return f"{self.nombres} {self.apellidos}".strip()


@dataclass
class Aporte:
    id: Optional[int] = None
    socio_id: int = 0
    monto: float = 0.0
    fecha: str = ""
    tipo: str = "aporte"          # aporte | ahorro
    descripcion: Optional[str] = None


@dataclass
class Prestamo:
    id: Optional[int] = None
    socio_id: int = 0
    monto: float = 0.0
    tasa_mensual: float = 0.0
    fecha_otorgado: str = ""
    plazo_meses: int = 1
    fecha_vencimiento: Optional[str] = None
    estado: str = "activo"        # activo | pagado | mora
    saldo_capital: float = 0.0
    descripcion: Optional[str] = None


@dataclass
class Pago:
    id: Optional[int] = None
    prestamo_id: int = 0
    fecha: str = ""
    monto_total: float = 0.0
    capital: float = 0.0
    interes: float = 0.0
    mora: float = 0.0
    descripcion: Optional[str] = None


@dataclass
class Movimiento:
    id: Optional[int] = None
    fecha: str = ""
    tipo: str = ""                # ingreso | egreso
    categoria: str = ""           # aporte | prestamo | pago_capital | interes | mora | gasto | otro
    monto: float = 0.0
    socio_id: Optional[int] = None
    referencia: Optional[str] = None
    descripcion: Optional[str] = None
    genera_interes: int = 0       # 1 si este movimiento genera interés
    tasa_interes: Optional[float] = None  # tasa mensual individual (None = usar la general)
