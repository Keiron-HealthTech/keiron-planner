# La distribución: cómo llega el plugin a la máquina de cada dev

Resolución del ticket [07](../issues/07-distribucion-e-instalacion.md), tipo
`map:grilling`. Cuatro rondas de grilling con el dev leader, diecisiete preguntas,
sesión del 2026-08-27, más nueve mediciones: los docs de plugins de Claude Code y
los de la API de Linear, el CLI `claude plugin`, el estado real del cache de
plugins de esta máquina, y dos sondas construidas y desarmadas.

Este ticket era el último bloqueante del mapa: el [10](../issues/10-que-chequean-los-checks.md)
esperaba por él. Y era el único que decidía cosas que ocurren **antes** de que
alguien abra Claude Code: dónde vive el plugin, cómo llega, y qué tiene que haber
en la máquina para que el primer comando funcione.

Se reparte, igual que el 06 y el 08: la entrada del marketplace va al repo de
`spec-driven-dev`, el manifiesto a `.claude-plugin/plugin.json`, el instalador a
`scripts/install.sh`, el comando a `commands/planner-setup.md`, y las instrucciones
de instalación al `README.md`. Es una fuente, no un archivo destino.

Va en español con los términos canónicos en inglés, por la razón de siempre: su
lector es el dev leader que va a mantener esto.

## Lo que cambió el terreno antes de la primera pregunta

Dos hechos medidos, y sin ellos la mitad de este ticket se hubiera decidido mal.

**El peer dependency dejó de ser una convención documentada.** `plugin.json`
tiene un campo `dependencies` real: un array de nombres, o de objetos
`{name, version, marketplace}` con rangos semver. Claude Code resuelve las
versiones contra tags git de la forma `{plugin-name}--v{version}`, auto-instala las
dependencias al instalar el plugin, las auto-habilita al habilitarlo, se niega a
deshabilitar una dependencia que otro plugin habilitado todavía necesita, y tiene
`claude plugin prune` para las auto-instaladas que quedaron huérfanas. Los errores
son tipados: `dependency-unsatisfied`, `range-conflict`,
`dependency-version-unsatisfied`, `no-matching-tag`. El filo: **una dependencia
declarada que no resuelve deshabilita al plugin que la declara**.

**Las dependencias cross-marketplace están bloqueadas por defecto.** Se habilitan
con `allowCrossMarketplaceDependenciesOn` en el `marketplace.json` del marketplace
**raíz**, que es el que hospeda el plugin que el usuario instala. La confianza no
se encadena a propósito. Y las dependencias que viven en un marketplace que el
usuario no agregó quedan sin resolver, o sea que el plugin queda deshabilitado.

De esos dos hechos sale casi todo lo que decide este documento, incluida la
elección del canal, que sin ellos parecía una cuestión de simetría.

## El canal: `keiron-planner` entra al marketplace de `spec-driven-dev`

No hay marketplace propio. La entrada va en el `marketplace.json` del repo
hermano, apuntando a nuestro repo:

```json
{
  "name": "keiron-planner",
  "description": "Planifica proyectos grandes sobre Linear: mapa de decisiones, frontera y colapso a milestones",
  "source": {
    "source": "github",
    "repo": "Keiron-HealthTech/keiron-planner"
  }
}
```

Sin `version` y sin `ref`, y los dos son a propósito. Ver "El release".

**Por qué al marketplace ajeno y no a uno propio.** Un solo `marketplace add` es
la diferencia entre que PM y Diseño lo instalen y que abran un ticket pidiendo
ayuda. El equipo ya tiene `spec-driven-dev` agregado, así que para la mayoría el
paso de agregar marketplace ya está hecho y la instalación entera es:

```
/plugin install keiron-planner@spec-driven-dev
```

Y lo segundo, que pesa más: con los dos plugins en el mismo marketplace la
dependencia sobre SDD queda **intra-marketplace**, o sea que resuelve y
auto-instala sin `allowCrossMarketplaceDependenciesOn` y sin que nadie tenga que
agregar un segundo marketplace para que el primero funcione. Con marketplace
propio, alguien que instala solo el planner se lleva un plugin deshabilitado por
`dependency-unsatisfied`, y el mensaje habla de un marketplace que todavía no
agregó.

