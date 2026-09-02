---
lang: es
---

# CHECKS

Este archivo es la tabla de afirmaciones del plugin, agrupada por el script que
las chequea. Es la única casa del conteo: una afirmación que no tiene fila acá no
existe, y ningún otro archivo del repo vuelve a contarlas. Los research donde
nacieron quedan como registro de su momento, y pueden decir números que ya no
valen.

**57 acuñadas, 51 no retiradas, 6 retiradas.**

La columna Estado es lo que la afirmación 50 va a leer, y toma tres valores. Una
afirmación acuñada que todavía no tiene script arranca en `pendiente`. Cambia de
estado en la misma task que escribe el check que la emite, y no antes: así se nota
cuando alguien construyó algo sin chequearlo. El tercer valor es de la afirmación
que otra reemplazó, y tiene su propia tabla al final.

El nombre del valor del medio no aparece en esta prosa a propósito. Vive solo
dentro de las celdas de la columna, así que un grep sobre este archivo cuenta
afirmaciones y nunca párrafos.

El script no es una columna: es el encabezado de cada bloque. Una columna sería
una segunda copia.

## Las no retiradas

### `check-roster.sh`
| Nº | Afirmación | Cómo | Brecha | Estado | Origen |
| --- | --- | --- | --- | --- | --- |
| 3 | `map-status.md` dice `ROUTE: read-only` y no existe `skills/map-status/` | extrae la línea `ROUTE:` y exige el literal, más la no existencia del directorio | ninguna | pendiente | 08 |
| 7 | El conjunto de tokens de `map-contract.md` es exactamente el que emiten los comandos | igualdad de conjuntos entre la tabla del contrato y los tokens que aparecen en `commands/*.md`. El seis no aparece en el script | ninguna | pendiente | 08, corregida por el 06 |
| 8+16 | Todo archivo de `commands/` declara un `ROUTE:`; los que rutean a skill apuntan a una que existe, y los dos que no son `map-status.md` y `planner-setup.md`, sin `skills/` correspondiente | recorre `commands/*.md`, parte los `ROUTE:` en dos conjuntos, verifica existencia y no existencia. Ni el seis ni el cuatro aparecen | el techo de 25 líneas por comando que el plugin hermano impone en su `check-commands.sh` no está acuñado acá y esta afirmación no lo mira: se respeta como convención y se verifica a mano. Tampoco mira el frontmatter ni la ausencia de restatements, que el hermano sí chequea | pendiente | 08 → 06 → 07 |
| 39a | `--bootstrap` aparece en `commands/map-new.md` y en ningún otro archivo de `commands/` | el conjunto de archivos que lo contienen es exactamente `{map-new.md}` | ninguna | pendiente | 14 |
| 50 | Los números marcados `viva` en `CHECKS.md` y los `[N]` que emiten los scripts son el mismo conjunto | igualdad de conjuntos entre la columna Nº de las filas `viva` y los `[N]` extraídos del fuente de los checks, anclados en la comilla que abre el literal que los lleva: desde que hay un check que no es bash, un indexado como `nodos[0]` es indistinguible de un `[0]` y sin el anclaje entran al conjunto tres números que nadie acuñó. Del lado del registro la celda de número se normaliza antes de ordenar, sacándole la letra a `39a` y `39b` y expandiendo la fila fusionada `8+16` en sus dos números | ninguna | pendiente | 10 |

