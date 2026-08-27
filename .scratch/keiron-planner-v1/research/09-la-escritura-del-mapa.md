# 09: La escritura del mapa, y cómo no pisar a una persona

Resolución del ticket 09. Fecha: 2026-08-27.

Este documento **se reparte**, como el del 08 y a diferencia del reference del
03: el contrato de las dos operaciones va a `LINEAR-OPERATIONS.md` al lado del
adapter, y la regla de las anclas a `skills/_shared/map-contract.md`. Es una
fuente, no un archivo destino.

Va en español con los términos canónicos en inglés. Su lector es el dev leader
que mantiene el adapter.

---

## El resumen, en un párrafo

Linear no da control de concurrencia sobre Documents, y el research del 02
propuso mitigarlo releyendo y comparando `updatedAt`. **Medido, eso no
funciona**: `updatedAt` está coalescido y puede quedar quieto cinco minutos
enteros con contenido nuevo ya persistido. Así que la estrategia no es detectar
el conflicto sino no tenerlo. El plugin no usa como base lo que leyó al empezar
la sesión: lee de nuevo justo antes de escribir, y aplica su edición como
operaciones ancladas sobre ese contenido fresco. La edición de la persona
sobrevive porque está en la base sobre la que el plugin escribe. La ventana de
riesgo baja de la duración de una sesión a **332 milisegundos medidos**. Para
que esos milisegundos sean reales, el read-modify-write ocurre entero adentro de
una sola invocación del script, con la edición pasada como argumentos
semánticos: el modelo nunca compone el markdown del mapa.

---

## 1. Por qué `updatedAt` no sirve, medido

El ticket preguntaba si alcanza con releer y comparar `updatedAt`. La respuesta
es no, y no por poco.

Harness: [`09-scripts/drift_probe.py`](09-scripts/drift_probe.py), stdlib sola,
subcomandos `fields`, `mutations`, `roundtrip`, `stamp`, `history`, `cost`.
Todo contra el Document sandbox del ticket 01 (`8d748d5c-0a07-4906-8a04-e02868d0d1e0`,
`documentContentId` `3492fb4f-5c48-45c7-959e-cf32b471eccd`) con la Personal API
key.

### `Document.updatedAt` está coalescido

Serie de cinco escrituras espaciadas 0, 3, 10, 30 y 65 segundos:

| Escritura | Espera | `updatedAt` tras la relectura | |
| --- | --- | --- | --- |
| 1 | 0 s | `16:01:32.268Z` | |
| 2 | 3 s | `16:01:32.268Z` | quieto |
| 3 | 10 s | `16:01:32.268Z` | quieto |
| 4 | 30 s | `16:02:36.228Z` | se movió, salto de ~64 s |
| 5 | 65 s | `16:02:36.228Z` | quieto |

Y la medición larga, que es la que cierra el caso: **una** escritura por API,
con el contenido nuevo confirmado visible en la relectura inmediata, y después
muestreo de `updatedAt` cada 5 segundos durante 300 segundos. **No se movió ni
una vez.** Quedó clavado en `16:06:42.822Z` los cinco minutos completos.
Registro en [`09-scripts/lag.out`](09-scripts/lag.out).

Eso no lo deja como una señal de grano grueso, utilizable para un chequeo
barato. Lo deja **inservible**: el falso negativo dura minutos, así que ni
siquiera admite el patrón "si `updatedAt` se movió, confirmo con el contenido".

### `content` sí sirve

Dos propiedades medidas, y hacen falta las dos:

- **Read-your-writes inmediato.** Seis escrituras, cada una con un marcador
  único, y las seis veces el marcador estaba en la relectura inmediata. 6/6.
- **Estable entre lecturas.** Seis lecturas seguidas sin ninguna escritura en el
  medio: el mismo `sha256` las seis veces (`bccc7b1e4e2febc0`, 364 bytes).

Sin la primera habría falsos negativos; sin la segunda, falsos positivos. Con
las dos, comparar el contenido de dos lecturas es una señal exacta.

### El round-trip no es identidad

Se escribió markdown con viñetas `-` y links `[t](url)`. Volvió con viñetas `*` y
URLs envueltas en `<>`:

```diff
- - [01: algo](https://linear.app/keiron/issue/CRM-1): una linea con tildes, ñ y
+ * [01: algo](<https://linear.app/keiron/issue/CRM-1>): una linea con tildes, ñ y
```

Confirma y afila la regla que el 03 ya había escrito: **la base de la edición es
lo que devuelve la API, nunca lo que el plugin creyó escribir.** Y decide la
Q3: se puede anclar por encabezados, que vuelven intactos, y no por viñetas ni
por URLs, que el serializador reescribe.

Dato lateral que se midió y no se usa: los comentarios HTML **sí** sobreviven el
round-trip. Un fingerprint oculto en el documento es técnicamente posible. Se
descarta igual, porque la comparación por secciones de la sección 5 da lo mismo
sin ensuciar un documento que leen personas.

### `updatedBy` existe, y no distingue nada

El research del 02 no lo vio: `Document` tiene 28 campos de salida e incluye
`updatedBy`. En papel resolvería el problema, porque diría quién tocó el mapa
último. En la práctica no, y la razón es el ticket 07: con Personal API key el
plugin escribe **como la misma persona** que edita en la UI. `updatedBy`
devuelve el mismo usuario en los dos casos.

Queda anotado como el primer costo concreto de la niebla "cuándo el plugin
escribe como app y no como persona". El día que el mapa lo mantenga una cuenta
de bot, `updatedBy` pasa a ser una señal real.

### El historial no es la red de seguridad que parecía

Corrección de un error propio antes que nada: `documentContentHistory(id:)` toma
el **`documentContentId`**, no el id del `Document`. Con el id del Document
devuelve cero entradas y parece que no hay historial.

Con el id correcto sí hay, pero es más débil de lo que el 02 esperaba: **cinco
entradas para unas veinte escrituras**, y las entradas se coalescen. La más
nueva tiene `createdAt` `16:01:31.588Z` y `contentDataSnapshotAt` `16:07:00.113Z`:
una sola entrada cuyo snapshot se sigue moviendo hacia adelante.

La consecuencia importa. Si una persona escribe a las 16:03 y el plugin la pisa
a las 16:04, las dos ediciones caen dentro de la misma entrada coalescida y **no
hay snapshot intermedio al que volver**. "Se puede revertir desde la UI" no
salva una edición individual. `contentData` sí viene completo (3623 caracteres
en el caso medido) y cuesta 4 de complejidad.

### El input sigue sin control de concurrencia, re-verificado

`DocumentUpdateInput` tiene 17 campos y ninguno es `version`, `etag`,
`expected*`, `lastSyncId`, `ifUnmodified`, `contentState`, `revision` ni `draft`.
Solo hay cuatro mutations de Document (`create`, `update`, `delete`,
`unarchive`), y cero mutations con `draft`, `revision` o `checkpoint` en el
nombre: la maquinaria de borradores de Linear sigue cerrada al público.

Y un detalle que muerde: **la mutation devuelve un `updatedAt` rancio.**
`documentUpdate` devolvió `02:42:36.408Z`, el valor previo a la escritura,
mientras una relectura inmediata daba `16:01:31.181Z`. El plugin no puede
encadenar escrituras usando el timestamp que le devuelve la mutation.

---

## 2. La estrategia: releer tarde y re-derivar

Hay dos familias de solución y se eligió la segunda.

**Snapshot y comparación** es lo que el ticket proponía: leer al empezar,
releer antes de escribir, comparar, y si difiere abortar o preguntar. Detecta el
conflicto. La ventana de riesgo es toda la sesión.

**Releer tarde y re-derivar** no detecta el conflicto: lo evita. El contenido que
se leyó al empezar la sesión **no es la base de la escritura**. Justo antes de
escribir, el plugin lee fresco y aplica su edición como operaciones ancladas
sobre *ese* contenido. La edición de la persona sobrevive sola, porque está en la
base sobre la que el plugin escribe.

La comparación no se tira. Se degrada de mecanismo a diagnóstico: sirve para
avisarle a la persona que su cambio entró, nunca para decidir si escribir.

### La ventana, medida

Ocho corridas de read, aplicar, write en un solo proceso:

| | Lectura | Aplicar en memoria | Ventana lectura → fin de escritura |
| --- | --- | --- | --- |
| mediana | ~240 ms | 0,0 ms | **332 ms** |
| mínimo | 226 ms | 0,0 ms | 317 ms |
| máximo | 434 ms | 0,0 ms | 391 ms |

Es una **cota superior**: mide hasta que vuelve la respuesta de la escritura, y
la ventana de riesgo real termina cuando la escritura llega al servidor.

Aplicar la edición en memoria cuesta cero. Todo el costo es de red, y por eso la
sección 4 importa tanto: si el modelo piensa en el medio, esos 332 ms se vuelven
minutos y la estrategia se cae.

---

## 3. Las tres primitivas, y las seis anclas

### Las anclas son los seis encabezados

Texto exacto, y son contrato. El 08 fijó cinco, el 06 agregó el sexto:

```markdown
## Destino
## Notas
## Decisiones hasta ahora
## Aún no especificado
## Fuera de alcance
## El colapso
```

El plugin ancla por esos títulos, nunca por posición ni por índice de línea, y
si falta alguno falla fuerte. Adentro de la sección opera por posición. **Nunca
un ancla que dependa de una viñeta o de una URL**, porque está medido que el
serializador las reescribe.

### Las primitivas son tres

| Primitiva | Sección | Quién la emite |
| --- | --- | --- |
| `append-line` | `## Decisiones hasta ahora` | `ticket:resolve`, y `/map-new` con las líneas de los research |
| `append-line` | `## Fuera de alcance` | `ticket:rule-out` |
| `append-line` | `## Aún no especificado` | una resolución que crea niebla nueva |
| `remove-bullet` | `## Aún no especificado` | una resolución cuya niebla graduó |
| `fill-section` | `## El colapso` | `/map-collapse`, una vez |

**`## Destino` y `## Notas` quedan fuera del conjunto.** No es que nunca cambien:
nuestro propio mapa v1 tiene una corrección a `Notas`, escrita al resolver el
ticket 06. Es que esa corrección es una **edición humana**, no una operación del
plugin. La escribe la persona en la UI y la estrategia de la sección 2 la
preserva sola. Meter "editar Notas" en el conjunto le daría al plugin permiso de
reescribir justo la sección que, según el 08, no otorga permisos.

### La clave de una viñeta de niebla es su título en negrita

Las viñetas de niebla tienen la forma `- **Título en negrita.** Cuerpo`, a veces
de varias líneas. `remove-bullet` las identifica por ese título, texto exacto, y
**tiene que aparecer exactamente una vez**. Cero coincidencias o más de una es
falla de ancla.

Es la misma regla que el MCP de Linear impone en su `patch`, y el 02 ya avisó por
qué: para un documento generado, un ancla ambigua es el modo de falla probable.

Consecuencia para la plantilla, y es dura: **el título en negrita de una viñeta
de niebla es una clave.** `map-templates.md` no puede permitir dos nieblas con el
mismo título.

### Idempotencia, y es asimétrica a propósito

Con la estrategia de la sección 2 el plugin escribe sobre contenido fresco que
puede incluir trabajo humano, incluido trabajo que ya hizo lo que el plugin venía
a hacer.

- **`remove-bullet` cuyo objetivo ya no está: no-op, con línea de reporte.** El
  estado final deseado ya se cumple. Abortar una resolución porque alguien hizo
  la mitad del trabajo a mano es el plugin siendo pedante.
- **`append-line` que ya está: falla de ancla, aborta.** Agregarla de nuevo deja
  la misma decisión dos veces en el índice, que es exactamente el daño silencioso
  que este ticket existe para evitar. El append chequea primero si su enlace al
  ticket ya está en la sección.

La asimetría es la decisión, no un descuido: sacar dos veces converge, agregar
dos veces diverge.

### Cuando un ancla no resuelve

Con esta estrategia el modo de falla ya no es pisar. Es no encontrar dónde
escribir, y pasa si la persona renombró un encabezado o reescribió la viñeta de
niebla que el plugin venía a sacar.

**Aborta, dice cuál ancla falló, y muestra el texto que iba a escribir.** Es
HITL, hay una persona sentada. Y el 03 dejó el mapa como último write de los
tres, así que abortar no pierde nada: la respuesta y el estado ya están
guardados.

