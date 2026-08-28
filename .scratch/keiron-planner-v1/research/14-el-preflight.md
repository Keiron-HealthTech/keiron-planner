# 14: El preflight, y cuántas veces corre

Resolución del ticket 14. Fecha: 2026-08-27.

> **Enmienda del 11.** Donde este documento diga que el mapa es un Document colgado
> del Project, léase el **overview del Project**, `Project.content`: el 11 lo mudó, y
> `map:create` ya no crea Document. El mapa no tiene título propio, así que el
> `DD: <proyecto>` desaparece. Detalle y mediciones en
> [`11-el-project-vivo.md`](11-el-project-vivo.md).

Este documento **se reparte**, como el del 09: el contrato del preflight y de
`--ctx` va a `LINEAR-OPERATIONS.md` al lado del adapter, y la regla del conductor
a `skills/_shared/map-contract.md`. Es una fuente, no un archivo destino.

Va en español con los términos canónicos en inglés. Su lector es el dev leader
que mantiene el adapter.

---

## El resumen, en un párrafo

El 08 escribió *un preflight por proceso que emite operaciones*, y razonó entero
sobre contexto de modelo. El 09 mostró que contra el adapter real la palabra
"proceso" significa invocación de Bash, así que leída literal la regla cobra un
preflight por operación. **La palabra era el error, no la regla**: se lee
**conductor**, un contexto de modelo que emite operaciones, y un subagente es un
conductor. Para que eso sea mecánico y no una costumbre, el `preflight` pasa a ser
un subcomando de verdad, imprime un blob opaco de 712 bytes por stdout, y todo
consumidor lo recibe como `--ctx`. Un consumidor sin `--ctx` **falla**: ninguno
sabe hacer un preflight, así que pagar dos es imposible por construcción. De paso
se cayó la premisa del ticket: "falla ocho veces" es falso, porque con el
preflight adentro de cada subcomando la primera invocación es la que falla, y esa
es exactamente la falla temprana que se quería. Lo que quedó en pie fue otra cosa,
y peor: **el preflight escribe**, crea los labels que faltan, y `/map-status`
promete dejar Linear byte a byte como estaba. La creación se muda a
`ticket:create`, su único consumidor real. Un `/map-work` típico queda en **cinco
invocaciones y un preflight**.

---

## 1. Lo que costaba de verdad

El 09 dejó anotado el costo en complejidad: 423 por preflight, contra "el techo de
10.000". Eso mezclaba dos techos distintos y había que medirlo de nuevo.

Medido contra `keiron` con la Personal API key, `research/14-scripts/preflight_probe.py`:

| Qué | Medido |
| --- | --- |
| Complejidad del preflight | **424** |
| Techo de complejidad **por query** | 10.000 |
| Techo de complejidad **por hora** | **3.000.000** |
| Techo de requests **por hora** | **2.500** |
| Round trip del preflight | 228 a 340 ms |
| Arranque del intérprete 3.9 de macOS, sin red | 122 ms de mediana |
| Ocho preflights como ocho procesos | **3.197 ms** |

El presupuesto horario no es el problema y no estuvo cerca de serlo: ocho
preflights son 3.392 de 3.000.000, el 0,11%, y ocho requests de 2.500. El 02 tenía
razón en que era holgado, y el número real es más holgado todavía de lo que decía.

**Lo que cuesta es tiempo, y son 3,2 segundos por `/map-work`.** Cada invocación
son ~120 ms de arrancar Python más ~280 ms de red. El intérprete de Command Line
Tools arranca en 87 ms contra los 122 del `/usr/bin/python3` que el 07 fijó como el
que va a haber en la máquina de cada dev, y la diferencia no mueve la aguja: 3.147
ms contra 3.197 ms.

### La premisa del ticket se cayó

El ticket 14 dice que un preflight por invocación rompe la promesa de fallar
temprano *porque falla ocho veces*. **No es cierto.** Si el preflight vive adentro
de cada subcomando, la primera invocación es la que falla, y esa es la falla
temprana que se quería. Solo fallaría ocho veces si el modelo siguiera adelante
después de un error, que es un problema distinto y peor.

Con la queja principal caída, el argumento quedó en 3,2 segundos, que sobre una
sesión de grilling con una persona del otro lado no es un argumento. Lo que
decidió el ticket fue lo que apareció midiendo, en la sección 4.

---

## 2. Proceso contra conductor