### `check-templates.sh`
| Nº | Afirmación | Cómo | Brecha | Estado | Origen |
| --- | --- | --- | --- | --- | --- |
| 9 | `map-templates.md` tiene los seis encabezados del DD con texto exacto y las tres secciones del cuerpo de la issue de ejecución | secuencia exacta de `## ` en cada bloque de plantilla, contra las anclas que el adapter escribe | ninguna | pendiente | 06, parcialmente reemplazada por la 43 |
| 25 | No hay dos viñetas de niebla con el mismo título en negrita, y `map-contract.md` dice que el título es una clave única | unicidad de los títulos en negrita del bloque de niebla, más un grep de la frase en el contrato | la segunda mitad es un grep de prosa: reescribir la frase falla el check sin que la regla cambie. Se acepta, se arregla en un commit | pendiente | 09 |
| 42 | La entrada de Decisiones hasta ahora es una línea: enlace, dos puntos y gist | cada viñeta del bloque de ejemplo ocupa exactamente una línea física | ninguna | pendiente | 04 |
| 43 | Las seis secciones del comentario de resolución con texto exacto, con `## Lo que se cayó` tercera, entre `## Por qué` y `## Niebla graduada` | secuencia **ordenada**, no conjunto: la posición es parte de la afirmación | ninguna | pendiente | 04 |
| 46 | Ninguna plantilla ni ningún comando contiene `<details>` ni `<summary>` | grep sobre `commands/*.md` y `map-templates.md`: cero | ninguna | pendiente | 04 |

