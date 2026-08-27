# Las ocho operaciones del mapa, expresadas en Linear

Resolución del ticket [03](../issues/03-seis-operaciones-en-linear.md), tipo
`map:grilling`. Tres rondas de grilling con el dev leader, sesión del
2026-08-26/27, más lecturas medidas contra el workspace `keiron`.

Este es el equivalente nuestro de la sección "Wayfinding operations" de los docs
de tracker de Matt. Cuando el plugin exista, vive como reference markdown al
lado del script del adapter, no como skill: es un contrato, no una disciplina
que el modelo tenga que razonar.

Van en español con los términos canónicos en inglés, que es la regla general de
`CONTEXT.md`. La excepción del ticket 05, inglés con frontmatter de SDD, existía
para que SDD pudiera importar el archivo copiándolo, y eso acá no puede pasar:
SDD nunca va a importar el adapter de Linear de un plugin de planificación.

## Son ocho, no seis

Matt lista seis. Nos faltaban dos, y las dos faltaban por la misma razón: existen
en el flujo y no están en el doc, así que el agente las improvisa cada vez.

- **Sacar de alcance** es otro id de estado y otra sección del mapa. Es además
  la única operación destructiva: cierra un ticket sin resolverlo.
- **Leer y actualizar el mapa** son las dos mitades de un read-modify-write.
  Nombrar solo la mitad que escribe deja la que lee sin dueño, y el ticket 09
  necesita exactamente ese punto para colgar su captura de `updatedAt`.

## El cliente

**GraphQL crudo contra `https://api.linear.app/graphql`, para las ocho.** Header
`Authorization` con la Personal API key pelada, sin prefijo `Bearer`. Un solo
cliente y un solo camino de auth.

El MCP de Linear queda fuera del camino crítico. El ticket 01 ya lo había forzado
para la consulta de frontera, porque el MCP escribe relaciones de bloqueo y no las
lee. Lo que se pierde es el azúcar `patch` de `save_document`, y no es pérdida: el
plugin hace su propio read-modify-write, y esa es justamente la ventana de control
que el ticket 09 necesita poder tocar.

## El preflight

Corre una vez por **proceso que emite operaciones**, antes de cualquiera de ellas.
Resuelve todo lo que las operaciones necesitan y **no guarda nada**: la fuente de verdad es Linear, no un
archivo de config. Un caché acá compra milisegundos y paga con un modo de fallo
que solo aparece cuando alguien tocó el workflow del team.

```graphql
query($team: String!, $labels: [String!]!) {
  viewer { id displayName }
  team(id: $team) {
    id key name
    states(first: 50) { nodes { id name type position } }
  }
  issueLabels(first: 250, filter: { name: { in: $labels } }) {
    nodes { id name team { id } }
  }
}
```

Medido: un round-trip, **423 de complejidad** contra el techo de 10.000 por query.
`team(id:)` acepta la key del team, o sea `"CRM"`, no hace falta el UUID.

Con eso resuelve:

- **`viewer.id`**, que es la toma.
- **Los dos ids de estado**: el `completed` de menor `position` para resuelto, y
  el `canceled` de menor `position` para fuera de alcance. En el team CRM eso da
  `Done` y `Canceled`.
- **Los ocho ids de label**, y **crea los que falten**, idempotente: busca por
  nombre exacto y crea solo lo que no existe. Nunca renombra ni borra.

Si algo no se resuelve, **falla fuerte y con mensaje accionable**. No hay
fallbacks: ver "Por qué no hay fallbacks".

> **Enmienda del ticket 08.** Este documento decía "una vez por sesión". Con los
> subagentes de research corriendo en paralelo, sesión y proceso dejan de ser lo
> mismo: **cada subagente corre su propio preflight**. Pasarle los ids resueltos
> por parámetro es acoplamiento a cambio de nada, y contradice la razón por la que
> acá se decidió no cachear. Cuesta 423 de complejidad por subagente contra un
> presupuesto por hora que el 02 midió como irrelevante.

### Los ocho labels

`map`, `map:research`, `map:prototype`, `map:grilling`, `map:task`, `hitl:pm`,
`hitl:design`, `hitl:dev`.

Planos y **workspace-level**, o sea creados con `teamId` omitido. Medido con
autorización, creando y borrando un label descartable: una Personal API key puede
crear labels workspace-level, `team` vuelve `null`, y no hace falta permiso de
admin. Eso resuelve de raíz cómo llega el label `map` a un team, porque no hay
que llevarlo a ninguno.

