# 13: Si una pestaña abierta puede pisar una escritura del plugin

**Tipo:** `map:task` · **Modo:** HITL (`hitl:dev`) · **RESUELTO** el 2026-08-27
**Bloqueado por:** nada.
**Tomado por:** Luis Felipe Jaña (`hitl:dev`), sesión del 2026-08-27.
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

---

# Resolución

Cuatro fases medidas con una persona en el navegador, y una quinta al revés que
no estaba prevista. El resultado se anotó en el deliverable del 09, sección 9:
[`research/09-la-escritura-del-mapa.md`](../research/09-la-escritura-del-mapa.md).
Harness: [`research/13-scripts/tab_probe.py`](../research/13-scripts/tab_probe.py).

## La respuesta

**No. Una pestaña abierta no puede deshacer una escritura por API.** El 09 queda
completo y `map:write` no cambia en nada.

Lo importante no es el resultado sino el mecanismo, porque es lo que hace que
generalice más allá de un navegador un martes. `documentUpdate(content:)`
**mueve `contentState`**, el estado Yjs serializado, en 5 de 5 escrituras.
`contentState` está en la salida del tipo `Document` pero no en
`DocumentUpdateInput`, y ninguna de las cuatro mutations de document lo toca. O
sea que el servidor no escribe el markdown por detrás del CRDT: lo convierte en
un update Yjs de verdad y lo emite por el canal de sync. No hay rama divergente
con la que un cliente pueda ganar, porque el servidor no deja ninguna abierta.

Las tres condiciones que pedía el ticket:

- **Pestaña visible y activa.** La escritura apareció sola en pantalla, sin
  refrescar, y sobrevivió 120 s. Y el sub-test que de verdad importaba: una línea
  tipeada por la persona **después** de la escritura se fusionó encima en vez de
  pisarla.
- **Pestaña abierta pero en segundo plano**, que era el caso real que el ticket
  quería. 300 s de reposo no movieron nada: una pestaña en segundo plano no
  empuja nada por su cuenta.
- **Cliente offline y divergente**, que no estaba en el plan y es estrictamente
  más duro. Con throttling `Offline`, la persona escribió una línea que quedó
  solo en su Yjs local, verificado por API que no había llegado al servidor. Con
  las dos ramas divergidas el plugin escribió, y al volver a online sobrevivieron
  las dos. La fusión fue un evento único y atómico: los tres campos se movieron
  juntos, una sola vez, y nada más se movió en los 159 s siguientes.

## La quinta fase, que corre al revés

El hallazgo de que el servidor hace reconciliación Yjs invita a una lectura
equivocada: que el 09 sobra. Se midió para cerrarla.

Con la línea de la persona ya en el servidor, el plugin escribió el markdown
previo a ella más su propia edición. **La línea de la persona desapareció.** El
CRDT no protege contra eso, porque desde su punto de vista no hubo conflicto:
hubo un cliente autorizado pidiendo un borrado. Una escritura del plugin no es
una rama concurrente, es un reemplazo autoritativo del documento entero.

Releer tarde y re-derivar sigue siendo necesario, y ahora está medido desde los
dos lados: el plugin puede destruir trabajo de una persona, y una persona no
puede destruir trabajo del plugin.

## Lo que se decidió, y no era obvio

- **No se agrega ninguna verificación posterior a la escritura.** Ni siquiera la
  versión tibia de un flag `--verify` apagado por defecto: apagado es código
  muerto que nadie prende, y prendido obliga a `map:write` a bloquear varios
  segundos para detectar algo cuyo mecanismo ya sabemos que no ocurre.
- **`contentState` no entra al contrato**, y eso a pesar de ser el detector de
  cambio perfecto que `updatedAt` no logró ser. Dice que algo cambió pero no qué,
  y el reporte de deriva del 09 existe justamente para nombrar la sección. Cuesta
  16 veces el payload, medido: 9884 bytes contra 616, con la misma complejidad.
  El contrato lo prohíbe explícitamente en `map:read` y `map:write`, por la misma
  razón por la que el 09 prohibió ramificar sobre `updatedAt`.

## Qué corrige o empuja

**Al enunciado de este mismo ticket**, que daba por hecho que el harness del 09
alcanzaba. No alcanzaba: `drift_probe.py` no sabe hacer relecturas cronometradas
ni mirar `contentState`. Se escribió `tab_probe.py`.

**A la sección 1 del 09**, el hecho menor que había quedado sin medir. Una
edición humana en la UI **también** viene coalescida. Cinco puntos nuevos
descartan las dos hipótesis tentadoras: no hay asimetría UI contra API, así que
el sello no sirve como señal de "acá tocó una persona"; y tampoco hay ventana
fija, porque 204 s de gap movieron el sello mientras el 09 midió 300 s de
congelamiento tras una sola escritura. La regla no está caracterizada y se
decidió no caracterizarla: la conclusión no depende de cuál sea.

**Al ticket 10**, las afirmaciones chequeables 30 y 31.

**Al ticket 14, nada.** Se revisó: el preflight sigue corriendo las mismas veces
porque el camino de escritura no ganó ningún paso.

## Niebla graduada

Ninguna, y el asunto se cierra plano. "Linear podría cambiar su editor" no es
niebla: es cierto de cada hecho medido en todo el mapa, y anotarlo acá y no en
los otros veinte sería arbitrario.

## Tickets nuevos

Ninguno.
