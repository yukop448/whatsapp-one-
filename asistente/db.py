"""Memoria del asistente: una base de datos SQLite con tres tablas.

- pendientes:   reuniones, compromisos, envíos de información y cotizaciones
- agentes:      los agentes especializados que tú creas
- ejecuciones:  historial de las tareas que cada agente ha resuelto
"""

import sqlite3
from datetime import datetime
from pathlib import Path

from asistente import config

TIPOS_PENDIENTE = ("reunion", "compromiso", "envio", "cotizacion")
ESTADOS_PENDIENTE = ("pendiente", "hecho", "cancelado")

ESQUEMA = """
CREATE TABLE IF NOT EXISTS pendientes (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    tipo        TEXT NOT NULL,
    titulo      TEXT NOT NULL,
    descripcion TEXT DEFAULT '',
    fecha       TEXT,             -- fecha límite o de la reunión (ISO: 2026-10-01T15:00)
    contacto    TEXT DEFAULT '',  -- persona o empresa involucrada
    monto       REAL,             -- solo para cotizaciones
    estado      TEXT NOT NULL DEFAULT 'pendiente',
    creado      TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS agentes (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre        TEXT NOT NULL UNIQUE,
    rol           TEXT NOT NULL,   -- descripción corta: para qué sirve
    instrucciones TEXT NOT NULL,   -- cómo debe trabajar (su "manual")
    busca_en_web  INTEGER NOT NULL DEFAULT 0,
    creado        TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS ejecuciones (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    agente    TEXT NOT NULL,
    tarea     TEXT NOT NULL,
    resultado TEXT NOT NULL,
    fecha     TEXT NOT NULL
);
"""


def _ahora() -> str:
    return datetime.now().isoformat(timespec="seconds")


def conectar(ruta: Path | str | None = None) -> sqlite3.Connection:
    """Abre la base de datos (y la crea si no existe)."""
    ruta = Path(ruta or config.RUTA_DB)
    if str(ruta) != ":memory:":
        ruta.parent.mkdir(parents=True, exist_ok=True)
    conexion = sqlite3.connect(ruta)
    conexion.row_factory = sqlite3.Row  # permite leer columnas por nombre
    conexion.executescript(ESQUEMA)
    return conexion


# ---------- Pendientes ----------

def crear_pendiente(conexion, tipo, titulo, descripcion="", fecha=None, contacto="", monto=None) -> dict:
    if tipo not in TIPOS_PENDIENTE:
        raise ValueError(f"Tipo inválido '{tipo}'. Usa uno de: {', '.join(TIPOS_PENDIENTE)}")
    cursor = conexion.execute(
        "INSERT INTO pendientes (tipo, titulo, descripcion, fecha, contacto, monto, creado) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (tipo, titulo, descripcion, fecha, contacto, monto, _ahora()),
    )
    conexion.commit()
    return obtener_pendiente(conexion, cursor.lastrowid)


def obtener_pendiente(conexion, pendiente_id: int) -> dict | None:
    fila = conexion.execute("SELECT * FROM pendientes WHERE id = ?", (pendiente_id,)).fetchone()
    return dict(fila) if fila else None


def listar_pendientes(conexion, tipo=None, estado="pendiente", hasta=None) -> list[dict]:
    """Lista pendientes filtrando por tipo, estado y fecha límite (hasta)."""
    consulta = "SELECT * FROM pendientes WHERE 1=1"
    parametros = []
    if tipo:
        consulta += " AND tipo = ?"
        parametros.append(tipo)
    if estado:
        consulta += " AND estado = ?"
        parametros.append(estado)
    if hasta:
        consulta += " AND fecha IS NOT NULL AND fecha <= ?"
        parametros.append(hasta)
    # Los que tienen fecha primero (los más urgentes arriba), luego los que no tienen
    consulta += " ORDER BY fecha IS NULL, fecha, id"
    return [dict(fila) for fila in conexion.execute(consulta, parametros)]


def actualizar_pendiente(conexion, pendiente_id: int, **cambios) -> dict:
    permitidos = {"titulo", "descripcion", "fecha", "contacto", "monto", "estado", "tipo"}
    cambios = {k: v for k, v in cambios.items() if k in permitidos and v is not None}
    if not cambios:
        raise ValueError("No hay cambios para aplicar.")
    if "estado" in cambios and cambios["estado"] not in ESTADOS_PENDIENTE:
        raise ValueError(f"Estado inválido. Usa uno de: {', '.join(ESTADOS_PENDIENTE)}")
    if "tipo" in cambios and cambios["tipo"] not in TIPOS_PENDIENTE:
        raise ValueError(f"Tipo inválido. Usa uno de: {', '.join(TIPOS_PENDIENTE)}")
    if obtener_pendiente(conexion, pendiente_id) is None:
        raise ValueError(f"No existe el pendiente #{pendiente_id}.")
    columnas = ", ".join(f"{k} = ?" for k in cambios)
    conexion.execute(f"UPDATE pendientes SET {columnas} WHERE id = ?", (*cambios.values(), pendiente_id))
    conexion.commit()
    return obtener_pendiente(conexion, pendiente_id)


# ---------- Agentes ----------

def crear_agente(conexion, nombre, rol, instrucciones, busca_en_web=False) -> dict:
    nombre = nombre.strip().lower()
    if obtener_agente(conexion, nombre):
        raise ValueError(f"Ya existe un agente llamado '{nombre}'.")
    conexion.execute(
        "INSERT INTO agentes (nombre, rol, instrucciones, busca_en_web, creado) VALUES (?, ?, ?, ?, ?)",
        (nombre, rol, instrucciones, int(busca_en_web), _ahora()),
    )
    conexion.commit()
    return obtener_agente(conexion, nombre)


def obtener_agente(conexion, nombre: str) -> dict | None:
    fila = conexion.execute("SELECT * FROM agentes WHERE nombre = ?", (nombre.strip().lower(),)).fetchone()
    return dict(fila) if fila else None


def listar_agentes(conexion) -> list[dict]:
    return [dict(fila) for fila in conexion.execute("SELECT * FROM agentes ORDER BY nombre")]


def registrar_ejecucion(conexion, agente, tarea, resultado) -> None:
    conexion.execute(
        "INSERT INTO ejecuciones (agente, tarea, resultado, fecha) VALUES (?, ?, ?, ?)",
        (agente, tarea, resultado, _ahora()),
    )
    conexion.commit()
