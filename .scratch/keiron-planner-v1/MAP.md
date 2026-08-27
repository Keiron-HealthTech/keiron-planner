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
  recién en `/sdd-apply`.
- El mapa asume un solo conductor, el dev leader. El claim se implementa igual
  porque cuesta una línea.
- La verificación son checks estructurales sobre el repo, al estilo de los
  `scripts/check-*.sh` de SDD. Nada de verificar comportamiento conversacional.

## Decisiones hasta ahora

<!-- una línea por ticket cerrado, con enlace al ticket que guarda el detalle -->

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

## Aún no especificado

La niebla: se ve venir, pero todavía no se puede formular con precisión.

- **La forma exacta de los checks estructurales.** Sabemos que van, no qué
  chequean. Depende de que exista la estructura del plugin.
- **Proyectos del CRM que ya arrancaron sin mapa.** Si se les puede poner uno
  encima a mitad de camino, y qué pasa con lo ya decidido.
- **La migración inversa hacia SDD**: cómo importa SDD las disciplinas una vez
  que este plugin las tenga estables.
- **Cómo sabemos que el mapa planifica mejor que SDD.** Hoy no tenemos con qué
  compararlos, y probablemente haga falta haber corrido los dos sobre proyectos
  parecidos.
- **Un espejo del glosario en Linear, para PM y Diseño.** El repo central los
  deja afuera, y son justamente quienes más pelean con la ambigüedad de los
  términos. Se ve el problema, no la forma.
- **Qué pasa con un ticket HITL de un rol que no entra a Linear.** El multi-rol
  ahora produce tickets para PM y Diseño; si esas personas no los miran, el mapa
  se traba sin que nadie lo note.
- **De quién son los tickets de un mapa cuando el workspace tiene más de un
  team.** Hoy `keiron` tiene uno solo, CRM, así que el `teamId` es derivable y el
  problema no se ve. Cuando aparezca un segundo team deja de serlo, y un mapa que
  cruza dos no tiene dónde poner sus tickets sin que alguien elija. Salió al
  resolver el 03, que lo dejó anotado como supuesto explícito.

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