```graphql
mutation($input: IssueLabelCreateInput!) {
  issueLabelCreate(input: $input) { success issueLabel { id name team { id } } }
}
```

Con `input: { name: "map:grilling" }` y sin `teamId`.

**Por qué planos y no grupos de Linear.** `map:grilling` es exactamente la
sintaxis de un label group, y la tentación es real. No va, por tres razones. Un
label group no se puede aplicar a un issue, lo dice literal la descripción de
`IssueLabel.isGroup`, así que con grupo no existiría el label `map` sobre el
ticket y la frontera tendría que filtrar por `labels.some.parent.name`, que es
posible pero no está medido. El nombre canónico de `CONTEXT.md` ya es
`map:research`, y bajo un grupo el label en Linear se llamaría solo `research`,
partiendo el nombre canónico del que muestra la UI. Y la convención existente del
equipo ya es plana con dos puntos, `EAV: Track A`.

Lo que se pierde: los grupos son de selección única, así que un ticket no podría
llevar dos tipos. Con labels planos eso pasa a ser uno de los checks
estructurales.

## Las ocho operaciones

El nombre canónico es el inglés, que es el que va a terminar en el código del
adapter. La prosa las llama por su nombre en español.

| Canónico | En prosa | Escrituras |
| --- | --- | --- |
| `preflight` | El preflight | crea los labels que falten |
| `map:create` | Crear el mapa | 2 |
| `map:read-write` | Leer y actualizar el mapa | 1 |
| `ticket:create` | Crear un ticket | 1 |
| `ticket:block` | Bloquear | 1 |
| `frontier:query` | Consultar la frontera | 0 |
| `ticket:claim` | Tomar | 1 |
| `ticket:resolve` | Resolver | 5, ver la enmienda del 08 |
| `ticket:rule-out` | Sacar de alcance | 5, ver la enmienda del 08 |


### 1. Crear el mapa · `map:create`

El mapa es un Document titulado `DD: <proyecto>` colgado de un Project.

**Adopta el Project si le pasan una URL, lo crea si no.** En el CRM los Projects
los suele abrir PM antes de que el dev leader se meta, y crear uno paralelo sería
partir el proyecto en dos.

```graphql
mutation($input: ProjectCreateInput!) {
  projectCreate(input: $input) { success project { id name slugId } }
}

mutation($input: DocumentCreateInput!) {
  documentCreate(input: $input) { success document { id title slugId updatedAt } }
}
```

`ProjectCreateInput` pide `teamIds`. `DocumentCreateInput` cuelga de `projectId`,
que es campo público, mientras `teamId`, `initiativeId` y `cycleId` están
marcados `[Internal]`.

**Falla si el Project ya tiene un Document de mapa.** Es el chequeo previo que
vuelve idempotente a la operación.

> **Enmienda del ticket 08.** Esta operación tiene una **variante que usa solo su
> segunda mitad**: el Document de research de un ticket `map:research`, que es el
> mismo `documentCreate` con título `RESEARCH: <título del ticket>` colgado del
> mismo `projectId`. No crea Project y no es una novena operación, porque no toca
> el read-modify-write del mapa ni su semántica. Reemplaza a la rama descartable
> `research/<nombre>` de wayfinder, que con once repos obliga a elegir uno.

**El mapa no lleva ningún label marcador.** `DocumentCreateInput` no tiene
`labelIds`: un Document de Linear no acepta labels. El label `Discovery` que
existe hoy es de issue y del team CRM, así que tampoco serviría. No hace falta:
el Project es la identidad y el Document se encuentra a través de él.

### 2. Leer y actualizar el mapa · `map:read-write`

Un read-modify-write, y se nombra entero porque sus dos mitades son la misma
operación.

```graphql
query($id: String!) {
  document(id: $id) { id title content updatedAt }
}

mutation($id: String!, $input: DocumentUpdateInput!) {
  documentUpdate(id: $id, input: $input) { success document { id updatedAt } }
}
```

`DocumentUpdateInput.content` es **markdown completo**, no hay parche. El plugin
edita el markdown en memoria y reescribe entero.

Dos reglas que vienen medidas de los tickets 01 y 02:

- **Las anclas de edición se toman de lo que devuelve la API**, nunca de lo que el
  plugin creyó escribir. Linear normaliza en la primera escritura: viñetas `- ` a
  `* `, links `[t](url)` a `[t](<url>)`, separadores de tabla. Después es punto
  fijo y no se acumula.
- Las tildes sobreviven intactas. Tablas y bold también.