El 08 escribió la regla así: *"Un subagente es una sesión a este efecto: tiene
contexto propio y no puede heredar los ids del padre sin que alguien se los pase.
La regla se lee un preflight por proceso que emite operaciones, no uno por sesión
de usuario."*

Todo el razonamiento es sobre contexto de modelo. "Proceso" era la palabra que
tenía a mano para decir "algo más chico que una sesión de usuario", y no describe
ningún proceso del sistema operativo. El 09 partió el adapter en subcomandos
invocados por Bash y volvió la palabra literal, que es cuando el error se ve.

**La regla se lee conductor**: un contexto de modelo que emite operaciones. La
sesión es un conductor. Cada subagente de research es un conductor. Un subcomando
no lo es.

Se consideraron y se descartaron dos lecturas más:

**Proceso literal**, o sea cada subcomando resolviendo lo suyo adentro. Nadie pasa
nada, cada invocación se basta sola, y un subcomando se puede correr a mano desde
una terminal sin ceremonia. Cuesta los 3,2 segundos, que no alcanzan para
descartarla. Lo que la descarta es la sección 4: con el preflight adentro de cada
subcomando, el preflight es invisible, y era una operación que escribía.

**Nadie**, o sea disolver el preflight y que cada subcomando resuelva en línea
exactamente lo que necesita, fusionado en la query que ya iba a mandar. Es la más
barata de las tres y la que mejor aprovecha la medición de la sección 8. Se
descarta porque disuelve el único lugar donde el plugin puede decir "tu team no es
CRM" antes de tocar nada.

### Solo siete de las doce operaciones lo necesitan

| Operación | Usa el ctx | Qué necesita |
| --- | --- | --- |
| `map:create` | sí | `team.id`, para `ProjectCreateInput.teamIds` |
| `map:read` | no | el id del Document sale del Project |
| `map:write` | no | idem, y la edición es semántica |
| `ticket:create` | sí | `team.id` + los ocho `labelIds` + `stateId` explícito |
| `ticket:block` | no | `issueId` y `relatedIssueId` aceptan `CRM-123` |
| `frontier:query` | sí | los **dos** ids cerrados |
| `ticket:claim` | sí | `viewer.id` |
| `ticket:resolve` | sí | el `completed` de menor `position`, más lo de `ticket:create` |
| `ticket:rule-out` | sí | el `canceled` de menor `position` |
| `milestone:create` | no | `projectId` y nombre, nada resuelto |
| `issue:create` | sí | `team.id` + `stateId` explícito |

**Corrige una suposición** que este mismo documento tenía a mitad de camino:
`frontier:query` **sí** necesita el preflight. El predicado de frontera del 03 no
testea `state.type`, compara contra el par de ids cerrados, y esa comparación
ocurre en el cliente. Sin los dos ids no hay predicado.

---

## 3. Lo que carga los ids

El 03 escribió *no guarda nada: la fuente de verdad es Linear, no un archivo de
config*, porque un caché *"compra milisegundos y paga con un modo de fallo que solo
aparece cuando alguien tocó el workflow del team"*. El 08 estiró esa regla para
negarse también a pasar ids de padre a subagente, llamándolo "acoplamiento a cambio
de nada".

Son dos cosas distintas y la regla cubre una sola. **Lo prohibido es persistir
entre corridas.** Un archivo que sobrevive a la sesión envejece, y el modo de fallo
que el 03 temía necesita justamente eso. Pasar ids resueltos hace tres segundos
entre dos invocaciones de la misma corrida no envejece: nace y muere adentro de la
misma sesión.

Queda escrito acá porque el 08 ya leyó la regla de la manera ancha una vez.

### El ctx es un blob opaco

El subcomando `preflight` imprime un JSON compacto y todo consumidor lo recibe
como `--ctx <blob>`, entero, ignorando lo que no usa.

| Forma | Bytes | Tokens aprox. | Por las siete invocaciones que lo consumen |
| --- | --- | --- | --- |
| JSON compacto | 712 | ~178 | ~1.250 |
| Base64 | 952 | ~238 | ~1.666 |

`ARG_MAX` es 1 MB, así que la línea de comandos no es una restricción. Base64 no
compra nada y cuesta un 34% más de contexto, así que el blob va en claro.

Se descartaron dos alternativas:

**Flags sueltos**, trece argumentos semánticos por invocación. Es exactamente lo
que el 09 prohibió para el mapa, el modelo componiendo el contenido en vez de pasar
algo que no interpreta, y son trece oportunidades de cruzar un id con otro.

