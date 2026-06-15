# Cómo crear el instalador de Banquito (con icono y acceso en escritorio)

El resultado es un único archivo **`Instalador-Banquito.exe`** que tus clientes
abren, dan "Siguiente → Instalar", y la app queda instalada en
`C:\Program Files\Banquito` con su **icono en el escritorio** y en el **menú inicio**.

## Lo necesitas hacer una sola vez por cada versión nueva

### Paso 1 — Generar el programa (.exe)
En tu PC con Windows, en la carpeta del proyecto:

- Doble clic en **`construir_exe.bat`** (o en una terminal: `pyinstaller banquito.spec`).
- Espera a que termine. Se crea la carpeta **`dist\Banquito`** con `Banquito.exe` dentro.

### Paso 2 — Instalar Inno Setup (gratis, una sola vez)
- Descárgalo de **https://jrsoftware.org/isdl.php** e instálalo.

### Paso 3 — Generar el instalador
1. Abre el archivo **`instalador.iss`** (doble clic; se abre con Inno Setup).
2. En el menú, elige **Build → Compile** (o el botón ▶ "Compile").
3. Al terminar, se crea la carpeta **`Salida`** con **`Instalador-Banquito.exe`** dentro.

### Paso 4 — Distribuir
- Ese **`Instalador-Banquito.exe`** es lo único que das a cada cliente.
- Lo abren, instalan, y listo: icono en escritorio + menú inicio.

## Notas importantes

- **Datos a salvo:** la base de datos y los reportes de cada cliente NO se guardan
  en `Program Files`; se guardan en su carpeta de usuario
  (`C:\Users\<usuario>\AppData\Local\Banquito`). Por eso no hay errores de permisos
  y los datos **no se borran** si se desinstala o se reinstala el programa.

- **Sin servidores ni internet:** la app es 100% local. El instalador es solo
  para el programa que usan los clientes; no hay nada más que instalar.

- **Actualizar la app:** cuando cambies algo del código, repite los pasos 1 y 3
  (no necesitas reinstalar Inno Setup). Sube el número de versión en `instalador.iss`
  (línea `#define MiVersion`) si quieres llevar control.
