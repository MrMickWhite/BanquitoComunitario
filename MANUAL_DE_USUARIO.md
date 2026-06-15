# 📘 Manual de Usuario — Banquito

_Elaborado por MrMickWhite. Soporte por correo: mrmickdesign@gmail.com._

---

## 1. Primer uso

1. Al abrir el programa por primera vez, te pedirá el **nombre de tu banco o caja**.
   Escríbelo y pulsa *Continuar*. (Esto se hace **una sola vez**.)
2. Aparece la pantalla de **Acceso**. Entra con:
   - **Usuario:** `usuario`
   - **Contraseña:** `usuario`
3. El sistema te pedirá **crear tu propio usuario y contraseña** (por seguridad).
   Guárdalos bien; con esos entrarás de ahora en adelante.

> También existe un usuario **administrador** que entrega el proveedor.

---

## 2. ¿Olvidaste tu contraseña?

1. En la pantalla de acceso pulsa **"¿Olvidaste tu contraseña?"**.
2. Escríbele al proveedor por **correo (mrmickdesign@gmail.com)** para que te dé tu
   **código de recuperación**.
3. Ingresa tu usuario, el código y tu nueva contraseña. Listo.

---

## 3. Secciones del programa

- **Dashboard:** resumen general (saldo, socios, capital prestado, aportes, etc.).
- **Socios:** registrar y administrar socios (nombre, C.I. / DNI) y ver su historial.
- **Aportes:** registrar aportes y la recaudación del día; eliminar aportes mal hechos.
- **Préstamos:** otorgar préstamos, registrar pagos, deshacer pagos y eliminar préstamos.
- **Movimientos:** ingresos y egresos varios (que no son de socios).
- **Cuadre de caja:** arqueo del efectivo, desglose y caja chica.
- **Reportes:** generar PDF generales o por socio (semanal, mensual, anual o por rango).
- **Configuración:** nombre del banco, logo, intereses, reglas, recaudación y tema.

---

## 4. Aportes, préstamos, intereses y mora

- Al registrar un **aporte**, puedes indicar si **genera interés** y a qué tasa.
- Al otorgar un **préstamo**, defines si **cobra interés** y la tasa; si lo pones
  en 0%, no cobra interés.
- Los **pagos** se reparten automáticamente: primero **mora**, luego **interés**,
  y por último **capital**.

> Si registras un movimiento con una **fecha de meses anteriores**, los intereses
> y la mora se calculan correctamente según los días transcurridos.

---

## 5. Cuadre de caja

- **Arqueo:** compara el efectivo real con lo que dice el sistema.
- **Caja chica:** fija un **fondo**, registra **gastos** y observa el
  **disponible** (fondo − gastado).

---

## 6. Reportes PDF

En **Reportes** eliges el tipo (General o por Socio) y el periodo (Semanal,
Mensual, Anual o por Rango de fechas). El PDF se guarda en una carpeta
**"Reportes [nombre del banco]"** en tu Escritorio.

Los reportes salen con el **logo y nombre de tu banco**. Si configuras un logo
propio (en Configuración → General), aparecerá en el encabezado y el logo de
Banquito quedará como marca de agua.

---

## 7. Configuración

- **🏦 General:** nombre del banco, carpeta de reportes, **logo propio** y la
  opción de *Borrar todo e iniciar de nuevo*.
- **💵 Intereses:** tasas de préstamo, mora, ahorro, aporte mínimo y días de gracia.
- **⚖️ Reglas:** tipo de interés (sobre saldo o fijo), tipo de mora (diaria o fija),
  modo de fin de año y si se incluye el interés estimado.
- **📅 Recaudación:** método de acumulación (semanal/mensual), día y cuota.
- **🎨 Apariencia:** tema claro u oscuro.

---

## 8. Preguntas frecuentes

**¿Necesito internet?**
No. El programa funciona 100% local. Solo necesitas internet si quieres pedir tu
código de recuperación por correo al proveedor.

**¿Puedo instalarlo en varias computadoras?**
Sí. Cada instalación funciona por separado, con su propio nombre de banco y sus
propios datos.

**¿Dónde se guardan mis datos?**
En tu carpeta de usuario (`%LOCALAPPDATA%\Banquito`). No se borran al reinstalar.

---

_Para cualquier información o soporte, escríbenos a **mrmickdesign@gmail.com**. Elaborado por **MrMickWhite**._
