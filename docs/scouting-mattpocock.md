---
lang: es
---

# Scouting: skills de mattpocock/skills para el flujo de planificación del equipo CRM

Fuente: https://github.com/mattpocock/skills (clonado y leído completo, 2026-08-26).
36 skills en 4 carpetas: `engineering`, `productivity`, `misc`, `in-progress`.

## Qué problema estamos resolviendo

El flujo actual del equipo CRM:

1. Workshops 2x semana con el product team completo. Entran ideas, pedidas, dolores.
2. Discovery con PM, Diseño y el dev que va a liderar.
3. Si es propuesta de producto, parte de un prototipo de Diseño. Si es técnica, va directo a Linear o se arma una PoC.
4. Idea validada, el dev leader arma el proyecto en Linear con tareas autocontenidas y Milestones.
5. Hoy usamos SDD (explore → propose → spec → design → tasks) para llegar a esas issues.

Los dolores que declaramos con SDD como framework de planificación:

- Pesado para el tamaño del problema.
- Nos casa con una solución demasiado temprano.
- El proyecto queda rígido.
- No atajamos casos borde.

Los tres primeros son el mismo problema: SDD es una cadena lineal de artefactos donde la fase `propose` fija la solución antes de que sepamos lo suficiente, y todo lo que viene después la elabora en vez de cuestionarla. El cuarto es consecuencia: si el plan se cierra temprano, no queda dónde anotar "esto todavía no lo sé".

## Ranking

### Tier S: el núcleo del plugin

**1. `wayfinder`** (engineering, user-invoked, 128 líneas)

Es la respuesta directa a "proyectos que no alcanzan con sdd explore". Su tesis es que planificar no es producir un plan sino despejar decisiones, una por sesión, hasta que el camino al destino esté claro.

Lo que ataca de nuestros dolores:

- **Casarse con una solución**: la regla es "produce decisiones, no entregables". El mapa nunca contiene la solución. Contiene el registro de qué se decidió y por qué. Un ticket es una pregunta, no un slice de build.
- **Rigidez**: el mapa es deliberadamente incompleto. Solo se tickea lo que ya se puede formular con precisión.
- **Casos borde**: la sección `Not yet specified` (fog of war) es literalmente el lugar donde vive lo que sabés que viene pero todavía no podés formular. Hoy no tenemos ese lugar. Los casos borde que no atajamos no es que se nos escapen, es que no tienen dónde anotarse hasta que alguien los tropieza.
- **Peso**: nunca resuelve más de un ticket por sesión (excepto research). Nadie tiene que aguantar el proyecto entero en la cabeza.

Además distingue 4 tipos de ticket, y la distinción HITL vs AFK mapea casi exacto a nuestro discovery:

| Tipo | Modo | Quién en nuestro equipo |
|---|---|---|
| `research` | AFK | agente en background |
| `prototype` | HITL | Diseño, o dev para PoC |
| `grilling` | HITL | PM + dev leader |
| `task` | ambos | quien tenga el acceso |

**Lo que falta y tenemos que construir**: el adapter de Linear. Matt solo trae GitHub, GitLab y markdown local. La sección "Wayfinding operations" del doc de tracker define map, child ticket, blocking, frontier query, claim y resolve. Hay que escribir la versión Linear de esas 6 operaciones. Linear tiene todo lo necesario (sub-issues, relaciones blocks/blocked-by nativas, labels, assignee) y tenemos el MCP conectado.

**2. `grilling`** (productivity, model-invoked, 28 líneas)

28 líneas y es el motor de la mitad del repo. Modela la conversación como un árbol de decisiones y trabaja por rondas: pregunta toda la frontera de una vez, cada pregunta numerada y con tu recomendación al lado, y espera. Una pregunta cuya respuesta depende de otra pregunta abierta va a la ronda siguiente, no a esta.

La regla que más me gusta: **encontrar hechos es trabajo del agente, decidir es trabajo tuyo**. Si una pregunta necesita un dato del entorno, despacha un subagente y sigue preguntando el resto de la frontera mientras tanto. Nunca te pregunta algo que podría averiguar solo.

Comparado con el Q&A de `sdd-explore`, esto es más barato y más denso. Y sirve igual para un workshop que para un discovery técnico, porque no asume código.