**Descartado: un marketplace nuevo de la org**, `Keiron-HealthTech/claude-plugins`,
que liste los dos por `source` github. Es el nombre correcto y el que se elegiría
si no hubiera nada instalado. Obliga a todo el equipo a agregar un marketplace que
ya tiene puesto, y deja dos marketplaces conociendo al mismo plugin mientras el
viejo siga configurado. Se paga una vez y se paga en la máquina de cada persona.

**El costo aceptado** es que un marketplace llamado `spec-driven-dev` hospede dos
plugins. Es cosmético y vive en un archivo que casi nadie abre.

### La PR al repo hermano

Entrar a un marketplace ajeno pide una PR ahí, **una sola vez**. Su alcance:

- La entrada en `.claude-plugin/marketplace.json`.
- Una línea en el `README.md` de SDD que diga que ese marketplace hospeda dos
  plugins, con el snippet de instalación del planner.

**No toca la skill `using-sdd`**, que hoy lista `superpowers` y `engram` como peer
dependencies. La dirección de la dependencia es planner hacia SDD; hacer que las
skills de SDD nombren al planner la invierte y le mete contexto a todo el que use
SDD sin mapear.

## La dependencia sobre SDD, declarada de verdad

En `.claude-plugin/plugin.json`:

```json
"dependencies": ["spec-driven-dev"]
```

Sin constraint de versión, y como string pelado.

**Por qué declararla.** El destino de este plugin es un traspaso. Un mapa
colapsado en issues que nadie puede construir es media herramienta, y prefiero que
la presencia de SDD la garantice el mecanismo antes que un párrafo de `CONTEXT.md`.
Al instalar el planner, SDD se auto-instala; al habilitarlo, se auto-habilita.

**El modo de fallo que se acepta**: si alguien desinstala SDD, el planner queda
deshabilitado con `dependency-unsatisfied`. El mensaje dice qué correr para
arreglarlo. En el otro sentido el mecanismo protege: deshabilitar SDD con el
planner habilitado está bloqueado, y el error trae el comando encadenado que apaga
los dos.

**Por qué sin constraint, y esto es medido.** SDD **no** tiene tags con la
convención que Claude Code necesita: tiene `v1.1.0` y `v1.2.0`, y su `plugin.json`
dice `1.3.0` sin tag ninguno. Su entrada de marketplace es `source: "./"`, o sea
ruta relativa, y para ese caso Claude Code instala la copia actual del marketplace
cuando no hay tag que satisfaga el rango, y chequea el constraint al cargar. Un
constraint hoy no se resolvería por tag y solo compraría el modo de fallo
`dependency-version-unsatisfied`, que también nos deshabilita, sin comprar
protección mientras los dos plugins sean nuestros y se muevan juntos.

**Nota que no es de este ticket.** Los tags de SDD están fuera de la convención
`{plugin-name}--v{version}`. Es un problema del repo hermano el día que alguien
quiera constreñir su versión, y hasta entonces no hace daño.

## El release: tags, versión y orden de publicación

**La convención de tags es `keiron-planner--v{version}`**, creada con
`claude plugin tag --push`.

Medido con una sonda: un repo git de juguete con solo `.claude-plugin/plugin.json`
adentro. `claude plugin tag --dry-run` derivó `keiron-planner--v0.1.0` de la
versión del manifiesto, **sin necesitar una entrada de marketplace alrededor**, y
avisó de paso que faltaba `author`. Eso es lo que hace viable el canal elegido:
publicar una versión no toca el repo de SDD.

Por eso la entrada del marketplace va **sin `version`**: si declarara la versión,
cada release nuestro pediría una PR al repo hermano para mantenerlas de acuerdo. Y
va **sin `ref`**, así la instalación sigue la rama por defecto de nuestro repo.

**La versión inicial es `0.1.0`.** Dice la verdad sobre algo cuyo primer milestone
todavía es un tracer bullet. SDD llegó a 1.x después de tres versiones de uso real.

**El orden de publicación**, y es la parte con consecuencia para el colapso:

1. El plugin existe en la rama por defecto de `Keiron-HealthTech/keiron-planner`,
   con `.claude-plugin/plugin.json` adentro.
2. `claude plugin tag --push` crea `keiron-planner--v0.1.0`.
3. Recién entonces, la PR al repo de SDD con la entrada del marketplace.

