---
lang: es
---

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
adapter. `README.md`, `CONTEXT.md` y `CLAUDE.md` van en español: su lector es una
persona del equipo, y el repo es internal. Los nombres de archivo siguen la regla
general y van en inglés.

**La columna la declara cada archivo, no una lista central.** Todo `.md` del árbol
del plugin lleva `lang: en` o `lang: es` en su frontmatter, y un archivo que nace
sin el campo falla un check. La prosa de arriba dice por qué cada uno cae donde
cae; el frontmatter es lo que se puede verificar. `vendor/` y `.scratch/` quedan
fuera del alcance.

## El mapa

| Canónico | En prosa | Qué es |
| --- | --- | --- |
| Map | Mapa | El DD vivo. **Es el overview del Project**, o sea `Project.content`, y no un Document aparte. Es un índice: **una línea por decisión**, con el enlace al ticket que guarda el detalle y un gist de **120 caracteres o menos**. Nunca repite el detalle. Lo decidió el ticket 11, midiendo que el overview es donde el DD del CRM se mantiene vivo y el Document es donde se muere. |
| Destination | Destino | Qué significa llegar. Se fija antes que nada y fija el alcance. Lo nombra la persona, siempre, y el plugin nunca lo propone. |
| Before the map | Antes del mapa | La sección donde `/map-new` preserva **verbatim** el overview que ya existía. Nunca se reescribe ni se reordena. Ahí viven las decisiones heredadas, sin enlace y sin gist, porque no tienen ticket detrás. Para meter una en el índice se abre un ticket de decisión y se resuelve, que es el camino normal. |
| Decision ticket | Ticket de decisión | Issue del Project con label `map`. Su cuerpo es una pregunta, no una tarea, y su título es esa pregunta en prosa, sin prefijo numérico. |
| Frontier | Frontera | Los tickets abiertos, sin bloqueantes abiertos y sin assignee. Lo tomable ahora. |
| Fog of war | Niebla | La sección "Aún no especificado" del mapa. Lo que se ve venir pero todavía no se puede formular con precisión. El test es si podés enunciar la pregunta, no si podés responderla. |
| Out of scope | Fuera de alcance | Trabajo que quedó más allá del destino. No es niebla y nunca gradúa. |
| Claim | Toma | El assignee del ticket. Es el primer write de la sesión, antes de cualquier trabajo. |
| Resolution | Resolución | Comentario con la respuesta en **seis secciones fijas**, estado Done, y una línea en Decisiones hasta ahora. La tercera es Lo que se cayó, donde vive la premisa que el ticket derribó al resolverse. Va como comentario y nunca en el cuerpo del ticket, para que la pregunta quede inmutable. |
| Collapse | Colapso | El paso del mapa a milestones e issues de ejecución. Un milestone es una decisión ya tomada, así que nace acá y nunca durante el mapeo. Es un evento único: corre con la frontera vacía, y una segunda corrida se niega. No se deshace: no hay descolapso. |
| Landing | Aterrizaje | El paso donde una decisión tomada **después** del colapso consigue su trabajo de ejecución. No es un colapso incremental: es un paso de `/map-work`, corre solo en sesiones HITL de `map:grilling` o `map:prototype`, y tiene tres desenlaces. Issues nuevas, ligar a una issue de ejecución que ya existe, o nada, y el tercero se marca con el label `map:no-landing`. Nunca aterriza en un corte terminado. Lo decidió el ticket 12. |

## Tipos de ticket

Todo ticket es HITL, que se trabaja con una persona que habla por si misma, o AFK,
que conduce el agente solo. Un ticket HITL solo se resuelve en ese intercambio
vivo: el agente nunca contesta por el humano.

| Label | Modo | Cuando |
| --- | --- | --- |
| `map` | Ambos | No es un tipo: es lo que hace que la issue sea un ticket de decisión, es por lo que filtra `frontier:query`, y su ausencia hace mentir a una lectura del mapa. |
| `map:research` | AFK | Falta un hecho que vive fuera del repo. |
| `map:prototype` | HITL | La pregunta es cómo debería verse o comportarse. |
| `map:grilling` | HITL | Conversación. El caso por defecto. |
| `map:task` | Ambos | Trabajo manual que desbloquea una decisión. Es el único tipo que hace en vez de decidir. |
| `hitl:pm` | HITL | El interlocutor es product. |
| `hitl:design` | HITL | El interlocutor es diseño. |
| `hitl:dev` | HITL | El interlocutor es desarrollo. |