**La seguridad de la mitad que escribe es del ticket 09**, no de este documento.
Acá queda nombrado el punto donde se captura el `updatedAt` de la lectura; qué se
hace con él cuando cambió es la decisión que el 09 tiene que tomar.

### 3. Crear un ticket · `ticket:create`

Un issue del Project, con label `map` más su tipo, más su `hitl:<rol>` si es HITL.

```graphql
mutation($input: IssueCreateInput!) {
  issueCreate(input: $input) { success issue { id identifier url } }
}
```

`input: { teamId, projectId, title, description, labelIds: [...] }`. Sin
`stateId`: el issue cae en el estado por defecto del team, que en CRM es
`Backlog`.

**El cuerpo del ticket es la pregunta y nada más.** El tipo es un label, el modo
es un label, el bloqueo es una relación y la toma es el assignee. Todo eso vive
en campos nativos de Linear. Los archivos markdown de este tracker local los
llevan en el cuerpo porque no tenían dónde más ponerlos, y ese no es el modelo a
imitar.

### 4. Bloquear · `ticket:block`

```graphql
mutation($input: IssueRelationCreateInput!) {
  issueRelationCreate(input: $input) { success issueRelation { id type } }
}
```

`IssueRelationCreateInput` tiene cuatro campos: `id`, `type`, `issueId`,
`relatedIssueId`. El enum `IssueRelationType` es `blocks`, `duplicate`, `related`,
`similar`, y **no tiene `blocked_by`**.

Para decir "C está bloqueado por D":

```
{ type: blocks, issueId: "CRM-3347", relatedIssueId: "CRM-3350" }
```

**El bloqueante siempre va del lado `issue`.** La relación se guarda una sola vez
y se ve desde los dos lados. `issueId` y `relatedIssueId` aceptan identificador
humano tipo `CRM-123`, no hace falta el UUID.

Se escribe en una segunda pasada, después de crear los tickets: necesitan existir
para poder referenciarse.

### 5. Consultar la frontera · `frontier:query`

Un round-trip, **3.847 de complejidad**, 61% de aire contra el techo de 10.000.

```graphql
query($id: String!, $label: String!) {
  project(id: $id) {
    name
    issues(first: 50, filter: { labels: { some: { name: { eq: $label } } } }) {
      pageInfo { hasNextPage }
      nodes {
        identifier title createdAt
        state { id name type }
        assignee { displayName }
        labels { nodes { name } }
        relations(first: 10) {
          pageInfo { hasNextPage }
          nodes { type relatedIssue { identifier state { id } } }
        }
        inverseRelations(first: 10) {
          pageInfo { hasNextPage }
          nodes { type issue { identifier state { id } } }
        }
      }
    }
  }
}
```

El tamaño de página es 50 por 10 y no se toca. La complejidad se cobra por lo que
la query **pide**, no por lo que devuelve, así que no se puede elegir un tamaño
generoso por las dudas.

El predicado se evalúa en el cliente. Está completo más abajo, en su propia
sección, porque es la parte de este documento que más fácil se implementa mal.

### 6. Tomar · `ticket:claim`

```graphql
mutation($id: String!, $input: IssueUpdateInput!) {
  issueUpdate(id: $id, input: $input) { success issue { identifier assignee { displayName } } }
}
```

Con `input: { assigneeId: <viewer.id> }`. Es el primer write de la sesión, antes
de cualquier trabajo.

**Una toma huérfana no se libera sola.** Si la sesión muere, el ticket queda
asignado y fuera de la frontera. Liberarlo automáticamente rompería la única
garantía que la toma da, así que no se hace: `/map-status` reporta los tickets
tomados con su antigüedad y la persona desasigna a mano. Un fallo invisible pasa
a ser una línea que se lee.

### 7. Resolver · `ticket:resolve`

> **Enmienda del ticket 08.** Son **cinco** escrituras, no tres. Antes del
> comentario van `ticket:create` y `ticket:block` de los tickets que la resolución
> haya generado, porque la sección "Tickets nuevos" del comentario los enlaza por
> nombre y tienen que existir para poder referenciarse. Un ticket creado y una
> sesión que muere antes del comentario deja un ticket huérfano visible en la
> frontera, que es un fallo barato; el orden inverso deja un comentario con
> enlaces rotos. El orden completo es: tickets nuevos, cableado, comentario,
> estado, mapa.
>
> Y cuando la resolución la conduce un subagente de research, esta operación es la
> **única que se parte entre procesos**: el subagente escribe el comentario y el
> estado, y el mapa lo escribe el padre, una vez, con las líneas de todos los
> subagentes juntas.

Tres escrituras, **en este orden**: comentario, estado, mapa.

