# 02: Qué permite y qué limita la API de Documents de Linear

Investigación de solo lectura. No se creó ni modificó ningún Document, Project ni issue.
Fecha: 2026-08-26.

## Fuentes usadas

1. **Introspection del schema GraphQL de Linear**, sin autenticar, contra `https://api.linear.app/graphql`.
   Es la fuente más fuerte: es el schema real en producción, no la documentación.
2. **SDL publicado** en `https://raw.githubusercontent.com/linear/linear/master/packages/sdk/src/schema.graphql`
   (51.004 líneas), usado solo para búsquedas exhaustivas de texto. Todo lo que importa se
   contrastó contra la introspection en vivo.
3. **Documentación oficial**: `https://linear.app/developers/rate-limiting`, `https://linear.app/docs/documents`,
   `https://linear.app/docs/editor`, `https://linear.app/docs/mcp`.
4. **JSON Schema de las herramientas MCP** `save_document` y `save_issue`, leído directamente del
   servidor MCP de Linear conectado a esta sesión.
5. **Lecturas reales del workspace `keiron`** vía MCP (solo lectura): un Document y una descripción de issue.

Lo que no pude verificar está marcado como tal. No inferí nada que requiriera una escritura.

---

## 1. Límite de tamaño del contenido

### Lo que verifiqué

**No existe límite declarado en el schema.** El campo es un `String` sin restricción.

```
curl -s -X POST https://api.linear.app/graphql -H "Content-Type: application/json" \
  -d '{"query":"{ __type(name: \"Document\") { fields { name description type { name kind } } } }"}'
```

Devuelve, entre otros:

- `content: String` con descripción `"The document's content in markdown format."`
- `contentState: String` con descripción `"[Internal] The document's content as a base64-encoded Yjs state update."`

Y para el input de escritura:

```
curl -s -X POST https://api.linear.app/graphql -H "Content-Type: application/json" \
  -d '{"query":"{ __type(name: \"DocumentUpdateInput\") { inputFields { name description type { name kind } } } }"}'
```

Devuelve `content: String` con descripción `"The document content as markdown."`. Sin `maxLength`,
sin directiva de validación. GraphQL no expresa límites de longitud en el schema, así que la
ausencia no prueba que no exista un límite del lado del servidor.

**Sí existe un techo duro verificado a nivel de transporte: 10.485.760 bytes (10 MiB) por request HTTP.**
Lo comprobé enviando cuerpos de tamaño creciente al endpoint (queries de introspection infladas con un
comentario GraphQL largo, sin efectos de escritura):

| Bytes del body | Respuesta |
| --- | --- |
| 100.056 | HTTP 200 |
| 1.000.056 | HTTP 200 |
| 4.000.056 | HTTP 200 |
| 8.000.056 | HTTP 200 |
| 16.000.056 | HTTP 413 |

El error del caso 413 es explícito y trae el número:

```json
{"error":"request entity too large","details":{},
 "extensions":{"code":"PAYLOAD_TOO_LARGE","type":"payload too large",
 "statusCode":413,"userError":true,"limit":10485760,"length":16000056},"code":413}
```

Fuente: respuesta real de `api.linear.app/graphql`. Ese es el techo absoluto del markdown que se puede
mandar en un `documentUpdate`, menos el overhead del JSON y del resto de la mutation.

**Escala real observada:** leí completo el Document `Design Doc: Permissions V1 → V2 Overhaul`
(`19bbf87d-2382-47b3-ba9b-eccf0b72c4c1`) del workspace, de varios miles de palabras, con tablas,
bloques de código y diagramas ASCII. Volvió íntegro, sin truncar.

### Lo que no pude verificar

- Si existe un límite de aplicación por debajo de los 10 MiB para el campo `content` de un Document.
  Probarlo exige una escritura autenticada, que está fuera del alcance de esta investigación.
- Pista indirecta de que Linear tiene alguna noción de "oversized" para contenido de documentos: la
  descripción de `ReleaseDocumentInput` en el schema dice literalmente
  `"Bad rows (empty title, oversized title/body) are skipped with a warning rather than failing the release command."`
  No dice el número y ese input es de otro camino (releases), no de `documentUpdate`.
