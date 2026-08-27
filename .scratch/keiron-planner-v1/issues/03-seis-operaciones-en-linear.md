# 03: Las operaciones de wayfinding, expresadas en Linear

**Tipo:** `map:grilling` · **Modo:** HITL (`hitl:dev`)
**Estado:** **RESUELTO** el 2026-08-27.
**Tomado por:** Luis Felipe Jaña (`hitl:dev`), sesión del 2026-08-26/27.

> El título decía "las seis operaciones". Son ocho. Ver la resolución.

## Pregunta

El doc de tracker de Matt define seis operaciones que todo tracker debe saber
hacer: crear el mapa, crear un ticket hijo, bloquear, consultar la frontera,
tomar y resolver. ¿Cómo se expresa cada una en Linear?

Estuvo bloqueado por 01 porque la consulta de frontera dependía de por dónde
leemos las relaciones, y por 02 porque crear y actualizar el mapa dependía de lo
que la API de Documents permitiera. Los dos están resueltos.

**Lo que el ticket 01 ya dejó resuelto de acá**: la consulta de frontera existe,
medida y probada, en
[`research/01-scripts/probe.py`](../research/01-scripts/probe.py). La operación de
consultar la frontera ya tiene su llamada concreta. Las otras cinco no.

## Lo ya decidido, que este ticket no revisita

El mapa es un Document `DD: <proyecto>` dentro de un Project. Los tickets de
decisión son issues del Project con label `map` más su tipo. El claim es el
assignee. Resuelto va a Done, fuera de alcance va a Canceled.

## Hecho cuando

> **Corregido al resolver.** El criterio original pedía "las seis operaciones con
> la llamada concreta que las implementa, y el fallback de cada una si la llamada
> no está disponible". Las dos mitades estaban mal. No son seis, son ocho. Y no
> hay fallbacks: eso Matt lo necesita porque sus docs cubren features de tier en
> dos trackers, y nosotros tenemos uno solo.

Existe el equivalente nuestro de la sección "Wayfinding operations": las ocho
operaciones con la llamada concreta que las implementa, más el preflight que
falla fuerte cuando algo que una operación necesita no está.

---

## Resolución

El documento completo es
[`research/03-operaciones-en-linear.md`](../research/03-operaciones-en-linear.md),
458 líneas. Es el artefacto que este ticket produce y el que se copia al plugin
cuando exista. Acá va lo que decidimos y por qué, no el detalle.

Tres rondas de grilling, dieciocho preguntas, frontera del árbol vacía.

### Son ocho, no seis

Faltaban dos, y las dos por la misma razón: existen en el flujo y no están en el
doc, así que el agente las improvisa cada vez.

- **Sacar de alcance** es otro id de estado y otra sección del mapa. Es además la
  única operación destructiva, porque cierra un ticket sin resolverlo.
- **Leer y actualizar el mapa** son las dos mitades de un read-modify-write, y se
  nombran juntas. Nombrar solo la que escribe deja la que lee sin dueño, y el
  ticket 09 necesita ese punto exacto para colgar su captura de `updatedAt`.

### Las decisiones

**El cliente es GraphQL crudo para las ocho.** Un solo cliente, un solo camino de
auth. El MCP de Linear queda fuera del camino crítico. Se pierde el azúcar `patch`
de `save_document` y no es pérdida: el plugin hace su propio read-modify-write, y
esa es justamente la ventana de control que el 09 necesita poder tocar.

**Cerrado es un par de ids, no un test de tipo.** Es la corrección que más pesa y
corrige al ticket 01. Detalle abajo.

**Los ocho labels son planos y workspace-level.** `map`, `map:research`,
`map:prototype`, `map:grilling`, `map:task`, `hitl:pm`, `hitl:design`,
`hitl:dev`. Nada de label groups de Linear: un grupo no se puede aplicar a un
issue, así que no existiría el label `map` sobre el ticket y la frontera tendría
que filtrar por padre. Se pierde la exclusividad de tipo que dan los grupos, y
pasa a ser un check estructural.