### `check-adapter.py`
| Nº | Afirmación | Cómo | Brecha | Estado | Origen |
| --- | --- | --- | --- | --- | --- |
| 11 | Toda ruta de creación de issues pasa `stateId` | AST: las llamadas cuyo payload contiene `issueCreate` o `issueBatchCreate` exigen la clave en el dict del mismo alcance | un payload armado dinámicamente no lo sigue | pendiente | 06 |
| 12 | `ticket:create` pasa `estimate: 0`; `issue:create` no pasa `estimate` | AST, dentro de la función de cada subcomando | ninguna | pendiente | 06 |
| 13 | `milestone:create` nunca pasa `targetDate` | AST: el literal no aparece en el subárbol de la función | ninguna | pendiente | 06 |
| 23 | `map:read` no contiene ninguna mutation en su ruta de ejecución | AST: grafo de llamadas desde la función; ninguna cadena alcanzable contiene `mutation` | llamadas indirectas por dict de handlers o `getattr` no se siguen | pendiente | 09 |
| 24 | `map:write` emite `project(id:)` y `projectUpdate` en la misma función, sin punto de retorno entre los dos (era `document(id:)` y `documentUpdate`; lo mudó el 11) | AST: mismo `FunctionDef`, y ningún `return`, `sys.exit` ni `raise` entre las dos sentencias | ninguna. La cerró el AST | pendiente | 09 |
| 26 | `map:write` acepta `--expect-sections` y su ausencia no aborta | AST: `add_argument` sin `required=True`, y ninguna salida no cero cuando el valor es `None` | ninguna | pendiente | 09 |
| 27 | Ninguna ruta lee ni escribe un archivo de estado del contenido del mapa | AST: el único acceso a disco permitido es la lectura de la ruta de la key | ninguna | pendiente | 09 |
| 28 | `map:write` tiene exactamente un reintento, y su flag interno no está expuesto como argumento | AST: el literal del contador vive en un solo lugar y no hay `add_argument` para el flag | un reintento escrito como recursión sin límite no se ve | pendiente | 09 |
| 29 | Ninguna ruta compara `updatedAt` para decidir si escribir | AST: `updatedAt` no aparece en ningún `If.test` ni `Compare` | ninguna | pendiente | 09 |
| 30 | Ninguna query pide `contentState` | cero ocurrencias en todo el archivo | ninguna. Es la única donde el archivo entero es más fuerte que la ruta, y a propósito | pendiente | 13, vía 09 |
| 31 | `map:write` no tiene verificación posterior a la escritura, ni flag ni interna, y ninguna ruta duerme entre el `projectUpdate` y el retorno (era `documentUpdate`; lo mudó el 11) | AST: sin `add_argument("--verify")`, sin `time.sleep` y sin relectura después de la sentencia | ninguna | pendiente | 13, vía 09 |
| 32 | Un subcomando por cada operación nombrada en `LINEAR-OPERATIONS.md` y ninguno de más, `preflight` incluido | igualdad de los tres conjuntos: los `add_parser` literales del AST, la tabla `Las doce operaciones` de `LINEAR-OPERATIONS.md` y la tabla `Las operaciones del tracker` de `CONTEXT.md`, más cero `add_parser` cuyo primer argumento no sea un literal de string. El doce no aparece | ninguna | viva | 14 |
| 33 | La query del preflight aparece en un solo lugar | AST: la constante se asigna una vez y se referencia solo desde la función del preflight | ninguna | viva | 14 |
| 34 | `preflight` no contiene ninguna mutation | igual que la 23 | la misma que la 23 | viva | 14 |
| 35 | Los siete subcomandos que consumen el ctx declaran `--ctx` requerido, y ninguno lo resuelve por su cuenta | AST: `required=True` en los siete, y la constante de la query del preflight no aparece en sus subárboles | ninguna. La cerró el AST | pendiente | 14 |
| 36 | `preflight` escribe por stdout algo que parsea como JSON y nada más | AST: todo `print` de la ruta lleva `file=sys.stderr` salvo el único que emite el ctx | ninguna | pendiente | 14 |
| 37 | El ctx tiene `labels` con las ocho claves y `discovery` como campo separado | igualdad de conjuntos entre las claves del dict y los labels de la tabla de tipos, más la ausencia de `Discovery` adentro | ninguna | pendiente | 14 |
| 38 | `ticket:create` crea los labels que vengan en `null`, ninguna ruta crea `discovery`, y `issueLabelCreate` aparece solo ahí | AST: alcanzabilidad de `issueLabelCreate` desde una sola función, y el literal ausente de su argumento | ninguna | pendiente | 14 |
| 39b | En el adapter, `--bootstrap` apaga exactamente una falla y no más | AST: la variable del flag aparece en exactamente una condición | ninguna | pendiente | 14 |
| 40 | `preflight` tiene exactamente cuatro fallas duras, todas con código no cero, y ninguna ruta consulta el Project (la mitad del Document se cae con el 11: ya no hay Document) | AST: cuenta las salidas no cero alcanzables, y verifica que `project` no aparezca en su query | ninguna. La cerró el AST | pendiente | 14 |
| 41 | `ticket:resolve` emite sus cinco escrituras en la misma invocación, sin punto de retorno entre ellas | el mismo análisis de la 24, con cinco sentencias en vez de dos | ninguna. La cerró el AST | pendiente | 14 |
| 44 | El adapter no envuelve texto | AST: ni `textwrap` importado ni ningún `join` sobre líneas cortadas en la ruta de `map:write` | un envoltorio escrito a mano con un bucle de índices no se ve | pendiente | 04 |
| 45 | El flag que agrega una decisión recibe el gist como argumento propio y rechaza más de 120 caracteres con código no cero | AST: `add_argument` propio, y una comparación contra el literal 120 que lleva a una salida no cero | ninguna | pendiente | 04 |
| 47 | `ticket:create` rechaza dos labels `map:<tipo>` en la misma issue, con código no cero | AST: existe una comparación que cuenta los labels con el prefijo del tipo y sale no cero si son más de uno | prueba que el código está, no que rechace bien. Solo un test de comportamiento la cerraría | pendiente | 10 |
| 48 | Ninguna ruta de `issue:create` agrega el label `map` | AST: el literal no aparece en su construcción de labels | ninguna | pendiente | 10 |
| 51 | `work:write` con la lista de issues vacía no llama a `issueBatchCreate` | AST: la llamada está adentro de una guarda sobre la lista | ninguna | pendiente | 12 |
| 52 | Toda construcción de `issueRelationCreate` con `type: "related"` en `linear.py` pone el ticket de decisión del lado `issueId` | AST, dentro de la función de `work:write` | ninguna | pendiente | 12 |
| 53 | El predicado de frontera evalúa bloqueos solo sobre `inverseRelations`, y ninguna rama lo evalúa sobre `relations` | AST | ninguna | pendiente | 12 |
| 54 | La lista de labels que `ticket:create` crea cuando faltan tiene nueve elementos e incluye `map:no-landing`, y ninguna otra función de `linear.py` crea labels | AST | ninguna | pendiente | 12 |

