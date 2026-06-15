"""Prueba de humo del backend: ejercita todo el flujo sin interfaz gráfica."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from database.connection import inicializar_base_de_datos
from config import settings
# Empezar desde cero para la prueba
if settings.DB_PATH.exists():
    settings.DB_PATH.unlink()

inicializar_base_de_datos()

from services import socio_service, aporte_service, prestamo_service, reporte_service
from reports import pdf_generator
from repositories import movimiento_repository

# 1) Socios
id1 = socio_service.agregar_socio("Ana", "García", "0102030405", "0999999999", "ana@mail.com")
id2 = socio_service.agregar_socio("Luis", "Pérez", "0203040506")
print("Socios creados:", id1, id2)

# 2) Aportes
aporte_service.registrar_aporte(id1, 100.0, "2025-01-15")
aporte_service.registrar_aporte(id1, 50.0, "2025-02-15")
aporte_service.registrar_aporte(id2, 200.0, "2025-01-20")
print("Aportes registrados. Saldo caja:", movimiento_repository.saldo_caja())

# 3) Préstamo a Luis
pid = prestamo_service.otorgar_prestamo(id2, 150.0, plazo_meses=3, fecha="2025-02-01")
print("Préstamo otorgado id:", pid, "| Saldo caja:", movimiento_repository.saldo_caja())

# 4) Deuda al cabo de un mes y un pago
deuda = prestamo_service.calcular_deuda_actual(pid, "2025-03-05")
print("Deuda al 2025-03-05:", deuda)
res = prestamo_service.registrar_pago(pid, 60.0, "2025-03-05")
print("Resultado del pago:", res)

# 5) Reportes + PDF
rep_gen = reporte_service.general_anual(2025)
print("Utilidad anual:", rep_gen["utilidad"], "| Saldo caja:", rep_gen["saldo_caja"])
ruta1 = pdf_generator.generar_reporte_general(rep_gen)
print("PDF general:", ruta1)

rep_socio = reporte_service.socio_anual(id2, 2025)
ruta2 = pdf_generator.generar_reporte_socio(rep_socio)
print("PDF socio:", ruta2)

print("\n✅ Backend OK")