**Un archivo con run id**, que baja el costo de contexto de 178 tokens a siete por
invocación. No va: un archivo que sobrevive a una sesión muerta es un caché con
TTL, que es literalmente lo que la regla de arriba deja afuera. Los 1.250 tokens
son ruido al lado de una sesión de grilling.

### Qué imprime `preflight`

Por **stdout**, exactamente el JSON del ctx y nada más, para que el modelo lo pase
sin editarlo. Todo lo legible por humanos, incluidos los avisos de labels
ausentes, va a **stderr**. El código de salida distingue el éxito de las cuatro
fallas duras de la sección 5.

---

## 4. El preflight deja de escribir

El preflight creaba los labels que faltaran, idempotente. Eso lo volvía una
operación de escritura, y el 08 puso `preflight: sí` en la columna de
`/map-status` de su tabla de reparto. El mismo 08 dice que `/map-status` *"no
escribe nada, en ningún modo, igual que `sdd-status` en el plugin hermano. Una
corrida deja Linear byte a byte como estaba."*

**Medido: hoy no existe ninguno de los ocho labels.** El 03 los había creado y
borrado al medir. Sobre el workspace de hoy, un `/map-status` crearía ocho labels
en `keiron`. No es hipotético.

`/map-status` es el único comando del plugin cuya garantía se puede verificar
mirando el workspace antes y después, y esa garantía vale más que la comodidad de
tener la creación en el arranque. **El preflight pasa a ser de solo lectura.**
Resuelve y reporta qué falta, y no crea nada.

### Quién crea entonces

**`ticket:create`, el único consumidor real.** `map:create` fue el primer candidato
y no sirve: crea un Project y un Document, y ninguno de los dos lleva labels, así
que sería un ritual de arranque puesto en un lugar arbitrario. Y no cubre el caso
que importa, que es alguien borrando `hitl:pm` tres semanas después de trazado el
mapa.

`ticket:create` busca por nombre exacto y crea solo lo que no existe, que es la
regla que el 03 ya había escrito. **Medido: crear los que falten es un round trip,
no ocho.** Con dos labels descartables en una sola mutation con alias: dos creados,
complejidad 5, 305 ms. Un `ticket:create` sobre un workspace donde falta algo paga
un round trip de más, una vez.

Se descartó mudar la creación a `/planner-setup`, el comando que creó el 07. Es por
máquina y los labels son por workspace, y el 07 le dejó la key como única
responsabilidad a propósito: quien instala en su máquina puede no tener intención
de tocar labels del workspace.

---

## 5. Las cuatro fallas duras

El 03 escribió *"si algo no se resuelve, falla fuerte y con mensaje accionable. No
hay fallbacks"*. Con el preflight de solo lectura esa lista se achicó y hay que
reescribirla.

Falla duro, con mensaje accionable y código de salida distinto de cero:

1. **La key ausente o rechazada.** Ya era la falla que el 07 le asignó al preflight.
2. **El team no encontrado.**
3. **No existe ningún estado de tipo `completed`, o ninguno de tipo `canceled`**, en
   el team. Sin ellos no hay ni resolución ni fuera de alcance ni predicado de
   frontera.
4. **El label `map` no existe**, salvo en bootstrap. Ver la sección 6.

Las tres primeras comparten una propiedad y por eso son duras: sin ellas ninguna
operación puede escribir en el lugar correcto, y ninguna se arregla sola. Un label
de tipo ausente no cumple ninguna de las dos, porque `ticket:create` lo crea.

**El preflight no valida el Project ni el Document.** Se queda con lo que es del
workspace. Una URL equivocada o un Project sin mapa explotan en `map:read`, que es
el paso 2 de todos modos, así que sigue siendo antes de la primera escritura, que
es lo que la promesa decía. Y meterle el Project al preflight le rompería la
simetría al subagente de research, que corre el suyo sin tener siempre el Project a
mano en ese momento.

---

## 6. El label `map` es distinto de los otros siete, y hay que decirlo

Medido sobre `CRM-3350` del sandbox del 01: se creó un label descartable, se
adjuntó a la issue, se borró el label, y **la issue sobrevivió con sus labels
originales y sin el borrado**. El sandbox quedó como estaba.

