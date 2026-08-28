# El aterrizaje: una decisión que llega después del colapso

Resolución del ticket [12](../issues/12-decision-nueva-sobre-mapa-colapsado.md),
tipo `map:grilling`. Siete rondas de grilling con el dev leader, veinticinco
preguntas, sesión del 2026-08-28, más once mediciones contra el workspace `keiron`
real.

El [06](06-el-colapso.md) dejó el colapso como evento único y graduó este ticket
con una respuesta provisoria: para la v1, quien resuelva una decisión posterior al
colapso crea la issue de ejecución a mano. Este documento la reemplaza.

Igual que el 06 y el 08, **se reparte**: el procedimiento va a
`skills/map-work/SKILL.md`, el bloque nuevo del reporte a `commands/map-status.md`,
la operación renombrada y el label nuevo a `scripts/LINEAR-OPERATIONS.md`, y los
términos a `CONTEXT.md`. Es una fuente, no un archivo destino.

Va en español con los términos canónicos en inglés, por la razón de siempre: su
lector es el dev leader que va a mantener esto.

## Qué es el aterrizaje

`Landing`, el aterrizaje: el paso donde una decisión tomada después del colapso
consigue su trabajo de ejecución, o queda ligada al que ya existe.

No es un colapso incremental, no es un comando y no es un modo. Es un paso más de
`/map-work`, que corre después de resolver el ticket cuando el Project ya tiene
milestones.

El nombre importa por una razón práctica y no por estética. El verbo funciona en la
prosa que este plugin va a escribir cien veces: una decisión aterriza en un corte, y
el reporte nuevo de `/map-status` lista **decisiones sin aterrizar**. Esa frase sola
explica el reporte entero. Se descartó `Late collapse`: llamarle colapso a algo que
no es un colapso reabre en el vocabulario la discusión que el diseño ya cerró.

## El hueco que había

El paso 3 de `/map-work` mira milestones solo cuando hay cero tickets abiertos. Con
un ticket abierto trabaja normal, resuelve, mete la línea en el índice, y en el paso
9 emite el token del veredicto: frontera vacía más al menos un milestone da
`colapsado`, o sea `sdd-new`.

O sea que hoy el plugin toma una decisión que nadie previó, la escribe en el mapa, y
despide a la persona con "el mapa está colapsado, andá a construir". La decisión no
tiene ni una issue de ejecución detrás y nadie lo nota. Esa es toda la falla, y es
silenciosa.

## Por qué el aterrizaje vive en `/map-work` y no en `/map-collapse`

El 06 le puso al modo incremental tres costos: precondición propia, deduplicación
contra lo ya creado, y semántica de merge sobre milestones existentes. Los tres son
reales **cuando el disparador es "colapsá otra vez"**, porque entonces el comando
tiene que redescubrir qué hay escrito y qué falta.

El evento verdadero es más chico. Es una decisión, resuelta ahora, por una sesión que
ya la tiene tomada y con una persona del otro lado que acaba de aprobar una
resolución. Con esa unidad no hay nada que deduplicar: el comando sabe exactamente
cuál es el ticket.

Lo que queda de los tres costos es la precondición, y es una línea: el Project tiene
al menos un milestone.

Se descartó un quinto comando. Cuesta un archivo más en `commands/`, una skill más, un
séptimo token en el conjunto cerrado, y la deduplicación que el 06 no quiso pagar.

## El procedimiento

`/map-work` pasa de nueve pasos a diez. Los ocho primeros no cambian.

8. **`ticket:resolve`**, cinco escrituras en orden, el mapa último.
9. **El aterrizaje**, si el Project tiene al menos un milestone y la sesión es HITL.
10. **El reporte de cierre con su token**, y para.

El aterrizaje, adentro:

1. **La ronda.** El agente propone uno de los tres desenlaces y la persona aprueba o
   lo cambia. Nada se escribe todavía.
2. **`milestone:create`**, solo si el desenlace pide un corte que no existe.
3. **`work:write`**, una invocación.
4. **`map:read-write`**, solo si nació un corte, para agregar su línea a
   `## El colapso`.

### Va después de `ticket:resolve`, y eso es una decisión

La regla del 03 dice que el último write es el que hace visible la operación, y por
eso el mapa va último adentro de `ticket:resolve`. Con el aterrizaje después,
`/map-work` deja de escribir el mapa al final del comando.

