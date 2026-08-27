# Los tres comandos del mapa, keironizados

Resolución del ticket [08](../issues/08-los-dos-modos-keironizados.md), tipo
`map:grilling`. Seis rondas de grilling con el dev leader, veinticinco preguntas,
sesión del 2026-08-27, más una medición contra el workspace `keiron`.

Wayfinder tiene dos modos. Nosotros tenemos cuatro comandos, y este documento
escribe tres. El procedimiento de `/map-collapse` es del ticket
[06](../issues/06-que-hace-map-collapse.md); acá queda nombrada solo la costura.

A diferencia del reference del ticket 03, que se copia entero al plugin, este
documento **se reparte**: cada procedimiento termina en su `SKILL.md`, el
contrato en `skills/_shared/map-contract.md` y las plantillas en
`skills/_shared/map-templates.md`. Es una fuente, no un archivo destino.

Va en español con los términos canónicos en inglés, igual que el reference del
03 y por la misma razón: su lector es el dev leader que va a mantener esto.

## Qué cambia de wayfinder

Ocho cosas. Las tres primeras son adaptaciones forzadas por Linear y por el
polyrepo, las dos del medio son endurecimientos, y las últimas tres son nuestras.

**El mapa no es un issue padre, así que el parentesco desaparece.** En wayfinder
el mapa es un issue y los tickets son sus hijos. Acá el mapa es un Document y los
tickets son issues del Project con label `map`. Lo que reemplaza al parentesco es
la pertenencia al Project más el label, que ya es lo que consulta la frontera del
03. El label queda cargando peso real: después del colapso, las issues de
ejecución viven en el mismo Project.

**No hay rama descartable de research.** Wayfinder captura los hallazgos de un
ticket de research en una rama `research/<nombre>` con un puntero desde el
ticket. Con once repos activos eso obliga a contestar en qué repo va la rama de un
proyecto que cruza cuatro, que es el mismo problema que ya mató al pointer file en
el 03. En su lugar, un Document de Linear hermano del DD, dentro del mismo
Project. No necesita elegir repo y lo pueden abrir PM y Diseño sin clonar nada.

**No hay skill de research.** Wayfinder resuelve un ticket de research con un
subagente que llama a la skill `research`. Nuestro mapa puso el Tier B completo,
research incluida, en Fuera de alcance, y ese límite no se corre. El prompt del
subagente vive en `skills/_shared/research-subagent.md` y lo invocan `/map-new` y
`/map-work` por igual.

**Las Notas no otorgan permisos.** El doc de diseño de wayfinder documenta su
falla más reportada: las Notas pueden anular el "plan, don't do", pero las escribe
el agente, así que la restricción y su exención viven en el mismo archivo que
controla el restringido. Hay un caso relatado de un agente que se escribió el
permiso y después se lo leyó como licencia, y construyó sobre un servidor vivo.
Acá esa anulación no existe. Las Notas llevan dominio, skills a consultar y
preferencias permanentes, y nada que cambie las reglas del plugin. Cerrarlo nos
sale más barato que a Matt, porque nuestro destino ya termina en el colapso por
decisión de encuadre.

**En un ticket de prototipo el agente nunca elige.** El mismo agujero, en otro
lugar: hay reportado un agente que construyó tres variantes de UI, eligió una él y
cerró el ticket, y Matt dice que la skill "no lo dice lo bastante fuerte". Acá un
ticket `map:prototype` con una sola variante construida, o sin una elección dicha
por la persona, no se resuelve, y la sección "La decisión" del comentario tiene
que nombrar quién eligió.

**Se saca el corte de "sin niebla no hace falta mapa".** El paso 2 de wayfinder
para y le avisa al usuario que no necesita mapa si el grilling breadth-first no
levanta niebla. En Keiron el DD lo tiene todo proyecto igual, así que ese corte
deja a la persona sin nada y con el trabajo por hacer a mano. `/map-new` crea
siempre el Project y el DD. Sin niebla, el mapa nace con Decisiones ya escritas,
cero tickets y veredicto `map-collapse`. El camino corto deja de ser un callejón
y pasa a ser la ruta más barata que atraviesa el plugin.