**La PR no va primero.** Una entrada viva apuntando a un repo sin
`.claude-plugin/` no reserva un lugar: publica una falla. No auto-instala a nadie,
pero el plugin aparece en el `/plugin` de todo el equipo y el primero que lo toque
se lleva un clon sin plugin adentro. Medido: el repo existe, es `INTERNAL`, está
vacío y todavía no tiene rama por defecto.

**Para el colapso**: la PR al repo hermano es la última tarea del último milestone,
y no una tarea de infraestructura del primero.

## La credencial: Personal API key, y OAuth a la niebla

La pregunta que este ticket tenía que cerrar, abierta desde el 01. La respuesta es
**Personal API key para la v1**.

Lo medido contra los docs de Linear:

| | Personal API key | OAuth 2.0 |
| --- | --- | --- |
| Requests por hora, por usuario | 5.000 | 5.000 |
| Complejidad por hora, por usuario | 3.000.000 | 2.000.000 |
| Techo por query | 10.000 | 10.000 |
| Header | `Authorization: <key>` | `Authorization: Bearer <token>` |
| Vida del token | no expira, se revoca a mano | 24 horas, con refresh |
| Qué hace falta para obtenerla | abrir Settings y copiar | app registrada, redirect URI, servidor de callback |
| Device flow | no aplica | **no existe** |
| Autoría de lo que escribe | la persona | la persona con `actor: user`, la app con `actor: app` |

Tres cosas de esa tabla decidieron:

**No hay device flow.** OAuth con PKCE evita el client secret, pero el redirect URI
sigue siendo obligatorio, así que hay que levantar un servidor local en un plugin
cuya regla es stdlib pelado y cero dependencias. Sumado al refresh de 24 horas, es
código con estado, y estado es lo que este plugin viene evitando en todas las
decisiones anteriores.

**El presupuesto va al revés de lo que suponíamos.** La key personal tiene un 50%
más de complejidad por hora que OAuth. El [02](../issues/02-api-documents-linear.md)
ya había medido que el presupuesto por hora es irrelevante para nuestro uso, así
que esto no elige por nosotros, pero elimina el argumento de rendimiento que
alguien podría traer a favor de OAuth.

**La autoría.** El [08](08-los-tres-comandos.md) contó con que el comentario de
resolución "gana autor y timestamp gratis". OAuth con `actor: app` se lo saca: los
comentarios los firmaría el plugin. Con `actor: user` la autoría se mantiene, pero
entonces OAuth solo compra scopes y revocación centralizada, que para un equipo
interno con un conductor por mapa no paga un servidor de callback.

**OAuth va a la niebla, no a fuera de alcance.** Vuelve el día que el plugin
escriba como app y no como persona, que es un cambio de producto y no una mejora
técnica: alguien va a querer que el mapa lo mantenga un bot y no una cuenta
humana. Ese día la pregunta se reabre con la respuesta de este ticket ya escrita.

## El setup, que es por máquina y no por repo

**No existe setup por repo.** El título de este ticket decía "setup por repo"
porque el mapa asumió un equivalente de `setup-matt-pocock-skills`. De esa
responsabilidad ya no queda nada:

- El [03](../issues/03-seis-operaciones-en-linear.md) sacó el caché de ids: el
  `teamId`, los dos de estado y los ocho de label se resuelven en cada sesión,
  porque la fuente de verdad es Linear.
- El 03 mandó los ocho labels al **preflight**, idempotente y solo los que falten,
  y midió que una Personal API key alcanza para crearlos workspace-level sin rol de
  admin.
- El [08](08-los-tres-comandos.md) decidió que el mapa entra por **URL de Linear**
  como `$ARGUMENTS`, y que el plugin nunca lo busca por cuenta propia.

No queda estado por repo que escribir. El plugin no tiene `docs/agents/*.md` ni
nada parecido, y el setup es **por máquina** con una sola responsabilidad: la key.

### `/planner-setup`

Un comando, `commands/planner-setup.md`, que corre
`${CLAUDE_PLUGIN_ROOT}/scripts/install.sh`.

**El nombre.** Los otros cinco comandos se llaman por lo que operan, y este no
toca ningún mapa: configura el plugin en una máquina. `/map-setup` haría creer que
configura un mapa, que es justo lo que no hace. `/keiron-planner-setup` repite el
nombre del plugin, que la UI de `/plugin` ya muestra al lado.

