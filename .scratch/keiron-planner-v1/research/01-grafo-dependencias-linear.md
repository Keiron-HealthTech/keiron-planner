# 01: Cómo lee el agente el grafo de dependencias de Linear

Reporte del ticket [01](../issues/01-grafo-dependencias-linear.md), tipo
`map:task`. Sesión del 2026-08-26, contra el Project descartable
[ZZ SANDBOX keiron-planner 01](https://linear.app/keiron/project/zz-sandbox-keiron-planner-01-3a2ec0e37ac5)
en el team CRM del workspace `keiron`.

Cada afirmación de acá se midió. Las que no, lo dicen.

## Veredicto

**El grafo se lee con GraphQL crudo, en un solo round-trip, sin dependencias.**
La premisa del ticket era que había que buscar por dónde leer las relaciones.
Resultó que la API siempre las expuso: lo que no las expone es el MCP.

## Las tres vías

| Vía | Requests para la frontera | Peso | Veredicto |
| --- | --- | --- | --- |
| GraphQL crudo | **1** | 0 dependencias | **v1** |
| `@linear/sdk` v91 | **15** medidos sobre 5 issues | 40 MB, 3 paquetes | plan B |
| `@kyaukyuai/linear-cli` v3.2.0 | sin medir, a propósito | binario sin verificar | descartada |

### GraphQL crudo

Una query, `POST https://api.linear.app/graphql`, header `Authorization` con la
Personal API key pelada, sin prefijo `Bearer`. El harness que la implementa está
en [`01-scripts/probe.py`](01-scripts/probe.py) y no importa nada fuera de la
stdlib de Python.

### `@linear/sdk` v91

Funciona y da la respuesta correcta. Expone `issue.relations()` e
`issue.inverseRelations()`, ambos `LinearFetch<IssueRelationConnection>`.

El problema es que son fetches lazy por issue. Medido con el contador
`x-ratelimit-requests-remaining` antes y después: **15 requests para 5 issues de
juguete**, contra 1 del GraphQL crudo. Parte de esos 15 son acceso lazy a `state`
y `assignee`, que se pueden evitar. El resto no: `inverseRelations()` es una
llamada por issue y el SDK no ofrece forma de batchearla. Sobre un mapa de 30
tickets eso es del orden de 90 requests para responder una pregunta.

Queda como plan B por si el día que el plugin necesite tipos generados pesa más
que el costo de red.

Detalle menor, por si confunde a alguien después: el JSDoc del propio SDK sobre
`relations()` dice "Inverse relations associated with this issue". Está mal
etiquetado. El comportamiento real es el de `relations`, no el de las inversas.

### `@kyaukyuai/linear-cli` v3.2.0

Descartada por seguridad, no la corrí. Correr un binario sin verificar para
evaluar si es seguro correrlo no tiene sentido.

El paquete de npm no trae el CLI: son 11 archivos, un shim generado por
cargo-dist con `postinstall: node ./install.js` que baja un binario de GitHub
releases con axios. **El release publica un `.sha256` por cada binario y el
instalador nunca los baja ni los compara.** Verificado con `grep` sobre
`binary-install.js`, `install.js` y `run-linear.js`: ninguno menciona sha,
checksum, integrity, hash ni verify.

Alrededor: repo `kyaukyuai/linear-cli` con 4 estrellas, 0 forks, creado el
2026-03-12, último push el 2026-04-13. Un solo mantenedor. La licencia dice MIT
en `package.json` de npm e ISC en GitHub. El repo está en TypeScript y el paquete
baja binarios con layout de cargo-dist, que es de Rust.

Nada de eso prueba mala intención. Sí dice que el plugin que van a instalar PM y
Diseño quedaría ejecutando código sin verificar de un proyecto de un mantenedor.
No vale la pena para ahorrar una query.

## Cómo se guarda y se lee una relación de bloqueo

Esto era el corazón del ticket, porque el enum de entrada `IssueRelationType`
tiene solo `blocks`, `duplicate`, `related` y `similar`. No tiene `blocked_by`.
Pero `IssueRelation.type` sale como `String` y no como el enum, así que el string
de salida podía ser cualquier cosa.

Medido escribiendo con `save_issue(id: "CRM-3350", blockedBy: ["CRM-3347"])`, que
es el camino que va a usar el plugin, y leyendo los dos lados:

- La relación se guarda **una sola vez**. El mismo `id`, `8412be7b-…`, aparece
  desde los dos issues.
- `type` vuelve como **`"blocks"`**. Nunca `"blocked_by"`.
- El MCP **normaliza al escribir**: pedirle "C está bloqueado por D" produce
  `issue = D`, `relatedIssue = C`. El bloqueante siempre queda del lado `issue`.

De ahí sale la regla, que es la línea que más importa de este reporte:

> Los bloqueantes de X son `X.inverseRelations.nodes` con `type == "blocks"`.
> El bloqueante es el campo `issue`.
> Lo que X bloquea son `X.relations.nodes` con `type == "blocks"`, y el bloqueado
> es `relatedIssue`.

## El techo de complejidad, que no estaba en el mapa

El ticket 02 concluyó que los rate limits eran irrelevantes. Es cierto para el
presupuesto por hora y **falso para el límite por query**, que es otro y no
aparecía en el análisis.

Hay dos límites, medidos en los headers de respuesta:

| Límite | Valor | Header |
| --- | --- | --- |
| Complejidad por query | **10.000** | el error lo dice, no hay header |
| Complejidad por hora | 3.000.000 | `x-ratelimit-complexity-limit` |
| Requests por hora | 2.500 | `x-ratelimit-requests-limit` |

La primera versión de la consulta de frontera pedía `first: 250` con las
conexiones anidadas sin acotar. La API la rechazó con HTTP 400:

```
"The query is too complex. Complexity: 83901.1. Maximum allowed complexity: 10000."
```

Dos cosas que hay que entender de eso:

**La complejidad se cobra por lo que la query pide, no por lo que devuelve.** El
sandbox tiene 5 issues y la query de `first: 50` pesa 4.737 igual. Es análisis
estático del shape. Consecuencia práctica: el tamaño de página no se puede elegir
"generoso por si acaso", porque el costo se paga siempre.

**El costo escala con página por anidadas.** Medido:

| Página | Anidadas | Complejidad | Resultado |
| --- | --- | --- | --- |
| 250 | 50 | 83.326 | rechazada |
| 100 | 50 | 33.331 | rechazada |
| 100 | 10 | 9.472 | pasa, 5% de aire |
| 75 | 10 | 7.104 | pasa, 29% de aire |
| **50** | **10** | **4.737** | **elegido, 53% de aire** |
| 50 | 5 | 2.537 | pasa, 75% de aire |

Elegido 50 por 10. Un mapa con más de 50 tickets de decisión es un mapa fuera de
control, y 10 bloqueantes en un ticket ya es demasiado. El 53% de aire deja
agregar campos después sin rediseñar la query, que es lo que hizo falta acá: sumar
`pageInfo` costó 2.500 de complejidad y llevó la versión de `first: 100` de 6.931
a 9.472.

## La consulta de frontera

Vive en [`01-scripts/probe.py`](01-scripts/probe.py), subcomando `frontier`. El
shape:

```graphql
query($id: String!, $label: String!) {
  project(id: $id) {
    name
    issues(first: 50, filter: { labels: { name: { eq: $label } } }) {
      pageInfo { hasNextPage }
      nodes {
        identifier title
        state { name type }
        assignee { displayName }
        labels { nodes { name } }
        relations(first: 10) {
          pageInfo { hasNextPage }
          nodes { type relatedIssue { identifier state { type } } }
        }
        inverseRelations(first: 10) {
          pageInfo { hasNextPage }
          nodes { type issue { identifier state { type } } }
        }
      }
    }
  }
}
```

El predicado se evalúa en el cliente: abierto, sin assignee, y sin ningún
bloqueante cuyo `state.type` no sea `completed` ni `canceled`.

> **ENMIENDA del 2026-08-27, ticket 03. Esa última parte está mal.**
>
> El test por tipo falla contra el team CRM, que tiene **dos estados de tipo
> `canceled`**: `Canceled` en position 4 y **`Blocked`** en position 3948.38.
> `Blocked` está en uso real, CRM-2766 está ahí. Un ticket parkeado ahí es
> semánticamente lo más abierto que hay, y este predicado lo lee como cerrado.
> Falla dos veces y en silencio: un ticket cuyo bloqueante alguien movió a
> `Blocked` aparece tomable, y un ticket de mapa movido a `Blocked` se cae de la
> frontera como si estuviera resuelto. `completedAt` y `canceledAt` tienen el
> mismo problema, porque los setea el tipo.
>
> El sandbox de este reporte no lo podía ver porque solo usó Backlog y Done.
>
> **Cerrado es exactamente los dos estados que el plugin escribe**, resueltos a
> id por un preflight: el `completed` de menor `position` y el `canceled` de
> menor `position`. Todo lo demás es abierto. Ver
> [`03-operaciones-en-linear.md`](03-operaciones-en-linear.md) y el harness
> corregido en [`03-scripts/frontier.py`](03-scripts/frontier.py).
>
> El resto de este reporte sigue en pie, incluida la regla de por qué el
> predicado no puede ser server-side.

### Por qué el predicado no puede ser server-side

`IssueFilter` tiene `hasBlockedByRelations` y `hasBlockingRelations`, con
comparador `RelationExistsComparator { eq: Boolean, neq: Boolean }`. Es tentador,
y contesta mal.

Filtra "tiene una relación de bloqueo", no "tiene un bloqueante abierto". Un
ticket cuyo bloqueante ya está Done sigue dando `true`, así que
`hasBlockedByRelations: { eq: false }` lo excluiría de la frontera cuando en
realidad es tomable. Ese es exactamente el caso más común en un mapa que avanza.

El sandbox tiene un issue puesto ahí para probarlo, CRM-3350, y el resultado de
correr la consulta:

```
FRONTERA, tomables ahora:
  CRM-3350  SANDBOX C: abierto, bloqueado por D que va a quedar Done
  CRM-3346  SANDBOX A: abierto, sin bloqueantes, sin assignee

Bloqueados:
  CRM-3349  SANDBOX B: abierto, bloqueado por A que sigue abierto  -> bloqueado por CRM-3346

Fuera de la frontera por otra razón:
  CRM-3348  SANDBOX E: abierto, sin bloqueantes, pero tomado  -> tomado por ljana
  CRM-3347  SANDBOX D: va a quedar Done, y bloquea a C  -> cerrado (Done)
```

Las cinco ramas del predicado, cada una con su issue. CRM-3350 sale tomable, que
es la respuesta correcta y la que el filtro booleano habría errado.

### La trampa del truncado silencioso

La query pide `pageInfo { hasNextPage }` en las tres conexiones y el cliente
avisa fuerte si alguna vino truncada.

No es prolijidad. Si la lista de bloqueantes de un ticket se corta en silencio, el
ticket aparece **tomable cuando está bloqueado**, alguien lo toma, y el mapa
avanza sobre una decisión que dependía de otra sin tomar. Es el peor modo de
fallo posible en esta consulta, porque no se ve.

## El test de chip, heredado del ticket 02

El ticket 02 dejó abierto si la API parsea
`<issue id="..." href="...">CRM-123</issue>` de vuelta a chip al escribir un
Document, porque requería una escritura autenticada.

**No lo parsea.** Y falla de una forma que conviene conocer.

Escrito `href="https://linear.app/keiron/issue/CRM-3346/sandbox-a-..."`, la API
devolvió:

```
<issue id="e6ba8212-..." href="[CRM-3346](https://linear.app/keiron/issue/CRM-3346/sandbox-a-...)">CRM-3346</issue>
```

El pipeline de markdown autolinkeó la URL **adentro del valor del atributo** y lo
corrompió. Eso prueba que el tag entró como texto y no como nodo de mención.
Probado también sin `href`: tampoco se parsea, sobrevive como texto literal.

**Consecuencia**: el índice de decisiones del mapa usa link markdown común a la
URL del issue. Es lo que ya estaba en el plan B del ticket 02, ahora confirmado.

Confirmación visual pendiente en
[el documento del sandbox](https://linear.app/keiron/document/test-chip-01-e25b36b293ee),
que tiene las tres formas una debajo de la otra.

## Cómo trata Linear al markdown que le mandamos

Esto salió de paso y toca directo al ticket 09, así que va acá.

Round-trip del formato real del mapa, con tildes, tablas, bold, listas y links.
Linear normaliza:

| Escrito | Devuelto |
| --- | --- |
| viñeta `- ` | viñeta `* ` |
| `[texto](url)` | `[texto](<url>)` |
| separador `\| --- \|` | separador `\| -- \|` |

**Las tildes sobreviven intactas.** Probadas siete: Cómo, Qué, sí, graduó, Aún,
Canónico, chequean. El ticket 02 sospechaba tildes escapadas y en este shape no
pasa. Tablas y bold también sobreviven.

**La normalización no se acumula.** Reescribir con exactamente lo que la API
devolvió da resultado idéntico, probado en cuatro rondas seguidas. Es un cambio
de una sola vez en la primera escritura y después es punto fijo.

Eso es buena noticia para el ticket 09: read-modify-write es estable y el
documento no se degrada sesión a sesión. La regla que ya venía del ticket 02 se
confirma y ahora se sabe por qué: **las anclas de `patch` se toman de lo que
devuelve la API, nunca de lo que el plugin creyó escribir**, porque la primera
escritura cambia las viñetas y los links.

Dato aparte, para cuando alguien quiera precisión byte a byte: el tipo `Document`
expone `contentState` además de `content`. Es el estado Yjs canónico. No lo
investigué.

## Lo que queda abierto

- **Confirmación visual del chip.** La evidencia de la API es concluyente pero un
  ojo humano sobre el documento cierra el tema en diez segundos.
- **Personal API key contra OAuth.** Anotado en el ticket
  [07](../issues/07-distribucion-e-instalacion.md). La key personal carga cada
  acción del plugin sobre la persona que la generó.
- **`contentState` y Yjs.** Sin investigar. Solo importaría si algún día hace
  falta escritura sin pasar por markdown.
- **Paginación de verdad.** El cliente avisa si hay truncado pero no pagina. Con
  50 por 10 no debería hacer falta nunca, y si hace falta el mapa tiene un
  problema peor que la query.
- **El orden de la frontera**, que este reporte no fijó. Lo fijó el ticket 03:
  `createdAt` ascendente, ordenado en el cliente. `Issue.sortOrder` no sirve, da
  el orden inverso al de creación y lo pisa cualquier cambio de estado.

## Cómo reproducir

```
# una vez, en una terminal de verdad
.scratch/keiron-planner-v1/research/01-scripts/install.sh

# el grafo desde los dos lados
.scratch/keiron-planner-v1/research/01-scripts/probe.py relations CRM-3350 CRM-3347

# la frontera
.scratch/keiron-planner-v1/research/01-scripts/probe.py frontier \
  400e790e-67c1-4eb0-8f4b-af388fc514a1 zz-sandbox-map
```

## El sandbox

No lo borres: el ticket 04 lo reusa.

| Issue | Estado | Relación | Frontera |
| --- | --- | --- | --- |
| CRM-3346 A | Backlog | bloquea a B | sí |
| CRM-3349 B | Backlog | bloqueado por A, abierto | no |
| CRM-3350 C | Backlog | bloqueado por D, Done | sí |
| CRM-3347 D | Done | bloquea a C | no |
| CRM-3348 E | Backlog | ninguna, con assignee | no |

Label descartable `zz-sandbox-map`, id `f1538853-…`. Se usó un label de sandbox
en vez de crear el label real `map` para no ensuciar el label picker del team
productivo. El filtro de GraphQL es idéntico, así que la evidencia vale igual.