**El multi-rol sale como ticket, no entra como feature.** Es la decisión del
ticket 05, y su punto de contacto con las operaciones se define acá: una pregunta
que el interlocutor de turno no puede contestar se convierte en un ticket HITL con
su `hitl:pm` o `hitl:design`, creado al resolver, en la misma segunda pasada de
crear y cablear.

**Existe `/map-status`, que en wayfinder no existe.** Es la consecuencia de que
nuestra frontera no se renderice sola: en el tracker de Matt el bloqueo nativo la
dibuja en la UI, y en Linear también, pero tres cosas que decidimos en el 03
quedan invisibles ahí. Las tomas huérfanas, la diferencia entre mapa trabado y
mapa listo, y el truncado.

## El reparto de las ocho operaciones

| Operación | `/map-new` | `/map-work` | `/map-status` | `/map-collapse` |
| --- | --- | --- | --- | --- |
| `preflight` | sí | sí | sí | del 06 |
| `map:create` | Project + Document | solo el Document, variante research | no | no |
| `map:read-write` | escribe una vez | escribe una vez | **solo lee** | del 06 |
| `ticket:create` | sí | sí | no | del 06 |
| `ticket:block` | sí | sí | no | del 06 |
| `frontier:query` | sí, al cerrar | sí, al abrir | sí | del 06 |
| `ticket:claim` | no | sí | no | no |
| `ticket:resolve` | sí, research, partida | sí | no | no |
| `ticket:rule-out` | no | sí | no | no |

Tres notas que el reparto obliga a hacer.

**`map:create` tiene dos mitades y la variante research usa solo una.** El
Document de research es el mismo `documentCreate` con otro título,
`RESEARCH: <título del ticket>`, colgado del mismo `projectId`. No es una novena
operación: no toca el read-modify-write del mapa ni su semántica.

**`ticket:resolve` es la única operación que se parte entre procesos.** Cuando la
resuelve un subagente de research, el subagente escribe el comentario y el estado,
que son recursos suyos y de nadie más, y el mapa lo escribe el padre, una vez, con
todas las líneas juntas. Ver "La concurrencia de los subagentes".

**`frontier:query` cierra `/map-new` además de abrir `/map-work`.** `/map-new`
acaba de crear los tickets y podría reportar de memoria, y no lo hace: relee. Es
la misma regla que el 03 fijó para las anclas del mapa, que se toman de lo que
devuelve la API y nunca de lo que el plugin creyó escribir.

## `/map-new`

Traza el mapa. Una sesión, y no resuelve ningún ticket de decisión a mano.

`$ARGUMENTS` es la idea suelta, o la URL de un Project a adoptar, o vacío. En los
tres casos grillea el destino igual.

1. **Preflight.** Falla fuerte y temprano si algo no está.
2. **Nombrar el destino.** Grilling más domain-modeling. El destino fija el
   alcance, así que se cierra antes que exista un solo ticket.
3. **Mapear la frontera**, grilling breadth-first, a lo ancho y no a lo hondo.
   A diferencia de wayfinder, **no hay corte acá**: sin niebla el mapa se crea
   igual y nace listo para colapsar.
4. **`map:create`.** Adopta el Project si le pasaron una URL, lo crea si no, y le
   cuelga el Document `DD: <proyecto>` con sus cinco encabezados. Destino y Notas
   llenos, la niebla en Aún no especificado, Decisiones hasta ahora vacío.
5. **`ticket:create`** para todo lo que se pueda enunciar con precisión ahora, y
   **`ticket:block`** en una segunda pasada, porque los tickets tienen que existir
   para poder referenciarse.
6. **Los subagentes de research**, todos en paralelo, uno por ticket
   `map:research` recién creado. Cada uno con el prompt de
   `skills/_shared/research-subagent.md`.
7. **`map:read-write`, una sola vez**, con las líneas de Decisiones de todos los
   research que volvieron.
8. **`frontier:query`** y el reporte de cierre, con su token.

El paso 3 es el que decide qué es ticket y qué es niebla, y el test es el de
wayfinder sin cambios: si podés enunciar la pregunta ahora, es ticket, aunque no
la puedas contestar. Si no, es niebla.

