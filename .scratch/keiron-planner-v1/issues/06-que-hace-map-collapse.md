# 06: Qué hace exactamente `/map-collapse`

**Tipo:** `map:grilling` · **Modo:** HITL (`hitl:dev`)
**Estado:** **RESUELTO** el 2026-08-27.
**Tomado por:** Luis Felipe Jaña (`hitl:dev`), sesión del 2026-08-27.

## Pregunta

Ya está decidido que el colapso llega hasta issues de Linear con sus milestones.
Falta el cómo, y es el paso que se lleva el trabajo que hoy hace a mano el dev
leader.

Preguntas que cuelgan de esta:

- Cómo se derivan los milestones desde las decisiones del mapa. Un milestone es
  un corte demoable, pero el mapa está organizado por decisiones, no por cortes.
  La traducción entre las dos formas es el corazón del ticket.
- Quién decide dónde cae cada corte: el agente propone y el humano aprueba, o al
  revés.
- Qué pasa con los tickets de decisión cerrados cuando nacen las issues de
  ejecución. Si quedan, si se archivan, si se enlazan.
- Si el colapso es un solo paso o se puede colapsar por partes, cuando una rama
  del mapa está clara y otra sigue en niebla.
- Dónde termina y arranca SDD. El destino dice que el colapso produce algo que
  SDD puede construir, y esa costura nunca se probó.

## Hecho cuando

Está escrito el procedimiento del colapso, con el criterio de corte de
milestones explícito y el punto de traspaso a SDD nombrado.

---

## La decisión

El documento completo es [`research/06-el-colapso.md`](../research/06-el-colapso.md),
557 líneas. Se reparte igual que el 08: el procedimiento a
`skills/map-collapse/SKILL.md`, la plantilla de la issue de ejecución y el sexto
encabezado del DD a `skills/_shared/map-templates.md`, las dos operaciones nuevas
a `scripts/LINEAR-OPERATIONS.md`.

Cuatro rondas de grilling, veinticuatro preguntas, frontera del árbol vacía, más
cuatro mediciones contra el workspace real y un colapso de juguete corrido de punta
a punta contra el sandbox.

**El colapso es HITL y es un evento único.** El agente propone, la persona aprueba,
y recién ahí se escribe. Una sesión con dos pasadas: primero los cortes, y solo con
los cortes aprobados, las issues adentro de cada uno. Mezclarlas hace que redibujar
un corte tire a la basura las issues que ya se propusieron para él, y redibujar
cortes es exactamente lo que el comando pone a la persona a hacer.

**Los cinco cuelgues de la pregunta, contestados.** Los milestones no se derivan del
mapa mecánicamente: una decisión no es un corte demoable, y el grafo de bloqueo es de
prerequisitos de conocimiento, no de capas de producto. El primero es siempre el
tracer bullet y **se grillea**, porque es la única pieza del colapso que las
decisiones no contienen. Los tickets de decisión cerrados no se tocan, y toda la
trazabilidad va en la `description` del milestone, que nombra las decisiones que
produjeron ese corte. No hay colapso por partes: la precondición ya lo mataba. Y SDD
entra en `/sdd-new`.

**La secuencia de escritura es N+2**, con N milestones y M issues. `issueBatchCreate`
dice literal en su schema "Creates a list of issues atomically", así que las M issues
del colapso entero se crean en una sola llamada. Eso decide también la recuperación:
la única ventana de falla es "milestones creados, issues no", y el estado sucio de
"algunas sí y otras no" no existe. Por eso el rechazo de la segunda corrida se parte
en dos: con cero issues de ejecución ofrece retomar; con issues adentro se niega duro.

**Los veredictos pasan de tres a cuatro.** El cuarto es `colapsado` y no es un adorno:
sin él, `/map-status` y `/map-work` mandan a colapsar un mapa ya colapsado para
siempre, y `/map-collapse` los rebota por ser la segunda corrida. Se detecta agregando
`projectMilestones` a la query que los dos ya hacen.

**Medido contra el workspace real**, con
[`research/06-scripts/collapse_probe.py`](../research/06-scripts/collapse_probe.py):
el team CRM tiene `cycleIssueAutoAssignCompleted: true` y `defaultIssueEstimate: 1`,
así que un ticket de decisión sin estimar infla el scope del Project en un punto y
entra solo al ciclo activo al cerrarse. Ya estaba pasando sobre nuestro propio
sandbox sin que nadie lo notara. `estimate: 0` lo saca del scope y cuesta cero
escrituras nuevas. Al ciclo se lo deja entrar.