**3. `prototype`** (engineering, model-invoked, 26 líneas + LOGIC.md + UI.md)

Ya prototipamos, pero informalmente. Lo que agrega Matt es la disciplina: **un prototipo es código descartable que responde una pregunta**, y la pregunta decide la forma. Dos ramas, y elegir mal desperdicia el prototipo entero:

- "¿este modelo de estados se siente bien?" → un HTML de un solo archivo, con botones de juego libre y walkthroughs guiados, que un no-desarrollador puede manejar.
- "¿cómo debería verse esto?" → varias variantes de UI radicalmente distintas en una ruta, conmutables por search param.

La regla 6 es la que nos falta hoy: el prototipo se captura como **fuente primaria** en una rama aparte, con un puntero desde la issue. La decisión validada entra a main, el prototipo no. Hoy los prototipos de Diseño y las PoC se evaporan y después nadie sabe por qué se decidió lo que se decidió.

La rama LOGIC es la que más nos sirve para CRM. Nuestros dolores son máquinas de estado (reagendamiento, confirmaciones, ciclo de vida del deal) y son exactamente lo que es difícil razonar en papel.

### Tier A: alto valor, entran en la v1

**4. `to-tickets`** (engineering, user-invoked, 105 líneas)

Es nuestro paso "el dev leader arma el proyecto en Linear". Aporta tres cosas que hoy hacemos a ojo:

- **Tracer bullets verticales**: cada slice corta un camino angosto pero completo por todas las capas, es demoable solo, y entra en una ventana de contexto fresca. Es lo mismo que buscamos con "tareas autocontenidas", pero con un test concreto.
- **Blocking edges explícitas**, nativas del tracker. Es lo que hace que un agente pueda agarrar cualquier ticket cuyos bloqueantes estén cerrados sin preguntar.
- **Expand-contract para refactors anchos**: la excepción al slicing vertical. Un rename de columna cuyo radio de impacto son mil call sites no entra en un tracer bullet. Primero expandir, después migrar por lotes del tamaño del radio, cada lote un ticket, y contraer al final. Esto SDD no lo modela y nos ha mordido.

**Gap**: Matt no modela Milestones. Nosotros los usamos y son estrictos. Hay que definir cómo agrupan los tickets, y mi apuesta es que un Milestone es un corte demoable que agrupa tracer bullets, no un corte temporal.

**5. `domain-modeling`** (engineering, model-invoked, 74 líneas)

`CONTEXT.md` como glosario del proyecto, y nada más que glosario. Sin detalles de implementación, sin spec, sin scratchpad. Más `docs/adr/` para decisiones difíciles de revertir.

El criterio para ofrecer un ADR es de tres condiciones, y tienen que darse las tres: difícil de revertir, sorprendente sin contexto, y resultado de un trade-off real. Si falta una, no hay ADR. Esa disciplina es lo que evita el cementerio de ADRs que nadie lee.

Para CRM esto vale mucho porque tenemos jerga propia y overloaded. Y a diferencia de todo lo demás, persiste entre proyectos: cada discovery deja el glosario más afilado que el anterior.

La técnica activa que importa: cuando el usuario usa un término que choca con el glosario, cortarlo ahí mismo. "Tu glosario define cancelación como X, pero parece que querés decir Y. ¿Cuál es?"

**6. `to-spec`** (engineering, user-invoked, 75 líneas)

Convierte la conversación en spec **sin entrevistar**. Ese es el punto entero: la entrevista ya pasó, esto solo sintetiza.

El contraste con SDD es lo interesante. Nuestro `sdd-spec` + `sdd-design` son dos fases obligatorias con sus propios sub-agentes. Acá la spec es la salida de una conversación que ya cerró, con una plantilla de 7 secciones y un paso de confirmación sobre los seams de testing. Más liviano y llega al mismo lugar.

En el flujo de wayfinder, `to-spec` es el **colapso del mapa**: junta las decisiones enlazadas en un plan construible. Matt es explícito en que saltarse ese colapso y mandar el mapa directo a implementar tira a la basura el detalle enlazado.

### Tier B: valiosas, candidatas a v2

