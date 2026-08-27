# 13: Si una pestaña abierta puede pisar una escritura del plugin

**Tipo:** `map:task` · **Modo:** HITL (`hitl:dev`)
**Bloqueado por:** nada. Tomable ahora.
**Origen:** creado al resolver el [09](09-concurrencia-humano-plugin.md).

## Pregunta

El 09 resolvió la falla que el ticket nombraba: el plugin pisando una edición
humana. La estrategia es releer tarde y re-derivar, y baja la ventana a 332 ms
medidos.

Falta la falla inversa, y esta estrategia **no la cubre**. Los Documents de
Linear son colaborativos sobre Yjs. Si una persona tiene el mapa abierto en una
pestaña, su cliente sostiene un estado Yjs propio. Cuando el plugin escribe por
API, esa pestaña puede hacer dos cosas distintas: adoptar el contenido nuevo, o
re-sincronizar empujando su estado viejo y **deshaciendo la escritura del
plugin**.

Si es lo segundo, la escritura del plugin desaparece sin error: `documentUpdate`
devuelve `success: true`, el script reporta que todo salió bien, y el mapa
vuelve solo al estado anterior unos segundos después.

## Por qué es `map:task` y no `map:research`

Un ticket de research lo conduce el agente solo, y este hecho no se puede medir
desde la API: necesita un navegador con una sesión de Linear abierta y una
persona que la tenga en pantalla. Es trabajo manual que desbloquea una decisión.

## El experimento

Diez minutos. El harness ya existe:
[`research/09-scripts/drift_probe.py`](../research/09-scripts/drift_probe.py).

1. Abrir el Document sandbox del 01 (`8d748d5c-0a07-4906-8a04-e02868d0d1e0`) en
   el navegador y dejar la pestaña visible.
2. Escribir una línea a mano y esperar a que Linear la sincronice.
3. Con la pestaña **todavía abierta**, correr una escritura por API.
4. Releer por API a los 5, 30 y 120 segundos, y mirar la pestaña.

Interesa además la variante de la pestaña **abierta pero inactiva** desde hace
rato, que es el caso real: alguien dejó el mapa abierto ayer.

De paso cierra el hecho menor que el 09 tampoco pudo medir: si una edición
humana en la UI mueve `Document.updatedAt` o si también viene coalescida como
las de la API.

## Qué cambia según el resultado

Si la pestaña adopta el contenido nuevo, no hay nada que hacer y el 09 queda
completo.

Si la pestaña puede deshacer la escritura, la estrategia del 09 sigue siendo
correcta pero **insuficiente**, y hay que decidir algo que hoy no está decidido:
verificar la escritura releyendo unos segundos después, avisarle a la persona
que cierre la pestaña, o aceptar el riesgo y documentarlo.

## Hecho cuando

Está medido si una pestaña abierta puede deshacer una escritura por API, con el
resultado anotado en el deliverable del 09, y decidido qué hacer si puede.
