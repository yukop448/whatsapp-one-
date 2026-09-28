"""Pruebas sin gastar dinero: usamos un Claude "falso" que responde lo que le indiquemos."""

from types import SimpleNamespace

import pytest

from asistente import db
from asistente.agentes import ejecutar_agente
from asistente.asistente import Asistente
from asistente.nucleo import conversar


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


def test_crear_y_listar_pendientes_por_fecha(conexion):
    db.crear_pendiente(conexion, "envio", "Enviar catálogo", fecha="2026-10-05T10:00")
    db.crear_pendiente(conexion, "reunion", "Reunión proveedor", fecha="2026-10-01T15:00")
    db.crear_pendiente(conexion, "compromiso", "Llamar a mamá")
    titulos = [p["titulo"] for p in db.listar_pendientes(conexion)]
    assert titulos == ["Reunión proveedor", "Enviar catálogo", "Llamar a mamá"]
    assert len(db.listar_pendientes(conexion, hasta="2026-10-02T00:00")) == 1


def test_tipo_invalido_da_error(conexion):
    with pytest.raises(ValueError):
        db.crear_pendiente(conexion, "fiesta", "No válido")


def test_marcar_pendiente_como_hecho(conexion):
    p = db.crear_pendiente(conexion, "cotizacion", "Cotizar telas", monto=1500000)
    db.actualizar_pendiente(conexion, p["id"], estado="hecho")
    assert db.listar_pendientes(conexion) == []
    assert db.listar_pendientes(conexion, estado="hecho")[0]["monto"] == 1500000


def test_asistente_registra_pendiente_con_herramienta(conexion):
    claude = ClaudeFalso([
        ("tool_use", [usar("crear_pendiente", {"tipo": "reunion", "titulo": "Reunión con Ana", "fecha": "2026-09-29T15:00"})]),
        ("end_turn", [texto("Listo, agendé la reunión con Ana mañana a las 3pm.")]),
    ])
    asistente = Asistente(cliente=claude, conexion=conexion)
    respuesta = asistente.responder("Mañana a las 3 tengo reunión con Ana")

    assert "Ana" in respuesta
    assert db.listar_pendientes(conexion)[0]["titulo"] == "Reunión con Ana"
    # El resultado de la herramienta se le devolvió a Claude
    resultado = claude.llamadas[1]["messages"][-1]["content"][0]
    assert resultado["type"] == "tool_result" and resultado["is_error"] is False


def test_error_de_herramienta_se_devuelve_a_claude(conexion):
    claude = ClaudeFalso([
        ("tool_use", [usar("actualizar_pendiente", {"id": 99, "estado": "hecho"})]),
        ("end_turn", [texto("No encontré ese pendiente.")]),
    ])
    conversar(claude, "sistema", [{"role": "user", "content": "hola"}], Asistente(claude, conexion).herramientas)
    resultado = claude.llamadas[1]["messages"][-1]["content"][0]
    assert resultado["is_error"] is True and "99" in resultado["content"]


def test_delegar_tarea_a_agente(conexion):
    db.crear_agente(conexion, "Redactor", "Redacta correos", "Tono cordial y breve.")
    claude = ClaudeFalso([("end_turn", [texto("Hola Ana, adjunto el catálogo...")])])

    resultado = ejecutar_agente(claude, conexion, "redactor", "Correo para Ana con el catálogo", "Usuario")

    assert resultado.startswith("Hola Ana")
    llamada = claude.llamadas[0]
    assert "Tono cordial y breve." in llamada["system"]
    assert [t["name"] for t in llamada["tools"]] == ["listar_pendientes"]  # solo lectura, sin web
    ejecuciones = conexion.execute("SELECT agente, resultado FROM ejecuciones").fetchall()
    assert ejecuciones[0]["agente"] == "redactor"


def test_agente_con_web_recibe_busqueda(conexion):
    db.crear_agente(conexion, "cotizador", "Compara precios", "Busca 3 opciones.", busca_en_web=True)
    claude = ClaudeFalso([("end_turn", [texto("Opción A...")])])
    ejecutar_agente(claude, conexion, "cotizador", "Cotiza bolsas", "Usuario")
    assert any(t.get("type") == "web_search_20260209" for t in claude.llamadas[0]["tools"])


def test_agente_inexistente(conexion):
    with pytest.raises(ValueError, match="No existe el agente"):
        ejecutar_agente(ClaudeFalso([]), conexion, "fantasma", "algo", "Usuario")