```graphql
mutation($input: CommentCreateInput!) {
  commentCreate(input: $input) { success comment { id url } }
}
```

`input: { issueId: "CRM-123", body: "<la respuesta en markdown>" }`. Después
`issueUpdate` con `stateId` = el id resuelto por el preflight. Después la
operación 2 sobre el mapa, agregando una línea al índice de Decisiones.

**La respuesta va como comentario, no en el cuerpo del ticket.** La pregunta
queda inmutable y auditable, y la respuesta gana autor y timestamp gratis.

El orden importa: si la sesión muere en el medio, la respuesta ya está escrita y
el ticket se puede volver a resolver sin perder nada. El orden inverso deja un
ticket en Done sin respuesta, que es un agujero que nadie ve.

### 8. Sacar de alcance · `ticket:rule-out`

La única operación destructiva: cierra un ticket **sin** resolverlo, porque
resultó estar más allá del destino.

Mismas escrituras que resolver, mismo orden, dos diferencias: el `stateId` es el
`canceled` que fijó el preflight, y la línea va a la sección **Fuera de alcance**
del mapa, nunca a Decisiones. Sus dos primeras escrituras, los tickets nuevos y su
cableado, casi siempre están vacías. Decisiones registra el camino que se
caminó, y un límite de alcance no es un paso de ese camino.

## El predicado de frontera, completo

Un ticket está en la frontera si cumple las tres:

1. **Está abierto**: `state.id` **no** es ninguno de los dos ids cerrados.
2. **No está tomado**: `assignee` es null.
3. **No tiene bloqueantes abiertos**: ninguno de sus `inverseRelations` con
   `type == "blocks"` tiene un `issue.state.id` fuera del conjunto cerrado.

Los bloqueantes de X son `X.inverseRelations.nodes` con `type == "blocks"`, y el
bloqueante es el campo `issue`. Lo que X bloquea son `X.relations.nodes` con
`type == "blocks"`, y el bloqueado es `relatedIssue`. El `type` vuelve siempre
como `"blocks"`, nunca como `"blocked_by"`.

### Cerrado es un par de ids, no un test de tipo

Esta es la corrección más importante de este ticket, y corrige al ticket 01.

El 01 dejó escrito que cerrado es `state.type in (completed, canceled)`. **Contra
el team CRM eso está mal.** El team tiene dos estados de tipo `canceled`:

| Estado | type | position | En uso |
| --- | --- | --- | --- |
| `Canceled` | canceled | 4 | sí |
| `Blocked` | canceled | 3948.38 | sí, CRM-2766 está ahí |

Un ticket parkeado en `Blocked` es semánticamente lo más abierto que hay, y el
test por tipo lo lee como cerrado. Falla dos veces y en silencio: un ticket cuyo
bloqueante alguien movió a `Blocked` aparece tomable, y un ticket de mapa movido
a `Blocked` se cae de la frontera como si estuviera resuelto. `completedAt` y
`canceledAt` tienen el mismo problema, porque los setea el tipo.

Por eso **cerrado es exactamente los dos estados que el plugin escribe**,
resueltos a id por el preflight. Todo lo demás es abierto. Falla del lado seguro:
un ticket arrastrado a `Blocked` queda abierto y visible, que a lo sumo molesta.

Aparte, y como higiene del workspace y no del plugin: `Blocked` tipado `canceled`
también le miente a los reportes de ciclo de Linear.

### El orden

**`createdAt` ascendente, ordenado en el cliente.** Es el orden en que se trazó el
mapa, es determinista, y no se lo reescribe nadie.

`PaginationOrderBy` solo tiene `createdAt` y `updatedAt`, sin control de
dirección, y el default de Linear es descendente. Ordenar los cincuenta nodos en
el cliente es gratis porque ya vinieron en el round-trip.

`Issue.sortOrder` existe y no sirve. Medido en el sandbox: ascendente da el orden
**inverso** al de creación, y mover CRM-3347 a Done le reescribió el `sortOrder`
de `-468154` a `-1020138`. No significa "orden en que se trazó" y lo pisa
cualquier cambio de estado.

### El truncado silencioso

La query pide `pageInfo { hasNextPage }` en las tres conexiones y el cliente avisa
fuerte si alguna vino truncada.

No es prolijidad. Si la lista de bloqueantes de un ticket se corta en silencio, el
ticket aparece tomable cuando está bloqueado, alguien lo toma, y el mapa avanza
sobre una decisión que dependía de otra sin tomar.

### Frontera vacía no significa una sola cosa