O sea: si alguien borra `map`, todo ticket de decisión sobrevive pero se queda sin
él. `frontier:query` filtra por nombre y devuelve **cero, sin error**. El paso 3 de
`/map-work` lee eso como "sin tickets abiertos" y emite `map-collapse` sobre un
mapa con catorce preguntas sin responder.

Es la respuesta más destructiva del conjunto y llega en silencio. Por eso `map` es
la cuarta falla dura, y por eso rompe a propósito la simetría de "los ocho labels
se tratan igual": los otros siete viajan como `null` y los crea `ticket:create`,
porque su ausencia **bloquea una escritura**. La de `map` **hace mentir a una
lectura**, y eso no se arregla solo.

Se descartaron dos parches en el consumidor. Que `frontier:query` compare lo que
devolvió contra el total de issues del Project, y que el veredicto exija cero
issues sobre el Project entero. Los dos arreglan en el consumidor un problema que
se ve entero en el productor, y el preflight ya trae los ocho ids.

### El bootstrap

La cuarta falla dura, leída literal, rompe `/map-new` sobre un workspace fresco:
el label no existe todavía porque quien lo va a crear es el primer `ticket:create`
del paso 5.

**`/map-new` pasa `--bootstrap` al preflight, y ese flag apaga la cuarta falla y
nada más.** Se apoya en algo que ya es verdad: `/map-new` es el único comando que
nunca lee una frontera preexistente, porque `map:create` se niega sobre un Project
que ya tiene mapa.

Un dato que hace que esto alcance: `frontier:query` filtra **por nombre**, no por
id, así que el `frontier:query` que cierra `/map-new` devuelve bien aunque su ctx
siga diciendo `map: null`. El `null` del ctx es solo el testigo de que el label no
estaba al arrancar, no un id que haga falta.

Se descartó deducirlo de los datos, fallando solo si `map` es `null` **y** alguno
de los otros siete existe. Cubre los dos casos sin flag y tiene un agujero si
alguien borra los ocho, pero lo que lo descarta es otra cosa: dentro de seis meses
alguien lee `if map is None and any(others)` y tiene que reconstruir este
razonamiento entero antes de poder tocarlo. El flag dice en el código lo que la
inferencia deduce.

---

## 7. La forma del ctx

Dos campos separados para los labels, y la separación es la regla:

```json
{
  "viewer": "27b3d9f8-...",
  "team": "267840b8-...",
  "done": "<el completed de menor position>",
  "canceled": "<el canceled de menor position>",
  "default": "<Team.defaultIssueState>",
  "labels": {
    "map": "<id o null>",
    "map:research": "<id o null>",
    "map:prototype": "<id o null>",
    "map:grilling": "<id o null>",
    "map:task": "<id o null>",
    "hitl:pm": "<id o null>",
    "hitl:design": "<id o null>",
    "hitl:dev": "<id o null>"
  },
  "discovery": "<id o null>"
}
```

`labels` tiene las ocho claves **siempre presentes**, con `null` en las ausentes.
`discovery` va aparte.

La razón es que no son la misma clase de cosa. Los ocho son nuestros y los creamos:
`ticket:create` crea todo `null` que encuentre en `labels`. `Discovery` es del
equipo, y `CONTEXT.md` dice que el plugin lo escribe cuando existe, lo saltea en
silencio cuando no, y **nunca lo crea**. Poner esa diferencia en la forma del ctx
en vez de en un `if` por nombre adentro de `ticket:create` es lo que la vuelve
chequeable.

Los valores medidos hoy contra `keiron`: `viewer` es `ljana`
`27b3d9f8-7b03-473c-ba7b-06d045fd9361`, `team` es `CRM`
`267840b8-2c3e-4209-8a86-5c95f29ded19`, `default` es `Backlog`, el `completed` de
menor `position` es `Done` y el `canceled` de menor `position` es `Canceled`.

---

## 8. Un subcomando sin `--ctx` falla

Es lo que vuelve mecánica la regla del conductor en vez de dejarla como una
costumbre.

**Ningún subcomando consumidor sabe hacer un preflight.** Invocado sin `--ctx`,
falla con un mensaje que dice que hay que correr `preflight` primero. Pagar dos
preflights es imposible por construcción, no por disciplina, y el ticket 10 lo
chequea con un grep: la query del preflight aparece en un solo lugar del adapter.

El costo es que correr un subcomando a mano desde una terminal pide dos pasos. Está
bien: el adapter no es una herramienta de línea de comandos para personas.