Se acepta, porque la regla habla de cada operación y no del comando, y porque lo que
de verdad decide es el modo de falla. Una sesión que muere en el medio del aterrizaje
deja una decisión resuelta, el mapa al día y ninguna issue, que es **exactamente el
estado que el reporte nuevo de `/map-status` muestra**. Con el aterrizaje antes o
adentro de `ticket:resolve`, una muerte deja issues de ejecución que el mapa no
menciona, y ese estado no lo reporta nadie.

### Solo en sesiones HITL, y solo en los tipos que deciden

Aterrizan `map:grilling` y `map:prototype`. No aterrizan `map:research`, que es AFK,
ni `map:task`, ni nada que corra sin una persona.

`map:research` queda afuera porque dejar que el agente decida solo qué construir es el
mismo agujero que el 08 cerró cuando les sacó a las Notas el poder de otorgar
permisos. Juntar la tanda de research para pedir una aprobación al final tampoco:
research es AFK justamente para no tener que sentar a nadie.

`map:task` queda afuera por definición. El 08 dice de ese tipo que "se gana el lugar
desbloqueando una decisión, nunca entregando un pedazo del destino", así que un
aterrizaje sobre un task no tiene qué aterrizar.

Los dos tipos excluidos tampoco aparecen en el reporte de decisiones sin aterrizar. Si
no pueden aterrizar nunca, listarlos como pendientes es ruido que en dos meses hace
que nadie mire el reporte.

## Los tres desenlaces

Este es el punto que más cambió en la sesión.

1. **Issues nuevas.** Lo que uno espera: la decisión agrega trabajo y nacen issues de
   ejecución.
2. **Ligar a una issue de ejecución que ya existe.** Cero issues nuevas, una relación.
3. **Nada.** La decisión no toca nada de lo que se está construyendo.

El desenlace del medio no estaba previsto y es probablemente el más común. La decisión
posterior al colapso típica no agrega trabajo: refina cómo se construye algo que ya
tiene issue. Sin ese desenlace, todas esas decisiones caen en el reporte como
pendientes, el reporte se llena de entradas legítimas, y en dos meses nadie lo mira.
Esa es la muerte estándar de un reporte y cuesta una sola `issueRelationCreate`
evitarla.

El tercero se registra con un label, porque un reporte que nunca puede llegar a cero
muere igual. Ver "El noveno label".

## El corte donde aterriza

El agente propone un corte existente, o uno nuevo insertado donde corresponda. La
persona aprueba o lo redibuja, igual que en el colapso.

**Nunca un corte con `status: done`.** Medido: un milestone con su única issue en
`Done` da `status: done` y 100%; se le agrega una issue en `Backlog` y queda `next` y
50%. Una decisión tardía que cae en un corte que el equipo ya demeó lo des-termina, y
eso le rompe un instrumento al equipo para ahorrarse un milestone.

**Insertar en el medio es determinístico**, y esto corrige al 06. Ver "Lo que este
documento corrige". Se pasa un `sortOrder` estrictamente entre los de los dos vecinos,
leídos de la API.

**`status` se lee antes de escribir y nunca se relee para verificar.** Es
denormalizado, tiene lag, y el lag devuelve el estado anterior. Es la tercera vez que
aparece esta familia en el mapa, después del lag de `Project.scope` y de la respuesta
de `issueUpdate` que miente sobre `cycle`, las dos del 06.

### Cuando todos los cortes están terminados

Si todos los milestones están en `done` y llega una decisión que pide corte, nace el
corte igual, **y el comando lo dice en voz alta**: todos los cortes estaban
terminados, esto reabre el proyecto, y puede ser la señal de que el destino estaba mal
trazado.

Es el único lugar donde el principio de "no hay descolapso" se vuelve observable. "Un
mapa que se reabre mucho" no es medible; "todos los cortes terminados y una decisión
nueva pidiendo corte" sí. Negarse sería peor que inútil, porque la persona está ahí
con una decisión real en la mano.

## El ancla, y la dirección que casi rompe la frontera

El aterrizaje deja rastro con una relación nativa de Linear, `type: related`, entre el
ticket de decisión y la issue de ejecución. No con prosa: la `description` del
milestone dice qué decisiones produjeron un corte, que es lo contrario de qué decisión
no produjo ninguno.

**La dirección es `issueId` = el ticket de decisión, `relatedIssueId` = la issue de
ejecución.** Esto contradice la convención de `ticket:block`, donde la fuente va del
lado `issue`, y la contradice a propósito.

