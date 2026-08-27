# 09: Cómo evita el plugin pisar una edición humana del mapa

**Tipo:** `map:grilling` · **Modo:** HITL (`hitl:dev`)
**Bloqueado por:** nada. Tomable ahora.
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