Se descarta explícitamente escribir al final del documento como recurso. Un mapa
con una decisión huérfana fuera de su sección se ve bien y está mal, y esa es la
peor clase de resultado.

---

## 4. Dónde vive el read-modify-write

Esta es la decisión que hace que la sección 2 sea real y no un dibujo.

El 08 decidió que el adapter es `scripts/linear.py` y que el modelo lo llama por
Bash. Si el modelo lee con una llamada, piensa, y escribe con otra, **la ventana
es el tiempo de pensar del modelo**: segundos o minutos, no los 332 ms medidos.

Así que son dos subcomandos, y la diferencia entre ellos es el punto entero:

**`linear.py map:read`** es solo lectura y no escribe nunca. Lo usan el paso 2 de
`/map-work` y `/map-status`.

**`linear.py map:write`** hace el read-modify-write completo **adentro de una
sola invocación**, sin volver al modelo en el medio. Recibe la edición como
argumentos semánticos:

```
linear.py map:write --doc <id> \
  --append-decision "<línea>" \
  --remove-fog "<título en negrita>" \
  --expect-sections '<json de seis hashes>'
```

El modelo compone **las líneas**; el script las **coloca**. El modelo nunca ve ni
compone el markdown del mapa entero.

Esto cobra lo que el 03 ya había decidido al nombrar `map:read-write` entero,
"porque sus dos mitades son la misma operación": son la misma operación **y la
misma llamada**.

### Los flags son atómicos entre sí

Una resolución típica hace dos cosas al mapa a la vez: agrega la línea a
Decisiones y saca la viñeta que graduó de la niebla. Van en **una** invocación,
aplicadas en orden fijo, todo o nada.

La edición del mapa de una resolución es **un** cambio lógico, no dos. Una
decisión aterriza y su niebla gradúa en el mismo movimiento, y un mapa donde la
decisión está pero la niebla sigue ahí es un mapa que miente.

La atomicidad sale gratis porque las tres primitivas operan en memoria: si
`remove-fog` falla el ancla, no se emite ningún `documentUpdate` y no hay nada
que deshacer. Dos invocaciones, en cambio, serían dos ventanas y un estado
intermedio publicado.

---

## 5. El reporte de deriva, y cómo el script sabe qué comparar

Con la sección 4, el script solo ve **una** lectura, la suya, milisegundos antes
de escribir. No sabe con qué comparar para decir que hubo deriva.

Se eligió **huellas por sección**. `map:read` imprime seis hashes, uno por
encabezado. El modelo los pasa a `map:write --expect-sections`. El script hashea
las seis secciones de su lectura fresca, compara, y nombra las que difieren.

Las dos alternativas y por qué no:

- **El modelo devuelve el contenido.** Decenas de KB por la línea de comandos.
  Caro en tokens y frágil.
- **`map:read` deja un sidecar en disco** y `map:write` lo levanta. Es la
  tentadora, porque es barata y cero tokens. Choca de frente con el 03, que
  decidió que no se cachea nada porque la fuente de verdad es el tracker. Y peor:
  un sidecar es un segundo lugar donde vive el mapa, y el día que se desincronice
  nadie va a mirar ahí.

Las huellas no violan la regla del 03, y la diferencia es exacta: no se está
cacheando datos para **leerlos** en vez de leer el tracker, se está guardando una
huella para **compararla**. Si la huella se pierde o llega mal, `map:write`
escribe igual y lo único que se pierde es el reporte, nunca la corrección.

### Qué se le dice a la persona

Una línea por sección tocada, sin diff:

```
El mapa cambió mientras trabajábamos: alguien editó `## Notas`.
Tu cambio quedó. La decisión se agregó igual.
```

Un diff completo en la salida de un comando es ruido que nadie lee y compite con
el reporte de cierre y su token. Y no filtrar por sección sería peor: si la
persona editó `Notas` y el plugin escribió en `Decisiones`, no hubo ningún
conflicto, y decirlo igual es correcto porque le confirma que su edición
sobrevivió.

**No hay aviso al empezar.** Con la ventana en 332 ms, un "no edites el mapa
mientras esto corre" pediría disciplina para un riesgo que ya no existe, y un
aviso que no hace falta enseña a ignorar los que sí.

---

## 6. El reintento, y el agujero que abre

Si el `documentUpdate` se corta por timeout o por un 500, el script no sabe si la
escritura llegó. Reintentar significa volver a correr el read-apply-write entero,
que es seguro por construcción, salvo por una cosa.

Si la primera escritura **sí** llegó, la relectura del reintento va a ver la
línea ya puesta, y la regla de idempotencia dice que un `append-line` duplicado
aborta. O sea: el reintento reportaría fracaso sobre una escritura que funcionó.

**Un solo reintento, y en el camino del reintento la regla se invierte: "ya
aplicado" es éxito, no falla.** El flag lo pone el script, no el modelo, así que
la excepción no se puede invocar desde afuera.

La asimetría de la idempotencia sigue valiendo donde importa, que es la primera
pasada: ahí un duplicado significa que alguien más lo puso y el plugin no debe
adivinar. En el reintento significa "fui yo hace 300 ms", que es otra cosa.

Sin esta salvedad, el modo de falla más probable de todos, un timeout, termina en
un reporte de error sobre un mapa que quedó correcto. Y la persona lo arregla a
mano y lo duplica de verdad.

---

## 7. Una sola política para los tres comandos

Los tres comandos que escriben el mapa lo escriben exactamente una vez, y los
tres tienen la forma de ventana larga que la sección 2 descarta. **Los tres ganan
una segunda lectura inmediatamente antes de escribir**, que es la que ocurre
adentro de `map:write`.

| Comando | Dónde estaba la lectura | Ventana antes | Ventana ahora |
| --- | --- | --- | --- |
| `/map-new` | crea el Document en el paso 4, lo escribe en el paso 7 | la duración de los subagentes de research | 332 ms |
| `/map-work` | `map:read-write`, la mitad que lee, en el paso 2 | la sesión entera | 332 ms |
| `/map-collapse` | escribe el mapa en el paso 3, tras N+2 writes | la duración del colapso | 332 ms |

`/map-new` merece una nota, porque el supuesto natural es que está exento: crea
el Document, así que no habría nada que pisar. Es falso. Lo crea en el paso 4 y
lo escribe en el paso 7, con los subagentes de research corriendo en el medio.
Esa ventana son minutos.

**El colapso no necesita una política propia**, aunque abortar ahí no cueste lo
mismo. En `/map-work` el mapa es el último de tres writes y abortar es gratis; en
`/map-collapse` es el último después de N+2, así que abortar deja milestones e
issues creados y el mapa sin marcar. Pero el 06 ya definió la recuperación del
colapso a medias, y un colapso que escribió todo y no pudo marcar el mapa cae en
ese caso: se retoma. La alternativa, una política especial que en el colapso
escriba igual para no dejar el estado a medias, es exactamente el "escribir al
final" que se descartó en la sección 3.

---

## 8. El alcance: solo el Document

`ticket:resolve` escribe tres cosas: un comentario, el estado del ticket y el
mapa. Este ticket cubre **solo el mapa**.

Un comentario es append-only: no hay nada que pisar. El estado del ticket es un
campo chico y el plugin es el único que lo escribe en esa transición. El Document
es la única superficie donde el plugin puede destruir prosa que escribió una
persona, y la única que se reescribe entera por diseño de la API.

---

## 9. Verificado contra no verificado

| Afirmación | Estado |
| --- | --- |
| `Document.updatedAt` está coalescido y no se mueve por escritura | Verificado. Serie de cinco escrituras espaciadas |
| `updatedAt` puede quedar quieto 300 s con contenido nuevo persistido | Verificado. Muestreo cada 5 s durante 300 s |
| `content` es read-your-writes inmediato | Verificado. 6/6 |
| `content` es estable entre lecturas sin escrituras | Verificado. Seis lecturas, mismo `sha256` |
| El round-trip reescribe viñetas y envuelve URLs | Verificado. Diff real |
| Los encabezados sobreviven el round-trip intactos | Verificado |
| Los comentarios HTML sobreviven el round-trip | Verificado |
| `Document.updatedBy` existe | Verificado. 28 campos de salida |
| `documentUpdate` devuelve un `updatedAt` previo a la escritura | Verificado |
| `DocumentUpdateInput` no tiene ningún campo de concurrencia | Verificado. 17 campos |
| No hay mutations de draft, revision ni checkpoint | Verificado. Cero coincidencias |
| `documentContentHistory` toma el `documentContentId`, no el id del Document | Verificado |
| Las entradas de historial se coalescen en una que sigue creciendo | Verificado. `createdAt` 16:01:31, `snapshotAt` 16:07:00 |
| La ventana read-aplicar-write es de 332 ms de mediana | Verificado. Ocho corridas |
| La relectura previa cuesta 2 de complejidad | Verificado |
| Si una edición humana en la UI mueve `updatedAt` o también viene coalescida | **No verificado.** Requiere una persona escribiendo en el navegador |
| Si una pestaña abierta con estado Yjs viejo puede **pisar** una escritura del plugin al re-sincronizar | **No verificado.** Es la falla inversa, y la única que esta estrategia no cubre. Graduó al ticket 13 |

---

## Lo que corrige o empuja

**Corrige al research del 02** en tres puntos:

1. **La mitigación que proponía no funciona.** El 02 cerró con "se mitiga
   releyendo antes de escribir y prefiriendo `patch` sobre reescritura completa".
   Releer antes de escribir sí, pero comparando contenido y no `updatedAt`; y el
   `patch` del MCP quedó fuera del camino desde que el 03 eligió GraphQL crudo.
2. **El historial de versiones no es la red de seguridad que describía.** Se
   coalesce, así que no salva una edición individual pisada dentro de la ventana.
3. **`updatedBy` existe** y el inventario de campos del 02 no lo listaba.

**Corrige la afirmación chequeable número 10 del ticket 06**, que dice que
`scripts/linear.py` tiene **diez** subcomandos, uno por operación. Con la
sección 4 son **once**: `map:read-write` se parte en `map:read` y `map:write`.
La invariante de un subcomando por operación se mantiene, pero el número cambia.

**Empuja al ticket 10.** Le deja las afirmaciones 22 a 29 de abajo, y le corrige
la 10.

**Empuja a la niebla "cuándo el plugin escribe como app y no como persona".** Le
da su primer costo concreto y medible: mientras la credencial sea Personal API
key, `updatedBy` no distingue al plugin de la persona.

**Anota, sin resolverlo, que el preflight puede ser por invocación.** Si cada
llamada a `linear.py` es un proceso, y el 08 dijo *un preflight por proceso que
emite operaciones*, entonces `/map-work` paga un preflight por operación y no uno
por sesión. Son 423 de complejidad medidos por preflight, contra un presupuesto
horario que el 02 midió como irrelevante, así que no es urgente. La sección 4 lo
volvió visible. Graduó al ticket 14.

---

## Las afirmaciones chequeables, para el ticket 10

Siguen la numeración: 1 a 6 del 08, 7 a 13 del 06, 14 a 21 del 07.

22. `scripts/linear.py` tiene **once** subcomandos, uno por operación nombrada en
    `LINEAR-OPERATIONS.md`, y ninguno de más. Entre ellos `map:read` y
    `map:write`. **Reemplaza a la afirmación 10 del ticket 06**, que decía diez.
23. `map:read` no contiene ninguna mutation. Grep de `mutation` en su ruta de
    ejecución: cero coincidencias.
24. `map:write` emite su `document(id:)` y su `documentUpdate` en la **misma
    función**, sin ningún punto de retorno al modelo entre los dos.
25. `map-templates.md` no tiene dos viñetas de niebla con el mismo título en
    negrita, y `map-contract.md` dice que el título es una clave única.
26. `map:write` acepta `--expect-sections` y su ausencia no aborta la escritura:
    solo suprime el reporte de deriva.
27. Ninguna ruta de `linear.py` lee ni escribe un archivo de estado del contenido
    del mapa. No hay sidecar.
28. `map:write` tiene exactamente un reintento, y la rama del reintento pasa el
    flag interno que convierte "ya aplicado" en éxito. Ese flag no está expuesto
    como argumento de línea de comandos.
29. Ninguna ruta de `linear.py` compara `updatedAt` para decidir si escribir.
    `updatedAt` puede pedirse y loguearse, nunca ramificar.
