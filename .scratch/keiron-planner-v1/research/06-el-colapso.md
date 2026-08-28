# El colapso: del mapa a milestones e issues de ejecución

Resolución del ticket [06](../issues/06-que-hace-map-collapse.md), tipo
`map:grilling`. Cuatro rondas de grilling con el dev leader, veinticuatro
preguntas, sesión del 2026-08-27, más cuatro mediciones contra el workspace
`keiron` real y un colapso de juguete corrido de punta a punta contra el sandbox.

> **Enmienda del 11.** Donde este documento diga que el mapa es un Document colgado
> del Project, léase el **overview del Project**, `Project.content`: el 11 lo mudó, y
> `map:create` ya no crea Document. El mapa no tiene título propio, así que el
> `DD: <proyecto>` desaparece. Detalle y mediciones en
> [`11-el-project-vivo.md`](11-el-project-vivo.md).

> El colapso no cambia: escribe milestones e issues en el Project, y eso no lo toca
> la casa del mapa.

`/map-collapse` es el cuarto comando y el último. El [08](08-los-tres-comandos.md)
escribió los otros tres y dejó acá la precondición, el token y el casillero. Este
documento escribe el procedimiento.

Igual que el 08, **se reparte**: el procedimiento termina en
`skills/map-collapse/SKILL.md`, la plantilla de la issue de ejecución en
`skills/_shared/map-templates.md`, el sexto encabezado del DD en el mismo archivo,
y las dos operaciones nuevas en `scripts/LINEAR-OPERATIONS.md`. Es una fuente, no
un archivo destino.

Va en español con los términos canónicos en inglés, por la razón de siempre: su
lector es el dev leader que va a mantener esto.

> **Enmienda del 12.** Donde este documento diga `issue:create`, léase
> **`work:write`**: el 12 la renombró porque en dos de sus tres desenlaces no crea
> ninguna issue. Sigue siendo una de las doce operaciones. Detalle en
> [`12-el-aterrizaje.md`](12-el-aterrizaje.md).

> **Y la explicación del `sortOrder` está al revés.** Linear no recalcula lo que se
> pide: recalcula solo el `0.0`, porque lo trata como campo ausente, y lo manda al
> **final**. Cualquier valor distinto de cero se respeta literal, así que insertar un
> corte entre dos que ya existen es determinístico. Medido en el 12.

> **`/map-work` gana dos operaciones que este documento le da solo a `/map-collapse`**,
> `milestone:create` y `work:write`, por el aterrizaje. La tabla de reparto cambia en
> esa columna.

## Qué es el colapso

El paso donde el mapa deja de producir decisiones y empieza a producir trabajo.
Toma un mapa con la frontera vacía y escribe, adentro del mismo Project,
milestones con issues de ejecución colgando. Ahí termina este plugin.

Es **HITL**, y no por accidente. El mapa está ordenado por decisiones y un
milestone es un corte demoable: la traducción entre las dos formas es un juicio,
no un mapeo. El agente propone, la persona aprueba, y recién con el visto bueno
se escribe algo en Linear.

Es **un evento único**. No hay colapso por partes ni colapso incremental, y una
segunda corrida se niega.

## La precondición y el nuevo veredicto

**Cero tickets de decisión abiertos**, que es exactamente el veredicto "listo para
colapsar" que `/map-status` ya reporta. Con un solo ticket abierto,
`/map-collapse` no corre.

El 08 fijó tres veredictos, y hoy hay **cuatro**. El cuarto es `colapsado`, y
existe porque sin él los otros dos comandos rompen apenas el colapso termina: con
cero tickets abiertos, tanto `/map-status` como el paso 3 de `/map-work` dirían
"listo para colapsar" para siempre y emitirían `map-collapse`, que a su vez se
negaría por ser la segunda corrida.

| Estado del mapa | Veredicto | Token |
| --- | --- | --- |
| Tickets abiertos, frontera con al menos uno tomable | en curso | `map-work` |
| Tickets abiertos, frontera vacía | trabado | `break-cycle` |
| Cero tickets abiertos, cero milestones | listo para colapsar | `map-collapse` |
| Cero tickets abiertos, al menos un milestone | **colapsado** | **`sdd-new`** |

Se detecta agregando `projectMilestones` a la query que los dos comandos ya
hacen. Sigue siendo un round-trip en los dos.

