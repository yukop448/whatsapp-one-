"""Configuración del asistente. Todo se lee del archivo .env."""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# Carpeta raíz del proyecto (donde está este repositorio)
RAIZ = Path(__file__).resolve().parent.parent

# Modelo de Claude que usan el asistente y los agentes
MODELO = os.getenv("ASISTENTE_MODELO", "claude-opus-5")

# Archivo de base de datos donde se guardan pendientes y agentes
RUTA_DB = Path(os.getenv("ASISTENTE_DB", RAIZ / "datos" / "asistente.db"))

# Tu nombre, para que el asistente te hable de forma personal
NOMBRE_USUARIO = os.getenv("ASISTENTE_NOMBRE_USUARIO", "jefe")

# Zona horaria para interpretar fechas ("mañana a las 3pm")
ZONA_HORARIA = os.getenv("ASISTENTE_ZONA_HORARIA", "America/Bogota")

# Carpeta con las habilidades (archivos .md) que usan los agentes
CARPETA_HABILIDADES = Path(os.getenv("ASISTENTE_HABILIDADES", RAIZ / "habilidades"))

# ---------- WhatsApp (API oficial de Meta) ----------
# Token de acceso de tu app de Meta
WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN", "")
# Identificador del número de WhatsApp del bot (Phone number ID, no el número en sí)
WHATSAPP_PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "")
# Palabra secreta que tú inventas para que Meta verifique tu servidor
WHATSAPP_VERIFY_TOKEN = os.getenv("WHATSAPP_VERIFY_TOKEN", "")
# "App secret" de tu app de Meta: sirve para comprobar que los mensajes vienen de Meta
WHATSAPP_APP_SECRET = os.getenv("WHATSAPP_APP_SECRET", "")
WHATSAPP_API_VERSION = os.getenv("WHATSAPP_API_VERSION", "v23.0")

# TU número de WhatsApp (con código de país, solo dígitos: 573001234567).
# Solo este número habla con tu asistente personal; los demás reciben atención al cliente.
NUMERO_DUENO = "".join(c for c in os.getenv("NUMERO_DUENO", "") if c.isdigit())
