# Mapa: keiron-planner v1

Tracker local en markdown. Los tickets viven en `issues/`, uno por archivo.
Este mapa es un índice: gista cada decisión y apunta al ticket que la guarda.
Nunca la repite.

## Destino

Una spec lista para que SDD la construya: todas las decisiones de diseño del
plugin resueltas, colapsadas en spec y tasks de SDD, con el colapso mismo
probado como costura entre los dos plugins.

## Notas

**Dominio**: un plugin de Claude Code para planificar proyectos grandes del
equipo CRM, sobre Linear. El glosario canónico es `CONTEXT.md` en la raíz.

**Skills que toda sesión consulta**: grilling y domain-modeling, salvo que el
tipo del ticket diga otra cosa.

**Preferencias permanentes**:

- `CONTEXT.md` es la fuente de verdad del vocabulario y se actualiza en el
  momento en que un término se resuelve, nunca al final.
- Nunca más de un ticket por sesión. Research es la única excepción.
- Prosa en español neutro, con tildes, sin modismos regionales y sin guiones
  largos.
- El repo de Matt Pocock es fuente primaria. Vive clonado en un lugar durable,
  no en `/tmp`.

**Decisiones de encuadre**, tomadas al trazar el mapa y no por un ticket:

- La propiedad de grilling, domain-modeling y prototype es de este plugin, no
  de SDD, porque acá se necesitan hoy y allá todavía no existen.
- El adapter soporta Linear y nada más.
- `/map-collapse` llega hasta issues de Linear con sus milestones. SDD entra
  recién en `/sdd-new`. (Decía `/sdd-apply`. Lo corrigió el ticket 06: para entrar
  en `/sdd-apply` tendrían que existir ya los artefactos de planificación de SDD, y
  un colapso que solo escribe Linear no los escribe.)
- El mapa asume un solo conductor, el dev leader. El claim se implementa igual
  porque cuesta una línea.
- La verificación son checks estructurales sobre el repo, al estilo de los
  `scripts/check-*.sh` de SDD. Nada de verificar comportamiento conversacional.

## Decisiones hasta ahora

<!-- una línea por ticket cerrado, con enlace al ticket que guarda el detalle -->

- [13: Si una pestaña abierta puede pisar una escritura del plugin](issues/13-pestana-abierta-pisa-al-plugin.md):
  no puede, y el 09 queda completo sin cambiarle nada. El mecanismo es que
  `documentUpdate` mueve `contentState`, el estado Yjs, así que el servidor convierte
  el markdown en un update colaborativo de verdad en vez de escribir por detrás del
  CRDT, y no deja ninguna rama con la que un cliente pueda ganar. Medido en tres
  condiciones, incluida una que el ticket no pedía y es la más dura: un cliente
  offline y divergente, que al reconectar fusionó las dos ramas en un solo evento
  atómico. Una quinta fase corre al revés y cierra la lectura equivocada de que el
  09 sobra: con markdown rancio el plugin **sí** borra una línea escrita en la UI,
  porque una escritura suya no es una rama concurrente sino un reemplazo
  autoritativo. No se agrega ninguna verificación posterior, y `contentState` queda
  prohibido en el contrato pese a ser el detector de cambio perfecto que
  `updatedAt` nunca fue: no dice qué sección cambió y cuesta 16 veces el payload.
- [09: Cómo evita el plugin pisar una edición humana del mapa](issues/09-concurrencia-humano-plugin.md):
  la estrategia no detecta el conflicto, lo evita. El plugin no escribe sobre lo que
  leyó al empezar la sesión: relee justo antes de escribir y aplica su edición sobre
  ese contenido fresco, así que la edición de la persona sobrevive por estar en la
  base. La ventana pasa de una sesión entera a 332 ms medidos. La premisa del ticket
  se cayó: `updatedAt` está coalescido y quedó quieto 300 segundos con contenido nuevo
  ya persistido, así que es inservible; la señal es `content`. Para que los 332 ms
  existan, `map:read-write` se parte en `map:read` y `map:write`, y el segundo hace el
  read-modify-write entero adentro de una sola invocación, con la edición como
  argumentos semánticos. El modelo nunca compone el markdown del mapa. Tres primitivas,
  seis anclas que son los encabezados, idempotencia asimétrica (sacar dos veces
  converge, agregar dos veces diverge) y un reintento donde esa regla se invierte. De
  paso midió que el historial de versiones se coalesce, así que no es la red de
  seguridad que el 02 creyó.