Y un mapa colapsado con un ticket abierto se trabaja normal: `/map-work` no mira
milestones cuando hay algo que resolver. Eso es lo que hace falta para el
[ticket 12](../issues/12-decision-nueva-sobre-mapa-colapsado.md).

## El procedimiento

`$ARGUMENTS`, igual que `/map-work` y `/map-status`: una URL de Project o de
cualquier ticket del mapa. Sin argumento pregunta y para. Nunca adivina.

1. **Preflight.** Uno, como todo proceso que emite operaciones.
2. **`map:read-write`, la mitad que lee**, más `frontier:query`, más
   `projectMilestones`, en el mismo round-trip.
3. **El veredicto, antes de proponer nada.** Con tickets abiertos, para. Con
   milestones y issues de ejecución, para: es la segunda corrida. Con milestones
   y cero issues de ejecución, ofrece retomar (ver "El colapso a medias").
4. **Primera pasada: los cortes.** Grilling más domain-modeling sobre el índice de
   Decisiones. El agente propone los milestones, la persona aprueba o los
   redibuja. Nada se escribe todavía.
5. **Segunda pasada: las issues.** Solo cuando los cortes están aprobados. Adentro
   de cada corte, el agente propone las issues de ejecución y la persona aprueba.
6. **`milestone:create`**, uno por corte, en orden.
7. **`issue:create`**, una sola llamada atómica con todas las issues de todos los
   milestones.
8. **`map:read-write`**, una vez, llenando `## El colapso`.
9. **El reporte de cierre con el token `sdd-new`**, y para.

Los pasos 4 y 5 son una sola sesión con dos pasadas, y la segunda no arranca hasta
que la primera está aprobada. Mezclarlas hace que redibujar un corte tire a la
basura las issues que ya se propusieron para él, y redibujar cortes es exactamente
lo que el paso 4 pone a la persona a hacer.

### Los cortes: de decisiones a milestones

Un milestone es un corte demoable que agrupa tracer bullets, nunca un corte
temporal. La cantidad no se fija de antemano: sale de la ronda.

**El primero es siempre el tracer bullet del proyecto**, por glosario, y eso no se
negocia en la ronda. Pero **no se deriva del mapa**: se grillea, porque es la
única pieza del colapso que las decisiones no contienen. Ningún ticket de decisión
contesta "cuál es la rebanada vertical más chica que prueba que la arquitectura
funciona"; el mapa contesta qué arquitectura, no por dónde empezar a probarla.

La derivación mecánica quedó descartada de entrada. Una decisión no es un corte
demoable, y el grafo de bloqueo del mapa es de prerequisitos de conocimiento, no
de capas de producto: dos decisiones que se bloquean entre sí pueden caer en el
mismo milestone, y dos que no se tocan pueden caer en cortes distintos.

**El nombre** es el corte demoable en prosa, sin prefijo numérico, por el mismo
argumento con el que el 08 se lo sacó a los títulos de los tickets: `sortOrder` ya
da el orden y la UI de Linear ya numera. **La `description`** nombra las
decisiones que produjeron ese corte, por nombre y con enlace al ticket. Esa es
toda la trazabilidad del colapso, y va acá y no en cada issue: una issue de
ejecución que enlaza cinco tickets de decisión es ruido que nadie lee.

**`targetDate` queda siempre nulo.** Porque el glosario dice que un milestone
nunca es un corte temporal, y porque `targetDate` es exactamente lo que habilita
que `ProjectMilestone.status` se ponga en `overdue`. Un milestone sin fecha nunca
puede estar atrasado, que es la propiedad que queremos.

### Las issues: qué se escribe en el cuerpo

El título se **invierte** respecto del ticket de decisión: un ticket de decisión
es una pregunta, una issue de ejecución es un imperativo.

El cuerpo es una plantilla fija, en español, con tres secciones:

```markdown
## Qué hay que construir
## Lo que ya está decidido    ← con enlace al ticket que guarda el detalle
## Qué queda fuera            ← el límite local de esta issue
```

**No es un proposal, y eso es deliberado.** `/sdd-new` corre su propio discovery
loop, y un cuerpo con forma de proposal lo hace saltear justamente el pensamiento
que existe para hacer. Lo que el cuerpo aporta es lo único que SDD no puede saber
por su cuenta: qué ya se decidió y dónde vive el porqué, para que el discovery
loop no vuelva a litigarlo.