### `check-packaging.sh`
| Nº | Afirmación | Cómo | Brecha | Estado | Origen |
| --- | --- | --- | --- | --- | --- |
| 14 | `plugin.json` existe, pasa `claude plugin validate --strict`, y declara `author` | corre el CLI y exige código cero; lee el JSON con `python3` para exigir `author` | `--strict` es más flaco de lo que suena: **un `SKILL.md` sin `name:` lo pasa limpio**. Medido. Ninguna afirmación cubre eso. Con un `marketplace.json` en `.claude-plugin/` el CLI valida el marketplace y no el plugin, y hoy no lo hay porque la entrada vive en el repo hermano. Y la validación corre sobre una copia aislada del manifiesto, porque `CLAUDE.md` en la raíz le arranca un warning que bajo `--strict` es un error, así que tampoco mira el plugin tal como se despacha | viva | 07 |
| 15 | `dependencies` con exactamente un elemento, `spec-driven-dev`, string y sin constraint | largo uno, tipo `str`, valor exacto | ninguna. Es un literal que vive una sola vez | viva | 07 |
| 17 | `install.sh` chequea el intérprete con `python3 -V` y no con `command -v python3`, y su mensaje nombra `xcode-select --install` | tres greps: dos presencias y una ausencia | ninguna | viva | 07 |
| 18 | `install.sh` no imprime la key en ninguna ruta, y guarda en `${XDG_CONFIG_HOME:-$HOME/.config}/keiron-planner/linear.key` | ruta literal presente una sola vez, y la variable de la key en exactamente la cantidad de ocurrencias que el check declara y en ninguna más | bash no tiene AST barato: un `echo "$*"` que la incluya indirectamente se escapa. **Es la brecha más cara de la tabla**, porque su modo de falla es una credencial en un log. Y hay una exposición que ninguna grep ve: la key viaja por `argv` de `curl` en el header de autorización, visible en `ps` para otros usuarios de la máquina; sacarla de ahí pide `--config` o un descriptor, y es otro change. El conteo exige igualdad, así que un uso nuevo legítimo la pone roja hasta que el número se actualice, y ese es su precio | viva | 07, celda `Cómo` editada por D2 y por D19 de CRM-3392 |
| 20 | El `README.md` tiene el snippet con `keiron-planner@spec-driven-dev` y nombra `/planner-setup` | dos greps | ninguna | pendiente | 07 |
| 21 | Ningún archivo trackeado matchea `*.key`, y `.gitignore` lo cubre | `git ls-files` sobre **todo lo trackeado**, `vendor/` y `.scratch/` incluidos, más `git check-ignore` sobre una ruta de prueba | ninguna | viva | 07 |
| 56 | `install.sh` corre bajo `dash` sin errores de portabilidad: el archivo parsea entero, y cada modo no interactivo sale con el código que declara y sin diagnóstico del intérprete | `dash -n` sobre el archivo, más tres ejecuciones con `HOME` y `XDG_CONFIG_HOME` seteadas a un temporal, una por modo no interactivo y una con un argumento inválido, exigiendo el código **exacto** de cada modo y la ausencia de una línea de diagnóstico de `dash` en stderr | tres puntos ciegos medidos. Uno, `$'...'` degrada a los bytes literales del dólar, la barra y la ene: sale con el código esperado, no escribe diagnóstico y pasa `dash -n`, o sea corrupción muda. Dos, `cmd_install` y `validate` no se ejecutan nunca, porque piden TTY y red, así que un bashismo de runtime ahí adentro no lo ve ninguna de las tres partes. Tres, las ramas que necesitan una key guardada tampoco se ejecutan, y ejercitar la de `cmd_verify` haría una llamada de red, que es lo que la aislación existe para evitar; la afirmación 57 sí la ejercita, con un `curl` falso al frente del `PATH`, así que el contrato de desenlaces no queda sin cobertura | viva | CRM-3392 |
| 57 | `install.sh` distingue los tres desenlaces de su validación, y el mensaje que lee la persona corresponde al desenlace: un fallo del que el script no pudo decidir nunca se reporta como credencial inválida | cuatro ejecuciones de `--verify` con una key plantada y un `curl` falso al frente del `PATH`, exigiendo el código exacto y una marca de texto propia de cada mensaje: una por desenlace, más una con un `python3` que existe y no reporta versión. El falso asierta además sobre el config que recibe por stdin, que tiene que ser una línea sola cuyo token de opción es la constante y con la key entera, y reconoce el fallo duro también agrupado, porque con él la rama de rechazo pasa a ser un desenlace 2 y el mensaje se invierte | tres límites. Uno, el `curl` es falso, así que lo verificado es cómo despacha el script sobre tres formas de respuesta y no que la API de Linear produzca esas formas. Dos, solo ejercita el sitio de llamada de `cmd_verify`; los otros dos, el de `cmd_install` y el del chequeo de reemplazo, piden TTY y no se ejecutan. Tres, del desenlace 2 cubre la rama en que `curl` falla y no la de una respuesta que no parsea como JSON, y de las herramientas que `validate` necesita cubre la de `python3` y no las demás | viva | CRM-3392 |

