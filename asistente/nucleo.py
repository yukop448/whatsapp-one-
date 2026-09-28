"""El "motor" que usan el asistente y todos los agentes para hablar con Claude.

Funciona en ciclo:
  1. Le mandamos a Claude la conversación y las herramientas disponibles.
  2. Si Claude pide usar una herramienta, la ejecutamos y le devolvemos el resultado.
  3. Repetimos hasta que Claude responde con texto final.
"""

import json
from dataclasses import dataclass
from typing import Callable

import anthropic

from asistente import config

# Si el modelo principal rechaza una solicitud por sus filtros de seguridad,
# la API reintenta automáticamente con el modelo alterno recomendado.
BETAS = ["server-side-fallback-2026-07-01"]

# Límite de vueltas por mensaje, para que un agente nunca quede en un ciclo infinito
MAX_VUELTAS = 25


@dataclass
class Herramienta:
    """Una acción que Claude puede ejecutar: su descripción + la función de Python."""

    nombre: str
    descripcion: str
    parametros: dict  # JSON Schema de las entradas
    funcion: Callable[..., object]

    def definicion(self) -> dict:
        return {"name": self.nombre, "description": self.descripcion, "input_schema": self.parametros}


def ejecutar_herramienta(herramientas: dict[str, Herramienta], nombre: str, entrada: dict) -> tuple[str, bool]:
    """Ejecuta la herramienta pedida. Devuelve (resultado en texto, ¿hubo error?)."""
    herramienta = herramientas.get(nombre)
    if herramienta is None:
        return f"Error: la herramienta '{nombre}' no existe.", True
    try:
        resultado = herramienta.funcion(**entrada)
    except Exception as error:  # el error se le devuelve a Claude para que lo corrija
        return f"Error: {error}", True
    if isinstance(resultado, str):
        return resultado, False
    return json.dumps(resultado, ensure_ascii=False, default=str), False


def recortar_historial(mensajes: list, maximo: int) -> list:
    """Deja solo los mensajes más recientes para no gastar de más en conversaciones largas.

    El corte siempre empieza en un mensaje de texto tuyo (no en la mitad del uso de una
    herramienta), porque Claude necesita ver cada herramienta junto a su resultado.
    """
    if len(mensajes) <= maximo:
        return mensajes
    for i in range(len(mensajes) - maximo, len(mensajes)):
        if mensajes[i]["role"] == "user" and isinstance(mensajes[i]["content"], str):
            return mensajes[i:]
    return mensajes[-1:]


def conversar(
    cliente: anthropic.Anthropic,
    sistema: str,
    mensajes: list,
    herramientas: list[Herramienta],
    herramientas_servidor: list[dict] | None = None,
) -> str:
    """Corre el ciclo con Claude y devuelve la respuesta final en texto.

    `mensajes` se modifica: queda con todo el historial (incluidas las herramientas),
    así la siguiente pregunta conserva el contexto.
    """
    por_nombre = {h.nombre: h for h in herramientas}
    definiciones = [h.definicion() for h in herramientas] + list(herramientas_servidor or [])

    for _ in range(MAX_VUELTAS):
        respuesta = cliente.beta.messages.create(
            model=config.MODELO,
            max_tokens=16000,
            system=sistema,
            tools=definiciones,
            messages=mensajes,
            betas=BETAS,
            fallbacks="default",
        )
        mensajes.append({"role": "assistant", "content": respuesta.content})

        if respuesta.stop_reason == "refusal":
            return "No pude completar esa solicitud. ¿Puedes reformularla?"

        # Una herramienta del servidor (ej. búsqueda web) pidió más tiempo: continuamos
        if respuesta.stop_reason == "pause_turn":
            continue

        pedidos = [bloque for bloque in respuesta.content if bloque.type == "tool_use"]
        if respuesta.stop_reason != "tool_use" or not pedidos:
            return "\n".join(b.text for b in respuesta.content if b.type == "text").strip()

        # Ejecutamos todas las herramientas pedidas y devolvemos los resultados juntos
        resultados = []
        for pedido in pedidos:
            texto, es_error = ejecutar_herramienta(por_nombre, pedido.name, pedido.input)
            resultados.append(
                {"type": "tool_result", "tool_use_id": pedido.id, "content": texto, "is_error": es_error}
            )
        mensajes.append({"role": "user", "content": resultados})

    return "Me detuve porque la tarea tomó demasiados pasos. Intenta dividirla en partes más pequeñas."