El `Fuera de alcance` del mapa **no se copia**. Es del proyecto entero, no de una
issue, y pegarlo en veinte cuerpos convierte el índice en un store, que es el
error que el mapa existe para no cometer. La sección "Qué queda fuera" lleva el
límite local de esa issue, que sale de la ronda, y el enlace al mapa alcanza para
el resto.

**Las issues de ejecución no llevan label `map`.** Eso es lo que hace que
`frontier:query` siga funcionando igual después del colapso, y es el peso real que
el 08 le dio al label cuando reemplazó el parentesco de wayfinder. Tampoco llevan
`Discovery`: no son discovery.

**No llevan `estimate`**, y quedan nulas. Estimar es un ritual del equipo, y un
agente adivinando fibonacci es precisión falsa que después alguien cree. La
consecuencia hay que decirla en voz alta: con `defaultIssueEstimate: 1`, un
colapso de veinte issues deja el scope del Project en veinte hasta que el equipo
estime. Eso está mal, se ve, y se corrige solo en la primera refinement. Un número
inventado no se ve y no se corrige.

**No se cablea ningún bloqueo entre ellas.** El adapter sabe hacerlo, pero el
orden de ejecución es del equipo y el milestone más el `sortOrder` ya dan el orden
grueso. Cablear relaciones que el equipo va a contradecir en la primera refinement
es ruido que después hay que desarmar a mano.

**Llevan `stateId` explícito**, y esto no es una preferencia sino una obligación
que salió medida. Ver "Las issues creadas por API caen en Triage".

## Las dos operaciones nuevas

El adapter pasa de ocho subcomandos a **diez**.

### 9. Crear un milestone · `milestone:create`

```graphql
mutation($input: ProjectMilestoneCreateInput!) {
  projectMilestoneCreate(input: $input) {
    success projectMilestone { id name sortOrder targetDate status }
  }
}
```

`input: { name, projectId, description, sortOrder }`. Sin `targetDate`, nunca.

**El `sortOrder` que devuelve no es el que se pidió.** Medido: se pasó `0.0` al
primer milestone y volvió `-36` en una corrida y `-61` en otra. Linear lo recalcula
para insertarlo al principio. El orden relativo sale bien, pero es la regla del 03
otra vez: las anclas salen de lo que devuelve la API y nunca de lo que el plugin
creyó escribir.

`ProjectMilestone.status` es **derivado** y no se escribe: `unstarted`, `next`,
`overdue` o `done`, calculado desde las issues y la fecha. Con `targetDate` nulo,
`overdue` es inalcanzable.

### 10. Crear una issue de ejecución · `issue:create`

```graphql
mutation($input: IssueBatchCreateInput!) {
  issueBatchCreate(input: $input) {
    success issues { id identifier url title projectMilestone { name } }
  }
}
```

Una sola llamada con **todas** las issues del colapso entero. `IssueCreateInput`
lleva `projectMilestoneId`, así que cada issue nace con su corte puesto y no hay
segunda pasada de cableado como la que necesitan los tickets de decisión.

`input.issues[]: { teamId, projectId, projectMilestoneId, stateId, title, description }`.
Sin `labelIds`, sin `estimate`.

**No es `ticket:create` con un flag.** Se descartó estirar la operación existente:
`ticket:create` tiene una invariante que el 03 escribió a propósito, "un issue
cuyo cuerpo es la pregunta y nada más", y un flag que la anula convierte esa
invariante en un comentario. Además el check estructural 5 del 08 cuenta
subcomandos del adapter contra operaciones nombradas en `LINEAR-OPERATIONS.md`, y
con dos operaciones sigue contando solo; con un flag hay que enseñarle a mirar
flags.

### El reparto completo, con las diez

| Operación | `/map-new` | `/map-work` | `/map-status` | `/map-collapse` |
| --- | --- | --- | --- | --- |
| `preflight` | sí | sí | sí | **sí** |
| `map:create` | Project + Document | solo el Document, variante research | no | **no** |
| `map:read-write` | escribe una vez | escribe una vez | solo lee | **escribe una vez** |
| `ticket:create` | sí | sí | no | **no** |
| `ticket:block` | sí | sí | no | **no** |
| `frontier:query` | sí, al cerrar | sí, al abrir | sí | **sí, al abrir** |
| `ticket:claim` | no | sí | no | **no** |
| `ticket:resolve` | sí, research, partida | sí | no | **no** |
| `ticket:rule-out` | no | sí | no | **no** |
| `milestone:create` | no | no | no | **sí** |
| `issue:create` | no | no | no | **sí** |