**Y las issues creadas por API caen en Triage**, no en el `defaultIssueState` del
team. Eso excede al colapso: corrige `ticket:create`, y no se había visto nunca
porque ninguna issue del sandbox se había creado por API.

## Por qué

Lo descartado que más costó.

**Que el colapso escribiera los artefactos de SDD**, para que SDD entrara en
`/sdd-apply` como decía el encuadre. Descartado por dos razones. Con once repos
activos, escribir `openspec/changes/` obliga a contestar en qué repo cae un milestone
que cruza cuatro, que es el mismo problema que mató al pointer file en el 03 y a la
rama de research en el 08. Y hace que este plugin escriba adentro del árbol de
artefactos del otro, que es el acoplamiento que la peer dependency existe para evitar.

**Sacar el ticket de decisión del ciclo activo**, para que no aparezca en el sprint
review. Descartado, aunque está medido y funciona. Este plugin existe para sacar la
planificación de Notion y meterla en el tracker, justamente para que deje de ser
invisible; esconderla de nuevo apenas llega es deshacer el trabajo. Con `estimate: 0`
la contaminación se reduce a unas filas etiquetadas que describen trabajo que de
verdad se hizo en ese sprint. Queda nombrada como salida de emergencia: cuesta pasar
`ticket:resolve` de cinco escrituras a siete round-trips, porque la mutación combinada
no sirve (devuelve `cycle: null` en su propia respuesta y el auto-assign le gana
después del commit).

**Un modo incremental del colapso.** Descartado para la v1: necesita precondición
propia, deduplicación contra lo ya creado y semántica de merge sobre milestones
existentes, o sea la mitad de la complejidad del comando, para un caso que todavía no
vimos ni una vez. Gradúa como ticket.

**Estirar `ticket:create` con un flag** en vez de dos operaciones nuevas. Descartado:
anula la invariante que el 03 escribió a propósito, "un issue cuyo cuerpo es la
pregunta y nada más", y rompe el check estructural que cuenta subcomandos contra
operaciones nombradas.

**Cablear bloqueos entre las issues de ejecución**, y **tocar el estado del Project**.
Los dos descartados por lo mismo: son decisiones del equipo y de PM, y un plugin que
las toma por ellos es la clase de sorpresa que hace que se desinstale.

## Niebla graduada

Ninguna. Este ticket no vació ningún parche de "Aún no especificado": el colapso era
el último tramo del camino que ya estaba trazado, no una zona en niebla.

## Tickets nuevos

- [12: Qué hace el plugin cuando aparece una decisión nueva sobre un mapa ya
  colapsado](12-decision-nueva-sobre-mapa-colapsado.md), sin bloqueantes. Sale de
  decidir que el colapso es un evento único. Para la v1 la respuesta es "a mano".

## Qué corrige o empuja

**A la decisión de encuadre del mapa**, ya bajada al mapa: "SDD entra recién en
`/sdd-apply`" pasa a `/sdd-new`. Las dos mitades no cerraban.

**Al reference del 03**, tres cosas, ya bajadas a
[`research/03-operaciones-en-linear.md`](../research/03-operaciones-en-linear.md):
`ticket:create` pasa `stateId` explícito, y la afirmación anterior era falsa y está
medida; pasa además `estimate: 0` y el label `Discovery`; y las operaciones son diez.
El preflight resuelve dos cosas más.

**Al 08**, dos cosas, ya bajadas a
[`research/08-los-tres-comandos.md`](../research/08-los-tres-comandos.md): los
veredictos son cuatro, y los encabezados del DD son seis. Tres de sus seis
afirmaciones chequeables quedaron desactualizadas y están corregidas ahí.

**A `CONTEXT.md`**, cuatro cosas: `Discovery` pasa a escribirse, las operaciones pasan
a diez, el conjunto de tokens pasa a seis, y se nombra dónde ocurre el traspaso a SDD.

**Al ticket 10**, que queda desbloqueado por el lado del 06: hereda siete afirmaciones
chequeables nuevas, numeradas de la 7 a la 13, y tres correcciones a las que ya tenía.

**Al ticket 09**, a favor otra vez: `/map-collapse` también escribe el mapa exactamente
una vez, así que el cuarto comando no le agrega superficie que proteger.