- [07: Distribución e instalación](issues/07-distribucion-e-instalacion.md): el
  plugin entra al marketplace de `spec-driven-dev` en vez de tener uno propio, porque
  el peer dependency dejó de ser una convención y pasó a ser un campo real de
  `plugin.json`, y una dependencia cross-marketplace queda bloqueada por defecto. Se
  declara de verdad y sin constraint, porque los tags de SDD están fuera de la
  convención que Claude Code necesita. La credencial es Personal API key: Linear no
  tiene device flow, y medido, la key tiene más presupuesto de complejidad que OAuth,
  no menos. El setup por repo no existe, y el título del ticket lo decía: el 03 y el
  08 se lo vaciaron entero, así que queda un comando nuevo, `/planner-setup`, con la
  key como única responsabilidad. El repo sin Linear también se disuelve. Y midió dos
  cosas de la máquina de quien instala: el intérprete es el 3.9 que trae macOS, y en
  un Mac sin Command Line Tools el chequeo del prototipo del 01 pasaría para fallar
  después.
- [06: Qué hace exactamente `/map-collapse`](issues/06-que-hace-map-collapse.md):
  el colapso es HITL y es un evento único. Una sesión con dos pasadas, primero los
  cortes y después las issues adentro de cada uno, con el agente proponiendo y la
  persona aprobando; el tracer bullet no se deriva del mapa, se grillea. Escribe N+2
  veces, porque `issueBatchCreate` es atómico, y eso también decide la recuperación:
  la única falla posible es milestones sin issues, y ahí ofrece retomar. Los
  veredictos pasan de tres a cuatro para que un mapa colapsado no se mande a colapsar
  para siempre, el adapter pasa de ocho operaciones a diez, y los tokens de cinco a
  seis. Y midió lo que el mapa le hace al sprint review: los tickets de decisión van
  con `estimate: 0` y entran al ciclo igual, a propósito. De paso encontró que todo
  lo que el plugin cree por API cae en Triage.
- [05: Cómo se adaptan grilling, domain-modeling y prototype al vivir acá](issues/05-adaptar-las-tres-disciplinas.md):
  el glosario del dominio vive en un repo central del CRM y el plugin no lo crea;
  el multi-rol sale de grilling como ticket HITL en vez de entrar como feature;
  las tres son model-invoked con `/grill` como única puerta; y se escriben en
  inglés con el frontmatter de SDD para que la importación futura sea copiar un
  archivo.
- [02: Qué permite y limita la API de Documents de Linear](issues/02-api-documents-linear.md):
  el Document sirve como casa del mapa y no hay blocker. El tamaño es irrelevante
  y el presupuesto de rate limit por hora también, aunque el 01 encontró después un
  límite de complejidad por query que este ticket no vio. La API solo acepta el
  contenido entero y el `patch` del MCP es azúcar útil. El riesgo real resultó ser otro: no hay control de
  concurrencia, y eso graduó al ticket 09.
- [01: Cómo lee el agente el grafo de dependencias de Linear](issues/01-grafo-dependencias-linear.md):
  la pregunta estaba mal planteada. La API siempre expuso las relaciones, es el MCP
  el que no las lee. Se leen con GraphQL crudo en un round-trip, sin dependencias;
  el SDK gasta 15 requests donde eso gasta 1, y el CLI de terceros queda descartado
  porque su instalador no verifica el binario que baja. El predicado de frontera va
  en el cliente, no en `hasBlockedByRelations`, que contesta mal cuando el
  bloqueante ya está Done. Y apareció un límite que el 02 no vio: 10.000 de
  complejidad por query, que fija la página en 50 por 10.