### `check-language.sh`
| Nº | Afirmación | Cómo | Brecha | Estado | Origen |
| --- | --- | --- | --- | --- | --- |
| 6 | Los archivos de la columna inglés no tienen prosa en español, y al revés | camina los `.md` con `lang: en`, saca bloques de código y tramos entre backticks, y falla si queda `áéíóúñ¿¡` o su mayúscula | **el sentido inverso no se chequea.** Inglés adentro de un `lang: es` no tiene señal barata y queda para lectura humana | viva | 08 |
| 49 | Todo `.md` del árbol del plugin declara `lang:` con valor `en` o `es` | camina los `.md` del árbol, excluidos `vendor/` y `.scratch/`, y exige el campo con valor del conjunto de dos | ninguna | viva | 10 |

### `check-py39.sh`
| Nº | Afirmación | Cómo | Brecha | Estado | Origen |
| --- | --- | --- | --- | --- | --- |
| 19 | `linear.py` corre en Python 3.9 | resuelve intérprete en orden `$PY39`, `python3.9`, `/usr/bin/python3` si reporta 3.9.x; falla duro si ninguno. Importa el módulo y corre `--help` de los doce subcomandos | prueba lo que se ejecuta al importar y al parsear argumentos. Una construcción de 3.10 escondida en una rama que solo corre contra la API no se ve. Y la cadena cuelga de un solo eslabón local: hoy `python3.9` no está en el PATH y el único 3.9 de la máquina es `/usr/bin/python3`, así que el día que macOS lo mueva a 3.11 el check se pone rojo por una razón ajena al adapter | viva | 07 |

### `check-prose.sh`
| Nº | Afirmación | Cómo | Brecha | Estado | Origen |
| --- | --- | --- | --- | --- | --- |
| 55 | `map-work.md` nombra la prohibición de aterrizar en un corte con `status: done` | un grep de prosa sobre `commands/map-work.md` | es un grep de prosa, así que reescribir la frase falla el check sin que la regla cambie. Es la misma brecha que la afirmación 25 y se acepta igual | pendiente | 12 |

## Las retiradas

| Retirada | La reemplaza | Qué decía de más |
| --- | --- | --- |
| 1 | 7 | cinco tokens de contrato; son seis |
| 2 | 8, después 16 | cinco archivos en `commands/`; son seis |
| 4 | 9, después 43 | cinco encabezados del DD y cinco secciones del comentario |
| 5 | 10 → 22 → 32 | ocho subcomandos; son doce |
| 10 | 22 → 32 | diez subcomandos |
| 22 | 32 | once subcomandos |