`/map-collapse` no toma nada. No hay ticket que tomar: la frontera está vacía por
precondición.

## La secuencia de escritura, y por qué es N+2

Con N milestones y M issues de ejecución, el colapso escribe **N+2 veces**:

1. N llamadas a `milestone:create`, una por corte. No hay mutación batch de
   milestones.
2. **Una** llamada a `issue:create` con las M issues. `issueBatchCreate` dice
   literal en su schema *"Creates a list of issues atomically"*.
3. Una llamada a `map:read-write`.

**Medido** con [`06-scripts/collapse_probe.py collapse`](06-scripts/collapse_probe.py):
5 de complejidad por milestone, 6 por un batch de tres issues. Un colapso de cinco
cortes y treinta issues queda muy por debajo del techo de 10.000 por query que el
01 encontró.

El mapa es el **último write**, así que el orden que el 03 fijó se respeta. Y
`/map-collapse` escribe el mapa **exactamente una vez**, igual que `/map-new` y
`/map-work`, así que el ticket 09 sigue teniendo la superficie mínima que el 08 le
dejó.

## El colapso a medias

La atomicidad del batch decide la forma de la recuperación. La única ventana de
falla real es entre el paso 6 y el paso 7: **milestones creados, issues no**. El
estado sucio de "algunas issues sí y otras no", que sería el imposible de
diagnosticar, no existe.

Así que el rechazo de la segunda corrida **se parte en dos**:

- **Milestones con cero issues de ejecución**: es un colapso que murió a la mitad.
  El comando lo reconoce, lo dice, y ofrece retomar reusando los milestones que ya
  existen. Arranca en el paso 5.
- **Milestones con issues de ejecución adentro**: es una segunda corrida de
  verdad, y se niega duro.

Idempotencia **por rechazo, no por merge**. Fusionar dos colapsos es la operación
destructiva que nadie pidió, y el mapa tiene una sola operación destructiva a
propósito, `ticket:rule-out`, que cierra un ticket y nada más.

## El sexto encabezado del DD

El 08 fijó cinco encabezados de nivel 2 con texto exacto, contrato, con falla
fuerte si falta alguno. Ahora son **seis**:

```markdown
## Destino
## Notas
## Decisiones hasta ahora
## Aún no especificado
## Fuera de alcance
## El colapso
```

Lo crea **vacío `/map-new`**, desde el principio, así que ningún DD nace sin él y
la falla fuerte sigue valiendo. Lo llena `/map-collapse` una sola vez, con los
milestones creados por nombre y enlace, y nada más.

No va en `Decisiones hasta ahora` por el mismo argumento con el que wayfinder dejó
`Fuera de alcance` afuera: Decisiones registra la ruta efectivamente caminada, y
un colapso no es un paso de esa ruta, es lo que pasa cuando la ruta se terminó. El
mapa sigue siendo un índice.

## La costura con SDD

**El colapso termina en Linear y nada más.** No escribe `openspec/changes/` ni
ningún otro archivo en ningún repo.

**SDD entra en `/sdd-new`, no en `/sdd-apply`.** Esto corrige una decisión de
encuadre del mapa, y la corrige contra un hecho: la puerta ya existe y nadie la
está usando. `sdd-orchestrator/SKILL.md:132` dice *"When the input is a Linear
issue, the orchestrator fetches it with the Linear MCP tools and passes the issue
context to sdd-explore"*.

Se descartó que el colapso escribiera los artefactos de SDD, por dos razones. La
primera es el polyrepo: con once repos activos, escribir `openspec/changes/`
obliga a contestar en qué repo cae un milestone que cruza cuatro, que es el mismo
problema que ya mató al pointer file en el 03 y a la rama de research en el 08. La
segunda es la dirección de la dependencia: SDD construye, el planner planifica, y
un plugin que escribe adentro del árbol de artefactos del otro es exactamente el
acoplamiento que la peer dependency existe para evitar.

**El token es `sdd-new`, y el conjunto cerrado pasa de cinco a seis:**

