# Asistente personal con agentes

Tu asistente virtual **para tu vida personal**: gestiona citas y reuniones, compromisos,
envíos de información y cotizaciones personales. Además crea **agentes especializados** y les delega tareas concretas.

También responde por **WhatsApp**: a ti como asistente personal y a los demás como atención
al cliente, usando las preguntas frecuentes de `habilidades/atencion-clientes.md`.

- Plan por fases: [PLAN.md](PLAN.md)
- Conectar WhatsApp paso a paso: [WHATSAPP.md](WHATSAPP.md)

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

En la terminal:

```bash
python main.py
```

Por WhatsApp (sigue primero [WHATSAPP.md](WHATSAPP.md)):

```bash
uvicorn servidor:app --port 8000
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

## Agentes y habilidades

Vienen 4 agentes listos: **redactor**, **cotizador**, **investigador** y **planeador**.
Cada uno usa una *habilidad*: un archivo de la carpeta `habilidades/` con su conocimiento y
sus reglas.

| Habilidad | La usa | Para qué |
|---|---|---|
| `atencion-clientes.md` | Atención al cliente por WhatsApp | Preguntas frecuentes de la marca. **Llénala con tus datos reales** |
| `redaccion-mensajes.md` | redactor | Tu tono y la estructura de mensajes y correos |
| `cotizaciones.md` | cotizador | Cómo comparar precios y detectar alertas |
| `investigacion.md` | investigador | Fuentes confiables y formato de respuesta |
| `planeacion.md` | planeador | Viajes, eventos y listas |

**Para crear una habilidad nueva**, copia cualquiera de esos archivos, cámbiale el `nombre`, la
`descripcion` y el contenido, y luego dile al asistente: *"créame un agente X con la habilidad Y"*.
Si editas una habilidad, los agentes que la usan aprenden el cambio de inmediato.

## Cómo está organizado el código

| Archivo | Qué hace |
|---|---|
| `main.py` | El chat en la terminal |
| `servidor.py` | Recibe los mensajes de WhatsApp y decide quién responde |
| `asistente/whatsapp.py` | Envía mensajes por WhatsApp y verifica que vengan de Meta |
| `asistente/atencion.py` | La atención al cliente (solo preguntas frecuentes) |
| `asistente/habilidades.py` | Lee los archivos de la carpeta `habilidades/` |
| `asistente/asistente.py` | La personalidad y las reglas de tu asistente |
| `asistente/nucleo.py` | El ciclo que habla con Claude y ejecuta herramientas |
| `asistente/herramientas.py` | Crear, listar y actualizar pendientes |
| `asistente/agentes.py` | Crear agentes y delegarles tareas |
| `asistente/db.py` | La base de datos (archivo `datos/asistente.db`) |
| `tests/` | Pruebas automáticas; se corren con `python -m pytest` y no gastan saldo |

## Costos

Cada mensaje consume saldo de tu cuenta de Anthropic. Puedes ver el gasto en la consola.
Para gastar menos, cambia el modelo en `.env` (`ASISTENTE_MODELO`).
