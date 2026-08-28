# 12: Qué hace el plugin cuando aparece una decisión nueva sobre un mapa ya colapsado

**Tipo:** `map:grilling` · **Modo:** HITL (`hitl:dev`)
**Estado:** **RESUELTO** el 2026-08-28.
**Tomado por:** Luis Felipe Jaña (`hitl:dev`), sesión del 2026-08-28.
**Origen:** graduado desde la niebla al resolver el [06](06-que-hace-map-collapse.md).

## Pregunta

El colapso es un evento único. Corre con la frontera vacía, escribe milestones e
issues de ejecución, y una segunda corrida se niega.

Pero durante la construcción aparece una pregunta que el mapa no vio. Alguien
crea el ticket de decisión, `/map-work` lo resuelve, y la decisión entra al índice
del mapa. No hay colapso que la lleve a ejecución.

Para la v1 esto ya tiene respuesta, y es "a mano": quien resuelve ese ticket crea
la issue de ejecución él mismo. La pregunta es qué hacemos cuando pase seguido.

Preguntas que cuelgan de esta:

- Si `/map-collapse` gana un modo incremental, o si es otro comando.
- Cómo se deduplica contra los milestones y las issues que ya existen, que es la
  mitad del costo de un modo incremental.
- En qué milestone cae una decisión posterior al colapso. Puede que en ninguno de
  los que existen, y entonces el colapso incremental también corta.
- Si el mapa se puede "descolapsar", o si un mapa colapsado que se reabre mucho es
  la señal de que el destino estaba mal trazado y lo que hace falta es un mapa
  nuevo.

## Hecho cuando

Está decidido si existe el colapso incremental, y si existe, cuál es su
precondición y cómo deduplica.

---

## La decisión

El documento completo es [`research/12-el-aterrizaje.md`](../research/12-el-aterrizaje.md),
401 líneas. Se reparte igual que el 06: el procedimiento a `skills/map-work/SKILL.md`,
el bloque nuevo del reporte a `commands/map-status.md`, la operación renombrada y el
label nuevo a `scripts/LINEAR-OPERATIONS.md`.

Siete rondas de grilling, veinticinco preguntas, frontera del árbol vacía, más once
mediciones contra el workspace real.

**No hay colapso incremental, no hay comando nuevo, y no hay descolapso.** Lo que hay
es un paso más de `/map-work`, el **aterrizaje** (`Landing`): cuando el Project ya
tiene milestones y la sesión es HITL, después de resolver el ticket el agente propone
qué hacer con esa decisión y la persona aprueba.

**Los tres costos que el 06 le puso al modo incremental existen cuando el disparador
es "colapsá otra vez".** Con el disparador en la cola de `/map-work` la sesión ya
tiene el ticket tomado y a la persona del otro lado, así que no hay nada que
deduplicar. De los tres queda la precondición, y es una línea: al menos un milestone.

**Los desenlaces son tres y no dos**, y ese fue el punto que más cambió: issues
nuevas, ligar a una issue de ejecución que ya existe, o nada. El del medio no estaba
previsto y es el más común, porque la decisión posterior al colapso típica refina cómo
se construye algo que ya tiene issue. Sin él, el reporte se llena de entradas
legítimas y en dos meses nadie lo mira.

**El rastro es una relación nativa `related`, con la dirección dada vuelta a
propósito.** Va `issueId` = el ticket de decisión. Medido: con la dirección "natural"
las relaciones caen en `inverseRelations`, que es de donde el predicado de frontera
saca los bloqueantes, no hay `filter` para separarlas, y subir la paginación es
impagable: `first: 25` en las dos conexiones cuesta 92,2% del techo y `first: 50`
devuelve HTTP 400. La regla queda en una línea: `inverseRelations` es solo de bloqueos.

**`/map-status` pasa de seis bloques a siete.** El séptimo lista las decisiones sin
aterrizar, por nombre y con antigüedad. No es un veredicto nuevo ni un token nuevo: los
tokens siguen siendo seis.

**El adapter sigue en doce subcomandos, pero uno se renombra.** `issue:create` pasa a
`work:write`, porque en dos de los tres desenlaces no crea ninguna issue. Y aparece el
noveno label, `map:no-landing`, para el desenlace deliberado de no hacer nada.

**Medido y anotado**: `sortOrder` se respeta salvo el cero, así que insertar un corte
entre dos que existen es determinístico; un corte `done` se reabre si le metés una
issue, así que aterrizar ahí queda prohibido; `status` y `progress` tienen lag y
devuelven el estado anterior, tercera vez que aparece esta familia; y borrar un
milestone deja sus issues vivas y sin corte, que es por lo que no hay descolapso.