| Token | Cuándo |
| --- | --- |
| `map-new` | No hay mapa. |
| `map-work` | La frontera tiene al menos un ticket tomable. |
| `map-collapse` | Cero tickets abiertos, cero milestones. |
| `release-claim` | Hay una toma vieja y la frontera está flaca. |
| `break-cycle` | Hay tickets abiertos y la frontera está vacía. |
| **`sdd-new`** | **El mapa está colapsado. Se terminó.** |

Es el mismo nombre y el mismo significado que el token `sdd-new` del vocabulario
cerrado de trece de SDD, así que la costura queda nombrada con la palabra que el
otro lado ya usa. Se descartó un terminal mudo tipo `collapsed`: dejaría a la
persona con las issues creadas y sin decirle qué sigue, que es la mitad del
trabajo que el comando existe para hacer.

**El token va pelado y el nombre va en la prosa.** El contrato de SDD dice "route
by the token, never by the prose": el token rutea, la prosa explica. La prosa del
reporte de cierre nombra la primera issue del primer milestone con su URL, que es
por donde alguien va a empezar. Hacerle cargar un argumento al token obligaría a
inventarle una forma de envelope que el contrato del 08 no tiene.

## Lo que el mapa le hace al sprint review

Esta sección es la respuesta a la única objeción que se llevó una ronda entera. El
mapa mete la planificación adentro de Linear, que es el punto del plugin, y en
Linear la planificación cae encima de los instrumentos con los que el equipo mide
la entrega. Todo lo que sigue está medido contra el team CRM, no supuesto.

### Los settings que deciden el problema

`06-scripts/collapse_probe.py settings`:

| Setting | Valor |
| --- | --- |
| `cyclesEnabled` | `true`, ciclos de 2 semanas, arrancan lunes |
| `cycleIssueAutoAssignStarted` | **`true`** |
| `cycleIssueAutoAssignCompleted` | **`true`** |
| `issueEstimationType` | `fibonacci` |
| `issueEstimationAllowZero` | `true` |
| `defaultIssueEstimate` | **`1`** |
| `triageEnabled` | `true` |
| `defaultIssueState` | `Backlog` |

`Project.progress` es `(puntos completados + 0,25 × puntos en curso) / puntos
totales`, y `Project.scope` es los puntos totales.

### Ya estaba pasando

El sandbox del ticket 01 tiene cinco issues, todas con `estimate` nulo, y el
Project marca `scope=5, progress=0.2`. O sea que `defaultIssueEstimate: 1` cuenta:
**un ticket de decisión sin estimar infla el scope del proyecto en un punto**. Un
mapa de quince tickets son quince puntos fantasma, y la barra de progreso se mueve
a medida que se cierran.

Y CRM-3347, la única de las cinco que estaba en `Done`, estaba metida en el ciclo
38. Las otras cuatro, en `Backlog`, sin ciclo. Eso es `cycleIssueAutoAssignCompleted`
disparando sobre nuestro propio sandbox, un día antes, sin que nadie lo pidiera ni
lo notara.

### La palanca que se usa: `estimate: 0`

Se pone en `ticket:create`, así que cuesta **cero escrituras nuevas**. Medido: con
`estimate: 0` en una de las cinco, `scope` pasó de 5 a 4 y `progress` de 0,2 a
0,25, o sea 1/4 en vez de 1/5. `issueEstimationAllowZero` ya está en `true` en el
team, así que no hay que cambiarle un setting a nadie.

Un ticket de decisión no es entrega, así que no puede pesar en la vara con la que
se mide la entrega. Esto no se discute.

Ojo con una cosa: **`scope` es denormalizado y tiene lag**. La relectura inmediata
después de la mutación todavía devolvía el valor viejo. No sirve para verificar en
línea.

### La palanca que no se usa: sacar el ticket del ciclo

Al cerrarse, el ticket de decisión igual entra al ciclo activo, así que aparece
listado en el sprint review. **Se acepta**, y va con cero puntos y con label `map`.

La razón es la razón del plugin. Existe para sacar la planificación de Notion y
meterla en el tracker, justamente para que deje de ser invisible; esconderla de
nuevo, apenas llega, es deshacer el trabajo. Con cero puntos la contaminación se
reduce a unas filas etiquetadas en la lista de cerrados, y esas filas describen
trabajo que de verdad se hizo en ese sprint: alguien se sentó una sesión entera a
resolver esa pregunta.