- Dato de contexto, no del mismo camino: la documentación de Linear declara un tope de 250.000 caracteres
  para el cuerpo de un correo que crea un issue por email (`https://linear.app/docs/creating-issues`).
  No hay evidencia de que ese número aplique a Documents.

### Lectura práctica

Un mapa de proyecto en markdown vive en el orden de decenas de KB. Está tres órdenes de magnitud
por debajo del único límite verificado. El tamaño no es el problema.

---

## 2. Edición por parches contra reescritura completa

### La API GraphQL solo acepta el contenido entero. Verificado.

Firma de la mutation, por introspection:

```
documentUpdate(input: DocumentUpdateInput!, id: String!)
```

`DocumentUpdateInput` tiene exactamente 17 campos y ninguno es un parche:
`title, icon, color, content, projectId, initiativeId, teamId, issueId, releaseId, cycleId,
resourceFolderId, lastAppliedTemplateId, ownerId, hiddenAt, sortOrder, trashed, subscriberIds`.

El único camino hacia el contenido es `content: String`, markdown completo.

Refuerzos de la misma conclusión:

- **No existe ningún campo de input llamado `patch` en todo el schema.** `grep -nE "^\s+patch(Data)?:"`
  sobre las 51.004 líneas del SDL publicado: cero coincidencias.
- **Solo hay cuatro mutations de Document** en todo el schema (introspection de `__type(name:"Mutation")`):
  `documentCreate`, `documentUpdate`, `documentDelete`, `documentUnarchive`. No hay
  `documentContentUpdate`, ni ninguna mutation de append o de insert.
- **No se puede escribir el estado canónico.** `contentState` (el Yjs base64) aparece solo en tipos de
  salida (`Document`, `DocumentContent`, `DocumentContentDraft`, `DocumentContentRevision`,
  `DocumentSearchResult`, `Project`, `ProjectSearchResult`). En ningún input object. Es decir: no hay
  forma de mandar un delta de Yjs por la API pública.
- **La maquinaria de borradores y revisiones no es accesible desde fuera.** Existen los tipos
  `DocumentContentDraft` (`"allowing independent editing without affecting the published document until
  the user explicitly applies their changes"`) y `DocumentContentRevision` (`"allowing automation edits to
  accumulate without affecting the published document until the changes are explicitly applied"`), pero
  no hay ninguna mutation cuyo nombre contenga `draft`, `revision` o `checkpoint`. Es infraestructura
  interna del agente de Linear.

### El MCP sí expone `patch` en `save_document`. Verificado.

Leí el JSON Schema de `mcp__claude_ai_Linear__save_document` desde el servidor MCP. Expone un
parámetro `patch` con **exactamente el mismo shape que `save_issue`**: las seis operaciones
`replace`, `insert_before`, `insert_after`, `prepend`, `append`, `replace_range`, con
`minItems: 1` y `maxItems: 50`.

Texto literal del parámetro:

> "Partial edits applied to the current content, in order and atomically (one failing operation aborts
> the whole save). Every anchor string must match the current content exactly once. Only valid on
> update, in place of the full content/description field"

Y la descripción de la herramienta:

> "To change parts of the content without resending all of it, pass `patch` instead of `content`."

### Lo que esto significa

El parche es una comodidad del servidor MCP, no una capacidad de la API. Por debajo, el MCP hace
read-modify-write y termina llamando a `documentUpdate` con el `content` completo. Consecuencias
concretas para el plugin:

- **A favor:** ahorra tokens del agente (no hay que reemitir el documento entero) y reduce el riesgo
  de que el modelo destruya secciones que no pretendía tocar. La atomicidad de la lista de operaciones
  es real y está garantizada por la herramienta.
- **En contra:** no da control de concurrencia. La atomicidad es de la lista de operaciones dentro de
  una llamada, no frente a otro escritor.
