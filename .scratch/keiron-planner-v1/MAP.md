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

<!-- Una línea por ticket cerrado: enlace al ticket, y el gist en 120
     caracteres o menos. El detalle vive en el comentario de resolución del
     ticket y el mapa nunca lo repite. Lo decidió el ticket 04, mirando. -->

- [11: Qué hace `/map-new` sobre un Project que ya arrancó](issues/11-map-new-sobre-project-vivo.md): El mapa se muda al overview del Project. Nunca reescribe prosa ajena, nunca se niega, y el destino lo nombra la persona.
- [10: Qué chequean los checks estructurales](issues/10-que-chequean-los-checks.md): Seis scripts y un job; 44 afirmaciones vivas de 50, y el adapter se chequea con un AST y no con grep.
- [04: Un mapa de juguete en Linear, para ver si el Document aguanta](issues/04-prototipo-mapa-en-linear.md): Aguanta. El índice es una línea por decisión, con el detalle solo en el ticket y tope de 120 caracteres.
- [14: Si el preflight corre por invocación o por sesión](issues/14-preflight-por-invocacion.md): Una vez por conductor, con la salida como blob opaco que todo consumidor recibe en `--ctx`.
- [13: Si una pestaña abierta puede pisar una escritura del plugin](issues/13-pestana-abierta-pisa-al-plugin.md): No puede: la escritura mueve el estado Yjs, así que no deja rama que un cliente pueda ganar.
- [09: Cómo evita el plugin pisar una edición humana del mapa](issues/09-concurrencia-humano-plugin.md): No detecta el conflicto, lo evita: relee justo antes de escribir y la ventana baja a 332 ms.
- [07: Distribución e instalación](issues/07-distribucion-e-instalacion.md): Entra al marketplace de `spec-driven-dev` y declara la dependencia de verdad, sin constraint.
- [06: Qué hace exactamente `/map-collapse`](issues/06-que-hace-map-collapse.md): Es HITL y es un evento único: dos pasadas, cortes y después issues, y escribe N+2 veces.
- [05: Cómo se adaptan grilling, domain-modeling y prototype al vivir acá](issues/05-adaptar-las-tres-disciplinas.md): Model-invoked con `/grill` como única puerta, en inglés y con el frontmatter de SDD.
- [02: Qué permite y limita la API de Documents de Linear](issues/02-api-documents-linear.md): No hay blocker: el tamaño y el rate limit son irrelevantes. (El mapa ya no vive en un Document. Lo mudó el 11.)
- [01: Cómo lee el agente el grafo de dependencias de Linear](issues/01-grafo-dependencias-linear.md): Con GraphQL crudo en un round-trip; el SDK gasta 15 requests donde eso gasta 1.
- [03: Las operaciones de wayfinding, expresadas en Linear](issues/03-seis-operaciones-en-linear.md): Son ocho y no seis, todas por GraphQL crudo y sin fallbacks.
- [08: Qué cambia de los dos modos de wayfinder al keironizarlos](issues/08-los-dos-modos-keironizados.md): Ocho cosas: tres adaptaciones forzadas, dos endurecimientos y tres nuestras.

## Aún no especificado

La niebla: se ve venir, pero todavía no se puede formular con precisión.

- **Cuándo el plugin escribe como app y no como persona.** El 07 cerró Personal
  API key para la v1 y midió lo que cuesta OAuth: sin device flow pide un servidor
  de callback y refresh de 24 horas. Lo que no se puede formular todavía es el
  disparador. El día que el mapa lo mantenga una cuenta de bot, `actor: app` le saca
  a la persona la autoría del comentario de resolución, y no está claro qué se pone
  en su lugar. El 09 le había encontrado un
  beneficio concreto y medible, que `Document.updatedBy` existe y con Personal API key
  no distingue al plugin de la persona. El 11 se lo sacó al mudar el mapa al overview:
  **`Project` no tiene `updatedBy`**, así que ya no hay campo que distinguir y la
  niebla vuelve a ser solo la pregunta por el disparador.
- **Cómo se prueba que el adapter hace lo que dice, y no solo que está escrito
  como dice.** La decisión de encuadre ruled out verificar comportamiento
  conversacional, y el del adapter nunca se conversó. El 10 lo volvió contable: seis
  de sus cuarenta y cuatro afirmaciones tienen una brecha que solo cierra un test de
  verdad, y la más cara es la 18, porque su modo de falla es una credencial en un log.
- **La migración inversa hacia SDD**: cómo importa SDD las disciplinas una vez
  que este plugin las tenga estables.
- **Cómo sabemos que el mapa planifica mejor que SDD.** Hoy no tenemos con qué
  compararlos, y probablemente haga falta haber corrido los dos sobre proyectos
  parecidos.
- **Un espejo del glosario en Linear, para PM y Diseño.** El repo central los
  deja afuera, y son justamente quienes más pelean con la ambigüedad de los
  términos. Se ve el problema, no la forma. El 11 le sacó la mitad que era de
  visibilidad: con el mapa en la portada del Project, PM y Diseño lo ven sin que
  nadie les avise. Lo que queda es el glosario, que no es el mapa.
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