## `/map-work`

Resuelve un ticket. Nunca más de uno por sesión, y research es la única
excepción.

`$ARGUMENTS` es una URL de Linear, que puede ser la del Project **o la de
cualquier ticket del mapa**, porque desde el issue se resuelve el Project en el
mismo round-trip. Acepta además un identificador de ticket para elegir cuál. Sin
argumento pregunta y para. Nunca adivina ni busca: en un workspace donde PM abre
Projects todo el tiempo, buscar el mapa por cuenta propia elige mal en silencio.

1. **Preflight.**
2. **`map:read-write`, la mitad que lee**, y **`frontier:query`**.
3. **El veredicto, antes de elegir nada.** Sin tickets abiertos, para y emite
   `map-collapse`. Con tickets abiertos y frontera vacía, para, reporta el mapa
   trabado y emite `break-cycle`. No toma nada en ninguno de los dos casos.

   > **Enmienda del ticket 06.** Los veredictos son **cuatro**. "Sin tickets
   > abiertos" se parte según haya milestones o no: sin milestones emite
   > `map-collapse` como dice arriba, con al menos uno el mapa ya está
   > **colapsado** y emite `sdd-new`. Sin esto, `/map-work` manda a colapsar un
   > mapa ya colapsado para siempre, y `/map-collapse` lo rebota por ser la
   > segunda corrida. Cuesta agregar `projectMilestones` a la query del paso 2,
   > que sigue siendo un round-trip. Con al menos un ticket abierto, `/map-work`
   > trabaja normal y no mira milestones.
4. **Elegir el ticket.** El que nombró el argumento, o el primero de la frontera
   en `createdAt` ascendente.
5. **El chequeo de rol, antes de tomar.** Si el label no es `hitl:dev`, el comando
   pregunta si quien está del otro lado es ese rol o puede hablar por él, y se
   niega a seguir si la respuesta es que no. Va antes de `ticket:claim` a
   propósito: tomar y después negarse deja una toma huérfana, que es justo lo que
   nadie libera.
6. **`ticket:claim`.** El primer write del trabajo.
7. **Resolver, según el tipo.** Ver la tabla de disciplinas.
8. **`ticket:resolve`**, cinco escrituras en orden. Ver "El orden de resolver".
9. **El reporte de cierre con su token**, y para. La sesión termina acá aunque la
   frontera tenga diez tickets más.

### Las disciplinas por tipo

| Label | Qué invoca | La regla que no se negocia |
| --- | --- | --- |
| `map:grilling` | grilling y domain-modeling | El agente nunca contesta por la persona. |
| `map:prototype` | prototype | El agente construye variantes y **nunca elige**. |
| `map:research` | subagentes, `research-subagent.md` | El único tipo AFK y la única excepción a uno por sesión. |
| `map:task` | ninguna | AFK si el agente puede solo, si no una checklist precisa. Hace en vez de decidir, y se gana el lugar desbloqueando una decisión, nunca entregando un pedazo del destino. |

Sobre research: `/map-work` agarra **todos** los `map:research` de la frontera, en
paralelo, con la misma forma que el paso 6 de `/map-new`. Es el mismo mecanismo
invocado desde otro lado, no un segundo mecanismo. Si el argumento nombra un
ticket de research, agarra ese solo.

Sobre prototipo: el artefacto vive donde su naturaleza lo pide, un Project
descartable de Linear si es un artefacto de Linear, una rama si es código, y el
ticket lo **enlaza** en vez de pegarlo. No hay un lugar único, porque el polyrepo
ya enseñó que no existe.

### Cuando una pregunta es de otro rol

Sale como ticket HITL con su `hitl:pm` o `hitl:design`, y la ronda sigue sin ella.
El ticket se crea al resolver, en el paso 8, junto con los demás.

Con una rama. Si la respuesta diferida **no** hace falta para resolver el ticket
actual, el ticket nuevo se crea y no bloquea nada. Si **sí** hace falta, la sesión
no resuelve: crea el ticket, lo cablea como bloqueante del actual, **suelta la
toma** y para. Eso no contradice la regla del 03 de que una toma no se libera
sola, porque aquella habla de tomas huérfanas de una sesión muerta y esta es una
devolución deliberada, con una persona mirando.

