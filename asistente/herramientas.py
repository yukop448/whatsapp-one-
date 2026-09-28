"""Herramientas para gestionar tus pendientes: reuniones, compromisos, envíos y cotizaciones."""

from asistente import db
from asistente.nucleo import Herramienta

DESCRIPCION_TIPOS = (
    "reunion = reunión o llamada agendada; "
    "compromiso = algo que prometiste hacer; "
    "envio = información o documentos que debes enviar a alguien; "
    "cotizacion = cotización que debes pedir, enviar o a la que debes hacerle seguimiento"
)


def herramientas_pendientes(conexion, solo_lectura: bool = False) -> list[Herramienta]:
    """Crea las herramientas de pendientes conectadas a la base de datos.

    Con solo_lectura=True solo se incluye la consulta (útil para los agentes).
    """

    def crear_pendiente(tipo, titulo, descripcion="", fecha=None, contacto="", monto=None):
        return db.crear_pendiente(conexion, tipo, titulo, descripcion, fecha, contacto, monto)

    def listar_pendientes(tipo=None, estado="pendiente", hasta=None):
        pendientes = db.listar_pendientes(conexion, tipo, estado, hasta)
        return pendientes or "No hay pendientes con esos filtros."

    def actualizar_pendiente(id, **cambios):
        return db.actualizar_pendiente(conexion, id, **cambios)

    listar = Herramienta(
        nombre="listar_pendientes",
        descripcion=(
            "Consulta los pendientes guardados, ordenados por fecha (los más urgentes primero). "
            "Úsala para responder '¿qué tengo hoy/esta semana?' o antes de actualizar uno."
        ),
        parametros={
            "type": "object",
            "properties": {
                "tipo": {"type": "string", "enum": list(db.TIPOS_PENDIENTE), "description": DESCRIPCION_TIPOS},
                "estado": {
                    "type": "string",
                    "enum": list(db.ESTADOS_PENDIENTE),
                    "description": "Por defecto 'pendiente'.",
                },
                "hasta": {
                    "type": "string",
                    "description": "Solo los que vencen antes de esta fecha ISO, ej. 2026-10-05T23:59.",
                },
            },
        },
        funcion=listar_pendientes,
    )
    if solo_lectura:
        return [listar]

    crear = Herramienta(
        nombre="crear_pendiente",
        descripcion="Guarda un nuevo pendiente para no olvidarlo.",
        parametros={
            "type": "object",
            "properties": {
                "tipo": {"type": "string", "enum": list(db.TIPOS_PENDIENTE), "description": DESCRIPCION_TIPOS},
                "titulo": {"type": "string", "description": "Resumen corto, ej. 'Enviar catálogo a Tienda X'."},
                "descripcion": {"type": "string", "description": "Detalles adicionales."},
                "fecha": {
                    "type": "string",
                    "description": "Fecha y hora de la reunión o fecha límite, formato ISO: 2026-10-01T15:00.",
                },
                "contacto": {"type": "string", "description": "Persona o empresa involucrada."},
                "monto": {"type": "number", "description": "Valor de la cotización, si aplica."},
            },
            "required": ["tipo", "titulo"],
        },
        funcion=crear_pendiente,
    )

    actualizar = Herramienta(
        nombre="actualizar_pendiente",
        descripcion=(
            "Modifica un pendiente existente: marcarlo como hecho o cancelado, cambiar su fecha, etc. "
            "Necesitas su id (búscalo con listar_pendientes)."
        ),
        parametros={
            "type": "object",
            "properties": {
                "id": {"type": "integer"},
                "estado": {"type": "string", "enum": list(db.ESTADOS_PENDIENTE)},
                "titulo": {"type": "string"},
                "descripcion": {"type": "string"},
                "fecha": {"type": "string", "description": "Formato ISO: 2026-10-01T15:00."},
                "contacto": {"type": "string"},
                "monto": {"type": "number"},
            },
            "required": ["id"],
        },
        funcion=actualizar_pendiente,
    )

    return [crear, listar, actualizar]
