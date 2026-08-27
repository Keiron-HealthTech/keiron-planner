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

## El mapa

| Canónico | En prosa | Qué es |
| --- | --- | --- |
| Map | Mapa | El DD vivo. Un Document de Linear titulado `DD: <proyecto>`, dentro del Project. Es un índice: lista las decisiones tomadas y apunta a los tickets que guardan el detalle, nunca lo repite. |
| Destination | Destino | Qué significa llegar. Se fija antes que nada y fija el alcance. |
| Decision ticket | Ticket de decisión | Issue del Project con label `map`. Su cuerpo es una pregunta, no una tarea. |
| Frontier | Frontera | Los tickets abiertos, sin bloqueantes abiertos y sin assignee. Lo tomable ahora. |
| Fog of war | Niebla | La sección "Aún no especificado" del mapa. Lo que se ve venir pero todavía no se puede formular con precisión. El test es si podés enunciar la pregunta, no si podés responderla. |
| Out of scope | Fuera de alcance | Trabajo que quedó más allá del destino. No es niebla y nunca gradúa. |
| Claim | Toma | El assignee del ticket. Es el primer write de la sesión, antes de cualquier trabajo. |
| Resolution | Resolución | Comentario con la respuesta, estado Done, y una línea en Decisiones hasta ahora. |
| Collapse | Colapso | El paso del mapa a milestones e issues de ejecución. Un milestone es una decisión ya tomada, así que nace acá y nunca durante el mapeo. |

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
- **Discovery**: el label que marca el DD de un proyecto. Sigue significando eso.
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

## Las operaciones del tracker

Lo que el adapter sabe hacer. Son ocho, y los comandos se arman con ellas. El
término canónico es el que aparece en el código.

| Canónico | En prosa | Qué es |
| --- | --- | --- |
| Preflight | El preflight | El chequeo que corre una vez por sesión, antes de cualquier operación. Resuelve lo que las operaciones necesitan y falla temprano y claro si algo no está. No guarda nada: la fuente de verdad es el tracker. |
| `map:create` | Crear el mapa | Adopta el Project si le pasan uno, lo crea si no, y le cuelga el Document del mapa. |
| `map:read-write` | Leer y actualizar el mapa | Las dos mitades de un read-modify-write, nombradas juntas porque son la misma operación. |
| `ticket:create` | Crear un ticket | Un issue del Project cuyo cuerpo es la pregunta y nada más. El tipo, el modo, el bloqueo y la toma viven en campos nativos del tracker. |
| `ticket:block` | Bloquear | La relación nativa de bloqueo. Se escribe en una segunda pasada, porque los tickets tienen que existir para poder referenciarse. |
| `frontier:query` | Consultar la frontera | La única operación que no escribe. |
| `ticket:claim` | Tomar | El primer write de la sesión. No se libera sola. |
| `ticket:resolve` | Resolver | Comentario, estado, mapa, en ese orden. |
| `ticket:rule-out` | Sacar de alcance | La única operación destructiva: cierra un ticket sin resolverlo. Su línea va a Fuera de alcance, nunca a Decisiones. |

## Dependencias

`keiron-planner` declara `spec-driven-dev` como peer dependency. La dirección es
la misma de siempre: SDD construye, el planner planifica.

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
