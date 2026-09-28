# Plan de trabajo: Asistente personal con agentes

Para tu **vida personal** (no la empresa): citas, pagos, trámites, familia, compras y viajes.

## La idea

```
                 TÚ  (terminal → luego WhatsApp)
                  │
                  ▼
        ┌─────────────────────┐
        │  ASISTENTE PERSONAL │  recuerda, organiza y delega
        └─────────┬───────────┘
      ┌───────────┼────────────────────────┐
      ▼           ▼                        ▼
  Pendientes   Agentes que TÚ creas     (más adelante)
  • citas       • redactor-mensajes      Google Calendar,
  • compromisos • cotizador (web)        Gmail,
  • envíos      • investigador           WhatsApp
  • cotizaciones• ... los que quieras
```

- **Asistente**: habla contigo, guarda tus pendientes y decide a qué agente mandar cada tarea.
- **Agentes**: "empleados" especializados. Cada uno tiene un rol y un manual de instrucciones.
  Los creas conversando ("créame un agente que redacte cotizaciones con mi formato").

## Fases

| Fase | Qué se construye | Estado |
|---|---|---|
| **1. Núcleo** | Asistente en la terminal, memoria de pendientes (SQLite), creación de agentes y delegación de tareas | ✅ Hecho |
| **2. Rutina diaria** | Resumen automático cada mañana ("hoy tienes…"), alertas de pendientes vencidos y conversaciones que se recuerdan al cerrar el programa | ⏳ Siguiente |
| **3. WhatsApp** | Hablarle por WhatsApp (API oficial de Meta). Solo responde a **tu** número | ⏳ |
| **4. Calendario y correo** | Conectar Google Calendar (citas reales) y Gmail (enviar la información, con tu aprobación antes de enviar) | ⏳ |
| **5. Cotizaciones y documentos** | Enviarle fotos o PDF de cotizaciones y facturas para que las lea, las compare y te recuerde hacerles seguimiento | ⏳ |
| **6. En la nube 24/7** | Publicarlo en un servidor (Railway/Render) para que funcione con el computador apagado | ⏳ |

Regla de seguridad para todas las fases: **los agentes preparan, tú apruebas**. Nada se envía
a terceros sin tu confirmación.

## Ideas de agentes para empezar

| Agente | Rol | ¿Busca en web? |
|---|---|---|
| `redactor` | Redacta mensajes y correos personales con tu tono (reclamos, solicitudes, felicitaciones) | No |
| `cotizador` | Compara precios: viajes, arreglos del hogar o del carro, seguros, compras grandes | Sí |
| `investigador` | Averigua requisitos de trámites, horarios, opiniones de un servicio | Sí |
| `planeador` | Organiza viajes, eventos familiares y listas de lo que hay que llevar o comprar | Sí |
