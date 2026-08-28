---
lang: es
---

# El colapso del mapa v1

Bitácora de la sesión del 2026-08-28, la que aplicó `/map-collapse` sobre el mapa
que diseñó el plugin que lo implementa. El plugin todavía no existe, así que las
operaciones las emitió [`collapse.py`](collapse.py), que hace a mano lo que van a
hacer `map:create`, `map:write`, `milestone:create` y `work:write`.

**Resultado**: el Project
[Plugin keiron-planner](https://linear.app/keiron/project/plugin-keiron-planner-29ba6f33194f),
con el mapa en su overview, cinco cortes demoables y veintiuna issues de ejecución.

## La precondición

Cero tickets de decisión abiertos y cero milestones, que es el veredicto **listo
para colapsar** del 08 afinado por el 06. Los catorce tickets de `issues/` estaban
`RESUELTO` y la frontera estaba vacía. Verificado archivo por archivo antes de la
primera pregunta.

## Lo que se hizo, en orden

Los nueve pasos del [06](../research/06-el-colapso.md), con una diferencia obligada:
el mapa v1 nunca vivió en Linear, porque se trazó con un tracker local en markdown
mientras el plugin no existía. Así que antes del colapso hubo que hacer a mano lo que
`/map-new` hace: crear el Project y escribir el mapa en su overview.

1. **El Project.** `Plugin keiron-planner`, team CRM, status `Backlog`, lead el dev
   leader. Se eligió el nombre por simetría con `Plugin spec-driven-dev`, que es el
   hermano y ya vivía en Linear con cinco milestones.
2. **El mapa en el overview**, con los seis encabezados del contrato y el índice de
   catorce decisiones enlazando a los blobs de GitHub del repo, que es internal y
   está publicado. Los tickets de decisión **no se recrearon** en Linear: son
   catorce tickets que nunca pasaron por el plugin, y recrearlos habría metido
   catorce issues cerradas en el ciclo activo por `cycleIssueAutoAssignCompleted`,
   que es justo la contaminación del sprint review que el 06 se ocupó de acotar.
3. **Primera pasada, los cortes.** Cinco preguntas, las cinco confirmadas tal como
   venían recomendadas.
4. **Segunda pasada, las issues.** Cuatro preguntas más, las cuatro confirmadas.
5. **`milestone:create`**, cinco veces, una por corte, sin `targetDate` ninguna.
6. **Las veintiuna issues en una sola llamada atómica**, `issueBatchCreate`.
7. **El mapa, último write**, llenando `## El colapso`.

Escrituras totales: N+2 con N=5, más las dos de crear el Project y escribirle el
mapa, que son de `/map-new` y no del colapso.

## El tracer bullet, que se grilleó

Es la única pieza del colapso que las decisiones no contienen, y por eso el 06 pide
grillearla. Quedó **`/map-status` de punta a punta**: manifiesto, instalador, key,
preflight, `frontier:query`, `map:read`, contrato y reporte.

Cruza todas las capas que existen, del marketplace a la API de Linear y de vuelta, y
es **read-only**, así que se demuestra contra un Project vivo del CRM sin escribir un
byte. Se descartó `/map-new` como tracer bullet porque agrega cinco operaciones de
escritura antes de haber probado que el pipe cierra, y el adapter solo porque no es
vertical: nadie puede correrlo como usuario.

## Los cinco cortes

| Orden | Corte | Issues |
| --- | --- | --- |
| 10 | El plugin se instala y lee un Project | 5 |
| 20 | El mapa se traza sobre un Project | 5 |
| 30 | Una decisión se resuelve en el mapa | 3 |
| 40 | El mapa colapsa y las decisiones tardías aterrizan | 4 |
| 50 | El equipo instala el plugin desde el marketplace | 4 |

La `description` de cada uno nombra las decisiones que lo produjeron, con enlace. Esa
es toda la trazabilidad del colapso, y va ahí y no en cada issue.

El corte 5 termina con la PR al marketplace del hermano, que el 07 pidió que fuera la
última tarea del último milestone y no una tarea de infraestructura del primero.

## Lo que se midió, y no estaba medido

**1. Hay dos project statuses tipados `backlog`, y el tipo no alcanza para elegir.**
`Backlog` en posición 0 y `To Do` en posición 1000, los dos con `type: backlog`.
Tomar el primero que devuelve la API da `To Do`. Es la misma familia de trampa que el
03 encontró con `Blocked` tipado `canceled`: el tipo de un estado de Linear no dice
lo que uno cree que dice, y la regla del 03, elegir por id resuelto y nunca por tipo,
se transfiere entera a los estados de Project.

**2. El `sortOrder` explícito se respeta literal.** Se pidieron 10, 20, 30, 40 y 50 y
volvieron 10, 20, 30, 40 y 50. Confirma la corrección que el 12 le hizo al 06: Linear
solo recalcula el `0.0`, porque lo trata como campo ausente.

**3. `ProjectMilestone` no expone `url`.** Ni en el schema de la API, verificado por
introspección, ni en lo que devuelve el MCP de Linear. **Corrige al 06**, que dice que
`## El colapso` se llena "con los milestones creados por nombre y enlace": el enlace no
existe. Los cortes van por nombre y se abren desde el overview del Project. Cuando el
plugin exista, `map:write` no puede prometer un enlace que la API no da, y fabricar el
patrón de URL de la UI sería inventar un enlace que Linear no garantiza.

**4. Las veintiuna issues cayeron en `Backlog` y no en Triage**, con `stateId`
explícito. Confirma la medición del 06 desde el lado bueno.

**5. `issueBatchCreate` con veintiuna issues anduvo en una sola llamada.** El 06 dejó
como supuesto que treinta anda y que trescientas no se probaron. Veintiuna ahora está
medido.

**6. El scope del Project quedó en 21 y el progress en 0.** Es exactamente lo que el 06
predijo y aceptó en voz alta: con `defaultIssueEstimate: 1` y sin `estimate`, un colapso
de veintiuna issues deja el scope en veintiuno hasta que el equipo estime. Está mal, se
ve, y se corrige solo en la primera refinement. Un número inventado no se ve.

**7. El mapa de 124 líneas volvió con 123.** Es la línea final vacía que el editor
limpia, consistente con las transformaciones que midieron el 04 y el 11. Los seis
encabezados sobrevivieron con texto exacto, que es lo que el plugin usa como ancla.

## Lo que este colapso corrige

**Al Destino del mapa.** Decía "colapsadas en spec y tasks de SDD". El 06 ya había
corregido esa idea en las decisiones de encuadre, pero la sección Destino quedó sin
tocar, y era la única parte del mapa que seguía prometiendo artefactos de SDD que el
colapso no escribe. Ahora dice milestones e issues de Linear listas para `/sdd-new`.

**Al 06**, una cosa: el enlace al milestone en `## El colapso` no se puede cumplir,
por el hallazgo 3.

## Lo que queda

El token es **`sdd-new`**, que es la costura con el plugin hermano. Lo que sigue es
`/sdd-new` sobre
[CRM-3391](https://linear.app/keiron/issue/CRM-3391), la primera issue del primer
corte: crear el esqueleto del plugin, su manifiesto y el andamio de checks.

La niebla del mapa **no se toca**: un colapso no gradúa niebla. Los seis parches de
`Aún no especificado` siguen ahí, y el que más cerca está de volverse formulable
sigue siendo cómo se prueba que el adapter hace lo que dice.

Y a partir de acá, toda decisión nueva sobre este mapa entra por el **aterrizaje** del
ticket 12, que es un paso de `/map-work` y no un segundo colapso. Hasta que el plugin
exista, a mano.

## Cómo se verificó

[`collapse.py`](collapse.py), stdlib pelado, siete subcomandos: `ids`, `project`,
`map`, `milestones`, `issues`, `colapso` y `verify`. Los datos de los cortes y de las
veintiuna issues viven aparte, en [`plan.py`](plan.py), y el cuerpo del mapa en
[`map-linear.md`](map-linear.md). El último subcomando relee todo desde Linear y es
el que produjo la tabla de cortes de arriba.