Queda **nombrada la salida de emergencia**, medida y lista, por si el sprint
review molesta de verdad: `ticket:resolve` pasa de cinco escrituras a seis, con
`cycleId: null` en un round-trip aparte después del cambio de estado, más una
relectura para verificar. Siete round-trips donde hoy hay cinco.

Y tiene que ser un round-trip aparte, porque acá hay una trampa medida: la
mutación combinada **no sirve**. `issueUpdate` con `{stateId: Done, cycleId: null}`
en una sola mutación devuelve `cycle: null` **en su propia respuesta**, y una
relectura fresca muestra el ciclo 38. El auto-assign corre después del commit,
asíncrono, y gana. La respuesta de la mutación miente.

La tercera salida, apagar `cycleIssueAutoAssignCompleted` en el team, quedó
descartada: es una línea y arregla el problema de raíz, pero afecta a todo lo que
el equipo hace y no es una decisión del plugin.

### El label `Discovery`

Los tickets de decisión llevan `Discovery` además de `map`, **cuando el label
existe en el workspace, y en silencio cuando no**. El preflight ya resuelve ids de
labels, así que cuesta un lookup y cero escrituras nuevas.

Es la respuesta más barata que existe a la objeción: los tickets de decisión caen
adentro del cajón que el equipo ya usa para separar discovery de entrega, en todas
las vistas y filtros que ya existen, sin que el plugin invente una convención
nueva que después hay que enseñarle a la gente.

### Las issues creadas por API caen en Triage

El hallazgo que excede al colapso, y el que corrige una afirmación que este
documento hizo mal en la ronda 1.

**Medido**, con `06-scripts/collapse_probe.py triage`, dos issues creadas en el
mismo batch:

| Issue | `stateId` | Estado resultante |
| --- | --- | --- |
| ZZ control SIN stateId | ausente | **`Triage` (type `triage`)** |
| ZZ control CON stateId | `defaultIssueState` | `Backlog` (type `backlog`) |

Con `triageEnabled: true`, Linear cuenta a la Personal API key como integración, y
manda al inbox de Triage todo lo que cree. `Team.defaultIssueState` dice `Backlog`
y no se aplica.

Nunca se había visto porque **ningún ticket del sandbox se creó por API**: las
issues CRM-3346 a CRM-3350 se hicieron a mano en la UI, y ni `probe.py` del 01 ni
`frontier.py` del 03 llaman a `issueCreate`. El primer `issueCreate` del proyecto
fue el de esta sesión.

La regla, para las dos operaciones que crean: **el preflight resuelve
`Team.defaultIssueState` y toda creación pasa `stateId` explícito.** En el team CRM
eso da `Backlog`, que además es el estado correcto para una issue de ejecución
recién nacida: `Todo` insinúa comprometida para el ciclo, y todavía no está ni
estimada ni refinada.

## Lo que este ticket no toca

**Ningún campo del Project.** `ProjectUpdateInput` tiene `statusId`, `leadId`,
`startDate`, `targetDate` y `priority`, y un colapso es el momento natural para
mover el Project de "planned" a "started". No lo hace. El ciclo de vida del
Project es de PM, el 03 ya decidió que el plugin **adopta** un Project en vez de
dueñarlo, y un plugin que le mueve el estado a un proyecto en el que PM está
trabajando es la clase de sorpresa que hace que se desinstale.

## Las afirmaciones chequeables, para el ticket 10

Lo que este ticket deja listo para que el 10 no lo re-derive. Se suman a las seis
que dejó el 08, y **corrigen dos de ellas**.

7. El conjunto de tokens de `map-contract.md` es exactamente **seis**, no cinco.
   Corrige la afirmación 1 del 08.
8. `commands/` tiene cinco archivos y **cuatro** rutean a una skill que existe.
   `map-collapse.md` deja de ser un casillero vacío. Corrige la afirmación 2 del 08.
9. `map-templates.md` tiene los **seis** encabezados del DD con texto exacto, las
   cinco secciones del comentario de resolución, y las **tres** secciones del
   cuerpo de la issue de ejecución. Corrige la afirmación 4 del 08.
10. `scripts/linear.py` tiene **diez** subcomandos, uno por operación nombrada en
    `LINEAR-OPERATIONS.md`, y ninguno de más.
11. Toda ruta de creación de issues en `linear.py` pasa `stateId`. Un
    `issueCreate` o un `issueBatchCreate` sin `stateId` es un bug, no un estilo.
