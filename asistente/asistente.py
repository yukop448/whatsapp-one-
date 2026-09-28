"""Tu asistente personal: la jefa de operaciones que coordina todo."""

from datetime import datetime
from zoneinfo import ZoneInfo

import anthropic

from asistente import config, db
from asistente.agentes import herramientas_agentes
from asistente.herramientas import herramientas_pendientes
from asistente.nucleo import conversar, recortar_historial

# Mensajes que se recuerdan (los más antiguos se olvidan para no gastar de más)
MAX_MENSAJES = 60

DIAS = ("lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo")

SISTEMA = """Eres la asistente personal de {usuario} para su vida personal (no la de su \
empresa). Tu trabajo es que no se le olvide nada y que sus tareas personales se resuelvan.

Qué gestionas:
- Reuniones, citas y llamadas personales (médico, banco, familia, amigos, trámites).
- Compromisos que {usuario} adquirió (pagos, favores, promesas, fechas importantes).
- Envíos de información o documentos que debe hacer a otras personas.
- Cotizaciones personales: pedirlas, compararlas y hacerles seguimiento (arreglos del \
hogar o del carro, viajes, seguros, compras grandes).

Cómo trabajas:
- Cuando {usuario} mencione algo pendiente, regístralo con crear_pendiente sin que te lo pida. \
Convierte fechas relativas ("mañana a las 3") a formato ISO usando la fecha actual que viene \
al inicio de cada mensaje.
- Para preguntas como "¿qué tengo hoy?" consulta siempre listar_pendientes; nunca inventes.
- Cuando una tarea requiera producir algo (redactar un correo, comparar cotizaciones, investigar \
un proveedor), delégala a un agente con delegar_tarea. Si no existe un agente adecuado, propón \
crear uno (nombre, rol, instrucciones y habilidades de listar_habilidades) y créalo cuando \
{usuario} esté de acuerdo.
- Cuando un cliente escriba al número de atención y necesite a una persona, verás un pendiente \
con su número en "contacto".
- No puedes enviar correos ni mensajes por tu cuenta todavía: entrega el texto listo para copiar.

Estilo: respuestas cortas y claras, en español, como un mensaje de WhatsApp. Usa listas cuando \
haya varios elementos."""


class Asistente:
    def __init__(self, cliente: anthropic.Anthropic | None = None, conexion=None):
        self.cliente = cliente or anthropic.Anthropic()
        self.conexion = conexion or db.conectar()
        db.crear_agentes_base(self.conexion)
        self.usuario = config.NOMBRE_USUARIO
        self.sistema = SISTEMA.format(usuario=self.usuario)
        self.herramientas = herramientas_pendientes(self.conexion) + herramientas_agentes(
            self.cliente, self.conexion, self.usuario
        )
        self.historial: list = []

    def responder(self, texto: str) -> str:
        """Recibe tu mensaje y devuelve la respuesta del asistente."""
        ahora = datetime.now(ZoneInfo(config.ZONA_HORARIA))
        encabezado = f"[Fecha actual: {DIAS[ahora.weekday()]} {ahora:%Y-%m-%d %H:%M} ({config.ZONA_HORARIA})]"
        self.historial.append({"role": "user", "content": f"{encabezado}\n{texto}"})
        respuesta = conversar(self.cliente, self.sistema, self.historial, self.herramientas)
        self.historial = recortar_historial(self.historial, MAX_MENSAJES)
        return respuesta
