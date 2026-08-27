# 01: Cómo lee el agente el grafo de dependencias de Linear

**Tipo:** `map:task` · **Modo:** HITL (`hitl:dev`)
**Estado:** RESUELTO (2026-08-26)
**Bloqueado por:** nada.
**Tomado por:** ljana (sesión del 2026-08-26).

## Pregunta

El MCP de Linear escribe relaciones de bloqueo pero no las lee. Sin poder
leerlas no hay consulta de frontera, y sin frontera no hay mapa. ¿Por dónde
las leemos?

## Lo ya investigado

- `save_issue` acepta `blockedBy`, `blocks`, `removeBlockedBy` y `removeBlocks`.
  La escritura está resuelta.
- Ni `get_issue` ni `list_issues` devuelven campo de relaciones. Verificado
  contra CRM-3167, que volvió sin la clave siquiera vacía.
- No hay CLI oficial. `@linear/cli` está muerto en 0.0.5. Lo oficial es
  `@linear/sdk` v91, un SDK de TypeScript sobre GraphQL.
- `@kyaukyuai/linear-cli` v3.2.0, abril 2026, agent-first con JSON estable y
  dry-run, expone `linear issue relation list --json` (emite el grafo de
  dependencias) más `relation add/delete blocked-by`, y cubre project,
  document, milestone, label y workflow-state. Un solo mantenedor.
- El endpoint GraphQL responde introspection sin autenticar, así que un script
  propio también es viable a cambio de manejar una API key.

## Por qué es task y no research

Requiere provisionar una API key de Linear y un Project descartable para
probar contra algo real. Eso solo lo puede hacer una persona.

## Agregado por el ticket 02

Aprovechando la misma API key y el mismo Project descartable, correr el test de
dos minutos que el research no pudo hacer por ser de solo lectura: **¿la API
convierte `<issue id="..." href="...">CRM-123</issue>` de vuelta en chip al
escribir un Document?**

Es binario y decide el formato del índice de decisiones del mapa. Si no lo
acepta, cada reescritura degrada los chips a texto plano y hay que usar links
markdown comunes a la URL del issue. Está verificado que el identificador pelado
`CRM-123` no produce chip.

## Hecho cuando

Las tres vías probadas contra un Project descartable, con el veredicto escrito:
cuál se usa en v1, cuál queda de plan B, y qué costo tiene cada una en
credenciales y dependencias.


## Resolución

Reporte completo con las mediciones:
[`research/01-grafo-dependencias-linear.md`](../research/01-grafo-dependencias-linear.md)

**El grafo se lee con GraphQL crudo, en un solo round-trip, sin dependencias.**

La pregunta estaba mal planteada y eso fue el hallazgo. No había que buscar por
dónde leer las relaciones: `Issue.relations` e `Issue.inverseRelations` siempre
estuvieron en la API. Lo que no las expone es el MCP. Re-verificado con evidencia
fresca, `get_issue` sobre CRM-3350 vuelve sin ningún campo de relaciones aunque la
relación se acababa de escribir con `save_issue` y funcionó.

### Las tres vías

| Vía | Requests para la frontera | Veredicto |
| --- | --- | --- |
| GraphQL crudo | 1 | **v1** |
| `@linear/sdk` v91 | 15 medidos sobre 5 issues | plan B |
| `@kyaukyuai/linear-cli` | sin medir, a propósito | descartada |

El SDK da la respuesta correcta pero `inverseRelations()` es un fetch por issue y
no se puede batchear. Sobre un mapa de 30 tickets son unos 90 requests para
contestar una pregunta.

El CLI de terceros queda descartado por seguridad: su `postinstall` baja un
binario de GitHub releases, el release publica un `.sha256` por binario, y el
instalador nunca los compara. No lo corrí, porque ejecutar un binario sin
verificar para decidir si es seguro ejecutarlo no tiene sentido.

### Cómo se lee una relación de bloqueo

Escribir con `save_issue(blockedBy:)` normaliza: la relación se guarda una sola
vez, `type` vuelve siempre como `"blocks"` y nunca `"blocked_by"`, y el bloqueante
queda siempre del lado `issue`.

> Los bloqueantes de X son `X.inverseRelations.nodes` con `type == "blocks"`, y el
> bloqueante es el campo `issue`.

### El límite que el ticket 02 no vio

Hay un techo de complejidad de **10.000 por query**, distinto del presupuesto de
3.000.000 por hora que el 02 declaró irrelevante. La primera versión de la
consulta pesaba 83.901 y la API la rechazó con HTTP 400.

La complejidad se cobra por lo que la query pide, no por lo que devuelve, así que
el tamaño de página se paga siempre. Elegido **50 tickets por 10 bloqueantes**:
pesa 4.737 y deja 53% de aire.

### El predicado va en el cliente, no en el filtro

`IssueFilter` tiene `hasBlockedByRelations`, y usarlo sería un bug. Filtra "tiene
relación de bloqueo", no "tiene bloqueante abierto", así que un ticket cuyo
bloqueante ya está Done queda fuera de la frontera cuando en realidad es tomable.
Probado con CRM-3350 en el sandbox.

La consulta pide `pageInfo` en las tres conexiones y avisa si algo vino truncado.
Una lista de bloqueantes cortada en silencio hace que un ticket bloqueado parezca
tomable, y ese es el peor modo de fallo de esta consulta porque no se ve.

### El test de chip que traía del ticket 02

**No se parsea.** Escrito con `href`, la API devuelve el atributo corrompido: el
pipeline de markdown autolinkea la URL adentro del valor. Sin `href` tampoco. El
índice de decisiones del mapa usa link markdown común a la URL del issue.

De paso quedó medido cómo trata Linear al markdown que le mandamos: normaliza
viñetas `-` a `*`, envuelve los links en `[texto](<url>)` y acorta el separador de
tablas. **Las tildes sobreviven**, contra lo que sospechaba el 02. Y la
normalización no se acumula: reescribir con lo que la API devolvió da resultado
idéntico, probado en cuatro rondas. Eso alimenta al ticket 09.

### Lo que se llevó a otros tickets

- **07**: el setup pide la API key y la guarda él mismo, porque lo van a correr PM
  y Diseño. Prototipo funcionando en
  [`research/01-scripts/install.sh`](../research/01-scripts/install.sh). Queda
  abierto allá si la v1 usa Personal API key u OAuth.
- **09**: read-modify-write sobre el Document es estable y no degrada. Las anclas
  de `patch` se toman de lo que devuelve la API.
- **03**: destrabado. Las seis operaciones ya tienen con qué expresar la consulta
  de frontera.
