"""Conexión con la API oficial de WhatsApp (WhatsApp Cloud API de Meta)."""

import hashlib
import hmac
import logging

import httpx

from asistente import config

log = logging.getLogger(__name__)

# WhatsApp no acepta mensajes de más de 4096 caracteres; dejamos margen
LIMITE_CARACTERES = 4000


def firma_valida(cuerpo: bytes, firma: str | None, secreto: str) -> bool:
    """Comprueba que el mensaje realmente viene de Meta (encabezado X-Hub-Signature-256)."""
    if not secreto:
        log.error("Falta WHATSAPP_APP_SECRET en el .env: se rechazan todos los mensajes por seguridad")
        return False
    if not firma or not firma.startswith("sha256="):
        return False
    esperado = hmac.new(secreto.encode(), cuerpo, hashlib.sha256).hexdigest()
    return hmac.compare_digest(esperado, firma.removeprefix("sha256="))


def extraer_mensajes(datos: dict) -> list[dict]:
    """Saca los mensajes recibidos del JSON que manda Meta.

    Devuelve una lista de {id, de, tipo, texto}. Ignora avisos de "entregado" o "leído".
    """
    mensajes = []
    for entrada in datos.get("entry", []):
        for cambio in entrada.get("changes", []):
            for mensaje in cambio.get("value", {}).get("messages", []):
                mensajes.append(
                    {
                        "id": mensaje.get("id"),
                        "de": mensaje.get("from", ""),
                        "tipo": mensaje.get("type"),
                        "texto": mensaje.get("text", {}).get("body", ""),
                    }
                )
    return mensajes


def partir_texto(texto: str, limite: int = LIMITE_CARACTERES) -> list[str]:
    """Divide un texto largo en partes, cortando preferiblemente en saltos de línea."""
    partes = []
    while len(texto) > limite:
        corte = texto.rfind("\n", 0, limite)
        if corte <= 0:
            corte = limite
        partes.append(texto[:corte].rstrip())
        texto = texto[corte:].lstrip()
    if texto:
        partes.append(texto)
    return partes


def enviar_mensaje(numero: str, texto: str) -> None:
    """Envía un mensaje de texto de WhatsApp a un número (solo dígitos, con código de país)."""
    url = (
        f"https://graph.facebook.com/{config.WHATSAPP_API_VERSION}/"
        f"{config.WHATSAPP_PHONE_NUMBER_ID}/messages"
    )
    encabezados = {"Authorization": f"Bearer {config.WHATSAPP_TOKEN}"}
    for parte in partir_texto(texto):
        cuerpo = {"messaging_product": "whatsapp", "to": numero, "type": "text", "text": {"body": parte}}
        respuesta = httpx.post(url, json=cuerpo, headers=encabezados, timeout=30)
        if respuesta.is_error:
            log.error("WhatsApp rechazó el envío a %s: %s", numero, respuesta.text)
            respuesta.raise_for_status()
