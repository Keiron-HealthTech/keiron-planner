# CONTEXT

Glosario del plugin `keiron-planner`. Es un glosario y nada más: no lleva
decisiones de implementación, ni spec, ni notas sueltas.

## Regla de idioma

El término canónico es el inglés y es el que aparece en skills, comandos, labels,
slugs y nombres de rama. La prosa que leen humanos va en español neutro, con
tildes normales, sin voz chilena ni argentina y sin modismos. Los anglicismos ya
asentados en el equipo no se traducen: tracer bullet, seam, milestone, dual-write,
backfill, kill-switch.

Sin guiones largos en la prosa. Si una frase los pide, se reescribe.

Dentro del plugin la regla es **por lector, no por tipo de archivo**. Lo que solo
lee el modelo va en inglés: los comandos, las skills y los contratos compartidos.
Lo que lee una persona en Linear va en español: el mapa, los tickets, los
comentarios de resolución y las plantillas que los generan. El reference de las
operaciones del tracker va en español, porque su lector es quien mantiene el
adapter. Los nombres de archivo siguen la regla general y van en inglés.

## El mapa

| Canónico | En prosa | Qué es |
| --- | --- | --- |
| Map | Mapa | El DD vivo. Un Document de Linear titulado `DD: <proyecto>`, dentro del Project. Es un índice: **una línea por decisión**, con el enlace al ticket que guarda el detalle y un gist de **120 caracteres o menos**. Nunca repite el detalle. |
| Destination | Destino | Qué significa llegar. Se fija antes que nada y fija el alcance. |
| Decision ticket | Ticket de decisión | Issue del Project con label `map`. Su cuerpo es una pregunta, no una tarea, y su título es esa pregunta en prosa, sin prefijo numérico. |
| Frontier | Frontera | Los tickets abiertos, sin bloqueantes abiertos y sin assignee. Lo tomable ahora. |
| Fog of war | Niebla | La sección "Aún no especificado" del mapa. Lo que se ve venir pero todavía no se puede formular con precisión. El test es si podés enunciar la pregunta, no si podés responderla. |
| Out of scope | Fuera de alcance | Trabajo que quedó más allá del destino. No es niebla y nunca gradúa. |
| Claim | Toma | El assignee del ticket. Es el primer write de la sesión, antes de cualquier trabajo. |
| Resolution | Resolución | Comentario con la respuesta en **seis secciones fijas**, estado Done, y una línea en Decisiones hasta ahora. La sexta es Lo que se cayó, donde vive la premisa que el ticket derribó al resolverse. Va como comentario y nunca en el cuerpo del ticket, para que la pregunta quede inmutable. |
| Collapse | Colapso | El paso del mapa a milestones e issues de ejecución. Un milestone es una decisión ya tomada, así que nace acá y nunca durante el mapeo. Es un evento único: corre con la frontera vacía, y una segunda corrida se niega. |

## Tipos de ticket

Todo ticket es HITL, que se trabaja con una persona que habla por si misma, o AFK,
que conduce el agente solo. Un ticket HITL solo se resuelve en ese intercambio
vivo: el agente nunca contesta por el humano.

| Label | Modo | Cuando |
| --- | --- | --- |
| `map:research` | AFK | Falta un hecho que vive fuera del repo. |
| `map:prototype` | HITL | La pregunta es cómo debería verse o comportarse. |
| `map:grilling` | HITL | Conversación. El caso por defecto. |
| `map:task` | Ambos | Trabajo manual que desbloquea una decisión. Es el único tipo que hace en vez de decidir. |

El interlocutor de un ticket HITL va como `hitl:pm`, `hitl:design` o `hitl:dev`.
Un ticket sin ninguno de esos labels es AFK, y esa ausencia es la señal.

## Terminos de Keiron que se conservan

- **DD**: el documento de discovery de un proyecto. El mapa es su versión viva.
- **Discovery**: el label de issue que el equipo usa para marcar trabajo de
  discovery. **No** es lo que identifica al DD: un Document de Linear no acepta
  labels, así que al mapa lo identifica el Project y el Document se encuentra a
  través de él. El plugin **lo escribe en todo ticket de decisión**, junto con
  `map`, cuando el label existe en el workspace, y lo saltea en silencio cuando no.
  Nunca lo crea. Las issues de ejecución no lo llevan: no son discovery.
- **Milestone**: un corte demoable que agrupa tracer bullets, nunca un corte
  temporal. El primero es siempre el tracer bullet del proyecto.
- **Tracer bullet**: una rebanada vertical que cruza todas las capas, demostrable
  por sí sola, del tamaño de una ventana de contexto fresca.
- **Dev leader**: quien conduce el mapa de un proyecto.

## Terminos que no usamos

- **Plan** para referirse al mapa. Un plan es una solución elegida; el mapa
  produce decisiones y todavía no elige.
- **Tarea** para un ticket de decisión. Un ticket de decisión es una pregunta.
  Las tareas aparecen recién en el colapso.
- **Fase** para un milestone. Una fase es tiempo, un milestone es un corte
  demoable.

## Comandos