La relación es simétrica en la UI y direccional en la API. Medido: leída desde el lado
`issueId` aparece en `relations`; desde el otro, en `inverseRelations`. Y el predicado
de frontera del 03 depende de `inverseRelations`, porque los bloqueantes de X son
`X.inverseRelations` con `type == "blocks"`.

Con la dirección "natural", las relaciones del aterrizaje caen adentro de
`inverseRelations` y compiten por el tope de paginación con los bloqueos. **No hay
forma de separarlas**: `Issue.relations` e `Issue.inverseRelations` aceptan `before`,
`after`, `first`, `last`, `includeArchived` y `orderBy`, y ningún `filter`.

Y el tope no se compra. Complejidad de la query de frontera contra el techo de 10.000,
subiendo el tamaño de página en las dos conexiones:

| `first` | Complejidad | Del techo |
| --- | --- | --- |
| 10 | 3.972 | 39,7% |
| 15 | 5.722 | 57,2% |
| 20 | 7.472 | 74,7% |
| 25 | 9.222 | 92,2% |
| 50 | 17.971 | **HTTP 400, `Query too complex`** |

Cada cinco lugares más cuestan 1.750. El 39,7% de base reproduce los 3.847 que midió el
03, más los campos que este ticket agrega.

Lo que estaba en juego es lo que el 03 ya nombró: si la lista de bloqueantes se corta en
silencio, un ticket bloqueado aparece tomable, alguien lo toma, y el mapa avanza sobre
una decisión que dependía de otra sin tomar. Dar vuelta la dirección saca las relaciones
del aterrizaje de esa conexión y no cuesta nada, porque `related` es simétrico y la
analogía con `ticket:block` no compraba nada. `blocks` es direccional y por eso su
convención tiene contenido.

**La regla queda enunciable en una línea: `inverseRelations` es solo de bloqueos, y esa
es la conexión que decide si un ticket es tomable.**

## El reporte: decisiones sin aterrizar

`/map-status` pasa de seis bloques a siete. El séptimo lista las decisiones sin
aterrizar, por nombre y con su antigüedad desde `completedAt`.

Nombres y no cuenta. La niebla muestra la cuenta porque es prosa adentro del mapa y no
tiene a qué apuntar; esto son tickets con nombre y URL, igual que Frontera y Bloqueados.
La antigüedad es toda la señal: una decisión sin aterrizar de ayer es una sesión que se
cortó, y una de dos meses es un agujero. Sin la fecha se ven igual.

El predicado, entero:

> Un ticket de decisión está **sin aterrizar** si su label de tipo es `map:grilling` o
> `map:prototype`, está cerrado, su `completedAt` es posterior al `createdAt` del
> milestone más viejo del Project, no tiene ninguna relación `related` en `relations`,
> y no lleva el label `map:no-landing`.

Los tres datos que no estaban en la query salen gratis. `Issue.completedAt` y
`ProjectMilestone.createdAt` son escalares, `labels` ya venía, y `relations` ya venía.

**No es un veredicto nuevo y no es un token nuevo.** El estado sigue siendo `colapsado`
con un detalle, y un séptimo token tocaría el conjunto cerrado de seis que la afirmación
7 verifica por igualdad de conjuntos. Se descartó además que `/map-work` sobre un mapa
colapsado sin tickets abiertos ofrezca retomar los aterrizajes pendientes: eso lo pone a
escribir trabajo de ejecución sin ningún ticket en la mano, que es el colapso incremental
entrando por la ventana.

### El colapso no hace backfill

Las decisiones anteriores al colapso no tienen relación, porque `/map-collapse` no las
escribe. Por eso el predicado discrimina por fecha.

Se descartó que el colapso las escribiera. Medido: no hay atajo. `IssueCreateInput` tiene
36 campos y ninguno liga issues, `IssueBatchCreateInput` tiene uno solo, y las únicas
mutaciones batch son `issueBatchCreate` e `issueBatchUpdate`. Ligar M issues cuesta M
round-trips a 530 ms cada uno, o sea unos 16 segundos en un colapso de treinta issues,
más una tercera ventana de falla que hoy no existe. Compra una uniformidad que el
predicado no necesita, porque "después del colapso" es justo el discriminador que hace
falta, y rompe la propiedad de la que el 06 estaba orgulloso: que la única ventana sucia
posible es "milestones sí, issues no".

## La operación se renombra: `issue:create` pasa a `work:write`