### El orden de resolver

Cinco escrituras, en este orden:

1. `ticket:create` de los tickets nuevos, incluidos los HITL de otro rol.
2. `ticket:block` para cablearlos.
3. El comentario de resolución, con sus cinco secciones.
4. El estado, `stateId` = el `completed` que fijó el preflight.
5. `map:read-write`, agregando la línea al índice de Decisiones y **vaciando de
   Aún no especificado** todo parche que acaba de graduar.

Los dos primeros pasos son nuevos respecto del reference del 03, que escribió
tres. Los tickets tienen que existir antes del comentario porque la sección
"Tickets nuevos" los enlaza por nombre. Un ticket creado y una sesión que muere
antes del comentario deja un ticket huérfano visible en la frontera, que es un
fallo barato. El orden inverso deja un comentario con enlaces rotos.

`ticket:rule-out` es la misma secuencia con dos diferencias: el `stateId` es el
`canceled` del preflight, y la línea va a Fuera de alcance y nunca a Decisiones.
Sus pasos 1 y 2 casi siempre están vacíos.

### Graduar la niebla

Es el paso que más fácil se saltea, porque no falla cuando se omite. Por eso la
sección **Niebla graduada** del comentario es obligatoria y tiene que decir
`ninguna` cuando no graduó nada. Un negativo explícito es lo único que vuelve
visible un paso omitido, y cuesta una línea en la plantilla.

Un check estructural no puede juzgar si la graduación fue correcta, porque eso es
comportamiento conversacional y la decisión de encuadre del mapa lo deja afuera.
Lo que sí puede es verificar que la plantilla tenga la sección.

## `/map-status`

Lee el mapa y la frontera. **No escribe nada**, en ningún modo, igual que
`sdd-status` en el plugin hermano. Una corrida deja Linear byte a byte como
estaba.

`$ARGUMENTS`, igual que `/map-work`: una URL de Project o de cualquier ticket.

Un round-trip: la query de frontera del 03 más `documents` sobre el mismo Project.

```graphql
query($id: String!, $label: String!) {
  project(id: $id) {
    name
    documents(first: 10) { pageInfo { hasNextPage } nodes { id title content updatedAt } }
    issues(first: 50, filter: { labels: { some: { name: { eq: $label } } } }) { ... }
  }
}
```

**Medido** contra el sandbox del ticket 01, con
[`08-scripts/status_cost.py`](08-scripts/status_cost.py):

| Query | Complejidad |
| --- | --- |
| frontera sola, la del 03 | 3.847 |
| más `documents` sin `content` | 3.871 |
| más `documents` con `content` | 3.872 |

Traer el mapa entero cuesta **25**, o sea 0,65% sobre la frontera sola. El aire
contra el techo de 10.000 por query sigue siendo 61%.

Seis bloques:

1. **Destino**, la línea del mapa.
2. **Veredicto**: trabado, listo para colapsar, colapsado, o en curso con sus
   cuentas. El cuarto lo agregó el ticket 06 y se detecta con `projectMilestones`
   en la misma query.
3. **Frontera**, por nombre, en `createdAt` ascendente.
4. **Tomados**, con su antigüedad. Una toma huérfana no se libera sola a
   propósito, así que esta es la única forma de que se vea.
5. **Bloqueados**, cada uno con sus bloqueantes por nombre.
6. **Truncado**, si alguna de las tres conexiones vino cortada.

De la niebla muestra la **cuenta de parches**, no el texto. Es lo suficiente para
notar que hay seis y nadie los mira, sin convertir el reporte en una copia del
mapa.

Los nombres son nombres. El identificador de Linear viaja adentro del enlace,
nunca en lugar del nombre: una pared de `CRM-3347, CRM-3348, CRM-3349` es
ilegible.

## La costura con `/map-collapse`

Lo único que este ticket fija del cuarto comando.