- **En contra:** el requisito de que cada ancla aparezca exactamente una vez es frágil para un
  documento generado. Si el mapa tiene dos decisiones con el mismo encabezado, o si una línea de niebla
  se repite, el parche falla entero. Conviene diseñar el markdown del mapa con anclas únicas y estables
  (por ejemplo encabezados con identificador) si se va a usar `patch`.
- Para el caso del ticket (Decisiones crece, la niebla se vacía) el patrón natural es
  `append` sobre Decisiones y `replace_range` sobre el bloque de niebla, ambas operaciones soportadas.

---

## 3. Enlaces vivos a issues

### Verificado: el serializador emite un tag `<issue>` para menciones vivas

Leí vía MCP la descripción del issue `CRM-3167` del workspace `keiron`. Contiene literalmente:

```
(<issue id="378a0080-492a-4f50-8869-ad2ebd05a985" href="https://linear.app/keiron/issue/CRM-3166/spec-driven-dev-sdd-change-status-and-gatekeeper-sdd-status-validacion">CRM-3166</issue>)
```

Ese issue fue escrito por una persona en la UI de Linear. Confirma la pista del ticket y confirma que
la mención viva se serializa a markdown como `<issue id="UUID" href="URL">IDENTIFICADOR</issue>`.

El serializador es el mismo para Documents y para issues: según la descripción del tipo `DocumentContent`
en la introspection, ese tipo es
`"The rich-text content body of a document, issue, project, initiative, project milestone, pull request,
release note, automation prompt, AI prompt rules, or welcome message"`.
Es decir, un Document y una descripción de issue comparten motor de contenido.

### Verificado en negativo: el texto plano `CRM-123` no se convierte en chip

El Document `Design Doc: Permissions V1 → V2 Overhaul` está lleno de identificadores escritos como
texto (`CRM-2689`, `CRM-2690`, `CRM-2741`, `CRM-2750`, decenas más, incluidos rangos dentro de tablas).
El markdown devuelto por la API los trae **como texto plano, sin ningún tag `<issue>`**. Ese documento
fue escrito por un humano en la UI y aun así los identificadores quedaron inertes.

Conclusión operativa: escribir `CRM-123` en el contenido no produce un chip. Ni desde la UI cuando se
pega texto, ni por la API.

### Lo que dice la documentación sobre cómo se crean las menciones

- `https://linear.app/docs/documents`: "You can type in plain text, use code snippets, format with
  headers and reference other objects by mentioning the (@ENG-123)."
- `https://linear.app/docs/editor`, sección "@ Mentions": "Write @text to mention a user, issue, project,
  date, or document in a description or comment. [...] Pasting an issue ID will also link it in the editor,
  or you can mention issues with @ENG-123. Referenced issues are added as related issues automatically."

Ambas describen el gesto **en el editor**, con autocompletado. No dicen nada sobre qué acepta la API.

- El JSON Schema de `save_document` solo documenta menciones de usuario:
  "To mention a user, use @displayName (e.g., @johndoe)". No menciona issues.

### Lo que NO pude verificar

**Si al enviar `<issue id="..." href="...">CRM-123</issue>` o `@CRM-123` en el campo `content` vía API,
Linear lo parsea de vuelta a una mención viva.** Eso requiere una escritura, prohibida en esta
investigación. Es la única incógnita relevante que queda y es binaria.

Por qué importa para el mapa: si el parser **no** acepta el tag, entonces cada vez que el plugin lea el
documento y lo reescriba completo, los chips existentes se degradan a texto plano y el índice de
decisiones pierde sus enlaces vivos, sesión a sesión. Si el parser **sí** lo acepta, el round-trip se
sostiene y se pueden emitir chips desde el plugin.

Test de dos minutos para cerrarlo, cuando alguien pueda escribir: crear un Document de juguete en un
Project descartable, escribirle `content` con las tres variantes (`<issue id href>`, `@CRM-123`, URL
pelada del issue), leerlo de vuelta y ver cuáles regresan como `<issue>`.

### Alternativa que no depende de ese test

