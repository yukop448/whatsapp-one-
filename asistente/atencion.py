"""Atención a clientes: responde a cualquier número que NO sea el tuyo.

Solo sabe lo que está en habilidades/atencion-clientes.md. No puede ver tu agenda,
tus pendientes ni tus agentes. Cuando no sabe algo o el cliente necesita a una persona,
te avisa con la herramienta avisar_al_dueno.
"""

from typing import Callable

from asistente import db
from asistente.habilidades import texto_para_agente
from asistente.nucleo import Herramienta, conversar, recortar_historial

SISTEMA_ATENCION = """Eres el asistente de atención al cliente por WhatsApp. Respondes a \
clientes, no al dueño del negocio.

{conocimiento}"""

# Mensajes que se recuerdan por cliente (los más antiguos se olvidan)
MAX_MENSAJES_CLIENTE = 30


class AtencionClientes:
    def __init__(self, cliente, conexion, avisar: Callable[[str], None]):
        """`avisar` es la función que le manda un mensaje al dueño (por WhatsApp)."""
        self.cliente = cliente
        self.conexion = conexion
        self.avisar = avisar
        self.conversaciones: dict[str, list] = {}

    def _herramientas(self, numero: str) -> list[Herramienta]:
        def avisar_al_dueno(motivo: str, nombre_cliente: str = ""):
            quien = f"{nombre_cliente} (+{numero})" if nombre_cliente else f"+{numero}"
            db.crear_pendiente(
                self.conexion, "compromiso", f"Responder a cliente {quien}", motivo, contacto=f"+{numero}"
            )
            self.avisar(f"📩 Cliente {quien} necesita atención:\n{motivo}")
            return "El dueño fue notificado y responderá personalmente."

        return [
            Herramienta(
                nombre="avisar_al_dueno",
                descripcion=(
                    "Notifica al dueño que este cliente necesita atención de una persona. "
                    "Úsala según las reglas de la habilidad de atención."
                ),
                parametros={
                    "type": "object",
                    "properties": {
                        "motivo": {"type": "string", "description": "Qué necesita el cliente, en una o dos frases."},
                        "nombre_cliente": {"type": "string", "description": "Nombre del cliente si lo dijo."},
                    },
                    "required": ["motivo"],
                },
                funcion=avisar_al_dueno,
            )
        ]

    def responder(self, numero: str, texto: str) -> str:
        sistema = SISTEMA_ATENCION.format(conocimiento=texto_para_agente(["atencion-clientes"]))
        historial = self.conversaciones.setdefault(numero, [])
        historial.append({"role": "user", "content": texto})
        respuesta = conversar(self.cliente, sistema, historial, self._herramientas(numero))
        self.conversaciones[numero] = recortar_historial(historial, MAX_MENSAJES_CLIENTE)
        return respuesta