| Comando | Que hace |
| --- | --- |
| `/map-new` | Traza el mapa: nombra el destino, mapea la frontera, crea el Project, el DD y los primeros tickets. |
| `/map-work` | Resuelve un ticket. Nunca más de uno por sesión, salvo research. |
| `/map-collapse` | Colapsa el mapa en milestones e issues de ejecucion. |
| `/map-status` | Lee el mapa y la frontera. No escribe. |
| `/planner-setup` | Pide la API key de Linear, la valida contra la API y la guarda. Por máquina, una vez. No es una operación del mapa. |

Cada comando cierra con un **next recommended**: un token de un conjunto cerrado
de seis que dice qué correr después. Es la costura entre comandos y lo único del
flujo que se puede verificar mecánicamente. El sexto, `sdd-new`, es además la
costura con el plugin hermano: se emite cuando el mapa está colapsado y el trabajo
pasa a SDD.

## Las operaciones del tracker

Lo que el adapter sabe hacer. Son doce, y los comandos se arman con ellas. El
término canónico es el que aparece en el código. Tres no escriben: `preflight`,
`frontier:query` y `map:read`.

El `preflight` corre **una vez por conductor**, y conductor es un contexto de
modelo que emite operaciones: la sesión es uno, cada subagente es uno, un
subcomando no. Su salida es un blob opaco que las otras once reciben como `--ctx`.
Un subcomando invocado sin `--ctx` falla, porque ninguno sabe hacer un preflight:
así la regla se cumple por construcción y no por disciplina. Nada persiste entre
corridas; pasar ids adentro de una misma corrida sí está permitido, y es el
mecanismo.

| Canónico | En prosa | Qué es |
| --- | --- | --- |
| `preflight` | El preflight | Solo lectura. Corre una vez por conductor, antes de cualquier otra operación, y resuelve lo que las demás necesitan. No guarda nada y no crea nada: la fuente de verdad es el tracker. Falla duro en cuatro casos y solo en esos cuatro: sin credencial, sin el team, sin algún estado de cerrado, y sin el label `map`. |
| `map:create` | Crear el mapa | Adopta el Project si le pasan uno, lo crea si no, y le cuelga el Document del mapa. |
| `map:read` | Leer el mapa | Solo lectura. Devuelve el contenido y una huella por cada encabezado. La usan `/map-status` y el paso que le muestra el estado a la persona. |
| `map:write` | Escribir el mapa | Un read-modify-write entero adentro de una sola invocación. Recibe la edición como argumentos semánticos, nunca markdown: relee justo antes de escribir para que la ventana sean milisegundos y no la sesión. |
| `ticket:create` | Crear un ticket | Un issue del Project cuyo cuerpo es la pregunta y nada más. El tipo, el modo, el bloqueo y la toma viven en campos nativos del tracker. Es además quien crea los labels del plugin que falten, porque es su único consumidor. Nunca crea `Discovery`. |
| `ticket:block` | Bloquear | La relación nativa de bloqueo. Se escribe en una segunda pasada, porque los tickets tienen que existir para poder referenciarse. |
| `frontier:query` | Consultar la frontera | Los tickets abiertos, sin bloqueantes abiertos y sin assignee. |
| `ticket:claim` | Tomar | El primer write de la sesión. No se libera sola. |
| `ticket:resolve` | Resolver | Los tickets nuevos, su cableado, el comentario, el estado y el mapa, en ese orden. El mapa siempre último. Las cinco escrituras van adentro de una sola invocación: el orden lo garantiza el adapter, nunca el modelo. |
| `ticket:rule-out` | Sacar de alcance | La única operación destructiva: cierra un ticket sin resolverlo. Su línea va a Fuera de alcance, nunca a Decisiones. |
| `milestone:create` | Crear un milestone | Un corte demoable del colapso. Nunca lleva fecha. |
| `issue:create` | Crear una issue de ejecución | Todas las del colapso en una sola llamada atómica. No lleva label `map` y su cuerpo es un imperativo, no una pregunta. |

## Dependencias

`keiron-planner` declara `spec-driven-dev` en el campo `dependencies` de su
`plugin.json`, sin constraint de versión. Es un mecanismo real y no una convención:
Claude Code auto-instala y auto-habilita la dependencia, y se niega a deshabilitarla
mientras el planner esté habilitado. La dirección es la misma de siempre: SDD
construye, el planner planifica.

Los dos plugins viven en el **mismo marketplace**, el de
`Keiron-HealthTech/spec-driven-dev`, que hospeda a los dos. Por eso la dependencia
resuelve intra-marketplace y quien instala agrega un solo marketplace.

**El traspaso ocurre en `/sdd-new`**, no más tarde. El colapso termina en issues de
Linear y no escribe archivos en el árbol de artefactos de SDD; SDD lee la issue de
Linear y corre su propio discovery loop desde ahí.

La propiedad de las disciplinas compartidas sigue a la necesidad, no al orden en
que se pensaron. Grilling, domain-modeling y prototype viven **en este plugin**,
porque toda sesión de `/map-work` las usa y en SDD todavía no existen. SDD las
importa cuando le hagan falta.

Lo que aporta este plugin y no existe en ningún otro lado: el mapa, la niebla,
los tickets de decisión, el colapso y el adapter de Linear.

## Atribución

El modelo del mapa viene de la skill `wayfinder` de
[mattpocock/skills](https://github.com/mattpocock/skills), MIT, Copyright 2026
Matt Pocock. También vienen de ahí grilling, domain-modeling y prototype.