### El preflight no se fusiona con la primera query

Medido, la fusión funciona y es barata:

| Query | Complejidad | Round trip |
| --- | --- | --- |
| `preflight` solo | 424 | 228 ms |
| `map:read` solo | 3 | 356 ms |
| `frontier:query` solo | 3.847 | 278 ms |
| `preflight` + `frontier:query` | 4.270 | 421 ms |
| `preflight` + `map:read` + `frontier:query` + `projectMilestones` | **4.333** | 287 ms |

El paso 1 y el paso 2 enteros de `/map-work` entran en un solo round trip con 57%
de aire contra el techo de 10.000 por query.

**Y aun así no se fusiona.** Bajo la regla del conductor eso ahorra un round trip
por comando, ~300 ms, no los 3,2 segundos del principio. No paga darles a
`map:read` y a `frontier:query` una segunda forma que el check estructural del
ticket 10 después tiene que conocer. Un subcomando, una operación, una forma.

La medición queda acá anotada como la salida que existe el día que la latencia
importe.

---

## 9. `ticket:resolve` es una invocación, no cinco

`CONTEXT.md` describe a `ticket:resolve` como una operación que abarca cinco
escrituras *en ese orden*, y a la vez `ticket:create`, `ticket:block` y `map:write`
existen como operaciones propias. Nunca se había dicho cuál de las dos lecturas
vale, y el ticket 14 contó ocho preflights suponiendo la otra.

**Es una invocación.** `ticket:resolve` hace las cinco escrituras adentro,
reusando a las otras tres como funciones. El orden lo garantiza el adapter y no el
modelo.

Es el mismo argumento con el que el 09 metió el read-modify-write entero adentro de
una invocación de `map:write`: si el orden importa y una sesión que muere en el
medio tiene consecuencias definidas, el orden no puede depender de que el modelo no
se distraiga entre dos llamadas a Bash. Acá importa más todavía, porque el 03
escribió el orden exacto y qué queda roto en cada punto de corte.

El caso del subagente de research, que escribe comentario y estado pero **no** el
mapa, sale con un flag: el 08 ya lo había marcado como la única operación que se
parte entre procesos.

---

## 10. El subagente corre el suyo

El 08 dijo que cada subagente corre su propio preflight, y su razón era que pasarlo
es "acoplamiento a cambio de nada". La sección 3 vació esa razón: pasar adentro de
una corrida ahora es el mecanismo normal.

**Se mantiene igual, y por otro motivo.** La regla del conductor vuelve al
subagente un conductor por definición, así que esto deja de ser una excepción y
pasa a ser la regla aplicada sin casos. Un conductor, un preflight.

Cuesta un round trip de ~300 ms al arrancar un subagente que va a trabajar minutos.
La alternativa, meterle el `--ctx` del padre en el prompt, mete 178 tokens de UUIDs
en un prompt de research que no habla de eso.

---

## 11. Qué pasa cuando el workspace cambia a mitad de corrida

Era la pregunta del ticket sobre la invocación siete que falla con seis ya
escritas. **Con un solo preflight, no hay invocación siete que preflightee**, así
que la pregunta cambia de forma: queda un ctx resuelto al empezar y usado hasta el
final.

Medido, la ventana es más angosta de lo que parece: **el id de un label sobrevive a
un rename.** Renombrar `Done` no cambia su id. Solo rompe un borrado o un
archivado, y entonces la escritura que usa ese id falla contra la API.

**No hay revalidación.** El preflight falla antes de la primera escritura, que es
su trabajo. Después, un id borrado hace fallar la escritura que lo usa, fuerte y
con el error de la API. Un segundo preflight antes de `ticket:resolve` compraría
una ventana angosta de un caso que necesita que alguien borre un estado del team
mientras vos resolvés un ticket, y pagaría con lo único que este ticket vino a
arreglar.

---

## 12. La cuenta

La pregunta del ticket era cuántas veces corre el preflight en un `/map-work`
típico. **Una.**

`/map-work` sobre un ticket de grilling que crea dos tickets nuevos:

| # | Invocación | Escribe |
| --- | --- | --- |
| 1 | `preflight` | no |
| 2 | `map:read --ctx` | no |
| 3 | `frontier:query --ctx` | no |
| 4 | `ticket:claim --ctx` | sí |
| 5 | `ticket:resolve --ctx` | sí, cinco veces adentro |

