"""Servidor que recibe los mensajes de WhatsApp y responde.

- Si te escribe TU número (NUMERO_DUENO) → responde tu asistente personal.
- Si escribe cualquier otro número → responde la atención al cliente.

Arrancarlo:  uvicorn servidor:app --port 8000
"""

import logging
import threading
from collections import deque

import anthropic
from fastapi import BackgroundTasks, FastAPI, HTTPException, Request
from fastapi.responses import PlainTextResponse

from asistente import config, db, whatsapp
from asistente.asistente import Asistente
from asistente.atencion import AtencionClientes

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("servidor")

MENSAJE_SOLO_TEXTO = "Por ahora solo puedo leer mensajes de texto 🙏"
MENSAJE_ERROR = "Tuve un problema para responder. Intenta de nuevo en un momento."


def avisar_al_dueno(texto: str) -> None:
    """Le manda un WhatsApp al dueño. Si falla (ej. pasaron 24h sin que el dueño escriba),
    queda el pendiente guardado de todas formas."""
    if not config.NUMERO_DUENO:
        log.warning("NUMERO_DUENO no está configurado; no se pudo avisar: %s", texto)
        return
    try:
        whatsapp.enviar_mensaje(config.NUMERO_DUENO, texto)
    except Exception:
        log.exception("No se pudo avisar al dueño por WhatsApp")


class Bot:
    """Reúne al asistente personal y a la atención al cliente."""

    def __init__(self, cliente=None, conexion=None, enviar=whatsapp.enviar_mensaje, avisar=avisar_al_dueno):
        cliente = cliente or anthropic.Anthropic()
        conexion = conexion or db.conectar()
        self.asistente = Asistente(cliente, conexion)
        self.atencion = AtencionClientes(cliente, conexion, avisar)
        self.enviar = enviar
        self._candado = threading.Lock()  # atiende un mensaje a la vez
        self._vistos: deque[str] = deque(maxlen=500)  # Meta a veces reenvía el mismo mensaje

    def atender(self, mensaje: dict) -> None:
        with self._candado:
            if mensaje["id"] in self._vistos:
                return
            self._vistos.append(mensaje["id"])

            numero = mensaje["de"]
            es_dueno = bool(config.NUMERO_DUENO) and numero == config.NUMERO_DUENO
            log.info("Mensaje de %s (%s)", numero, "dueño" if es_dueno else "cliente")

            try:
                if mensaje["tipo"] != "text" or not mensaje["texto"].strip():
                    respuesta = MENSAJE_SOLO_TEXTO
                elif es_dueno:
                    respuesta = self.asistente.responder(mensaje["texto"])
                else:
                    respuesta = self.atencion.responder(numero, mensaje["texto"])
            except Exception:
                log.exception("Error respondiendo a %s", numero)
                respuesta = MENSAJE_ERROR
            try:
                self.enviar(numero, respuesta or "👍")
            except Exception:
                log.exception("No se pudo enviar la respuesta a %s", numero)


app = FastAPI(title="Asistente WhatsApp")
_bot: Bot | None = None


def obtener_bot() -> Bot:
    global _bot
    if _bot is None:
        _bot = Bot()
    return _bot


@app.get("/")
def estado():
    return {"estado": "funcionando"}


@app.get("/webhook")
def verificar(request: Request):
    """Meta llama aquí una sola vez para confirmar que el servidor es tuyo."""
    parametros = request.query_params
    if (
        parametros.get("hub.mode") == "subscribe"
        and config.WHATSAPP_VERIFY_TOKEN
        and parametros.get("hub.verify_token") == config.WHATSAPP_VERIFY_TOKEN
    ):
        return PlainTextResponse(parametros.get("hub.challenge", ""))
    raise HTTPException(status_code=403, detail="Token de verificación incorrecto")


@app.post("/webhook")
async def recibir(request: Request, tareas: BackgroundTasks):
    """Meta llama aquí cada vez que llega un mensaje."""
    cuerpo = await request.body()
    if not whatsapp.firma_valida(cuerpo, request.headers.get("X-Hub-Signature-256"), config.WHATSAPP_APP_SECRET):
        raise HTTPException(status_code=401, detail="Firma inválida")

    bot = obtener_bot()
    for mensaje in whatsapp.extraer_mensajes(await request.json()):
        # Respondemos "recibido" a Meta de inmediato y pensamos la respuesta en segundo plano
        tareas.add_task(bot.atender, mensaje)
    return {"ok": True}
