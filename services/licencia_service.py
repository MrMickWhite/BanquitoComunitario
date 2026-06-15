"""
Servicio de Licencias — control de prueba (7 días), activación y vencimiento.

Funciona SIN internet. La clave de activación va atada al "código de equipo"
(único por PC) y a una fecha de vencimiento, firmada con una frase secreta
(settings.LICENCIA_SECRETO, que vive en config/local_secrets.py).

Estados posibles (estado_licencia()["estado"]):
  - "prueba"     -> en periodo de prueba, aún con días disponibles
  - "activo"     -> licencia válida y vigente
  - "por_vencer" -> activa pero vence en <= 15 días
  - "bloqueado"  -> prueba terminada / licencia vencida / sin activar
  - "manipulado" -> se detectó que atrasaron el reloj de la PC

La clave NUNCA depende de internet ni de un servidor.
"""

import json
import hmac
import hashlib
import platform
import uuid
from datetime import date, timedelta
from config import settings

DIAS_PRUEBA = 7
DIAS_AVISO = 5
_ESTADO_FILE = settings.DATA_DIR / "licencia.dat"


# --------------------------------------------------------------------------- #
#  Código de equipo (huella única de la PC)
# --------------------------------------------------------------------------- #
def _machine_raw() -> str:
    # En Windows usamos el MachineGuid del registro (estable). Si no, MAC + nombre.
    try:
        import winreg
        k = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                           r"SOFTWARE\Microsoft\Cryptography")
        val, _ = winreg.QueryValueEx(k, "MachineGuid")
        winreg.CloseKey(k)
        return str(val)
    except Exception:
        return f"{uuid.getnode()}-{platform.node()}"


def codigo_equipo() -> str:
    h = hashlib.sha256(_machine_raw().encode("utf-8")).hexdigest().upper()
    return f"BQ-{h[:4]}-{h[4:8]}-{h[8:12]}"


# --------------------------------------------------------------------------- #
#  Generación / validación de claves (la generación la usa tu calculadora)
# --------------------------------------------------------------------------- #
_PLAN_CHAR = {"mensual": "M", "semestral": "S", "anual": "A"}
_CHAR_PLAN = {v: k for k, v in _PLAN_CHAR.items()}


def _firma(codigo: str, plan_char: str, vence_str: str) -> str:
    secreto = (getattr(settings, "LICENCIA_SECRETO", "") or "").encode("utf-8")
    payload = f"{codigo}|{plan_char}|{vence_str}".encode("utf-8")
    return hmac.new(secreto, payload, hashlib.sha256).hexdigest().upper()


def generar_clave(codigo_equipo_cliente: str, plan: str, vence: date) -> str:
    """Genera la clave para un código de equipo + plan + fecha de vencimiento.
    (La usa el GENERADOR de licencias del proveedor.)"""
    pc = _PLAN_CHAR.get(plan, "A")
    vstr = vence.strftime("%Y%m%d")
    sig = _firma(codigo_equipo_cliente.strip().upper(), pc, vstr)[:12]
    bruto = f"{pc}{vstr}{sig}"  # 1 + 8 + 12 = 21 chars
    # Formatear en grupos de 4 para que sea fácil de leer/teclear
    return "-".join(bruto[i:i + 4] for i in range(0, len(bruto), 4))


def _parsear_clave(clave: str):
    bruto = (clave or "").replace("-", "").replace(" ", "").upper()
    if len(bruto) != 21:
        return None
    pc, vstr, sig = bruto[0], bruto[1:9], bruto[9:21]
    if pc not in _CHAR_PLAN:
        return None
    return pc, vstr, sig


def validar_clave(clave: str, codigo=None):
    """Valida una clave contra el código de equipo actual.
    Devuelve (ok, plan, fecha_vencimiento) o (False, None, None)."""
    codigo = (codigo or codigo_equipo()).strip().upper()
    p = _parsear_clave(clave)
    if not p:
        return False, None, None
    pc, vstr, sig = p
    if _firma(codigo, pc, vstr)[:12] != sig:
        return False, None, None
    try:
        vence = date(int(vstr[:4]), int(vstr[4:6]), int(vstr[6:8]))
    except Exception:
        return False, None, None
    return True, _CHAR_PLAN[pc], vence


# --------------------------------------------------------------------------- #
#  Estado guardado (archivo local)
# --------------------------------------------------------------------------- #
def _cargar():
    try:
        with open(_ESTADO_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _guardar(d):
    try:
        with open(_ESTADO_FILE, "w", encoding="utf-8") as f:
            json.dump(d, f)
    except Exception:
        pass


def _hoy():
    return date.today()


def _d(s):
    return date.fromisoformat(s) if s else None


# --------------------------------------------------------------------------- #
#  Estado de la licencia (lo consulta la app al arrancar)
# --------------------------------------------------------------------------- #
def estado_licencia() -> dict:
    st = _cargar()
    hoy = _hoy()
    codigo = codigo_equipo()

    # Primera vez: arranca la prueba
    if "instalado" not in st:
        st["instalado"] = hoy.isoformat()
        st["ultima_fecha"] = hoy.isoformat()
        _guardar(st)

    # Detección de trampa de reloj: si la fecha actual es ANTERIOR a la última vista
    ultima = _d(st.get("ultima_fecha")) or hoy
    if hoy < ultima:
        return {"estado": "manipulado", "codigo": codigo, "dias": 0,
                "vence": None, "plan": None}
    # Avanzar la última fecha vista
    if hoy > ultima:
        st["ultima_fecha"] = hoy.isoformat()
        _guardar(st)

    # ¿Está activado?
    clave = st.get("clave")
    if clave:
        ok, plan, vence = validar_clave(clave, codigo)
        if ok:
            dias = (vence - hoy).days
            if dias < 0:
                return {"estado": "bloqueado", "motivo": "vencida",
                        "codigo": codigo, "dias": 0, "vence": vence, "plan": plan}
            estado = "por_vencer" if dias <= DIAS_AVISO else "activo"
            return {"estado": estado, "codigo": codigo, "dias": dias,
                    "vence": vence, "plan": plan}
        # Clave inválida (p. ej. movieron el archivo a otra PC) -> sigue evaluando prueba

    # Prueba
    instalado = _d(st.get("instalado")) or hoy
    dias_usados = (hoy - instalado).days
    dias_rest = DIAS_PRUEBA - dias_usados
    if dias_rest > 0:
        return {"estado": "prueba", "codigo": codigo, "dias": dias_rest,
                "vence": instalado + timedelta(days=DIAS_PRUEBA), "plan": None}
    return {"estado": "bloqueado", "motivo": "prueba_terminada",
            "codigo": codigo, "dias": 0, "vence": None, "plan": None}


def activar(clave: str):
    """Activa la app con una clave. Devuelve (ok, mensaje)."""
    ok, plan, vence = validar_clave(clave)
    if not ok:
        return False, "La clave no es válida para este equipo."
    if vence < _hoy():
        return False, "Esa clave ya está vencida."
    st = _cargar()
    st["clave"] = clave.strip()
    st["plan"] = plan
    st["activado_hasta"] = vence.isoformat()
    st["ultima_fecha"] = _hoy().isoformat()
    _guardar(st)
    nombre = settings.PLANES.get(plan, {}).get("nombre", plan)
    return True, f"¡Activado! Plan {nombre}, válido hasta {vence.strftime('%d/%m/%Y')}."


def puede_entrar() -> bool:
    return estado_licencia()["estado"] in ("prueba", "activo", "por_vencer")
