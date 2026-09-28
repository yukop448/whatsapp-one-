# Conectar el asistente a WhatsApp (paso a paso)

Al terminar vas a tener un contacto en tu WhatsApp ("Mi Asistente") con el que chateas.

- **Tu número** (el que pones en `NUMERO_DUENO`) habla con tu asistente personal.
- **Cualquier otro número** recibe atención al cliente con las respuestas de
  `habilidades/atencion-clientes.md`, sin acceso a tu agenda ni a tus datos.

Tiempo estimado: 30–45 minutos la primera vez.

---

## Paso 1: Crear la app en Meta

1. Entra a https://developers.facebook.com e inicia sesión con tu Facebook.
2. Arriba a la derecha: **Mis apps → Crear app**.
3. Caso de uso: **"Conectar con clientes a través de WhatsApp"**. Ponle un nombre (ej. "Mi Asistente").
4. Asóciala a tu portafolio comercial (Business) o crea uno nuevo.

## Paso 2: Obtener el número de prueba y tus datos

En el menú de la app entra a **WhatsApp → Configuración de la API** (API Setup). Ahí verás:

| Lo que ves en Meta | Dónde va en tu `.env` |
|---|---|
| Token de acceso temporal | `WHATSAPP_TOKEN` |
| Identificador del número de teléfono (Phone number ID) | `WHATSAPP_PHONE_NUMBER_ID` |

Luego ve a **Configuración de la app → Básica** y copia la **Clave secreta de la app**
(App Secret) en `WHATSAPP_APP_SECRET`.

## Paso 3: Crear el contacto y recibir tu primer mensaje

1. En **Configuración de la API**, en el campo **"Para"** (To), agrega tu número personal
   de WhatsApp y confírmalo con el código que te llega.
2. Pulsa **"Enviar mensaje"**. Te llega un "Hello World" a tu WhatsApp desde el número de prueba.
3. En tu celular guarda ese número como contacto: **"Mi Asistente"**. ✅

## Paso 4: Llenar el `.env`

```env
ANTHROPIC_API_KEY=sk-ant-...
ASISTENTE_NOMBRE_USUARIO=TuNombre

WHATSAPP_TOKEN=EAAG...
WHATSAPP_PHONE_NUMBER_ID=1234567890
WHATSAPP_APP_SECRET=abc123...
WHATSAPP_VERIFY_TOKEN=inventa-una-palabra-secreta
NUMERO_DUENO=573001234567
```

`NUMERO_DUENO` es tu número con código de país y sin `+` ni espacios.

## Paso 5: Encender el servidor y publicarlo en internet

Meta necesita una dirección de internet (https) para entregarte los mensajes. Para probar
desde tu computador usamos **ngrok**, que es gratis: https://ngrok.com/download

En una terminal:

```bash
uvicorn servidor:app --port 8000
```

En otra terminal:

```bash
ngrok http 8000
```

ngrok te muestra una dirección como `https://abcd-1234.ngrok-free.app`. Cópiala.

## Paso 6: Conectar Meta con tu servidor (webhook)

1. En Meta: **WhatsApp → Configuración** → sección **Webhook** → **Editar**.
2. **URL de devolución de llamada**: `https://abcd-1234.ngrok-free.app/webhook`
3. **Token de verificación**: la misma palabra que pusiste en `WHATSAPP_VERIFY_TOKEN`.
4. Pulsa **Verificar y guardar**.
5. En **Campos del webhook**, activa la suscripción a **messages**.

## Paso 7: ¡Tu primer mensaje! 🎉

Desde tu WhatsApp escríbele a "Mi Asistente":

> Hola, ¿qué agentes tienes disponibles?

En la terminal del servidor verás `Mensaje de 57300... (dueño)` y en segundos te llega la respuesta.

---

## Problemas comunes

| Síntoma | Solución |
|---|---|
| No llega nada y la terminal no muestra mensajes | Revisa el Paso 6 (URL con `/webhook` al final y suscripción a **messages**). ngrok cambia la dirección cada vez que lo reinicias, así que hay que actualizarla en Meta |
| La terminal dice "Firma inválida" o "Falta WHATSAPP_APP_SECRET" | Copia de nuevo la clave secreta de la app (Paso 2) |
| Te responde como si fueras un cliente | `NUMERO_DUENO` no coincide exactamente con tu número (revisa el código de país) |
| Funcionaba y al otro día dejó de responder | El token temporal dura 24 horas. Genera uno nuevo o crea un token permanente (ver abajo) |
| Error 131030 en la terminal | Tu número no está agregado en el campo "Para" del Paso 3 |

## Para usarlo de verdad con clientes

El número de prueba solo le puede escribir a 5 números verificados. Para atender clientes reales:

1. **Número propio:** agrega un número real en **WhatsApp → Configuración de la API → Agregar número**.
   Ese número no puede estar en uso en la app de WhatsApp normal.
2. **Token permanente:** en business.facebook.com → **Configuración → Usuarios del sistema**,
   crea un usuario del sistema con permiso `whatsapp_business_messaging` y genera su token.
3. **Verificación del negocio**, en el mismo portafolio comercial, para superar los límites de envío.
4. **Servidor 24/7:** publica el proyecto en Railway o Render (fase 6 del plan) para no depender
   de tu computador ni de ngrok.
5. **Llena `habilidades/atencion-clientes.md`** con la información real. Todo lo marcado
   [COMPLETAR] el bot no lo afirma: le avisa al dueño.

**Regla de las 24 horas de WhatsApp:** el bot puede responder libremente durante las 24 horas
siguientes al último mensaje de cada persona. Por eso, si llevas más de 24 horas sin escribirle
a tu asistente, los avisos de "cliente necesita atención" pueden no llegarte. Igual quedan
guardados como pendientes, y los ves al preguntar "¿qué tengo pendiente?".
