# 09: Cómo evita el plugin pisar una edición humana del mapa

**Tipo:** `map:grilling` · **Modo:** HITL (`hitl:dev`) · **RESUELTO** el 2026-08-27
**Bloqueado por:** nada.
**Tomado por:** Luis Felipe Jaña, sesión 2026-08-27.
**Origen:** graduado desde la niebla por el research del ticket 02.

## Pregunta

Linear no da control de concurrencia sobre Documents. `DocumentUpdateInput` no
tiene versión, etag ni `expectedUpdatedAt`, y los Documents son colaborativos en
tiempo real sobre Yjs. Gana el último que escribe.

Eso significa que si alguien tiene el mapa abierto en una pestaña mientras el
plugin lo reescribe, su edición se pierde sin aviso. **No es el caso de
concurrencia que pusimos fuera de alcance**: aquel era entre sesiones del
plugin, y lo resolvimos asumiendo un solo conductor. Este es el plugin
destruyendo trabajo de una persona, y ocurre con un solo conductor igual.

## Por qué graduó de la niebla

Al trazar el mapa la niebla decía "sesiones concurrentes sobre un mismo mapa",
que era demasiado difuso para ticketear. El research del 02 lo volvió preciso:
no hay locking, el modo de fallo es last-write-wins, y el afectado es un humano
y no otra sesión.

## Preguntas que cuelgan de esta

- Si alcanza con releer justo antes de escribir y comparar `updatedAt`, que el
  tipo `Document` sí expone en salida, para detectar que alguien tocó el mapa.
- Qué hace el plugin cuando detecta esa deriva: aborta, reintenta sobre el
  contenido nuevo, o le muestra el conflicto a la persona.
- Si preferir `patch` sobre reescritura completa alcanza como mitigación, dado
  que igual es read-modify-write por debajo y la ventana sigue existiendo.
- Si conviene que el mapa se escriba una sola vez al final de la sesión, en vez
  de varias veces, para achicar la ventana.

## Agregado por el ticket 03

Este ticket ya tiene su punto de enganche nombrado. El 03 decidió que **leer y
actualizar el mapa es una sola operación**, un read-modify-write, precisamente
porque nombrar solo la mitad que escribe dejaba la que lee sin dueño y este ticket
se cuelga de la lectura.

Lo que el 03 dejó fijo y este ticket no revisita:

- El cliente es **GraphQL crudo**, así que el `patch` del MCP no está disponible y
  tampoco hace falta discutirlo. El plugin hace el read-modify-write él mismo, y
  eso es a favor de este ticket: la ventana entre leer y escribir es código
  nuestro, no el interior de una herramienta de terceros.
- `document(id:)` devuelve `content` y `updatedAt` en la misma lectura, así que
  capturar el `updatedAt` no cuesta un round-trip extra.
- Las anclas de edición se toman de lo que devuelve la API, nunca de lo que el
  plugin creyó escribir.
- En resolver y en sacar de alcance, el mapa es el **último** write de los tres. Un
  fallo al escribir el mapa deja la respuesta y el estado ya guardados, así que la
  estrategia que elija este ticket puede abortar sin perder trabajo.

Lo que sigue siendo de este ticket: qué hace el plugin cuando el `updatedAt`
cambió entre la lectura y la escritura.

## Hecho cuando

Está decidida la estrategia de escritura del mapa, con el caso de la edición
humana concurrente resuelto de alguna forma explícita, aunque sea abortar y
avisar.

---

# Resolución

Tres rondas de grilling, quince preguntas, frontera del árbol vacía.
Deliverable: [`research/09-la-escritura-del-mapa.md`](../research/09-la-escritura-del-mapa.md).
Harness: [`research/09-scripts/drift_probe.py`](../research/09-scripts/drift_probe.py).

## La decisión

**La estrategia no detecta el conflicto: lo evita.** El plugin no usa como base
de su escritura el contenido que leyó al empezar la sesión. Lee de nuevo justo
antes de escribir y aplica su edición como operaciones ancladas sobre ese
contenido fresco. La edición de la persona sobrevive porque está en la base sobre
la que el plugin escribe. La ventana de riesgo baja de la duración de una sesión
a **332 ms medidos**, mediana de ocho corridas.

Las tres preguntas que el ticket dejaba abiertas quedan contestadas, y la primera
al revés de lo que suponía:

- **¿Alcanza con comparar `updatedAt`?** No, y no por poco. Está coalescido:
  medido, quedó quieto **300 segundos** con contenido nuevo ya persistido y
  legible. Es inservible como señal. La señal es `content`, que sí está medido
  read-your-writes (6/6) y estable entre lecturas (seis lecturas, mismo hash).
- **¿Qué hace cuando detecta deriva?** Nada, porque ya la incorporó. Lo único que
  hace es contarla: una línea por sección que la persona tocó, sin diff.
- **¿Escribir una sola vez al final achica la ventana?** El 03 y el 06 ya habían
  dejado el mapa como escritura única y última de cada comando. Lo que faltaba no
  era la escritura sino **la lectura**, y ahí estaba toda la ventana.