**7. `to-questionnaire`** (productivity, 54 líneas). Para cuando lo que bloquea no está ni en tu cabeza ni en el código sino en la de otra persona. Comercial, soporte, un stakeholder de negocio. La inversión que propone es astuta: te entrevista sobre **el envío** (a quién va, qué necesitás de vuelta), nunca sobre el tema, porque el tema es justo lo que no sabés. Encaja con nuestro ciclo de workshops de 2x semana, donde la ventana síncrona es cara.

**8. `triage`** (engineering, 112 líneas). El on-ramp de las pedidas y dolores que llegan crudos. Máquina de estados de 5 roles más 2 categorías. Lo que más aporta: el paso de **verificar el claim antes de discutirlo** (reproducir el bug, chequear si ya está implementado buscando por concepto de dominio y no por las palabras del pedido), y `.out-of-scope/` como base de conocimiento de lo ya rechazado. Nos evitaría re-discutir la misma pedida cada tres meses.

**9. `research`** (engineering, 12 líneas). Agente en background contra fuentes primarias, deja un markdown citado. Es el resolvedor de los tickets `research` de wayfinder, así que en la práctica entra junto con wayfinder aunque su valor propio sea chico.

**10. `handoff`** (productivity, 16 líneas). Cruce de sesión, de directorio o de persona. En nuestro flujo el handoff real es PM → Diseño → dev leader, y hoy se hace por Slack. Incluye una sección "suggested skills" para el que retoma.

### Tier C: no van al plugin, pero copiamos el patrón

- **`ask-matt`** (90 líneas). Un router sobre las demás skills, escrito como mapa de flujos con on-ramps. Es el mejor documento del repo y el patrón que deberíamos copiar para la entrada del plugin. Su sección "Phase boundaries" (continuar, clear, handoff, subagente, compact) es aplicable tal cual.
- **`writing-for-agents`** (81 líneas). Guía de estilo para escribir skills. La usamos mientras construimos, no la enviamos.
- **`setup-matt-pocock-skills`** (116 líneas). El patrón de configuración por repo. Nosotros necesitamos el equivalente para Linear, y este es el molde.
- **`wait-what`** (7 líneas). Barata y sorprendentemente útil en sesiones con gente no técnica: "eso no me llegó, re-explicámelo con el vocabulario del CONTEXT.md". Cuesta nada incluirla.
- **`retro`** (in-progress, 44 líneas). Retro sobre el entorno del agente, no sobre el equipo. Interesante más adelante.

### Fuera de alcance

Ya cubierto por SDD o irrelevante para planificación: `tdd`, `code-review`, `implement`, `diagnosing-bugs`, `resolving-merge-conflicts`, `codebase-design`, `improve-codebase-architecture`, `wizard`, `teach`, y todo `misc/`.

`improve-codebase-architecture` es buena pero es salud de codebase, no planificación. Genera ideas que entran al flujo, no lo conduce.

## Los cuatro gaps que el plugin tiene que llenar

Ninguno lo resuelve Matt, porque su repo asume un dev solo con GitHub.

1. **Adapter de Linear.** Las 6 operaciones de wayfinding traducidas a Linear vía MCP. Es el bloqueante técnico principal.
2. **Milestones.** Matt no los modela. Definir qué es un Milestone en términos de tracer bullets y cómo se derivan del mapa cuando colapsa.
3. **Intake de workshop.** No hay nada para el ritual de 2x semana con el product team completo. Cómo entra una idea cruda, qué la promueve a discovery, dónde vive mientras tanto.
4. **Multi-rol en HITL.** `grilling` asume un humano. Nuestro discovery tiene PM, Diseño y dev leader, y cada ticket HITL tiene un dueño distinto. Un ticket de prototipo es de Diseño, uno de grilling técnico es del dev leader. El mapa tiene que saber a quién le toca.

## Recomendación

La v1 del plugin es wayfinder sobre Linear, con grilling y prototype adentro, y to-tickets como salida. `to-spec` y `domain-modeling` entran en el medio. SDD no se reemplaza: queda para cuando la solución ya está decidida y hay que construirla bien. El plugin cubre lo de antes, que es justo donde SDD nos aprieta.
