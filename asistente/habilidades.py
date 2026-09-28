"""Habilidades: archivos de conocimiento que les das a tus agentes.

Cada habilidad es un archivo .md en la carpeta habilidades/ con este formato:

    ---
    nombre: cotizaciones
    descripcion: Cómo comparar cotizaciones
    ---
    (instrucciones y conocimiento en texto normal)

Para crear una habilidad nueva solo agregas un archivo; no hay que tocar el código.
"""

from dataclasses import dataclass
from pathlib import Path

from asistente import config


@dataclass
class Habilidad:
    nombre: str
    descripcion: str
    contenido: str


def leer_habilidad(ruta: Path) -> Habilidad:
    texto = ruta.read_text(encoding="utf-8")
    datos = {"nombre": ruta.stem, "descripcion": ""}
    contenido = texto
    if texto.startswith("---"):
        encabezado, _, contenido = texto[3:].partition("\n---")
        for linea in encabezado.strip().splitlines():
            clave, _, valor = linea.partition(":")
            datos[clave.strip()] = valor.strip()
    return Habilidad(datos["nombre"], datos["descripcion"], contenido.strip())


def cargar_habilidades(carpeta: Path | None = None) -> dict[str, Habilidad]:
    """Lee todas las habilidades de la carpeta. Devuelve {nombre: Habilidad}."""
    carpeta = Path(carpeta or config.CARPETA_HABILIDADES)
    habilidades = [leer_habilidad(ruta) for ruta in sorted(carpeta.glob("*.md"))]
    return {h.nombre: h for h in habilidades}


def texto_para_agente(nombres: list[str], carpeta: Path | None = None) -> str:
    """Une el contenido de varias habilidades para ponerlo en las instrucciones de un agente."""
    disponibles = cargar_habilidades(carpeta)
    faltantes = [n for n in nombres if n not in disponibles]
    if faltantes:
        raise ValueError(
            f"No existen las habilidades: {', '.join(faltantes)}. "
            f"Disponibles: {', '.join(disponibles) or 'ninguna'}."
        )
    return "\n\n".join(f"## Habilidad: {n}\n{disponibles[n].contenido}" for n in nombres)