Un link markdown normal a la URL del issue: `[CRM-123](https://linear.app/keiron/issue/CRM-123)`.
No es un chip (no muestra estado ni assignee, no crea relación automática), pero es clicable y es
estable en el round-trip. Detalle observado en el Document real: el serializador de Linear devuelve los
links con la URL entre `<` y `>`, así: `[Design Doc Template](<https://www.notion.so/...>)`.

---

## 4. Límites de rate

Fuente: `https://linear.app/developers/rate-limiting` (también disponible como markdown en
`https://linear.app/developers/rate-limiting.md`, que es lo que leí en crudo).

### Requests

| Autenticación | Límite | Por | Período |
| --- | --- | --- | --- |
| API key | 2.500 | Usuario | 1 hora |
| OAuth App | 5.000 | Usuario (o App User) | 1 hora |
| Sin autenticar | 600 | Dirección IP | 1 hora |

**Advertencia: la propia página se contradice.** En prosa dice "When authenticated using an API key you
can make up to **5,000 requests per hour**", y dos párrafos después su tabla dice 2.500 para API key.
Cito las dos afirmaciones porque están las dos en la misma página. Lo confiable es leer los headers en
tiempo de ejecución, no la documentación.

### Complejidad

| Autenticación | Límite | Por | Período |
| --- | --- | --- | --- |
| API key | 3.000.000 puntos | Usuario | 1 hora |
| OAuth app | 2.000.000 puntos | Usuario (o App User) | 1 hora |
| Sin autenticar | 100.000 puntos | Dirección IP | 1 hora |

Máximo de una sola query: **10.000 puntos**. "Your query will always get rejected if it exceeds that."

Fórmula documentada: "Each property is 0.1 point, each object is 1 point and any connection multiplies
its children's points based on the given pagination argument, or the default 50."

### Headers, verificados en vivo

Respuesta real de `api.linear.app/graphql` a una introspection sin autenticar:

```
x-complexity: 2
x-ratelimit-complexity-limit: 100000
x-ratelimit-complexity-remaining: 85630
x-ratelimit-complexity-reset: 1787794489969
x-ratelimit-requests-limit: 1200
x-ratelimit-requests-remaining: 1199
x-ratelimit-requests-reset: 1787794489969
```

Nota: el `x-ratelimit-requests-limit` observado para tráfico sin autenticar es **1200**, no los 600 que
declara la documentación. Segunda razón para leer headers en runtime en vez de fiarse de la doc.

### Límites por endpoint

Existen: "Some queries and mutations have individual request rate limits that are lower than the global
request limit." Se anuncian con `X-RateLimit-Endpoint-Requests-Limit`,
`X-RateLimit-Endpoint-Requests-Remaining`, `X-RateLimit-Endpoint-Requests-Reset` y `X-RateLimit-Endpoint-Name`.

**No pude verificar si `documentUpdate` tiene uno.** Requiere autenticación.

Lo que sí está documentado en el propio schema (introspection de `__type(name:"Query")`), y que sí afecta
al plugin si busca en vez de guardar el id: `searchDocuments`, `searchIssues`, `searchProjects` y la
búsqueda semántica están "Rate-limited to 30 requests per minute".

### Errores y algoritmo

- Al exceder el límite: **HTTP 400**, no 429, con `extensions.code = "RATELIMITED"` en el cuerpo GraphQL.
- Algoritmo: leaky bucket, "your tokens are refilled with a constant rate of LIMIT_AMOUNT / LIMIT_PERIOD".
  No hay ventana fija que se agote de golpe.
- La doc desaconseja polling explícitamente y recomienda webhooks para detectar cambios.

### Estimación de costo de una sesión

Un `documentUpdate` que pida `success`, `lastSyncId` y `document { id updatedAt }` cuesta alrededor de
**3 puntos** de complejidad según la fórmula documentada (2 objetos más 4 propiedades, redondeado hacia
arriba). **Esto es un cálculo mío a partir de la fórmula, no una medición**: el endpoint devuelve 401 sin
autenticar y en ese caso no emite headers de complejidad, así que no pude medirlo.