Lo demás que quedó fijo:

- **Tres primitivas**: `append-line`, `remove-bullet`, `fill-section`. `Destino` y
  `Notas` quedan fuera del conjunto, y su edición humana se preserva sola.
- **Seis anclas**, los seis encabezados del DD, texto exacto. Nunca viñetas ni
  URLs, porque está medido que el serializador las reescribe. Si un ancla no
  resuelve, aborta y muestra el texto que iba a escribir.
- **La clave de una viñeta de niebla es su título en negrita**, y tiene que
  aparecer exactamente una vez. Eso vuelve el título una clave única de la
  plantilla.
- **Idempotencia asimétrica**: `remove-bullet` ausente es no-op, `append-line`
  duplicado aborta. Sacar dos veces converge, agregar dos veces diverge.
- **`map:read-write` se parte en dos subcomandos.** `map:read`, solo lectura, para
  el paso 2 de `/map-work` y para `/map-status`. `map:write`, que hace el
  read-modify-write entero **adentro de una sola invocación**, con la edición como
  argumentos semánticos. El modelo compone las líneas; el script las coloca, y
  nunca ve el markdown del mapa.
- **Los flags de `map:write` son atómicos entre sí.** Una resolución agrega la
  decisión y saca la niebla en un solo cambio lógico. Gratis, porque las
  primitivas operan en memoria antes del único `documentUpdate`.
- **El reporte de deriva usa huellas por sección**, seis hashes que `map:read`
  emite y `map:write` compara. No un sidecar en disco, que sería un segundo lugar
  donde vive el mapa.
- **Un reintento**, y en su camino la regla de idempotencia se invierte: "ya
  aplicado" es éxito. Sin eso, un timeout termina reportando error sobre un mapa
  que quedó correcto.

## Por qué

Porque detectar y abortar le devuelve el problema a la persona, y re-derivar
sobre contenido fresco lo resuelve sin que nadie decida nada. La medición decidió
la forma: si `updatedAt` hubiera funcionado, comparar habría sido más barato que
re-derivar. No funciona, y `content` sí, y una vez que la base de la escritura es
una lectura fresca la comparación deja de hacer falta para nada más que avisar.

La parte que no es obvia es la de dónde vive el read-modify-write. Sin eso la
estrategia es un dibujo: si el modelo lee, piensa y después escribe, la ventana
es su tiempo de pensar. Los 332 ms solo existen si las dos mitades ocurren en la
misma invocación del script, y por eso `map:write` recibe argumentos semánticos
en vez de markdown.

## Niebla graduada

Ninguna. Este ticket **nació** de la niebla, graduado por el research del 02, y no
vació ningún parche nuevo del mapa.

Sí le puso un costo concreto a una niebla que sigue abierta: **cuándo el plugin
escribe como app y no como persona**. `Document.updatedBy` existe y en papel
resolvería la autoría de la última edición, pero con Personal API key el plugin
escribe como la misma persona que edita en la UI, así que no distingue nada. La
niebla no se puede formular mejor todavía, pero ahora se sabe qué se gana el día
que se despeje.

## Tickets nuevos

- [13: Si una pestaña abierta puede pisar una escritura del plugin](13-pestana-abierta-pisa-al-plugin.md),
  `map:task`, HITL. Es la falla inversa y la única que esta estrategia no cubre.
  No se pudo medir en esta sesión porque necesita una persona escribiendo en el
  navegador.
- [14: Si el preflight es por invocación o por sesión](14-preflight-por-invocacion.md),
  `map:grilling`. Lo volvió visible la decisión de partir el adapter en
  subcomandos que son procesos.

## Qué corrige o empuja

**Al research del 02**, tres cosas. Su mitigación no funciona: releer sí, pero
comparando contenido y no `updatedAt`, y el `patch` del MCP quedó fuera del camino
desde que el 03 eligió GraphQL crudo. El historial de versiones no es la red de
seguridad que describía, porque se coalesce en una entrada que sigue creciendo y
no salva una edición individual pisada dentro de la ventana. Y su inventario de
campos de `Document` no listaba `updatedBy`.

**A la afirmación chequeable número 10 del ticket 06**, que dice que
`scripts/linear.py` tiene diez subcomandos. Son **once**: `map:read-write` se
parte en `map:read` y `map:write`. La invariante de un subcomando por operación se
mantiene; cambia el número.

**A la secuencia de los tres comandos que el 08 y el 06 fijaron.** Los tres ganan
una segunda lectura inmediatamente antes de escribir, la que ocurre adentro de
`map:write`. Incluido `/map-new`, que parecía exento por crear el Document y no lo
está: lo crea en el paso 4 y lo escribe en el paso 7, con los subagentes de
research en el medio.

**A `CONTEXT.md`**, dos cosas. La operación `map:read-write` se parte en dos, así
que las operaciones pasan de diez a once. Y `frontier:query` deja de ser "la única
operación que no escribe", porque ahora `map:read` tampoco.

**Al ticket 10**, las afirmaciones chequeables 22 a 29, y la corrección de la 10.
