# Asistente personal con agentes

Tu asistente virtual **para tu vida personal**: gestiona citas y reuniones, compromisos,
envíos de información y cotizaciones personales. Además crea **agentes especializados** y les delega tareas concretas.

El plan completo por fases está en [PLAN.md](PLAN.md).

## Instalación (una sola vez)

1. Instala Python 3.11 o superior: https://www.python.org/downloads/
2. Abre una terminal en esta carpeta y ejecuta:

   ```bash
   python -m venv .venv
   source .venv/bin/activate        # En Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. Copia `.env.example` como `.env` y pon tu llave de Claude
   (se crea en https://console.anthropic.com → API Keys).

## Uso

```bash
python main.py
```

Ejemplos de lo que le puedes decir:

- "El jueves a las 10am tengo cita con el odontólogo"
- "Le prometí a mi hermana enviarle las fotos del viaje antes del viernes"
- "El 15 debo pagar la tarjeta de crédito"
- "¿Qué tengo pendiente esta semana?"
- "Ya le envié las fotos a mi hermana"
- "Créame un agente cotizador que busque precios en internet y me entregue una tabla con 3 opciones"
- "Pídele al cotizador que compare tiquetes Bogotá–Cartagena para diciembre"
- "Me cotizaron $800.000 por pintar el apartamento, recuérdame pedir otras dos cotizaciones"

## Cómo está organizado el código

| Archivo | Qué hace |
|---|---|
| `main.py` | El chat en la terminal |
| `asistente/asistente.py` | La personalidad y las reglas de tu asistente |
| `asistente/nucleo.py` | El ciclo que habla con Claude y ejecuta herramientas |
| `asistente/herramientas.py` | Crear, listar y actualizar pendientes |
| `asistente/agentes.py` | Crear agentes y delegarles tareas |
| `asistente/db.py` | La base de datos (archivo `datos/asistente.db`) |
| `tests/` | Pruebas automáticas; se corren con `python -m pytest` y no gastan saldo |

## Costos

Cada mensaje consume saldo de tu cuenta de Anthropic. Puedes ver el gasto en la consola.
Para gastar menos, cambia el modelo en `.env` (`ASISTENTE_MODELO`).
