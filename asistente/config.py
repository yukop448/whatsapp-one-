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