**El alcance: solo la key**, con los tres modos que el prototipo del 01 ya validó
(interactivo, `--verify`, `--remove`), incluida la validación de la credencial
contra la API trayendo `viewer` y `organization` antes de guardarla.

No chequea la forma del workspace. El 03 decidió no cachear nada precisamente
porque la fuente de verdad es Linear, y un chequeo de forma en el instalador valida
un estado que cambia cinco minutos después: son dos verdades y la vieja gana por
estar escrita. El preflight es el dueño de eso y ya está decidido que falla
temprano y claro.

**El disparo.** Un comando y nada más. Medido: **no hay post-install hook** en
`plugin.json`.

Descartado, un hook `SessionStart` que detecte la key faltante: hablaría en toda
sesión de todo repo aunque nadie esté mapeando, y no podría pedirla igual, porque
el instalador exige TTY y se niega sin él. El aviso de key faltante lo da el
preflight, que es donde el aviso importa.

Descartado, una instrucción en el README para correr el script a mano: la ruta real
es `~/.claude/plugins/cache/spec-driven-dev/keiron-planner/<version>/scripts/install.sh`,
y eso no es una instrucción que se le pueda dar a Diseño.

### Dónde vive la key, y dos casas descartadas

Se queda donde el 01 la puso: `${XDG_CONFIG_HOME:-~/.config}/keiron-planner/linear.key`,
`0600`, con el directorio `0700`, fuera de todo repo.

**Descartado `userConfig` del plugin.** El manifiesto puede declarar opciones de
usuario, y `claude plugin install --config key=value` las setea por el mismo camino
que `/plugin configure`. Deja una credencial en un `settings.json` que puede
terminar commiteado.

**Descartado `${CLAUDE_PLUGIN_DATA}`**, o sea `~/.claude/plugins/data/{id}/`, que
existe para datos que sobreviven a los updates. La key no es dato del plugin: es de
la persona, y sobrevive a desinstalarlo.

## El intérprete: Python 3.9

El adapter es `scripts/linear.py` con stdlib pelado y el instalador es `sh` más
`curl` más `python3`, así que el intérprete es requisito del plugin entero y no
solo del instalador.

**El plugin apunta al `python3` del sistema y `linear.py` es compatible con 3.9.**
Medido en la máquina del dev leader: `/usr/bin/python3` es **3.9.6**. La única
forma de que PM y Diseño no tengan que instalar nada es usar el intérprete que ya
está. El costo es concreto y acotado: sin `match`, y sin uniones `X | Y` en
anotaciones salvo con `from __future__ import annotations`. Nada de eso lo necesita
un script que arma queries y parsea JSON.

Descartado sacar Python del camino con `curl` más `jq`: cambia una decisión del 08
a cambio de depender de `jq`, que macOS no trae.

**El caso del Mac sin Command Line Tools.** En macOS `/usr/bin/python3` existe como
stub aunque las CLT no estén instaladas, y recién al ejecutarlo salta el diálogo
del sistema. El prototipo del 01 chequea con `command -v python3`, así que hoy
pasaría el chequeo y fallaría después: exactamente el modo de fallo que el 01 quiso
evitar.

**El instalador chequea ejecutando `python3 -V` y parseando la versión**, no con
`command -v`, y cuando eso falla el mensaje nombra el caso: faltan las herramientas
de línea de comandos, correr `xcode-select --install`.

Esto último es comportamiento conocido de macOS y no una medición: esta máquina
tiene las CLT puestas, así que el stub no se pudo observar.

## El repo sin Linear, que se disuelve

La pregunta original era qué pasa si alguien instala el plugin en un repo sin
Linear, dado que no soportamos tracker local. No pasa nada, y no hay nada que
construir para eso.

**El plugin es workspace-scoped, no repo-scoped.** No lee el repo para nada salvo
el puntero del glosario de dominio, el mapa entra por URL, y la credencial es de
máquina. El instalador no se niega a correr fuera de un repo git porque no tiene
por qué saber dónde lo corrieron.

Los dos fallos posibles ya tienen dueño: sin key, falla el preflight, temprano y
claro; sin URL, `/map-work` pregunta y para, que es lo que el 08 ya decidió.

## El repo central de dominio