El adapter sigue en **doce** subcomandos. Lo que cambia es el nombre y el trabajo de uno.

`work:write`, "escribir el trabajo", recibe una lista de issues que puede venir vacía,
una lista de relaciones, y opcionalmente el label del desenlace "nada". Escribe todo
adentro de una sola invocación, por la misma razón por la que `ticket:resolve` mete
cinco escrituras adentro de una: el orden lo garantiza el adapter y nunca el modelo.

```
work:write --ctx <blob>
  --issues '[{ teamId, projectId, projectMilestoneId, stateId, title, description }]'
  --relate '[{ decisionId, issueId }]'
  --no-landing <ticketId>
```

El renombre se decidió en dos tiempos, y vale contarlo. Cuando la operación era "crear
issues y ligarlas", el nombre quedaba corto y se aceptó el costo. Con el label del
desenlace "nada", la operación tiene tres desenlaces y en dos de ellos no crea ninguna
issue, así que el nombre pasó de corto a falso. Una operación llamada Crear una issue que
termina escribiendo un label y ninguna issue es la clase de nombre por el que alguien
implementa otra cosa. Y el momento de renombrar es este, cuando lo único que existe son
documentos de research.

Se descartó partirla en dos y llegar a trece operaciones: es una operación entera de
superficie por una sola mutación.

**Con la lista de issues vacía no se llama a `issueBatchCreate`.** No es prolijidad, es
obligación: medido, la API rechaza la lista vacía con `Argument Validation Error` y el
constraint `arrayNotEmpty`, "issues should not be empty".

Todo lo demás que el 06 fijó para esta operación sigue igual: `stateId` explícito, sin
`estimate`, sin `labelIds`, sin label `map`, y las issues nacen con su corte puesto.

## El noveno label: `map:no-landing`

Marca la decisión posterior al colapso que deliberadamente no produce trabajo. Lo escribe
el aterrizaje, en un round-trip que solo se paga en ese desenlace, y saca al ticket del
reporte.

Existe por el mismo argumento que el desenlace del medio: un reporte que nunca puede
llegar a cero es un reporte que la gente deja de mirar.

Hay que decir la parte incómoda. Los ocho labels de hoy describen la pregunta, cuatro el
tipo y tres el interlocutor más el `map` de pertenencia. Este describe la resolución, así
que es un label de otra clase.

**Lo sigue creando `ticket:create`**, junto con los demás que falten, aunque no lo use.
Lo que la invariante del 03 protegía es que la creación de labels viva en un solo lugar, y
eso se conserva entero; lo que se cae es su justificación, "porque es su único consumidor".
Se descartó que el preflight lo resuelva y falle duro si falta: el preflight falla duro en
cuatro casos justamente porque la lista es corta, y este es un label que la mayoría de las
sesiones no toca nunca.

## El aterrizaje a medias

Nace un corte nuevo y `work:write` falla. Queda un milestone vacío y la decisión sin
aterrizar.

Se acepta y se nombra, que es la misma forma que eligió el 06 para el colapso a medias.
El estado sucio es visible desde los dos lados: el corte vacío se ve en Linear, y la
decisión aparece en el reporte de decisiones sin aterrizar.

Se descartó que el aterrizaje borre el corte que creó. Sería una segunda operación
destructiva, por una ruta de error, y el mapa tiene una sola a propósito.

## Las afirmaciones chequeables, para el ticket 10

Siguen la numeración global. Las cincuenta acuñadas llegan a cincuenta y cinco.

51. `work:write` con la lista de issues vacía no llama a `issueBatchCreate`. AST: la
    llamada está adentro de una guarda sobre la lista.
52. Toda construcción de `issueRelationCreate` con `type: "related"` en `linear.py` pone
    el ticket de decisión del lado `issueId`. AST, dentro de la función de `work:write`.
53. El predicado de frontera evalúa bloqueos solo sobre `inverseRelations`, y ninguna
    rama lo evalúa sobre `relations`. AST.
54. La lista de labels que `ticket:create` crea cuando faltan tiene nueve elementos e
    incluye `map:no-landing`, y ninguna otra función de `linear.py` crea labels. AST.
55. `map-work.md` nombra la prohibición de aterrizar en un corte con `status: done`.
    **Brecha**: es un grep de prosa, así que reescribir la frase falla el check sin que la
    regla cambie. Es la misma brecha que la afirmación 25 y se acepta igual.

## Lo que este documento corrige

