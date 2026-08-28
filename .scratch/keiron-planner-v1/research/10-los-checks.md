# 10: Los checks estructurales

Deliverable del ticket [10](../issues/10-que-chequean-los-checks.md), `map:grilling`,
`hitl:dev`. Cinco rondas, veinticinco preguntas, frontera del árbol vacía.

La decisión de encuadre del mapa dice que la verificación son checks estructurales
sobre el repo, al estilo de los `scripts/check-*.sh` de SDD, y nada de verificar
comportamiento conversacional. Este documento la vuelve concreta: **cincuenta
afirmaciones acuñadas, cuarenta y cuatro vivas, seis retiradas**, repartidas en seis
scripts que corren en un solo job de CI.

> **Enmienda del 12.** Donde este documento diga `issue:create`, léase
> **`work:write`**: el 12 la renombró porque en dos de sus tres desenlaces no crea
> ninguna issue. Sigue siendo una de las doce operaciones. Detalle en
> [`12-el-aterrizaje.md`](12-el-aterrizaje.md).

> Las afirmaciones **12** y **48** nombran `issue:create` y hay que leerlas con el
> nombre nuevo. El 12 suma además cinco, de la **51** a la **55**, así que las acuñadas
> pasan de cincuenta a cincuenta y cinco.

## El resumen, en un párrafo

Los seis tickets que cerraron el 2026-08-27 dejaron cuarenta y seis afirmaciones
numeradas y repartidas en seis documentos, con tres reemplazos encadenados que nadie
había recontado. Recontadas: seis están retiradas y quedan cuarenta vivas, dos de
ellas reemplazadas solo a medias. Este ticket las consolida en una tabla, les asigna
script y método, y les escribe la brecha cuando el check prueba menos que la
afirmación. Acuña cuatro nuevas, las 47 a 50. La decisión que más cambia la forma del
resultado es que `check-adapter` **no es bash**: seis afirmaciones no hablan del
archivo sino de la *ruta de ejecución*, que un grep no puede expresar, así que ese
script es Python y lee `linear.py` con `ast`. Eso cerró de verdad cuatro
afirmaciones que habían quedado por irreducibles.

---

## 1. El recuento, que nadie había hecho

Las seis retiradas no son un detalle de contabilidad: cada una es un check que
alguien podría escribir mal si lee el research donde nació y no el que la reemplazó.

| Retirada | La reemplaza | Qué decía de más |
| --- | --- | --- |
| 1 | 7 | cinco tokens de contrato; son seis |
| 2 | 8, después 16 | cinco archivos en `commands/`; son seis |
| 4 | 9, después 43 | cinco encabezados del DD y cinco secciones del comentario |
| 5 | 10 → 22 → 32 | ocho subcomandos; son doce |
| 10 | 22 → 32 | diez subcomandos |
| 22 | 32 | once subcomandos |

Y dos están reemplazadas **a medias**, que es la trampa peor, porque leerlas enteras
da mitad verdad:

- De la **8** sobrevive "los que rutean apuntan a una skill que existe". Su conteo de
  archivos lo corrige la 16.
- De la **9** sobreviven los seis encabezados del DD y las tres secciones del cuerpo
  de la issue de ejecución. Sus cinco secciones del comentario las corrige la 43,
  que las lleva a seis.

La tabla de la sección 5 las publica ya consolidadas, en su forma final y en un solo
lugar. Es el valor entero de este ticket: dejar de tener cuarenta afirmaciones
repartidas en seis documentos con tres cadenas de reemplazo cruzándolas.

---

## 2. Los seis scripts

El reparto es por concern, siguiendo la forma de `../spec-driven-dev`, que tiene
`check-commands.sh`, `check-envelope.sh` y `check-judges.sh` planos en `scripts/`.