**La precondición**: cero tickets de decisión abiertos y frontera vacía, que es
exactamente el veredicto "listo para colapsar" de `/map-status`. Con un solo
ticket abierto, `/map-collapse` no corre.

**El token**: `map-collapse` lo emiten `/map-status` y el final de `/map-work`
cuando se cumple la precondición.

**El casillero**: `commands/map-collapse.md` y `skills/map-collapse/SKILL.md`
existen en el árbol. El contenido es del ticket 06.

> **Enmienda del ticket 06, que cerró.** El casillero dejó de estar vacío: el
> procedimiento está en [`06-el-colapso.md`](06-el-colapso.md). Dos cosas de esta
> sección cambiaron. La precondición se afinó a **cero tickets abiertos y cero
> milestones**, porque un mapa colapsado también tiene cero tickets abiertos. Y el
> token que emite `/map-collapse` al terminar no estaba fijado acá: es `sdd-new`,
> el sexto. El colapso además agregó dos operaciones al adapter,
> `milestone:create` e `issue:create`, así que la tabla de reparto de arriba es de
> ocho sobre cuatro comandos y la completa es de diez.

## El contrato compartido

`skills/_shared/map-contract.md`, en inglés porque su único lector es el modelo.

**Los tokens** de `next_recommended`, conjunto cerrado. Eran cinco; el ticket
06 agregó el sexto:

| Token | Cuándo |
| --- | --- |
| `map-new` | No hay mapa. |
| `map-work` | La frontera tiene al menos un ticket tomable. |
| `map-collapse` | Cero tickets abiertos. |
| `release-claim` | Hay una toma vieja y la frontera está flaca. |
| `break-cycle` | Hay tickets abiertos y la frontera está vacía. |
| `sdd-new` | El mapa está colapsado. Agregado por el ticket 06. |

Todos en inglés y no en español, aplicando la regla de idioma: el término
canónico es el inglés y es el que aparece en slugs. En las rondas de grilling
salieron como `desbloquear-toma` y `destrabar-ciclo`, antes de que la regla por
archivo estuviera decidida.

**El contrato de argumentos** y **la tabla de tipo de ticket a disciplina** van en
el mismo archivo, que son las otras dos cosas que más de un comando lee.

## Las plantillas

`skills/_shared/map-templates.md`, en español porque lo que genera lo lee una
persona en Linear. Tres archivos en `_shared/` y no uno: meter una plantilla en
español adentro del contrato en inglés es exactamente la clase de archivo que se
pudre.

### El esqueleto del DD

Seis encabezados de nivel 2, con **texto exacto**, y son contrato. Eran cinco; el
sexto lo agregó el ticket 06:

```markdown
## Destino
## Notas
## Decisiones hasta ahora
## Aún no especificado
## Fuera de alcance
## El colapso
```

`## El colapso` lo crea **vacío `/map-new`**, así que ningún DD nace sin él y la
falla fuerte de abajo sigue valiendo. Lo llena `/map-collapse` una sola vez, con
los milestones creados por nombre y enlace. No va en Decisiones por el mismo
argumento con el que `Fuera de alcance` quedó afuera: Decisiones registra la ruta
caminada, y un colapso no es un paso de esa ruta.

El plugin ancla por esos títulos, nunca por posición ni por índice de línea, y si
falta alguno **falla fuerte** en vez de escribir en el lugar equivocado. La
normalización que Linear aplica en la primera escritura, que el 02 midió sobre
viñetas, enlaces y tablas, no toca encabezados, así que la ancla es estable.

Notas lleva dominio, skills a consultar y preferencias permanentes. **No otorga
permisos.**

### El comentario de resolución

Cinco secciones, todas obligatorias, y las vacías lo dicen:

```markdown
## La decisión
## Por qué
## Niebla graduada        ← o "ninguna"
## Tickets nuevos         ← o "ninguno"
## Qué corrige o empuja   ← o "nada"
```

Va como comentario y no en el cuerpo del ticket: la pregunta queda inmutable y la
respuesta gana autor y timestamp gratis.

Los tres tickets que cerramos en el mapa v1 produjeron exactamente estas cinco
secciones sin que nadie se lo pidiera. La quinta no es adorno: el 03 le encontró
un defecto al 01, y sin un lugar fijo esa corrección hubiera vivido solo en la
prosa.