12. `ticket:create` pasa `estimate: 0`; `issue:create` no pasa `estimate`.
13. `milestone:create` nunca pasa `targetDate`.

Y una que **no** es estructural sobre el repo, que se suma a la que el 08 ya le
dejó al 10: que ninguna issue de ejecución lleve label `map`. Se chequea contra
Linear, no contra el repo.

## Lo que este documento corrige

Cinco cosas, en cuatro documentos.

**A la decisión de encuadre del mapa.** Decía "`/map-collapse` llega hasta issues
de Linear con sus milestones. SDD entra recién en `/sdd-apply`". La primera mitad
queda; la segunda pasa a **`/sdd-new`**. Las dos no cerraban: para que SDD entre en
`/sdd-apply` tienen que existir ya `proposal.md`, `specs/`, `design.md` y
`tasks.md`, y un colapso que solo escribe Linear no los escribe.

**Al reference del 03**, tres cosas:

1. **`ticket:create` pasa `stateId` explícito.** El documento dice hoy "Sin
   `stateId`: el issue cae en el estado por defecto del team, que en CRM es
   `Backlog`". Es falso y está medido: cae en `Triage`.
2. **`ticket:create` pasa `estimate: 0`**, y el ticket de decisión lleva el label
   `Discovery` además de `map` cuando existe.
3. **Las operaciones son diez, no ocho.** Se suman `milestone:create` e
   `issue:create`.

**Al 08**, dos cosas:

1. **Los veredictos son cuatro, no tres**, y el cuarto es `colapsado`. Toca a
   `/map-status` y al paso 3 de `/map-work`, los dos con la misma corrección:
   agregar `projectMilestones` a la query que ya hacen.
2. **Los encabezados del DD son seis, no cinco.** El sexto es `## El colapso`, lo
   crea vacío `/map-new`.

**A `CONTEXT.md`**, dos cosas: `Discovery` pasa de "el plugin no lo lee ni lo
escribe" a "lo escribe en todo ticket de decisión cuando existe", y la tabla de
operaciones del tracker pasa a diez.

## Supuestos

- Todo lo que el 03 y el 08 supusieron sigue supuesto: **un solo team** en el
  workspace, un solo conductor por mapa, un mapa de hasta cincuenta tickets, y las
  escrituras atribuidas a quien generó la key.
- **`issueBatchCreate` no tiene un límite de tamaño documentado**, y no se midió
  dónde está. Un colapso de treinta issues anda; uno de trescientos no se probó.
  Con el techo de cincuenta tickets de decisión que ya supone el mapa, no parece
  alcanzable, pero es un supuesto y no un hecho.
- El label `Discovery` es del team CRM. En un workspace sin él, el plugin lo
  saltea en silencio y nada se rompe.

## Lo que este documento no decide

- **Qué hace el plugin cuando aparece una decisión nueva sobre un mapa ya
  colapsado.** Es el [ticket 12](../issues/12-decision-nueva-sobre-mapa-colapsado.md),
  que gradúa con este. Para la v1: el colapso es un evento único, no gana modo
  incremental, y quien resuelva ese ticket crea la issue de ejecución a mano.
- **Qué chequean los checks estructurales.** Es el ticket 10, que este documento
  termina de desbloquear por el lado del 06.
- **Cómo se hace segura la escritura del mapa** frente a una edición humana. Es el
  ticket 09. Este documento no le agrega superficie: `/map-collapse` escribe el
  mapa exactamente una vez, igual que los otros dos que escriben.
- **Distribución, key y dónde vive el repo central de dominio.** Es el 07.

## Cómo se verificó

Todo lo medido en este documento sale de
[`06-scripts/collapse_probe.py`](06-scripts/collapse_probe.py), stdlib pelado, sin
dependencias, cuatro subcomandos:

| Subcomando | Qué prueba |
| --- | --- |
| `settings` | Los settings del team CRM y sus doce estados |
| `pollution` | Que `defaultIssueEstimate: 1` cuenta, y que `estimate: 0` saca del scope |
| `triage` | Las dos issues del mismo batch, con y sin `stateId` |
| `collapse` | El colapso de juguete entero: 2 milestones más 3 issues atómicas |

Los cuatro corren contra el Project `ZZ SANDBOX keiron-planner 01` y el team CRM
reales. Los que escriben, borran lo que escribieron. La introspection del schema
corre sin autenticar.