| Script | Qué mira | Afirmaciones |
| --- | --- | --- |
| `check-roster.sh` | igualdades de conjuntos sobre el árbol y el markdown | 3, 7, 8+16, 39a, 50 |
| `check-templates.sh` | texto exacto en `map-templates.md` y `map-contract.md` | 9, 25, 42, 43, 46 |
| `check-adapter.py` | el AST de `linear.py` | 11 a 13, 23 a 41 sin la 25, 44, 45, 47, 48 |
| `check-packaging.sh` | el manifiesto, el instalador y el repo | 14, 15, 17, 18, 20, 21 |
| `check-language.sh` | la columna de idioma | 6, 49 |
| `check-py39.sh` | que el adapter corra en 3.9 | 19 |

Más dos que no chequean nada: `check-common.sh`, que los seis sourcean, y
`check-all.sh`, que los corre.

**`check-common.sh` es una divergencia deliberada de SDD**, donde los tres scripts
duplican su propio `fail()`. Acá viven las raíces del árbol del plugin, el par
`fail`/`report` y el `bail` del tercer tier. Duplicar el acumulador seis veces es la
misma segunda copia que la sección 4 prohíbe.

### La enmienda al árbol de archivos del 08

El 08 escribió `scripts/check-*.sh`. Pasa a ser `scripts/check-*`, con dos
extensiones, porque `check-adapter.py` no puede ser bash. Ver la sección 3.

---

## 3. Por qué el adapter se chequea con un AST y no con grep

Es la decisión de forma más grande del ticket, y no salió de una preferencia sino de
leer las afirmaciones con cuidado.

**Seis de ellas no dicen "el archivo", dicen "su ruta de ejecución"**: la 23, la 27,
la 29, la 30, la 34 y la 44. Un grep sobre `linear.py` no sabe qué función llama a
cuál, así que solo puede afirmar sobre el archivo entero. Eso es *más fuerte* que lo
que la afirmación pide, y la diferencia se cobra el día que `map:read` y `map:write`
compartan un helper: el check falla sin que la invariante se haya roto.

