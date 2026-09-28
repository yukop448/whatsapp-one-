"""Pruebas del servidor de WhatsApp y la atención al cliente (sin Meta ni Claude reales)."""

import hashlib
import hmac
import json

import pytest
from fastapi.testclient import TestClient

import servidor
from asistente import config, db, whatsapp
from asistente.atencion import AtencionClientes
from conftest import ClaudeFalso, texto, usar

DUENO = "573001112233"
CLIENTE = "573009998877"
SECRETO = "secreto-de-prueba"


def mensaje_meta(de, cuerpo, id_="wamid.1", tipo="text"):
    mensaje = {"from": de, "id": id_, "type": tipo}
    if tipo == "text":
        mensaje["text"] = {"body": cuerpo}
    return {"entry": [{"changes": [{"value": {"messages": [mensaje]}}]}]}


def firmar(cuerpo: bytes) -> str:
    return "sha256=" + hmac.new(SECRETO.encode(), cuerpo, hashlib.sha256).hexdigest()


@pytest.fixture
def entorno(monkeypatch, conexion):
    monkeypatch.setattr(config, "NUMERO_DUENO", DUENO)
    monkeypatch.setattr(config, "WHATSAPP_VERIFY_TOKEN", "mi-token")
    monkeypatch.setattr(config, "WHATSAPP_APP_SECRET", SECRETO)
    enviados, avisos = [], []

    def crear_bot(respuestas):
        claude = ClaudeFalso(respuestas)
        bot = servidor.Bot(
            cliente=claude,
            conexion=conexion,
            enviar=lambda numero, t: enviados.append((numero, t)),
            avisar=avisos.append,
        )
        monkeypatch.setattr(servidor, "_bot", bot)
        return claude

    return crear_bot, enviados, avisos


def publicar(datos):
    cuerpo = json.dumps(datos).encode()
    return TestClient(servidor.app).post(
        "/webhook", content=cuerpo, headers={"X-Hub-Signature-256": firmar(cuerpo), "Content-Type": "application/json"}
    )


def test_verificacion_de_meta(entorno):
    cliente = TestClient(servidor.app)
    ok = cliente.get("/webhook", params={"hub.mode": "subscribe", "hub.verify_token": "mi-token", "hub.challenge": "123"})
    assert ok.status_code == 200 and ok.text == "123"
    malo = cliente.get("/webhook", params={"hub.mode": "subscribe", "hub.verify_token": "otro", "hub.challenge": "123"})
    assert malo.status_code == 403


def test_rechaza_mensajes_sin_firma_valida(entorno):
    crear_bot, enviados, _ = entorno
    crear_bot([])
    cuerpo = json.dumps(mensaje_meta(DUENO, "hola")).encode()
    respuesta = TestClient(servidor.app).post("/webhook", content=cuerpo, headers={"X-Hub-Signature-256": "sha256=falsa"})
    assert respuesta.status_code == 401 and enviados == []


def test_dueno_habla_con_asistente_personal(entorno):
    crear_bot, enviados, _ = entorno
    claude = crear_bot([("end_turn", [texto("Hola jefe, hoy no tienes pendientes.")])])
    assert publicar(mensaje_meta(DUENO, "¿qué tengo hoy?")).status_code == 200
    assert enviados == [(DUENO, "Hola jefe, hoy no tienes pendientes.")]
    nombres = {t["name"] for t in claude.llamadas[0]["tools"]}
    assert "crear_pendiente" in nombres and "delegar_tarea" in nombres


def test_cliente_recibe_atencion_sin_acceso_a_lo_personal(entorno):
    crear_bot, enviados, _ = entorno
    claude = crear_bot([("end_turn", [texto("¡Hola! Los envíos tardan 2-5 días.")])])
    publicar(mensaje_meta(CLIENTE, "¿cuánto tarda el envío?"))
    assert enviados == [(CLIENTE, "¡Hola! Los envíos tardan 2-5 días.")]
    llamada = claude.llamadas[0]
    assert [t["name"] for t in llamada["tools"]] == ["avisar_al_dueno"]
    assert "Atención a clientes" in llamada["system"]


def test_mensaje_repetido_se_responde_una_vez(entorno):
    crear_bot, enviados, _ = entorno
    crear_bot([("end_turn", [texto("Hola")])])
    publicar(mensaje_meta(CLIENTE, "hola", id_="wamid.X"))
    publicar(mensaje_meta(CLIENTE, "hola", id_="wamid.X"))
    assert len(enviados) == 1


def test_audio_recibe_aviso_de_solo_texto(entorno):
    crear_bot, enviados, _ = entorno
    crear_bot([])
    publicar(mensaje_meta(CLIENTE, "", tipo="audio"))
    assert enviados == [(CLIENTE, servidor.MENSAJE_SOLO_TEXTO)]


def test_error_de_claude_no_deja_al_cliente_sin_respuesta(entorno):
    crear_bot, enviados, _ = entorno
    crear_bot([])  # el Claude falso falla porque no tiene respuestas
    publicar(mensaje_meta(CLIENTE, "hola"))
    assert enviados == [(CLIENTE, servidor.MENSAJE_ERROR)]


def test_cliente_escalado_avisa_al_dueno_y_crea_pendiente(conexion):
    avisos = []
    claude = ClaudeFalso([
        ("tool_use", [usar("avisar_al_dueno", {"motivo": "Quiere comprar 200 camisetas", "nombre_cliente": "Laura"})]),
        ("end_turn", [texto("Le aviso al equipo, te escriben pronto.")]),
    ])
    atencion = AtencionClientes(claude, conexion, avisos.append)
    respuesta = atencion.responder(CLIENTE, "Quiero 200 camisetas al por mayor")
    assert "pronto" in respuesta
    assert "Laura" in avisos[0] and "200 camisetas" in avisos[0]
    pendiente = db.listar_pendientes(conexion)[0]
    assert pendiente["contacto"] == f"+{CLIENTE}"


def test_partir_texto_largo():
    partes = whatsapp.partir_texto("linea\n" * 1500, limite=4000)
    assert len(partes) == 3 and all(len(p) <= 4000 for p in partes)


def test_firma_sin_secreto_se_rechaza():
    assert whatsapp.firma_valida(b"{}", "sha256=abc", "") is False