## Por qué

Lo descartado que más costó.

**Un quinto comando, o un modo incremental de `/map-collapse`.** El comando cuesta un
archivo más en `commands/`, una skill más y un séptimo token; el modo cuesta la
deduplicación que el 06 no quiso pagar. Los dos resuelven un evento más grande que el
que de verdad ocurre.

**Que el colapso original escribiera las relaciones**, para que el ancla fuera
uniforme. Medido: no hay atajo, ni campo en `IssueCreateInput` ni mutación batch, así
que son M round-trips a 530 ms. Unos 16 segundos en un colapso de treinta issues, más
una tercera ventana de falla, para comprar una uniformidad que el predicado no
necesita: "después del colapso" ya es el discriminador, y sale gratis de `completedAt`
contra el `createdAt` del milestone más viejo.

**Que el aterrizaje corriera en sesiones AFK.** Dejar que el agente decida solo qué
construir es el mismo agujero que el 08 cerró cuando les sacó a las Notas el poder de
otorgar permisos.

**Que el aterrizaje borrara el corte que creó** cuando la escritura falla. Sería una
segunda operación destructiva por una ruta de error, y el mapa tiene una sola a
propósito. Se nombra la ventana y no se automatiza la recuperación, igual que el 06 con
el colapso a medias.

**Subir la paginación de las relaciones** en vez de dar vuelta la dirección. Está
medido arriba y no alcanza el techo.

## Lo que se cayó

**La premisa del propio ticket, que el caso era uno solo.** El ticket dice "aparece una
pregunta que el mapa no vio" y trata eso como un caso único. Son tres eventos
distintos: la decisión que agrega trabajo, la que invalida trabajo ya escrito, y el
ticket que se saca de alcance. Solo el primero es de este plugin.

**La explicación que el 06 dio del `sortOrder`.** Decía que Linear recalcula lo que se
pide y lo mete al principio. Medido: recalcula solo el `0.0`, porque lo trata como campo
ausente, y lo manda al final. Con dos milestones en 10 y 20, pedir `0.0` devolvió 1002.

**La convención de dirección de `ticket:block` aplicada a `related`.** Se cerró en la
ronda 1 y se cayó en la ronda 3 contra una medición. `blocks` es direccional y por eso su
convención tiene contenido; `related` es simétrico, así que la analogía no compraba nada
y sí ponía en riesgo el predicado de frontera.

**La justificación de la invariante de `ticket:create` sobre los labels**, que era
"porque es su único consumidor". Con el noveno label deja de ser cierta. La regla se
conserva, la razón se reescribe: es el único que crea labels, y eso es lo que importaba.

**Que el nombre `issue:create` alcanzaba.** Se aceptó en la ronda 4 sabiendo que quedaba
corto, y en la ronda 6 pasó a ser falso.

## Niebla graduada

Ninguna. Este ticket no vació ningún parche de "Aún no especificado", y agranda un poco
el de cómo se prueba el adapter: cinco afirmaciones nuevas, cuatro contra el AST.

## Tickets nuevos

Ninguno.

## Qué corrige o empuja

**Al mapa**, una línea nueva en Fuera de alcance: qué hace el plugin cuando una decisión
posterior al colapso invalida trabajo ya escrito. No gradúa. El colapso entrega el
trabajo y a partir de ahí el tracker es del equipo.

**Al 06**, tres cosas, ya bajadas a
[`research/06-el-colapso.md`](../research/06-el-colapso.md): la explicación del
`sortOrder`, el renombre de `issue:create` a `work:write`, y que `/map-work` ahora usa
`milestone:create` y `work:write`, que cambia su columna en la tabla de reparto.

**Al ticket 10**, cinco afirmaciones nuevas, de la 51 a la 55, y dos correcciones de
nombre: la 12 y la 48 nombran `issue:create`.

**A `CONTEXT.md`**, cinco cosas: entra `Landing` en el glosario, `/map-work` gana el paso,
la tabla de operaciones renombra `issue:create` y le cambia la descripción, la lista de
las siete que consumen `--ctx` usa el nombre nuevo, y la invariante de los labels de
`ticket:create` pierde su justificación y conserva la regla.

**Al 08, a favor**: el reporte de `/map-status` pasa de seis bloques a siete, y el
conjunto cerrado de seis tokens no se toca.