El [05](../issues/05-adaptar-las-tres-disciplinas.md) decidió que el glosario
canónico vive en un repo central del CRM y que cada repo lo alcanza con un puntero
de una línea en su `CLAUDE.md`. Lo que quedaba abierto acá era cómo el plugin
resuelve dónde está.

**Lee ese puntero, y no agrega una superficie de config nueva.** Cumple con "es
config, no descubrimiento", que es como el 05 lo pidió: el puntero es config
versionada del repo y viaja con él, no una búsqueda. Cuando falta, la skill procede
en silencio y no sugiere crear nada, que es la regla que el 05 tomó de CRM-3308.

Descartada una config global al lado de la key: obligaría a cada dev a ponerla a
mano y quedaría desincronizada del repo que sí sabe la respuesta.

## Qué se publica

El repo que se clona en la máquina de cada dev es este, entero. Hoy tiene tracked
`vendor/mattpocock-skills` (164 archivos, 1 MB, el clon de Matt en `6654f6b`) y
`.scratch/keiron-planner-v1` con el mapa y sus research. **Los dos se publican.**

El riesgo grande era que los `SKILL.md` de `vendor/` se cargaran en el contexto de
todo el equipo. **Medido con una sonda, y no ocurre.** Armé un plugin de juguete
con un `SKILL.md` en `skills/` y otro colgado de
`vendor/mattpocock-skills/skills/productivity/grilling/`, lo publiqué en un
marketplace local descartable, lo instalé en scope local y le pedí el inventario
con `claude plugin details`. El anidado no aparece: solo se descubren los de
`skills/` en la raíz del plugin. La sonda quedó desinstalada y el marketplace
removido.

Lo que queda entonces es 1 MB de disco por dev y cero tokens, y a cambio:

- `vendor/` es la fuente primaria y la base de la atribución MIT que `CONTEXT.md`
  ya declara. Tenerlo en el commit exacto es lo que hace verificable de dónde salió
  cada disciplina.
- El mapa en `.scratch/` es el registro de cómo se decidió el plugin, trazado con
  el método que el plugin implementa. Borrarlo del repo publicado sería tirar el
  único ejemplo trabajado que existe.

**Hallazgo lateral de la sonda, y es para el 10**: el inventario de
`claude plugin details` mete los comandos en la fila "Skills". No sirve como
chequeo estructural de cuántos comandos tiene el plugin; hay que contar archivos.

## El árbol de archivos, con lo que agrega este ticket

Sobre el árbol que fijó el 08:

```
keiron-planner/
├── .claude-plugin/
│   └── plugin.json               nuevo: name, version 0.1.0, author, dependencies
├── commands/
│   ├── map-new.md
│   ├── map-work.md
│   ├── map-collapse.md
│   ├── map-status.md
│   ├── grill.md
│   └── planner-setup.md          nuevo: ROUTE a scripts/install.sh, sin skill
├── skills/
├── scripts/
│   ├── linear.py                 compatible con 3.9
│   ├── LINEAR-OPERATIONS.md
│   ├── install.sh                el prototipo del 01, con el chequeo de python3 -V
│   └── check-*.sh                del 10
├── README.md                     nuevo: el snippet de instalación y /planner-setup
├── LICENSE                       nuevo: MIT, por la atribución que CONTEXT.md declara
├── CONTEXT.md
├── vendor/                       se publica
└── .scratch/                     se publica
```

`commands/` pasa de cinco archivos a seis. `planner-setup.md` no tiene skill, por
la misma razón que `map-status.md` no la tiene: no hay disciplina que conducir, hay
un script que correr.

## Las afirmaciones chequeables, para el ticket 10

El 08 dejó seis, numeradas 1 a 6, y el 06 agregó siete, numeradas 7 a 13. Estas
siguen desde ahí.

14. `.claude-plugin/plugin.json` existe, valida con `claude plugin validate`, y
    declara `author`.
15. `plugin.json` declara `dependencies` con exactamente un elemento,
    `spec-driven-dev`, como string y sin constraint de versión.
16. `commands/` tiene **seis** archivos, y `planner-setup.md` no tiene skill
    correspondiente: no existe `skills/planner-setup/`.
17. `scripts/install.sh` chequea el intérprete ejecutando `python3 -V` y no con
    `command -v python3`, y su mensaje de fallo nombra `xcode-select --install`.