**Cinco invocaciones, un preflight.** No ocho, que era la cuenta del ticket, ni
nueve, que es lo que daría si `ticket:resolve` fueran cinco invocaciones.

Los otros comandos:

- **`/map-status`**: `preflight`, `map:read`, `frontier:query`. Tres invocaciones,
  un preflight, **cero escrituras**, que ahora es verdad y se puede verificar.
- **`/map-new`**: `preflight --bootstrap`, `map:create`, `ticket:create` por
  ticket, `ticket:block` por relación, `map:write` una vez, `frontier:query`. Un
  preflight para el padre, más uno por cada subagente de research.
- **`/map-collapse`**: un preflight, y las N+2 escrituras que fijó el 06.

---

## Qué corrige o empuja

**Al ticket 08**, la regla del preflight. Decía "por proceso que emite
operaciones" y se lee "por conductor". El razonamiento del 08 no cambia, cambia la
palabra. Y su tabla de reparto queda igual salvo que la fila `preflight` de la
columna `/map-status` deja de ser una escritura.

**Al ticket 03**, tres cosas. El preflight ya no crea labels, así que la frase
*"los ocho ids de label, y crea los que falten, idempotente"* se parte: resuelve
acá, crea en `ticket:create`. Su lista de fallas duras se reescribe en cuatro. Y su
regla de no cachear queda acotada explícitamente a no persistir entre corridas,
porque el 08 ya la leyó de la manera ancha una vez.

**Al ticket 09**, nada que corregir. Este ticket es el que él graduó, y su nota
decía que el costo era complejidad. El costo real era latencia y la queja era
falsa, y el hallazgo que decidió el ticket fue otro.

**A `CONTEXT.md`**, cuatro cosas. Las operaciones pasan de once a **doce**, porque
el preflight entra a la cuenta como operación propia. Las que no escriben pasan de
dos a **tres**: `frontier:query`, `map:read` y `preflight`. La fila `Preflight` se
reescribe entera: corre una vez por conductor, no guarda nada, no crea nada, y
emite un ctx que todo consumidor recibe. Y `ticket:create` gana la creación de los
labels que falten.

**Al ticket 10**, la corrección de la afirmación 22 y las afirmaciones 32 a 41.

**A la niebla, nada.** Este ticket no vació ningún parche y no abrió ninguno.

---

## Las afirmaciones chequeables, para el ticket 10

Siguen la numeración: 1 a 6 del 08, 7 a 13 del 06, 14 a 21 del 07, 22 a 31 del 09.

32. `scripts/linear.py` tiene **doce** subcomandos, uno por operación nombrada en
    `LINEAR-OPERATIONS.md`, y ninguno de más. Entre ellos `preflight`.
    **Reemplaza a la afirmación 22 del ticket 09**, que decía once.
33. La query del preflight aparece en **un solo lugar** del adapter. Grep de
    `issueLabels(first: 250` o del nombre de la constante: una coincidencia. Es lo
    que vuelve imposible pagar dos preflights.
34. `preflight` no contiene ninguna mutation. Grep de `mutation` en su ruta de
    ejecución: cero coincidencias. Es el tercer subcomando de solo lectura, con
    `map:read` y `frontier:query`.
35. Los siete subcomandos que consumen el ctx declaran `--ctx` como argumento
    **requerido**, y ninguno tiene una rama que lo resuelva por su cuenta cuando
    falta.
36. `preflight` escribe por stdout algo que parsea como JSON y nada más. Todo
    `print` legible por humanos de su ruta va a stderr.
37. El ctx tiene `labels` con las ocho claves y `discovery` como campo **separado**.
    No existe la clave `Discovery` adentro de `labels`.
38. `ticket:create` crea los labels que vengan en `null` dentro de `labels`, y no
    tiene ninguna ruta que cree `discovery`. Grep de `issueLabelCreate`: aparece
    solo en `ticket:create`.
39. `--bootstrap` aparece en `commands/map-new.md` y en ningún otro archivo de
    `commands/`. En el adapter, apaga exactamente una falla y no más.
40. `preflight` tiene exactamente cuatro fallas duras y las cuatro salen con código
    distinto de cero. Ninguna ruta del preflight consulta el Project ni el
    Document.
41. `ticket:resolve` emite sus cinco escrituras adentro de la misma invocación, sin
    ningún punto de retorno al modelo entre ellas. Es la misma invariante que la
    afirmación 24 le pide a `map:write`.
