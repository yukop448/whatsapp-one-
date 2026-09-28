"""Chatea con tu asistente desde la terminal.

Uso:  python main.py
Salir: escribe "salir"
"""

import anthropic

from asistente.asistente import Asistente


def main() -> None:
    asistente = Asistente()
    print(f"Asistente lista. Hola, {asistente.usuario} 👋  (escribe 'salir' para terminar)\n")

    while True:
        try:
            texto = input("Tú: ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not texto:
            continue
        if texto.lower() in ("salir", "exit", "chao"):
            break

        try:
            respuesta = asistente.responder(texto)
        except anthropic.AuthenticationError:
            print("\n⚠️  Tu ANTHROPIC_API_KEY no es válida. Revisa el archivo .env\n")
            continue
        except anthropic.RateLimitError:
            print("\n⚠️  Demasiadas solicitudes seguidas. Espera un momento e intenta de nuevo.\n")
            continue
        except anthropic.APIConnectionError:
            print("\n⚠️  No hay conexión con Claude. Revisa tu internet.\n")
            continue
        except anthropic.APIStatusError as error:
            print(f"\n⚠️  Error de la API ({error.status_code}): {error.message}\n")
            continue

        print(f"\nAsistente: {respuesta}\n")

    print("¡Hasta luego!")


if __name__ == "__main__":
    main()