18. `scripts/install.sh` no imprime la key en ninguna ruta de ejecución, y guarda
    en `${XDG_CONFIG_HOME:-$HOME/.config}/keiron-planner/linear.key`.
19. `scripts/linear.py` corre en Python 3.9: sin `match` y sin uniones `X | Y` en
    anotaciones salvo con `from __future__ import annotations`.
20. El `README.md` tiene el snippet de instalación con
    `keiron-planner@spec-driven-dev` y nombra `/planner-setup`.
21. Ningún archivo tracked del repo matchea `*.key`, y `.gitignore` lo cubre.

La 21 es la única que chequea una ausencia. Vale la pena igual: el costo de que
falle una vez es una credencial en un repo internal.

## Lo que este documento corrige

**Al 08, dos cosas**, ya bajadas a [`08-los-tres-comandos.md`](08-los-tres-comandos.md):
el árbol de archivos gana `commands/planner-setup.md`, `.claude-plugin/plugin.json`,
`README.md` y `LICENSE`; y su afirmación chequeable número 2 pasa de cinco archivos
en `commands/` a seis.

**A `CONTEXT.md`, dos cosas**, ya bajadas: la tabla de comandos gana
`/planner-setup`, y la sección de Dependencias deja de decir que el peer dependency
es una convención para decir cómo se declara de verdad y en qué marketplace vive el
plugin.

**Al mapa**, una: `CONTEXT.md` decía que el plugin "declara `spec-driven-dev` como
peer dependency" cuando el mecanismo no existía. Ahora existe y se usa.

## Supuestos

**Que `source: github` alcanza un repo `internal` con las credenciales de git de
quien instala.** La evidencia a favor está medida: el marketplace de SDD en
`~/.claude/plugins/marketplaces/spec-driven-dev` es un clon git con `origin` en
HTTPS, y el cache del plugin instalado también tiene `.git`. Pero eso está probado
para el repo del **marketplace**, no para un plugin traído por `source` desde otro
repo. No se pudo medir sin crear el repo antes o instalar una copia de prueba de
SDD en el entorno del dev leader. **Se verifica la primera vez que alguien
instala**, y si pidiera un token el arreglo es una línea: cambiar `source: github`
por `source: url` con la URL `.git` completa, que usa el credential helper.

**Que todo el equipo está en macOS.** El instalador es POSIX `sh` y no asume shell,
pero el chequeo del intérprete y el mensaje de `xcode-select --install` sí asumen
macOS. En Linux el mensaje va a estar fuera de lugar sin ser dañino.

**Que la PR al repo de SDD se acepta.** Es nuestro repo, así que es un supuesto
sobre nosotros mismos.

## Lo que este documento no decide

**Cómo se actualiza el plugin.** El auto-update está apagado por defecto en
marketplaces que no son de Anthropic, y en esta máquina el marketplace de SDD ya
tiene `autoUpdate: true`, así que el planner va a viajar con esa configuración sin
que nadie decida nada. No hay decisión que tomar hasta que alguien se queje.

**Qué pasa cuando el plugin se publique fuera de Keiron.** Está en Fuera de
alcance del mapa y sigue estándolo.

**Los tags de SDD.** Fuera de la convención, y es del repo hermano.

## Cómo se verificó

Los docs de plugins de Claude Code (`plugins-reference`, `plugin-dependencies`,
`plugin-marketplaces`) y los de la API de Linear (OAuth 2.0, GraphQL, rate
limiting). Sobre la máquina: `claude plugin --help` y los `--help` de `install`,
`uninstall`, `marketplace`, `details` y `prune`; `known_marketplaces.json` e
`installed_plugins.json`; los tags y el `marketplace.json` de `../spec-driven-dev`;
`gh repo view` sobre el repo nuevo; y `/usr/bin/python3 -V` con `xcode-select -p`.

Dos sondas construidas y desarmadas:

1. **El tag sin marketplace**: repo git de juguete con solo `plugin.json`, y
   `claude plugin tag --dry-run` para ver de dónde deriva el nombre del tag.
2. **El inventario de componentes**: plugin de juguete con un `SKILL.md` en la raíz
   y otro anidado bajo `vendor/`, publicado en un marketplace local, instalado en
   scope local, inventariado con `claude plugin details`, y después desinstalado con
   el marketplace removido.