Un ticket sin ninguno de esos labels es AFK, y esa ausencia es la señal.

## Terminos de Keiron que se conservan

- **DD**: el documento de discovery de un proyecto. El mapa es su versión viva.
  El equipo ya usa `DD: <proyecto>` como **título de issue**, con label `Discovery`
  y por fuera de todo Project. El plugin no toca esas issues ni reusa el prefijo:
  el mapa no tiene título propio porque el nombre del Project es su nombre.
- **Discovery**: el label de issue que el equipo usa para marcar trabajo de
  discovery. **No** es lo que identifica al DD: al mapa lo identifica el Project,
  porque el mapa *es* el overview del Project. Que un Project ya tenga mapa lo dice
  la presencia de las secciones del mapa, que es la huella por encabezado que
  `map:read` ya devuelve, y no un marcador ni un label. El plugin **lo escribe en todo ticket de decisión**, junto con
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
| `/map-new` | Traza el mapa: nombra el destino, mapea la frontera, adopta o crea el Project, escribe el mapa en su overview y crea los primeros tickets. Sobre un Project que ya arrancó nunca se niega: muestra lo que encontró y pide confirmación una vez. |
| `/map-work` | Resuelve un ticket. Nunca más de uno por sesión, salvo research. Sobre un Project que ya tiene milestones agrega el aterrizaje, después de resolver. |
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
subcomando no. Su salida es un blob opaco que reciben como `--ctx` las **siete**
operaciones que lo consumen: `map:create`, `ticket:create`, `frontier:query`,
`ticket:claim`, `ticket:resolve`, `ticket:rule-out` y `work:write`. Las otras
cuatro no lo necesitan. Un subcomando consumidor invocado sin `--ctx` falla, porque
ninguno sabe hacer un preflight: así la regla se cumple por construcción y no por
disciplina. Nada persiste entre corridas; pasar ids adentro de una misma corrida sí
está permitido, y es el mecanismo.

| Canónico | En prosa | Qué es |
| --- | --- | --- |
| `preflight` | El preflight | Solo lectura. Corre una vez por conductor, antes de cualquier otra operación, y resuelve lo que las demás necesitan. No guarda nada y no crea nada: la fuente de verdad es el tracker. Falla duro en cuatro casos y solo en esos cuatro: sin credencial, sin el team, sin algún estado de cerrado, y sin el label `map`. |
| `map:create` | Crear el mapa | Adopta el Project si le pasan uno, lo crea si no, y escribe el mapa en su overview. Las secciones del mapa van arriba; lo que ya estaba se preserva verbatim debajo, bajo Antes del mapa. No borra ni reescribe nunca prosa que escribió una persona. |
| `map:read` | Leer el mapa | Solo lectura. Devuelve el contenido y una huella por cada encabezado. La usan `/map-status` y el paso que le muestra el estado a la persona. |
| `map:write` | Escribir el mapa | Un read-modify-write entero adentro de una sola invocación. Recibe la edición como argumentos semánticos, nunca markdown: relee justo antes de escribir para que la ventana sean milisegundos y no la sesión. |
| `ticket:create` | Crear un ticket | Un issue del Project cuyo cuerpo es la pregunta y nada más. El tipo, el modo, el bloqueo y la toma viven en campos nativos del tracker. Es además el **único** que crea los labels del plugin que falten, los nueve, aunque no los use todos. Nunca crea `Discovery`. |
| `ticket:block` | Bloquear | La relación nativa de bloqueo. Se escribe en una segunda pasada, porque los tickets tienen que existir para poder referenciarse. |
| `frontier:query` | Consultar la frontera | Los tickets abiertos, sin bloqueantes abiertos y sin assignee. |
| `ticket:claim` | Tomar | El primer write de la sesión. No se libera sola. |
| `ticket:resolve` | Resolver | Los tickets nuevos, su cableado, el comentario, el estado y el mapa, en ese orden. El mapa siempre último. Las cinco escrituras van adentro de una sola invocación: el orden lo garantiza el adapter, nunca el modelo. |
| `ticket:rule-out` | Sacar de alcance | La única operación destructiva: cierra un ticket sin resolverlo. Su línea va a Fuera de alcance, nunca a Decisiones. |
| `milestone:create` | Crear un milestone | Un corte demoable del colapso. Nunca lleva fecha. |
| `work:write` | Escribir el trabajo | Lo que produce un colapso o un aterrizaje, en una sola invocación: las issues de ejecución en una llamada atómica, las relaciones `related` hacia su ticket de decisión, y el label `map:no-landing` cuando no hubo trabajo. La lista de issues puede venir vacía. Ninguna issue lleva label `map` y su cuerpo es un imperativo, no una pregunta. |