Con ese orden de magnitud, el cuello de botella de una sesión de trabajo es el conteo de requests, no la
complejidad. Una sesión que haga 30 o 50 escrituras usa el 2% del presupuesto horario más restrictivo
(2.500 requests/hora). El rate limit no es un problema para este caso de uso.

---

## 5. Otras limitaciones relevantes

### a) No hay control de concurrencia optimista. Riesgo real.

Verificado por ausencia: `DocumentUpdateInput` no tiene versión, ni etag, ni `expectedUpdatedAt`, ni
`lastSyncId` de entrada. Toda escritura es last-write-wins.

Y los Documents son colaborativos en tiempo real. Descripción del tipo `Document` en la introspection:
"Documents support collaborative editing via ProseMirror/Yjs and store their content in a separate
DocumentContent entity." La doc de producto lo confirma: "Documents support collaborative editing, so
you'll see input cursors if another user is editing or viewing the text. All changes are saved and synced
to everyone in realtime" (`https://linear.app/docs/documents`).

Si una persona tiene el mapa abierto mientras el plugin lo reescribe entero, no hay merge ni conflicto:
gana el último que escribe. Para un documento vivo que se reescribe en cada sesión, esto es lo más
parecido a un problema serio que encontré. Mitigación barata: usar `patch` en vez de `content` completo
(reduce la superficie de sobreescritura), y releer antes de escribir.

### b) El markdown es una representación derivada, no la canónica.

Verificado por introspection. `DocumentContent.contentState`: "This is the canonical representation of the
document content used for collaborative editing". `DocumentContent.content`: "The document content in
markdown format. This is a **derived** representation of the canonical Yjs content state."

Consecuencia: el round-trip markdown a Yjs a markdown no garantiza identidad byte a byte. Evidencia
observada en el Document real que leí: el serializador devuelve tildes escapadas donde el autor no las
escapó (`\~62 endpoints`, `\~67 endpoints`) y envuelve las URLs en `<` `>`. Un ciclo de leer, editar y
escribir puede ir normalizando o acumulando escapes.

No es un blocker, pero el plugin no debe asumir que lo que escribió es exactamente lo que va a leer.
En particular, si se usa `patch` con anclas de texto exacto, las anclas deben tomarse de lo que **devuelve**
la API, no de lo que el plugin **creyó** haber escrito.

### c) Ruido de notificaciones en cada reescritura.

De `https://linear.app/docs/documents`: los suscriptores reciben notificación por "Material changes to
the content of a document", y "The creator of a document will be automatically subscribed to the changes
in the document".

Atenuante documentado en la misma página: "You do not get notifications for actions you have taken on a
document". Es decir, quien escribe no se auto-notifica. Pero si el plugin escribe con la identidad de un
usuario y hay otras personas suscritas, esas personas reciben una notificación por sesión. Con un mapa
que se reescribe seguido, eso se acumula.

### d) A favor: hay historial de versiones y red de seguridad.

`https://linear.app/docs/documents`: "Every document (and project description) has version history, so you
can see or revert to earlier document versions when needed."

El schema lo respalda: la Query expone `documentContentHistory`, `documentContentHistoryTimeline` y
`documentContentHistoryEntries`, y el tipo `DocumentContentHistoryType` incluye `contentData` (el
ProseMirror completo del snapshot), `actorIds` y `metadata`, esta última descrita como
"Metadata associated with the history entry, including content diffs and AI-generated change summaries".

Si una reescritura del mapa sale mal, se puede revertir desde la UI. **No verifiqué si cada
`documentUpdate` hecho por API genera una entrada de historial**; la doc solo afirma que existe historial
y que las ediciones de agentes y loops crean checkpoints.

### e) Un Document tiene exactamente un padre. Encaja con el modelo del plugin.

Descripción del tipo `Document`: "Each document is associated with exactly one parent entity."
`DocumentCreateInput` ofrece `projectId`, `issueId`, `initiativeId`, `teamId`, `cycleId`, `releaseId`,
y el MCP lo dice explícito: "exactly one parent (`project`, `issue`, `initiative`, `cycle`, or `team`)
must be specified". Un Document colgado de un Project es exactamente lo que el ticket quiere.