- [03: Las operaciones de wayfinding, expresadas en Linear](issues/03-seis-operaciones-en-linear.md):
  son ocho y no seis. Faltaban sacar de alcance, que es la única destructiva, y leer
  y actualizar el mapa, que son las dos mitades de un mismo read-modify-write. Las
  ocho van por GraphQL crudo, sin fallbacks, con un preflight por sesión que no
  cachea nada. Corrige al 01: cerrado no es un test de `state.type`, porque el team
  CRM tiene `Blocked` tipado `canceled` y en uso; es el par de ids que el plugin
  escribe. Y los labels van planos y workspace-level, lo que disuelve la niebla
  sobre cómo llega el label `map` a un team.
- [08: Qué cambia de los dos modos de wayfinder al keironizarlos](issues/08-los-dos-modos-keironizados.md):
  ocho cosas cambian. Tres son adaptaciones forzadas, y la más pesada es que no hay
  rama descartable de research: con once repos obliga a elegir uno, así que los
  hallazgos van a un Document hermano del DD. Dos son endurecimientos, y los dos
  cierran fallas que el propio doc de wayfinder reporta: las Notas dejan de poder
  anular el "plan, don't do", y en un ticket de prototipo el agente nunca elige.
  Tres son nuestras: se saca el corte de "sin niebla no hace falta mapa", porque acá
  el DD lo tiene todo proyecto igual; el multi-rol sale como ticket HITL creado al
  resolver; y existe `/map-status`, que en wayfinder no existe. Las ocho operaciones
  quedaron repartidas, el adapter es un script y no el modelo componiendo GraphQL, y
  el árbol de archivos del plugin quedó fijado.

## Aún no especificado

La niebla: se ve venir, pero todavía no se puede formular con precisión.

- **Cuándo el plugin escribe como app y no como persona.** El 07 cerró Personal
  API key para la v1 y midió lo que cuesta OAuth: sin device flow pide un servidor
  de callback y refresh de 24 horas. Lo que no se puede formular todavía es el
  disparador. El día que el mapa lo mantenga una cuenta de bot, `actor: app` le saca
  a la persona la autoría del comentario de resolución, y no está claro qué se pone
  en su lugar. El 09 le encontró el primer beneficio concreto y medible:
  `Document.updatedBy` existe, y con Personal API key no distingue al plugin de la
  persona porque son el mismo usuario.
- **La migración inversa hacia SDD**: cómo importa SDD las disciplinas una vez
  que este plugin las tenga estables.
- **Cómo sabemos que el mapa planifica mejor que SDD.** Hoy no tenemos con qué
  compararlos, y probablemente haga falta haber corrido los dos sobre proyectos
  parecidos.
- **Un espejo del glosario en Linear, para PM y Diseño.** El repo central los
  deja afuera, y son justamente quienes más pelean con la ambigüedad de los
  términos. Se ve el problema, no la forma.
- **Cómo se le avisa a un rol que no entra a Linear.** El multi-rol produce
  tickets para PM y Diseño. El 08 le sacó la mitad invisible: `/map-status` los
  muestra en la frontera con su antigüedad, así que un mapa trabado por esto ya se
  ve. Lo que sigue difuso es cómo llega el aviso a esa persona.
- **De quién son los tickets de un mapa cuando el workspace tiene más de un
  team.** Hoy `keiron` tiene uno solo, CRM, así que el `teamId` es derivable y el
  problema no se ve. Cuando aparezca un segundo team deja de serlo, y un mapa que
  cruza dos no tiene dónde poner sus tickets sin que alguien elija. Salió al
  resolver el 03, que lo dejó anotado como supuesto explícito. El 06 lo agrandó sin
  poder formularlo mejor: ahora también las issues de ejecución del colapso
  necesitan un `teamId`, y un milestone que cruza dos teams es más común que un
  ticket de decisión que los cruce.

## Fuera de alcance

Ruled out del destino. No gradúa nunca. Si lo querés, es un mapa nuevo.

- **El intake del workshop.** Es un ritual de equipo antes que una herramienta,
  y merece su propio mapa con el product team en la sala.
- **El Tier B completo**: triage, to-questionnaire, handoff y research como
  skills propias del plugin.
- **Reemplazar SDD** en cualquier grado.
- **Publicar el plugin fuera de Keiron.**
- **Tracker local en markdown como capacidad del plugin.** Este mapa usa uno
  porque el plugin todavía no existe, no porque el plugin vaya a soportarlo.