## Los checks

La verificación del plugin son checks estructurales sobre el repo, al estilo de
los `scripts/check-*.sh` de `spec-driven-dev`. No verifican comportamiento
conversacional: eso quedó fuera de alcance al trazar el mapa.

| Término | Qué es |
| --- | --- |
| Afirmación | Una invariante estructural del repo, escrita como una oración verificable y con un método que la chequea. Es el término del que cuelgan los demás. Cada una tiene un número, y ese número aparece entre corchetes en el mensaje de falla del script que la emite. |
| Estado | Lo que una afirmación dice de sí misma en la tabla, y toma estos valores. `pendiente` es acuñada pero todavía sin script que la chequee. `viva` es la que un script emite hoy. `retirada` es la que otra afirmación reemplazó, y se conserva con su puntero para que nadie la reescriba leyendo el research donde nació. Una fila pasa a `viva` en la misma task que escribe su check, y no antes: así se nota cuando alguien construyó algo sin chequearlo. |
| `scripts/CHECKS.md` | Donde vive la tabla de afirmaciones, agrupada por el script que las chequea. Es la **única casa del conteo**: una afirmación que no tiene fila acá no existe, y ningún otro archivo del repo vuelve a contarlas. El script no es una columna, es el encabezado de cada bloque, porque una columna sería una segunda copia. |
| `scripts/_common.sh` | El contrato que cada script de check sourcea. No lleva shebang ni bit de ejecución, así que queda fuera del namespace `check-*` y no entra al glob del runner. Tiene un gemelo en Python, `scripts/_common.py`, con las mismas funciones y la misma forma de mensaje, porque no todo script del set es bash. |
| `fail` | Acumula una falla y sigue. Su mensaje lleva el número de la afirmación entre corchetes, y ese literal es lo que permite comparar lo que los scripts emiten contra lo que la tabla dice. |
| `report` | Imprime todas las fallas acumuladas y sale distinto de cero. Una corrida nombra todo lo que está roto, no lo primero que encontró. |
| `bail` | El tercer tier: cuando falta el archivo o la herramienta que el check mira, reporta y sale ahí mismo. Las fallas derivadas de una fuente ausente son ruido, y sepultan el mensaje que importa. |
| `require_nonempty` | La regla anti vacuidad como función: un check cuya fuente falta o cuya extracción da vacío falla, nunca pasa. Una aserción que quiere acumular en vez de cortar no usa el helper, usa `fail`. |
| `scripts/run-checks.sh` | Corre todos los checks y agrega sus códigos de salida. La lista sale de un glob y no de ninguna lista escrita, así que agregar un check no toca ni el runner ni el workflow. Ejecuta cada check como subproceso y nunca lo sourcea. |
| El idioma de los scripts | Comentarios y mensajes de falla en español, con los términos canónicos en inglés. Su lector es el dev leader. No llevan `lang:` porque la columna de idioma es de los `.md`. Y la prohibición de guiones largos de `Regla de idioma` **alcanza también a los mensajes que los scripts emiten**: la regla no distingue prosa de salida de programa. |

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