## La concurrencia de los subagentes

Wayfinder dispara los subagentes de research en paralelo, y resolver toca el mapa.
Con tres tickets de research eso son tres read-modify-write sobre el mismo
Document, desde una sola sesión. **No lo cubre la decisión de encuadre del
conductor único**, porque acá el conductor único genera tres escritores.

El reparto: cada subagente escribe **su** Document de research y **su** comentario
de resolución con **su** cambio de estado, que son recursos suyos y de nadie más.
El mapa, que es el único recurso compartido, lo escribe **solo el padre**, una
vez, con todas las líneas juntas.

Baja las escrituras del mapa de N a 1, que es un regalo para el ticket 09: menos
ventanas que proteger. Y el mapa sigue siendo el último write, así que el orden
del 03 se respeta.

**Cada subagente corre su propio preflight.** Un subagente es una sesión a este
efecto: tiene contexto propio y no puede heredar los ids del padre sin que alguien
se los pase, que es acoplamiento a cambio de nada y contradice la razón por la que
el 03 decidió no cachear. Cuesta 423 de complejidad por subagente, medido, contra
un presupuesto por hora que el 02 midió como irrelevante. La regla se lee **un
preflight por proceso que emite operaciones**, no uno por sesión de usuario.

## El árbol de archivos

Sigue la forma real de `../spec-driven-dev`: contratos en
`skills/_shared/*-contract.md`, checks en `scripts/check-*.sh` planos, y un
archivo fino por comando que rutea a una skill.

```
keiron-planner/
├── .claude-plugin/                  del 07
├── commands/
│   ├── map-new.md
│   ├── map-work.md
│   ├── map-collapse.md
│   ├── map-status.md                ROUTE: read-only, sin skill
│   └── grill.md                     la puerta suelta del 05
├── skills/
│   ├── _shared/
│   │   ├── map-contract.md          inglés
│   │   ├── map-templates.md         español
│   │   └── research-subagent.md     inglés
│   ├── map-new/SKILL.md
│   ├── map-work/SKILL.md
│   ├── map-collapse/SKILL.md        casillero del 06
│   ├── grilling/SKILL.md
│   ├── domain-modeling/SKILL.md
│   └── prototype/SKILL.md
├── scripts/
│   ├── linear.py                    el adapter, un subcomando por operación
│   ├── LINEAR-OPERATIONS.md         español, el reference del 03
│   ├── install.sh                   del 07
│   └── check-*.sh                   del 10
└── CONTEXT.md
```

`/map-status` no tiene skill: lee `map-contract.md` directo y llama al adapter.

### El adapter es un script, no el modelo

Las ocho operaciones las emite `scripts/linear.py`, stdlib pelado, un subcomando
por operación, y el modelo lo llama por Bash. El modelo **no** compone GraphQL.

El propio 03 dice que el predicado de frontera es "la parte de este documento que
más fácil se implementa mal". Un script lo implementa una vez en vez de una vez
por sesión. Las ocho son un contrato y no una disciplina, así que no hay nada ahí
que el modelo tenga que razonar. Un script se puede chequear estructuralmente y un
modelo componiendo queries no. Y ya tenemos dos prototipos que funcionan así,
`probe.py` e `install.sh`, los dos sin dependencias.

Lo que se pierde es que el modelo improvise una query. Es lo que queremos perder.

### Idioma por archivo

La regla es por lector, no por tipo.

| Lector | Idioma | Qué |
| --- | --- | --- |
| Solo el modelo | inglés | `commands/*.md`, `skills/*/SKILL.md`, `map-contract.md`, `research-subagent.md` |
| Una persona, en Linear | español | el mapa, los tickets, los comentarios, y `map-templates.md` que los genera |
| El dev leader que mantiene el adapter | español | `LINEAR-OPERATIONS.md` |

Los nombres de archivo, los tokens, los labels y los slugs siguen en inglés, que
es la regla general de `CONTEXT.md`.

## Lo que este documento corrige del reference del 03