**La identidad del mapa viaja como URL y no se persiste nada.** Medido:
`project(id:)` y `document(id:)` aceptan el UUID, el `slugId` pelado y el slug
completo de la URL, y el Document del mapa viene en la misma query que el
Project. Es la única opción que sobrevive al polyrepo: con once repos, un pointer
file commiteado obliga a contestar en qué repo vive el mapa de un proyecto que
cruza cuatro.

**Un preflight por sesión, que no cachea nada.** Resuelve el `viewer`, los dos ids
de estado y los ocho ids de label, y crea los labels que falten. Un round-trip,
423 de complejidad. Un caché acá compra milisegundos y paga con un modo de fallo
que solo aparece cuando alguien tocó el workflow del team.

**Sin fallbacks.** El preflight falla fuerte y temprano en su lugar. Un fallback
que nunca se ejercita es un segundo camino de código que se pudre.

**El último write es el que hace visible la operación.** Resolver es comentario,
después estado, después mapa: si la sesión muere en el medio, la respuesta ya
está escrita y el ticket se puede volver a resolver. El orden inverso deja un
ticket en Done sin respuesta, que es un agujero que nadie ve.

**La resolución va como comentario**, no en el cuerpo del ticket. La pregunta
queda inmutable y la respuesta gana autor y timestamp gratis.

**El orden de la frontera es `createdAt` ascendente**, en el cliente.
`Issue.sortOrder` no sirve: medido, ascendente da el orden inverso al de creación,
y mover un issue a Done le reescribió el `sortOrder` de `-468154` a `-1020138`.

**Una toma huérfana no se libera sola.** `/map-status` la reporta con su
antigüedad y la persona desasigna. Liberar automático rompería la única garantía
que la toma da.

**Frontera vacía no significa una sola cosa.** Sin tickets abiertos, el mapa está
listo para colapsar. Con tickets abiertos, está trabado, típicamente por un ciclo.
Son opuestos y se ven igual, y la detección es gratis porque el subgrafo entero ya
vino en el round-trip.

### El defecto que este ticket le encontró al 01

El 01 dejó escrito que cerrado es `state.type in (completed, canceled)`. Contra el
team CRM eso está mal, y el sandbox del 01 no lo podía ver porque solo usó Backlog
y Done.

El team CRM tiene **dos estados de tipo `canceled`**: `Canceled` en position 4 y
**`Blocked`** en position 3948.38. `Blocked` está en uso real, CRM-2766 está ahí
ahora. Un ticket parkeado en `Blocked` es semánticamente lo más abierto que hay, y
el test por tipo lo lee como cerrado. Falla dos veces y en silencio: un ticket
cuyo bloqueante alguien movió a `Blocked` aparece tomable, y un ticket de mapa
movido a `Blocked` se cae de la frontera como si estuviera resuelto.

Por eso cerrado es exactamente los dos estados que el plugin escribe, resueltos a
id por el preflight. Falla del lado seguro: un ticket arrastrado a `Blocked` queda
abierto y visible.

El reporte del ticket 01 quedó enmendado con esto.

### Lo que se midió

El predicado corregido corre contra el sandbox del 01 y clasifica bien sus cinco
ramas, ahora en orden de creación. Harness en
[`research/03-scripts/frontier.py`](../research/03-scripts/frontier.py), con
subcomandos `preflight` y `frontier`. La frontera pesa 3.847 de complejidad, menos
que la versión del 01, con 61% de aire contra el techo de 10.000.

La única escritura de esta sesión fue autorizada y revertida: un label descartable
creado y borrado para saber si una Personal API key puede crear labels
workspace-level. Puede, `team` vuelve `null`, y no hace falta permiso de admin.
Eso resuelve de raíz cómo llega el label `map` a un team, porque no hay que
llevarlo a ninguno.

### Lo que este ticket no decide

- Cómo se hace segura la escritura del mapa frente a una edición humana
  concurrente. Es el [09](09-concurrencia-humano-plugin.md), y ahora tiene el
  punto de enganche nombrado.
- Dónde vive el script del adapter y cómo llega la key. Es el
  [07](07-distribucion-e-instalacion.md).
- Qué comando invoca cada operación y en qué orden. Es el
  [08](08-los-dos-modos-keironizados.md), que este ticket desbloquea.