Con tickets abiertos y frontera vacía, el mapa está **trabado**, típicamente por
un ciclo: A bloquea a B y B bloquea a A. Sin tickets abiertos y frontera vacía, el
mapa está **listo para colapsar**. Son opuestos y se ven igual, y sin la
distinción `/map-status` le dice "terminaste" a alguien que está trabado.

Detectarlo es gratis: el subgrafo entero ya vino en el round-trip.

Un bloqueante sacado de alcance no genera este caso: va a `Canceled`, que es uno
de los dos ids cerrados, así que desbloquea bien.

## Reglas transversales

### El último write es el que hace visible la operación

Toda operación de más de una escritura se ordena para que un crash a mitad de
camino deje estado recuperable, y es idempotente con un chequeo previo.

GraphQL ejecuta las mutations raíz **en serie y sin rollback**, así que meterlas
en un solo request no compra atomicidad: compra que fallen en orden. Es de la
spec de GraphQL, no está medido contra Linear.

### La identidad del mapa viaja como URL

La persona pega la URL de Linear y el plugin resuelve los ids en la sesión. **No
se persiste nada en ningún repo.**

Medido: `project(id:)` y `document(id:)` aceptan las tres formas, el UUID, el
`slugId` pelado y el slug completo de la URL.

```
project(id: "zz-sandbox-keiron-planner-01-3a2ec0e37ac5")   OK
project(id: "3a2ec0e37ac5")                                OK
project(id: "400e790e-67c1-4eb0-8f4b-af388fc514a1")        OK
```

Y `project { documents { nodes { id title } } }` trae el Document del mapa en la
misma query, así que no hace falta buscarlo por título, que el ticket 02 ya había
marcado como frágil.

Es la única opción que sobrevive al polyrepo. Con once repos activos, un pointer
file commiteado obliga a contestar en qué repo vive el mapa de un proyecto que
cruza cuatro.

### Por qué no hay fallbacks

Los docs de tracker de Matt traen un fallback por operación porque tienen que
cubrir GitHub sin sub-issues y GitLab sin blocking nativo, que son features de
tier. Nosotros tenemos un solo tracker, una sola API, y ninguna de las ocho
operaciones toca un campo `[Internal]`.

En su lugar, el preflight falla fuerte y temprano. Un fallback que nunca se
ejercita es un segundo camino de código que se pudre, y acá se pudriría sin que
nadie se entere.

## Supuestos

- **El workspace tiene un solo team.** Hoy `keiron` tiene exactamente uno, CRM,
  así que el `teamId` es derivable. Si aparece un segundo, deja de serlo y hay
  que decidir de quién son los tickets de un mapa.
- **Un mapa no pasa de cincuenta tickets de decisión.** Es el tamaño de página, y
  un mapa más grande que eso es un mapa fuera de control.
- **Las escrituras se atribuyen a quien generó la Personal API key.** Personal
  API key contra OAuth sigue abierto en el ticket 07.

## Lo que este documento no decide

- **Cómo se hace segura la escritura del mapa** frente a una edición humana
  concurrente. Es el ticket 09. Acá queda nombrado el punto de enganche.
- **Dónde vive el script del adapter y cómo llega la key.** Es el ticket 07.
- ~~**Qué comando invoca cada operación y en qué orden.** Es el ticket 08.~~
  Resuelto: el reparto está en
  [`08-los-tres-comandos.md`](08-los-tres-comandos.md).

## Cómo se verificó

Todo lo medido de acá salió de lecturas contra el workspace `keiron` y de
introspection del schema, más una sola escritura autorizada, un label descartable
creado y borrado, para saber si una Personal API key puede crear labels
workspace-level.

El predicado corregido se corrió contra el sandbox del ticket 01,
[ZZ SANDBOX keiron-planner 01](https://linear.app/keiron/project/zz-sandbox-keiron-planner-01-3a2ec0e37ac5),
con sus cinco ramas. Script en
[`03-scripts/frontier.py`](03-scripts/frontier.py). Resultado:

```
FRONTERA (createdAt asc):
   CRM-3346  SANDBOX A: abierto, sin bloqueantes, sin assignee
   CRM-3350  SANDBOX C: abierto, bloqueado por D que va a quedar Done
BLOQUEADOS:
   CRM-3349  <- ['CRM-3346']
FUERA DE LA FRONTERA POR OTRA RAZON:
   CRM-3347  cerrado (Done)
   CRM-3348  tomado por ljana
```

Las cinco ramas, cada una con su issue, y ahora en orden de creación. El sandbox
no se borra: el ticket 04 lo reusa.
