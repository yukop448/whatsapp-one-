"""Piezas compartidas por las pruebas: un Claude falso que no gasta dinero."""

from types import SimpleNamespace

import pytest

from asistente import db


def texto(t):
    return SimpleNamespace(type="text", text=t)


def usar(nombre, entrada, id_="t1"):
    return SimpleNamespace(type="tool_use", name=nombre, input=entrada, id=id_)


class ClaudeFalso:
    """Imita client.beta.messages.create devolviendo respuestas preparadas en orden."""

    def __init__(self, respuestas):
        self.respuestas = list(respuestas)
        self.llamadas = []
        self.beta = SimpleNamespace(messages=SimpleNamespace(create=self._create))

    def _create(self, **kwargs):
        # Copiamos los mensajes: la lista original sigue creciendo después de la llamada
        self.llamadas.append({**kwargs, "messages": list(kwargs["messages"])})
        stop_reason, contenido = self.respuestas.pop(0)
        return SimpleNamespace(stop_reason=stop_reason, content=contenido)


@pytest.fixture
def conexion():
    return db.conectar(":memory:")
