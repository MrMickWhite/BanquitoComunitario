# 🏦 Banquito — Sistema de Gestión de Caja de Ahorro y Crédito Comunitario

**Banquito** es una aplicación de escritorio para administrar **cajas de ahorro y
crédito comunitario** (bancos comunales, cooperativas pequeñas, cajas solidarias).
Funciona **sin internet**, guarda todo localmente y genera **reportes PDF con
apariencia profesional**.

Pensado para gente no técnica: se instala como un programa normal de Windows, con
su icono en el escritorio, y todo se opera con clics y en español.

---

## ✨ Características

- **Socios**: registro con C.I./DNI, activación, historial.
- **Aportes**: registro de ahorros, con opción de que generen interés.
- **Préstamos**: otorgamiento con tasa configurable, pagos, y cálculo automático
  de **interés** y **mora**.
- **Movimientos varios**: ingresos y egresos fuera de socios.
- **Cuadre de caja**: arqueo, desglose y caja chica.
- **Reportes PDF profesionales**:
  - *Reporte General Ejecutivo* (para la directiva).
  - *Estado de Cuenta de Socio* (estilo extracto bancario).
  - Encabezado corporativo con **logo configurable**, tarjetas de resumen,
    tablas modernas, numeración de páginas y firmas.
- **Reglas financieras configurables**: tipo de interés (sobre saldo o fijo),
  tipo de mora (diaria o fija), reparto de fin de año, etc.
- **Login local seguro**: contraseñas cifradas (PBKDF2 + salt), usuario
  administrador y recuperación por código.
- **Interfaz** moderna en modo **claro/oscuro**, en español.

> 100% local: no requiere internet, ni servidores, ni servicios externos.

---

## 🧩 Tecnología

Python · CustomTkinter (interfaz) · SQLite (base de datos, un solo archivo) ·
ReportLab (PDF) · Pillow (imágenes).

Arquitectura modular por capas: `models`, `repositories`, `services`, `ui`.

---

## ✅ Requisitos (solo para desarrollar/compilar)

- **Python 3.10 o superior**
- En Linux, el paquete del sistema `python3-tk` (en Windows y macOS ya viene).

## 🚀 Ejecutar desde el código

```bash
pip install -r requirements.txt
python main.py
```

La primera vez se crea sola la base de datos en `data/banquito.db` y se pide el
**nombre del banco/caja** (una sola vez).

---

## 🔐 Acceso y cuentas

- **Usuario inicial:** `usuario` / `usuario`. Al entrar la primera vez, el
  sistema **obliga a crear tu propio usuario y contraseña**.
- **Administrador:** definido en `config/local_secrets.py` (ver más abajo).
- **Recuperación de contraseña:** desde "¿Olvidaste tu contraseña?", con un
  **código fijo** que el proveedor entrega al cliente. El cliente solo puede
  cambiar su contraseña con ese código.

### Claves privadas (`config/local_secrets.py`)

Las claves reales (admin y código de recuperación) **no se publican** en este
repositorio. Viven en `config/local_secrets.py`, que está en `.gitignore`.

Para usarlo en tu equipo:

1. Copia `config/local_secrets.example.py` y renómbralo a `config/local_secrets.py`.
2. Pon tus valores reales.
3. Compila normalmente: el `.exe` tomará esos valores.

Si ese archivo no existe, la app **igual funciona** con valores por defecto
(`usuario`/`usuario` y `mrmick`/`123456`), pero la recuperación por código queda
deshabilitada hasta que lo configures.

---

## 📦 Generar el instalador para Windows

Ver **[COMO_CREAR_INSTALADOR.md](COMO_CREAR_INSTALADOR.md)**. En resumen:

```bash
pip install -r requirements.txt pyinstaller pillow
pyinstaller banquito.spec --noconfirm --clean
```

Luego, con **Inno Setup**, abre `instalador.iss` y compila para obtener
`Salida/Instalador-Banquito.exe`, el único archivo que se distribuye a los
clientes.

Los datos de cada instalación se guardan en la carpeta del usuario
(`%LOCALAPPDATA%\Banquito`), nunca dentro de `Archivos de Programa`, así que no
hay problemas de permisos ni se pierden al reinstalar.

---

## 📁 Estructura del proyecto

```
banquito/
├── main.py                # Punto de entrada
├── config/                # Configuración y claves (local_secrets es privado)
├── database/              # Conexión y esquema SQLite
├── models/                # Entidades
├── repositories/          # Acceso a datos
├── services/              # Lógica de negocio
├── reports/               # Generador de PDF
├── ui/                    # Interfaz (ventanas, vistas, componentes)
├── utils/                 # Utilidades (fechas, rutas, logo)
├── assets/                # Logo e icono
├── banquito.spec          # Configuración de PyInstaller
└── instalador.iss         # Script de Inno Setup
```

---

## 👤 Autor

**MrMickWhite** — Soporte por correo: **mrmickdesign@gmail.com**

Hecho con dedicación para apoyar a las cajas de ahorro comunitario. 💚
