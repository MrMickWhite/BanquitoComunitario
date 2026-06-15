-- =====================================================================
-- Esquema de la base de datos del Banquito (SQLite)
-- Se ejecuta automáticamente la primera vez que se abre el programa.
-- "IF NOT EXISTS" => seguro de correr siempre, no borra datos existentes.
-- =====================================================================

-- Socios / miembros de la caja
CREATE TABLE IF NOT EXISTS socios (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    nombres         TEXT    NOT NULL,
    apellidos       TEXT    NOT NULL,
    documento       TEXT    UNIQUE,              -- cédula / DNI
    telefono        TEXT,
    email           TEXT,
    fecha_ingreso   TEXT    NOT NULL,            -- formato ISO: YYYY-MM-DD
    activo          INTEGER NOT NULL DEFAULT 1,  -- 1 activo, 0 inactivo
    notas           TEXT
);

-- Aportes / ahorros que entrega cada socio
CREATE TABLE IF NOT EXISTS aportes (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    socio_id    INTEGER NOT NULL,
    monto       REAL    NOT NULL,
    fecha       TEXT    NOT NULL,                -- YYYY-MM-DD
    tipo        TEXT    NOT NULL DEFAULT 'aporte', -- aporte | ahorro
    descripcion TEXT,
    FOREIGN KEY (socio_id) REFERENCES socios(id) ON DELETE CASCADE
);

-- Préstamos otorgados a socios
CREATE TABLE IF NOT EXISTS prestamos (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    socio_id          INTEGER NOT NULL,
    monto             REAL    NOT NULL,          -- capital prestado
    tasa_mensual      REAL    NOT NULL,          -- tasa de interés mensual aplicada
    fecha_otorgado    TEXT    NOT NULL,          -- YYYY-MM-DD
    plazo_meses       INTEGER NOT NULL DEFAULT 1,
    fecha_vencimiento TEXT,                      -- próxima fecha de pago esperada
    estado            TEXT    NOT NULL DEFAULT 'activo', -- activo | pagado | mora
    saldo_capital     REAL    NOT NULL,          -- capital que aún se debe
    descripcion       TEXT,
    FOREIGN KEY (socio_id) REFERENCES socios(id) ON DELETE CASCADE
);

-- Pagos que el socio hace sobre un préstamo
CREATE TABLE IF NOT EXISTS pagos (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    prestamo_id INTEGER NOT NULL,
    fecha       TEXT    NOT NULL,                -- YYYY-MM-DD
    monto_total REAL    NOT NULL,               -- lo que entregó el socio
    capital     REAL    NOT NULL DEFAULT 0,      -- parte que abona al capital
    interes     REAL    NOT NULL DEFAULT 0,      -- parte que paga interés
    mora        REAL    NOT NULL DEFAULT 0,      -- parte que paga mora
    descripcion TEXT,
    FOREIGN KEY (prestamo_id) REFERENCES prestamos(id) ON DELETE CASCADE
);

-- Libro general de caja: TODO movimiento de dinero pasa por aquí.
-- Permite saber el saldo disponible y armar reportes globales.
CREATE TABLE IF NOT EXISTS movimientos (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    fecha       TEXT    NOT NULL,                -- YYYY-MM-DD
    tipo        TEXT    NOT NULL,                -- ingreso | egreso
    categoria   TEXT    NOT NULL,                -- aporte | prestamo | pago_capital | interes | mora | gasto | otro
    monto       REAL    NOT NULL,
    socio_id    INTEGER,                         -- opcional
    referencia  TEXT,                            -- p.ej. "prestamo:5", "aporte:12"
    descripcion TEXT,
    genera_interes INTEGER NOT NULL DEFAULT 0,   -- 1 si este movimiento genera interés
    tasa_interes   REAL,                          -- tasa mensual individual (NULL = usar la general)
    FOREIGN KEY (socio_id) REFERENCES socios(id) ON DELETE SET NULL
);

-- Parámetros editables desde la interfaz (sobreescriben los de settings.py)
CREATE TABLE IF NOT EXISTS parametros (
    clave   TEXT PRIMARY KEY,
    valor   TEXT NOT NULL
);

-- Usuarios del sistema (login). La contraseña se guarda hasheada con salt.
CREATE TABLE IF NOT EXISTS usuarios (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario             TEXT    UNIQUE NOT NULL,
    email               TEXT,
    telefono            TEXT,
    password_hash       TEXT    NOT NULL,
    salt                TEXT    NOT NULL,
    confirmado          INTEGER NOT NULL DEFAULT 1,
    codigo_confirmacion TEXT,
    debe_cambiar        INTEGER NOT NULL DEFAULT 0,     -- 1 = debe cambiar usuario/clave al entrar
    es_admin            INTEGER NOT NULL DEFAULT 0,
    fecha_creacion      TEXT    NOT NULL
);

-- Banco de 100 códigos de 5 cifras para la confirmación por WhatsApp.
-- El registro elige uno (no usado) y lo envía al número del usuario.
CREATE TABLE IF NOT EXISTS codigos_confirmacion (
    id      INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo  TEXT    UNIQUE NOT NULL,   -- 5 cifras, ej: "04827"
    usado   INTEGER NOT NULL DEFAULT 0
);

-- Índices para acelerar consultas frecuentes por fecha y por socio
CREATE INDEX IF NOT EXISTS idx_aportes_socio   ON aportes(socio_id);
CREATE INDEX IF NOT EXISTS idx_aportes_fecha    ON aportes(fecha);
CREATE INDEX IF NOT EXISTS idx_prestamos_socio  ON prestamos(socio_id);
CREATE INDEX IF NOT EXISTS idx_pagos_prestamo   ON pagos(prestamo_id);
CREATE INDEX IF NOT EXISTS idx_movimientos_fecha ON movimientos(fecha);
