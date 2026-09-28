"""Tus agentes especializados.

Cada agente es un "empleado" con un rol y un manual de instrucciones. El asistente
principal los crea cuando se lo pides y les delega tareas específicas. Los agentes
pueden consultar tus pendientes y (si lo activas) buscar en internet, pero no pueden
modificar tu agenda ni delegar a otros agentes: eso solo lo hace tu asistente.
"""

from asistente import db
from asistente.habilidades import cargar_habilidades, texto_para_agente
from asistente.herramientas import herramientas_pendientes
from asistente.nucleo import Herramienta, conversar

BUSQUEDA_WEB = {"type": "web_search_20260209", "name": "web_search", "max_uses": 5}

PLANTILLA_SISTEMA_AGENTE = """Eres "{nombre}", un agente especializado que trabaja para {usuario}.
Tu rol: {rol}

Tus instrucciones:
{instrucciones}

{habilidades}

Recibes tareas del asistente personal de {usuario}. Entrega el resultado completo y listo \
para usar (un correo redactado, un resumen, una tabla comparativa, etc.). Si te falta un \
dato indispensable, dilo claramente al final en una sección "Falta confirmar"."""


def ejecutar_agente(cliente, conexion, nombre: str, tarea: str, usuario: str) -> str:
    """Pone a trabajar a un agente en una tarea y guarda el resultado."""
    agente = db.obtener_agente(conexion, nombre)
    if agente is None:
        disponibles = ", ".join(a["nombre"] for a in db.listar_agentes(conexion)) or "ninguno"
        raise ValueError(f"No existe el agente '{nombre}'. Agentes disponibles: {disponibles}.")

    sistema = PLANTILLA_SISTEMA_AGENTE.format(
        nombre=agente["nombre"],
        usuario=usuario,
        rol=agente["rol"],
        instrucciones=agente["instrucciones"],
        habilidades=texto_para_agente(agente["habilidades"]),
    )
    herramientas_servidor = [BUSQUEDA_WEB] if agente["busca_en_web"] else []
    mensajes = [{"role": "user", "content": tarea}]

    resultado = conversar(
        cliente,
        sistema,
        mensajes,
        herramientas_pendientes(conexion, solo_lectura=True),
        herramientas_servidor,
    )
    db.registrar_ejecucion(conexion, agente["nombre"], tarea, resultado)
    return resultado


def herramientas_agentes(cliente, conexion, usuario: str) -> list[Herramienta]:
    """Herramientas del asistente principal para crear agentes y delegarles trabajo."""

    def crear_agente(nombre, rol, instrucciones, busca_en_web=False, habilidades=()):
        texto_para_agente(list(habilidades))  # valida que las habilidades existan
        agente = db.crear_agente(conexion, nombre, rol, instrucciones, busca_en_web, habilidades)
        return f"Agente '{agente['nombre']}' creado."

    def listar_agentes():
        agentes = db.listar_agentes(conexion)
        if not agentes:
            return "Todavía no hay agentes creados."
        return [
            {
                "nombre": a["nombre"],
                "rol": a["rol"],
                "busca_en_web": bool(a["busca_en_web"]),
                "habilidades": a["habilidades"],
            }
            for a in agentes
        ]

    def listar_habilidades():
        return [{"nombre": h.nombre, "descripcion": h.descripcion} for h in cargar_habilidades().values()]

    def delegar_tarea(agente, tarea):
        return ejecutar_agente(cliente, conexion, agente, tarea, usuario)

    return [
        Herramienta(
            nombre="crear_agente",
            descripcion=(
                "Crea un agente especializado permanente (ej. 'cotizador', 'redactor-correos'). "
                "Úsala solo cuando el usuario pida crear un agente o apruebe tu propuesta de crearlo."
            ),
            parametros={
                "type": "object",
                "properties": {
                    "nombre": {"type": "string", "description": "Nombre corto sin espacios, ej. 'cotizador'."},
                    "rol": {"type": "string", "description": "Una frase: para qué sirve este agente."},
                    "instrucciones": {
                        "type": "string",
                        "description": "Manual detallado: cómo trabaja, tono, formato de entrega, datos fijos.",
                    },
                    "busca_en_web": {
                        "type": "boolean",
                        "description": "True si necesita buscar información en internet (precios, proveedores...).",
                    },
                    "habilidades": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Nombres de habilidades a darle (consúltalas con listar_habilidades).",
                    },
                },
                "required": ["nombre", "rol", "instrucciones"],
            },
            funcion=crear_agente,
        ),
        Herramienta(
            nombre="listar_agentes",
            descripcion="Muestra los agentes especializados disponibles y su rol.",
            parametros={"type": "object", "properties": {}},
            funcion=listar_agentes,
        ),
        Herramienta(
            nombre="listar_habilidades",
            descripcion="Muestra las habilidades (archivos de conocimiento) que se les pueden dar a los agentes.",
            parametros={"type": "object", "properties": {}},
            funcion=listar_habilidades,
        ),
        Herramienta(
            nombre="delegar_tarea",
            descripcion=(
                "Envía una tarea específica a uno de los agentes y devuelve su resultado. "
                "El agente NO ve esta conversación: incluye en 'tarea' todo el contexto que necesita "
                "(nombres, fechas, montos, tono, formato esperado)."
            ),
            parametros={
                "type": "object",
                "properties": {
                    "agente": {"type": "string", "description": "Nombre del agente."},
                    "tarea": {"type": "string", "description": "La tarea completa con todo su contexto."},
                },
                "required": ["agente", "tarea"],
            },
            funcion=delegar_tarea,
        ),
    ]