**Al 06, tres cosas.**

1. **El `sortOrder` de un milestone se respeta, salvo el cero.** El 06 dice "el
   `sortOrder` que devuelve no es el que se pidió... Linear lo recalcula para insertarlo
   al principio". Es falso como regla y la explicación está al revés. Medido: `0.0` es lo
   único que Linear recalcula, porque lo trata como campo ausente, y lo manda **al
   final**. Con dos milestones en 10 y 20, pedir `0.0` devolvió 1002 y no pasar el campo
   devolvió 1975. Pedir `15.0` devolvió 15 y quedó entre los dos. La regla del 03 sobre
   sacar las anclas de lo que devuelve la API sigue valiendo igual, pero por prolijidad y
   no porque el valor cambie.
2. **`issue:create` se llama `work:write`** y hace tres cosas en vez de una.
3. **`/map-work` usa dos operaciones que antes no usaba**, `milestone:create` y
   `work:write`, así que la tabla de reparto del 06 cambia en esa columna.

**A las afirmaciones 12 y 48 del ticket 10**, las dos por el renombre: la 12 dice
"`issue:create` no pasa `estimate`" y la 48 dice "ninguna ruta de `issue:create` agrega el
label `map`". Las dos siguen siendo verdad y las dos nombran una operación que ya no se
llama así.

**A `CONTEXT.md`**, cinco cosas: entra `Landing` en el glosario, `/map-work` gana el paso,
la tabla de operaciones renombra `issue:create` a `work:write` y le cambia la descripción,
la lista de las siete operaciones que consumen `--ctx` sigue siendo de siete con el nombre
nuevo, y la invariante de `ticket:create` sobre los labels pierde su justificación y
conserva la regla.

## Supuestos

- Todo lo que el 03, el 06 y el 08 supusieron sigue supuesto: un solo team en el
  workspace, un solo conductor por mapa, un mapa de hasta cincuenta tickets, y las
  escrituras atribuidas a quien generó la key.
- **Una decisión no produce más de nueve issues de ejecución.** Con más, sus relaciones
  desbordan el tope de `relations(first: 10)` y el aviso de truncado del 03 se dispara.
  No se le pone un tope duro porque no se vio el caso, pero el número existe y conviene
  saberlo.
- El aterrizaje hereda el problema del `teamId` que el 03 dejó anotado. Una issue de
  ejecución nacida tarde necesita team igual que una nacida en el colapso, y en un
  workspace con dos teams sigue sin haber quién lo elija.

## Lo que este documento no decide

- **Qué hace el plugin cuando una decisión posterior al colapso invalida trabajo ya
  escrito.** Va a Fuera de alcance y no gradúa. El colapso entrega el trabajo, y a partir
  de ahí el tracker es del equipo: cambiar una issue de ejecución que ya se empezó a mover
  es lo que el equipo hace en Linear todos los días. Es la decisión de la sesión con la que
  menos cómodo quedé, porque manda afuera algo que sí se ve venir.
- **Cómo se prueba que el adapter hace lo que dice.** Sigue en niebla, y este documento la
  agranda un poco: cinco afirmaciones nuevas, cuatro de ellas contra el AST.

## Cómo se verificó

Todo lo medido sale de [`12-scripts/reopen_probe.py`](12-scripts/reopen_probe.py), stdlib
pelado, sin dependencias, diez subcomandos:

| Subcomando | Qué prueba |
| --- | --- |
| `schema` | Qué mutaciones y campos existen para borrar, mover y reordenar |
| `order` | Que un milestone se inserta entre dos que ya existen |
| `sort0` | Que `0.0` es lo único que Linear recalcula, y que va al final |
| `orphan` | Que borrar un milestone deja sus issues vivas y sin corte |
| `move` | Que una issue se mueve de corte, y que el batch de una sola anda |
| `dedup` | El costo de leer milestones, descriptions y el corte de cada issue |
| `relate` | La relación `related` y su asimetría entre las dos conexiones |
| `fields` | Que no hay atajo para escribir relaciones |
| `donecut` | Que un corte terminado se reabre, y el lag de `status` |
| `relcost` | Cuánto cuesta ligar M issues a su ticket |

Corren contra el Project `ZZ SANDBOX keiron-planner 01` y el team CRM reales. Los que
escriben, borran lo que escribieron; el sandbox quedó verificado limpio, con sus cinco
issues de siempre y cero milestones. La introspection del schema corre sin autenticar.