**Y cuatro más habían quedado por irreducibles**, con una brecha escrita al lado: la
24 ("en la misma función, sin ningún punto de retorno entre los dos"), la 35
("ninguna rama que lo resuelva por su cuenta"), la 40 ("exactamente cuatro fallas
duras") y la 41. Sobre un árbol sintáctico las cuatro son afirmaciones exactas, no
aproximaciones. "El mismo `FunctionDef`, sin `return` ni `sys.exit` ni `raise` entre
las dos sentencias" es algo que se decide, no algo que se estima.

`linear.py` es Python y el runner de CI ya trae `python3`, así que `import ast` no
cuesta ninguna dependencia. Lo que se paga es que un script del set no es bash, y que
quien lo mantenga necesita leer AST. Se compra a cambio de no escribir veintidós
afirmaciones en un lenguaje que no puede decir seis de ellas, y taparlo con una
columna de brechas que en realidad serían limitaciones de la herramienta y no del
problema.

---

## 4. Las reglas que gobiernan a los seis

### Ningún número que ya viva en el repo se escribe dos veces

Un número hardcodeado en un check es una **segunda copia** de un hecho, y una segunda
copia es justamente la deriva que el check existe para atrapar. `check-commands.sh`
de SDD lo dice en un comentario: el roster no se hardcodea, se extrae de las tablas
consumidoras en tiempo de corrida, para que renombrar un encabezado vacíe un conjunto
y falle ruidosamente en vez de pasar vacuamente.

La regla es **por número de copias**, no por gusto:

- Donde dos archivos del repo ya cargan el mismo conjunto, el check compara los dos
  conjuntos y el número **no aparece en el script**. Es el caso de la 7 (contrato
  contra comandos), la 8+16 (`commands/` contra sus destinos de `ROUTE:`), la 9 y la
  43 (encabezados de la plantilla contra anclas del adapter), la 32 (tabla de
  `LINEAR-OPERATIONS.md` contra subparsers) y la 37 (claves de `labels` contra la
  tabla de tipos). El "seis" y el "doce" desaparecen.
- Donde el número **es la única copia**, se hardcodea sin culpa y con el número de
  afirmación al lado. Es el caso del reintento único de la 28, las cuatro fallas de
  la 40, el `estimate: 0` de la 12, los 120 caracteres de la 45 y el elemento único
  de `dependencies` de la 15. Ahí el check es la segunda copia a propósito, porque la
  primera está en código y no en una tabla.

### Los seis acumulan, y hay un tercer tier

SDD tiene dos políticas partidas por tamaño: sus dos scripts chicos salen en la
primera falla y `check-envelope.sh`, el de 49 KB, acumula y reporta todas juntas con
las siguientes prefijadas `also:`. Acá **los seis acumulan**, incluidos los chicos.
La razón para acumular no es que el script sea grande, es que una corrida diga todo
lo que está roto.

El tercer tier se copia tal cual de `check-envelope.sh`: cuando falta el archivo que
el script mira, reporta y sale ahí mismo sin correr las demás aserciones, porque
veintiún fallas derivadas de un archivo ausente son ruido.

### La regla anti-vacuidad

Copiada de SDD, y es lo que hace segura la política de la sección 6: **un check cuya
fuente falta o cuya extracción da vacío falla, nunca pasa**. Un chequeo de pertenencia
sobre un directorio vacío no prueba nada, y el día que alguien borre
`map-templates.md` el check no se puede volver verde por falta de trabajo.

### La salida nombra el número

`check-adapter: FAIL [30] — contentState aparece en linear.py:412`. Es lo que hace
que una falla se pueda leer contra el research que la escribió, en vez de tener que
reconstruir por qué alguien pensó que eso importaba.

### Todas rompen. No hay tier de aviso

Ningún check avisa sin fallar. Un check que avisa es un check que nadie mira, y el
segundo estado hace que el verde deje de significar algo. La candidata natural a
amarilla era la 6, la de idioma; en vez de dejarla amarilla se le bajó el alcance a
algo binario. Ver la sección 7.

---

## 5. La tabla

Es la salida del ticket. Vive acá mientras el plugin no exista, y **baja a
`scripts/CHECKS.md` en la misma task de SDD que escriba el primer check**. Ver la
sección 8.

Las columnas son las que fijó la ronda 4: número, afirmación, cómo, brecha, estado y
origen. El script es el encabezado de cada bloque, porque ponerlo además como columna
sería la segunda copia que la sección 4 prohíbe.

Los tres estados son `pendiente`, `viva` y `retirada`. **Hoy las cuarenta y cuatro
están `pendiente`**, porque no existe ni un archivo del plugin. El pasaje a `viva` es
la línea que toca la task de SDD que escribe el check, y es donde se nota si alguien
construyó algo sin chequearlo.

### `check-roster.sh`

| Nº | Afirmación | Cómo | Brecha | Estado | Origen |
| --- | --- | --- | --- | --- | --- |
| 3 | `map-status.md` dice `ROUTE: read-only` y no existe `skills/map-status/` | extrae la línea `ROUTE:` y exige el literal, más la no existencia del directorio | ninguna | pendiente | 08 |
| 7 | El conjunto de tokens de `map-contract.md` es exactamente el que emiten los comandos | igualdad de conjuntos entre la tabla del contrato y los tokens que aparecen en `commands/*.md`. El seis no aparece en el script | ninguna | pendiente | 08, corregida por el 06 |
| 8+16 | Todo archivo de `commands/` declara un `ROUTE:`; los que rutean a skill apuntan a una que existe, y los dos que no son `map-status.md` y `planner-setup.md`, sin `skills/` correspondiente | recorre `commands/*.md`, parte los `ROUTE:` en dos conjuntos, verifica existencia y no existencia. Ni el seis ni el cuatro aparecen | ninguna | pendiente | 08 → 06 → 07 |
| 39a | `--bootstrap` aparece en `commands/map-new.md` y en ningún otro archivo de `commands/` | el conjunto de archivos que lo contienen es exactamente `{map-new.md}` | ninguna | pendiente | 14 |
| 50 | Los números marcados `viva` en `CHECKS.md` y los `[N]` que emiten los scripts son el mismo conjunto | igualdad de conjuntos entre la columna Nº de las filas `viva` y los `[N]` extraídos de los mensajes de `fail` | ninguna | pendiente | 10 |

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
| 32 | Un subcomando por cada operación nombrada en `LINEAR-OPERATIONS.md` y ninguno de más, `preflight` incluido | igualdad de conjuntos entre los `add_parser` del AST y los nombres canónicos de la tabla. El doce no aparece | ninguna | pendiente | 14 |
| 33 | La query del preflight aparece en un solo lugar | AST: la constante se asigna una vez y se referencia solo desde la función del preflight | ninguna | pendiente | 14 |
| 34 | `preflight` no contiene ninguna mutation | igual que la 23 | la misma que la 23 | pendiente | 14 |
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

### `check-packaging.sh`

| Nº | Afirmación | Cómo | Brecha | Estado | Origen |
| --- | --- | --- | --- | --- | --- |
| 14 | `plugin.json` existe, pasa `claude plugin validate --strict`, y declara `author` | corre el CLI y exige código cero; lee el JSON con `python3` para exigir `author` | `--strict` es más flaco de lo que suena: **un `SKILL.md` sin `name:` lo pasa limpio**. Medido. Ninguna de las cuarenta y cuatro cubre eso | pendiente | 07 |
| 15 | `dependencies` con exactamente un elemento, `spec-driven-dev`, string y sin constraint | largo uno, tipo `str`, valor exacto | ninguna. Es un literal que vive una sola vez | pendiente | 07 |
| 17 | `install.sh` chequea el intérprete con `python3 -V` y no con `command -v python3`, y su mensaje nombra `xcode-select --install` | tres greps: dos presencias y una ausencia | ninguna | pendiente | 07 |
| 18 | `install.sh` no imprime la key en ninguna ruta, y guarda en `${XDG_CONFIG_HOME:-$HOME/.config}/keiron-planner/linear.key` | ruta literal presente, y ningún `echo`/`printf` cuyo argumento sea la variable de la key | bash no tiene AST barato: un `echo "$*"` que la incluya indirectamente se escapa. **Es la brecha más cara de la tabla**, porque su modo de falla es una credencial en un log | pendiente | 07 |
| 20 | El `README.md` tiene el snippet con `keiron-planner@spec-driven-dev` y nombra `/planner-setup` | dos greps | ninguna | pendiente | 07 |
| 21 | Ningún archivo trackeado matchea `*.key`, y `.gitignore` lo cubre | `git ls-files` sobre **todo lo trackeado**, `vendor/` y `.scratch/` incluidos, más `git check-ignore` sobre una ruta de prueba | ninguna | pendiente | 07 |

### `check-language.sh`

| Nº | Afirmación | Cómo | Brecha | Estado | Origen |
| --- | --- | --- | --- | --- | --- |
| 6 | Los archivos de la columna inglés no tienen prosa en español, y al revés | camina los `.md` con `lang: en`, saca bloques de código y tramos entre backticks, y falla si queda `áéíóúñ¿¡` o su mayúscula | **el sentido inverso no se chequea.** Inglés adentro de un `lang: es` no tiene señal barata y queda para lectura humana | pendiente | 08 |
| 49 | Todo `.md` del árbol del plugin declara `lang:` con valor `en` o `es` | camina los `.md` del árbol, excluidos `vendor/` y `.scratch/`, y exige el campo con valor del conjunto de dos | ninguna | pendiente | 10 |

### `check-py39.sh`

| Nº | Afirmación | Cómo | Brecha | Estado | Origen |
| --- | --- | --- | --- | --- | --- |
| 19 | `linear.py` corre en Python 3.9 | resuelve intérprete en orden `$PY39`, `python3.9`, `/usr/bin/python3` si reporta 3.9.x; falla duro si ninguno. Importa el módulo y corre `--help` de los doce subcomandos | prueba lo que se ejecuta al importar y al parsear argumentos. Una construcción de 3.10 escondida en una rama que solo corre contra la API no se ve | pendiente | 07 |

---

## 6. Dónde y cuándo corren

### Un solo job

`.github/workflows/checks.yml`, sobre `push` a main y sobre `pull_request`, con **un
solo job** que corre `./scripts/check-all.sh`, que a su vez saca la lista de un glob
de `scripts/check-*`.

SDD tiene un job por script, y acá no, por una razón que la sección 4 ya fijó: con un
job por script la lista de checks queda escrita **dos veces**, en el YAML y adentro de
`check-all.sh`, y el día que alguien agregue un check a uno y se olvide del otro, el
check nuevo no corre en algún lado y nadie se entera. Con el glob la lista existe una
vez y agregar un check no toca el YAML nunca.

La granularidad que se pierde la recupera la política de acumular: una corrida roja
igual nombra todas las aserciones violadas. Y el job único es el que necesitan los dos
setup pesados, que se pagan una vez y no seis:

- `npm i -g` del CLI de Claude Code, para el `claude plugin validate --strict` de la 14.
- `actions/setup-python` en 3.9, exportado como `PY39`, para la 19. **Medido**: el
  manifiesto de `actions/python-versions` tiene 32 releases de la serie, la última
  `3.9.25` estable, con binarios para `linux-24.04`, que es lo que hoy es
  `ubuntu-latest`.

El modo de falla que se acepta es que CI dependa de un `npm i -g` que puede fallar por
razones ajenas al repo.

### Verde local y verde en CI significan lo mismo

Es la regla que decide dos cosas que podrían haber ido para otro lado:

- **`claude plugin validate --strict` corre adentro de `check-packaging.sh`**, no como
  un paso suelto del YAML. La única máquina donde este repo importa es una que tiene
  Claude Code instalado, así que la dependencia es gratis en la práctica y el CLI
  ausente es un error honesto, no un caso a soportar.
- **La 19 es un script y no un job**. **Medido**: `/usr/bin/python3` en una Mac con
  Command Line Tools es 3.9.6, y las Command Line Tools son exactamente las que
  `install.sh` ya exige y que la afirmación 17 ya nombra. Así que el intérprete ya
  está puesto en toda máquina del equipo por una dependencia que ya se paga.

Cada excepción a esa regla es una forma de que alguien empuje algo roto.

### Nada de hooks

Un hook es local y se saltea con `--no-verify`.

### Cuándo se escribe cada check

**Cada check nace en la misma task de SDD que construye lo que chequea**, y ahí su
fila pasa de `pendiente` a `viva`. No se escriben todos ahora, que dejaría CI rojo
durante toda la construcción, ni todos al final, que los vuelve una tarea de
verificación que se recorta cuando falta tiempo.

Lo que hace segura esa política es la regla anti-vacuidad de la sección 4: un check
cuya fuente falta falla en vez de pasar.

---

## 7. Las dos afirmaciones que no eran sobre el repo

El 08 dejó una y el 06 dejó su gemela, las dos contra Linear y no contra el repo:
que ningún ticket lleve dos labels `map:<tipo>`, que es la exclusividad que se perdió
al elegir labels planos en vez de label groups, y que ninguna issue de ejecución
lleve label `map`.

**No se pierden y no se chequean contra Linear. Se mueven al adapter.** `ticket:create`
rechaza dos labels de tipo, `issue:create` no tiene ninguna ruta que agregue `map`, y
entonces las dos son afirmaciones sobre `linear.py`: las nuevas 47 y 48.

Es el mismo movimiento que ya había hecho la 45 con el tope de 120 caracteres: en vez
de verificar que nadie escribió un gist largo, hacer que el adapter lo rechace, y
después chequear el adapter. Convierte una invariante de datos en una invariante de
código, que es lo que un check estructural sabe mirar.

**Descartado un `check-linear.sh` que pegue contra la API**: mete una credencial en CI
y ata el verde del build al estado de un workspace que cambia por razones ajenas al
repo.

Lo que se acepta perder está escrito en la brecha de la 47: el check prueba que el
código de rechazo está, no que rechace bien.

---

## 8. La columna de idioma, que no existía

La afirmación 6 no tenía contra qué chequear. La tabla lector → idioma vive en
`08-los-tres-comandos.md`, que es research, y la regla no se puede derivar del
directorio: `map-contract.md` (inglés) y `map-templates.md` (español) son vecinos en
`skills/_shared/`.

**La columna va en el frontmatter del propio archivo, `lang: en` o `lang: es`.** Una
lista central se olvida de actualizar; el frontmatter no se puede olvidar, porque un
archivo nuevo que nace sin él falla la 49. `CONTEXT.md` se queda con la regla en prosa,
que es para humanos, y ninguna de las dos listas es la segunda copia de la otra.

**Medido, y era el riesgo real de esta decisión**: `lang:` en el frontmatter de un
comando o de una skill pasa `claude plugin validate --strict` limpio, y
`skills/_shared/*.md` ni siquiera lo camina como skill. El único lugar donde el campo
rompe es adentro de `plugin.json`, donde `--strict` lo reporta como
`Unknown field 'lang'. Claude Code ignores it at load time.` El manifiesto es JSON y no
prosa, así que no lo necesita.

**El alcance es todo `.md` del árbol del plugin**, `README.md` y `CONTEXT.md`
incluidos. La frontera natural no es el directorio sino si el archivo es prosa: un
`.md` lo es por definición, un `.py` es código con prosa adentro. Dejar afuera a
`README.md` y `CONTEXT.md` sería dejar afuera justo los dos más leídos por humanos, y
el check pasaría a decir "algunos archivos declaran su columna", que no es una
invariante.

**`README.md` va en español**, `lang: es`, junto con `CONTEXT.md` y `CLAUDE.md`. Su
lector es una persona del equipo, y la costumbre del género de los README de GitHub no
le gana a la regla que el glosario ya fijó. El repo es internal, que es lo que dice
"Publicar el plugin fuera de Keiron" en Fuera de alcance. El snippet de instalación no
entra en el conteo porque el detector exenta lo que va entre backticks.

### El detector, y por qué es asimétrico

Detectar español adentro de un archivo en inglés cuesta una clase de caracteres.
Detectar inglés adentro de uno en español no tiene ninguna señal barata. Así que el
check hace la mitad barata y **la otra mitad se escribe como brecha** en vez de
bajarse la afirmación entera. La mitad barata cubre el caso real, que es alguien
escribiendo una explicación en español adentro de una skill.

Los tramos entre backticks y los bloques de código quedan exentos, porque los archivos
en inglés tienen que citar cadenas en español: `map-contract.md` nombra anclas como
`## Decisiones hasta ahora`.

---

## 9. Lo que este documento corrige o empuja

**A `CONTEXT.md`, una cosa, ya bajada.** La tabla de operaciones decía que la salida
del preflight "es un blob opaco que las otras **once** reciben como `--ctx`" y que "un
subcomando invocado sin `--ctx` falla". Son **siete**, no once. El 14 lo tiene medido
en su tabla de la sección 2 (`map:read`, `map:write`, `ticket:block` y
`milestone:create` no lo usan) y su sección 8 dice "ningún subcomando **consumidor**
sabe hacer un preflight". Salió al escribir la afirmación 35, que dice siete: si no se
corregía, `CONTEXT.md` y el check se contradecían.

**Al ticket 08**, dos cosas. Su árbol de archivos dice `scripts/check-*.sh` y pasa a
`scripts/check-*`, con dos extensiones. Y su tabla de idioma por archivo deja de ser
la fuente: la fuente es el frontmatter `lang:` de cada archivo, y esa tabla queda como
el razonamiento de por qué cada uno cae donde cae.

**Al ticket 07**, una: su `README.md` nace con `lang: es`.

**A los tickets 06, 08 y 09**, la contabilidad: seis de las afirmaciones que sus
documentos numeran están retiradas, y dos más lo están a medias. La tabla de la
sección 1 dice cuál reemplaza a cuál. Los research no se reescriben, y por eso la
tabla de la sección 5 mantiene las retiradas visibles con su puntero.

**Lo que queda sin cubrir y no es de nadie**: `claude plugin validate --strict` no
atrapa un `SKILL.md` sin `name:`. Está medido y escrito en la brecha de la 14. Quien
escriba `check-roster.sh` puede cerrarlo casi gratis, porque ya camina `skills/`.

---

## 10. Las afirmaciones chequeables, para quien construya

Siguen la numeración global: 1 a 6 del 08, 7 a 13 del 06, 14 a 21 del 07, 22 a 31 del
09 y del 13, 32 a 41 del 14, 42 a 46 del 04.

47. `ticket:create` rechaza dos labels `map:<tipo>` en la misma issue, con código
    distinto de cero. Es la primera de las dos que el 08 y el 06 habían dejado contra
    Linear, movida al adapter.
48. Ninguna ruta de `issue:create` agrega el label `map`. Es la segunda.
49. Todo `.md` del árbol del plugin declara `lang:` en su frontmatter, con valor `en`
    o `es`. Excluye `vendor/` y `.scratch/`.
50. Los números marcados `viva` en `CHECKS.md` y los `[N]` que emiten los seis scripts
    son el mismo conjunto.

Una quinta candidata murió sola: verificar que el YAML del workflow y `check-all.sh`
listen lo mismo no hace falta cuando la lista existe una sola vez, en un glob.

**El total pasa a cincuenta acuñadas, cuarenta y cuatro vivas y seis retiradas.**

---

## Supuestos

- Todo lo que el 03, el 08 y el 06 supusieron sigue supuesto: un solo team en el
  workspace, un solo conductor por mapa, un mapa de hasta cincuenta tickets, y las
  escrituras atribuidas a quien generó la key.
- **El repo del plugin es `Keiron-HealthTech/keiron-planner`**, que existe y es lo que
  la entrada de marketplace del 07 apunta. Verificado en esta sesión.
- Los checks corren en GitHub Actions. Si el equipo se mudara de CI, la sección 6 se
  reescribe y las cincuenta afirmaciones no se tocan.

## Lo que este documento no decide

- **Cómo se prueba el comportamiento del adapter.** Los checks prueban que el código
  está escrito como dice, nunca que hace lo que dice. Seis brechas de la tabla solo se
  cierran con tests de verdad. Va a la niebla.
- **El contenido de los checks**, o sea el código. Acá está qué verifica cada uno y
  con qué método; escribirlos es trabajo de SDD.
- **Qué pasa cuando una afirmación se contradice con el código que se está
  construyendo.** Hoy la respuesta implícita es que gana la afirmación y el check
  falla, pero no se conversó qué hacer si la afirmación es la que está mal.

## Cómo se verificó

Todo lo que este documento llama medido salió de esta sesión, contra el CLI real:

- `claude plugin validate --strict` sale 1 con warnings y `claude plugin validate`
  sale 0; un manifiesto sin `description` es warning.
- `lang:` en frontmatter de comando y de skill pasa `--strict`; en `plugin.json` no.
- `skills/_shared/*.md` no se camina como skill.
- Un `SKILL.md` sin `name:` pasa `--strict`; uno sin bloque de frontmatter no.
- `/usr/bin/python3` es 3.9.6 con Command Line Tools.
- `actions/python-versions` publica 3.9.25 estable para `linux-24.04`.
- `git remote -v` apunta a `Keiron-HealthTech/keiron-planner`, y `.gitignore` ya cubre
  `*.key`, así que la mitad de la 21 ya es cierta hoy.