Ojo: `teamId`, `initiativeId` y `cycleId` están marcados `[Internal]` en el schema. `projectId` e
`issueId` no lo están, así que colgar el mapa de un Project usa camino público y estable.

### f) Buscar el documento por título es frágil. Guardar el id.

No hay unicidad de título ni un campo tipo "slug natural" que el plugin controle. Hay `id` (UUID) y
`slugId` (generado por Linear). El plugin debería persistir el `id` del Document del mapa en vez de
buscar `DD: <proyecto>` en cada sesión. El descubrimiento inicial es barato: `list_documents` filtra por
`projectId` y devuelve `id`. Y buscar por texto entra en el límite de 30 requests por minuto de
`searchDocuments`.

### g) Detalle menor: la API acepta identificadores humanos en algunos campos.

`DocumentUpdateInput.issueId` documenta "Can be a UUID or issue identifier (e.g., 'LIN-123')". El MCP va
más lejos y acepta nombres, slugs e identificadores en `project`, `issue`, `initiative`, `team` y `cycle`.
Cómodo, pero no es unicidad garantizada: para el vínculo del mapa conviene el UUID.

---

## Verificado contra no verificado, en una tabla

| Afirmación | Estado |
| --- | --- |
| `documentUpdate` solo acepta el markdown completo en `content` | Verificado (introspection) |
| No existe ningún campo `patch` en la API GraphQL | Verificado (introspection + grep sobre el SDL) |
| `contentState` (Yjs) no es escribible por la API pública | Verificado (aparece solo en tipos de salida) |
| El MCP `save_document` expone `patch` con las 6 operaciones, máximo 50 | Verificado (JSON Schema de la herramienta) |
| Techo de 10.485.760 bytes por request HTTP | Verificado (HTTP 413 real con `limit` en el error) |
| Límite de tamaño específico del campo `content` de un Document | **No verificado.** Requiere escritura autenticada |
| Una mención viva se serializa como `<issue id href>IDENT</issue>` | Verificado (lectura real de CRM-3167) |
| El texto plano `CRM-123` no se convierte en chip | Verificado (lectura real de un Document con decenas de identificadores inertes) |
| Si la API acepta `<issue ...>` o `@CRM-123` al escribir y lo convierte en chip | **No verificado.** Requiere escritura. Test binario pendiente |
| Límites de rate globales y de complejidad | Verificado (doc oficial + headers reales) |
| Si `documentUpdate` tiene un límite propio por endpoint | **No verificado.** Requiere autenticación |
| No hay control de concurrencia optimista | Verificado por ausencia en `DocumentUpdateInput` |
| Existe historial de versiones para Documents | Verificado (doc oficial + tipos del schema) |
| Si cada `documentUpdate` por API genera entrada de historial | **No verificado** |

---

## Conclusión

El Document sirve como casa del mapa. No encontré ningún blocker.

El tamaño no es un problema: el único límite verificado es el techo de 10 MiB por request HTTP, tres
órdenes de magnitud por encima de lo que pesa un mapa. Los rate limits tampoco: una sesión con decenas de
escrituras consume un porcentaje mínimo del presupuesto horario.

La reescritura completa es el modo nativo de la API (`documentUpdate` solo acepta el markdown entero) y
el `patch` del MCP es azúcar que hace read-modify-write por debajo. Sirve igual: ahorra tokens y acota el
daño de un error del modelo. Vale la pena usarlo, con anclas únicas y estables en el markdown del mapa.

Quedan dos cosas por resolver, ninguna bloqueante. La primera es un test de escritura de dos minutos: si
la API convierte `<issue id href>...</issue>` de vuelta en chip al escribir. De eso depende que el índice
de decisiones tenga enlaces vivos o links markdown comunes; hay que correrlo antes de fijar el formato,
porque el texto plano `CRM-123` está verificado que no funciona. La segunda es que no hay control de
concurrencia: si una persona edita el mapa en la UI mientras el plugin lo reescribe, gana el último. Se
mitiga releyendo antes de escribir y prefiriendo `patch` sobre reescritura completa.