Tres cosas, y van bajadas al reference cuando el plugin exista.

**`ticket:resolve` son cinco escrituras, no tres.** `ticket:create` y
`ticket:block` de los tickets nuevos van antes del comentario, porque la sección
"Tickets nuevos" los enlaza por nombre. El 03 escribió tres porque la plantilla
del comentario todavía no existía.

**`map:create` tiene una variante que usa solo su segunda mitad**, el
`documentCreate` del Document de research. No es una novena operación.

**El preflight es uno por proceso que emite operaciones**, no uno por sesión. Con
subagentes en paralelo, sesión y proceso dejan de ser lo mismo.

## Lo que este documento corrige de `CONTEXT.md`

**`Discovery` no es lo que marca el DD.** El glosario dice hoy que es "el label
que marca el DD de un proyecto" y que sigue significando eso. El 03 midió que un
Document de Linear no acepta labels, y que el `Discovery` que existe es un label
de issue del team CRM. Lo que identifica al mapa es el Project, y el Document se
encuentra a través de él. El plugin no lee ni escribe ese label nunca.

**Los títulos de los tickets no llevan prefijo numérico.** Nuestro tracker local
numera porque un directorio de archivos markdown no tiene otro orden. Linear tiene
`createdAt`, que el 03 ya eligió como el orden de la frontera, y muestra el
identificador al lado del título en toda su UI. El título es la pregunta en prosa
y nada más.

## Las afirmaciones chequeables, para el ticket 10

Lo que este ticket deja listo para que el 10 no lo re-derive.

1. El conjunto de tokens de `map-contract.md` es exactamente el que emiten los
   comandos. Cinco, ni uno más.
2. `commands/` tiene cinco archivos, y los tres que rutean apuntan a una skill que
   existe.
3. `map-status.md` dice `ROUTE: read-only` y **no** existe `skills/map-status/`.
4. `map-templates.md` tiene los cinco encabezados del DD y las cinco secciones del
   comentario, con texto exacto.
5. `scripts/linear.py` tiene un subcomando por cada una de las ocho operaciones
   nombradas en `LINEAR-OPERATIONS.md`, y ninguno de más.
6. Los archivos de la columna inglés no tienen prosa en español, y al revés.

> **Enmienda del ticket 06.** Tres de estas seis quedaron desactualizadas y el 06
> las corrige, con las suyas numeradas de la 7 a la 13 en
> [`06-el-colapso.md`](06-el-colapso.md). La 1 pasa a **seis** tokens. La 2 pasa a
> **cuatro** archivos que rutean a una skill, porque `map-collapse.md` dejó de ser
> un casillero. La 4 pasa a **seis** encabezados del DD, y le suma las tres
> secciones del cuerpo de la issue de ejecución. La 5 pasa a **diez** subcomandos.

Y una que **no** es estructural sobre el repo, así que el 10 tiene que decidir qué
hacer con ella: que ningún ticket de un mapa lleve dos labels `map:<tipo>`. Es lo
que el 03 dejó pendiente al elegir labels planos en vez de label groups, y se
chequea contra Linear, no contra el repo.

## Supuestos

- **Un solo conductor por mapa**, el dev leader. Es decisión de encuadre. El
  chequeo de rol del paso 5 de `/map-work` se apoya en esto para no preguntar en
  la sesión típica.
- Todo lo que el 03 supuso sigue supuesto: un solo team en el workspace, un mapa
  de hasta cincuenta tickets, y las escrituras atribuidas a quien generó la key.

## Lo que este documento no decide

- **El procedimiento de `/map-collapse`.** Es el ticket 06. Acá queda la
  precondición, el token y el casillero.
- **Qué chequean los checks estructurales.** Es el ticket 10, que gradúa con este.
- **Qué hace `/map-new` sobre un Project que ya arrancó.** Es el ticket 11, que
  gradúa con este.
- **Cómo se hace segura la escritura del mapa** frente a una edición humana. Es el
  ticket 09, y este documento le achica el problema: `/map-new` y `/map-work`
  escriben el mapa exactamente una vez cada uno.
- **Distribución, key y dónde vive el repo central de dominio.** Es el 07.
