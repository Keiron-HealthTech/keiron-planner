# 07: Distribución e instalación

**Tipo:** `map:grilling` · **Modo:** HITL (`hitl:dev`)
**Estado:** **RESUELTO** el 2026-08-27.
**Bloqueado por:** nada.
**Tomado por:** Luis Felipe Jaña (`hitl:dev`), sesión del 2026-08-27.

> El título decía "Distribución, instalación y setup por repo". El setup por repo
> no existe. Ver la resolución.

## Pregunta

SDD se instala desde un marketplace propio en `Keiron-HealthTech/spec-driven-dev`.
Este plugin es un repo aparte. ¿Cómo llega a la máquina de cada dev?

Preguntas que cuelgan de esta:

- Marketplace propio o se agrega al de spec-driven-dev.
- Cómo se declara y se verifica el peer dependency con SDD, dado que hoy es una
  convención documentada y no un mecanismo real.
- Qué hace el setup por repo, que es nuestro equivalente de
  `setup-matt-pocock-skills`: qué configura, dónde deja la config, y si hace
  falta cuando el tracker es siempre Linear.
- Qué pasa si alguien lo instala en un repo sin Linear, dado que decidimos no
  soportar tracker local.
- **Agregado por el ticket 05**: cómo resuelve el plugin dónde está el repo
  central de dominio. Es config, no descubrimiento, y el plugin tiene que
  funcionar igual cuando ese repo todavía no existe.

## Agregado por el ticket 01

El setup tiene que **pedir la API key de Linear y guardarla el propio script**, no
documentar cómo hacerlo a mano. La razón es quién lo corre: el plugin lo van a
instalar PM y Diseño, no solo devs, así que "exportá esta variable de entorno en
tu shell" no es una instrucción que se pueda dar.

Forma validada en la sesión del ticket 01, con el prototipo en
[`research/01-scripts/install.sh`](../research/01-scripts/install.sh):

- POSIX `sh`, no bash ni fish, porque no sabemos qué shell usa quien lo corre.
- La key se **valida contra la API antes de guardarla**. Una key mal pegada tiene
  que fallar en el instalador con un mensaje que se entienda, no diez minutos
  después en medio de una sesión de mapa.
- Vive en `${XDG_CONFIG_HOME:-~/.config}/keiron-planner/linear.key`, con `0600`
  y el directorio `0700`. Fuera de todo repo, así que ningún commit la puede
  filtrar.
- Entrada sin eco, para que no quede en el scrollback de la terminal.
- Modos `--verify` y `--remove`, porque revocar es parte del ciclo de vida de una
  credencial y nadie se acuerda de hacerlo a mano.

**Queda abierto acá**: si la v1 usa Personal API key o OAuth. La key personal
carga cada acción del plugin sobre la persona que la generó y hay que rotarla a
mano; OAuth es la respuesta correcta a plazo pero pide una app registrada y un
servidor de callback. Es la pregunta de distribución que este ticket tiene que
cerrar.

## Agregado por el ticket 03

**El setup se encogió.** El 03 decidió que los ids que las operaciones necesitan,
el `teamId`, los dos de estado y los ocho de label, se resuelven en cada sesión y
**no se cachean**, porque la fuente de verdad es Linear. Eso saca del setup todo lo
que no sea la key: un caché acá compra milisegundos y paga con un modo de fallo que
solo aparece cuando alguien tocó el workflow del team.

Los ocho labels los crea el **preflight**, no el setup, idempotente y solo los que
falten. Medido con autorización: una Personal API key puede crear labels
workspace-level, y no hace falta permiso de admin. Así que el setup no tiene que
pedir un rol especial ni documentar un prerequisito manual.

Queda entonces con una sola responsabilidad, la key, que es la forma que ya
validó el prototipo del ticket 01. Y la pregunta abierta de este ticket sigue
siendo la misma: Personal API key contra OAuth.

## Hecho cuando

Está decidido el canal de distribución y qué configura el setup, con el caso
del repo sin Linear resuelto de alguna forma, aunque sea fallar temprano y
claro, y con Personal API key contra OAuth resuelto.

## La decisión

El documento completo es [`research/07-distribucion.md`](../research/07-distribucion.md).
Se reparte: la entrada del marketplace al repo de `spec-driven-dev`, el manifiesto
a `.claude-plugin/plugin.json`, el instalador a `scripts/install.sh`, el comando a
`commands/planner-setup.md`, y el snippet de instalación al `README.md`.

Cuatro rondas de grilling, diecisiete preguntas, frontera del árbol vacía, más
nueve mediciones y dos sondas construidas y desarmadas.

**El peer dependency dejó de ser una convención documentada.** `plugin.json` tiene
un campo `dependencies` real, con semver resuelto contra tags git
`{plugin-name}--v{version}`, auto-instalación al instalar y auto-habilitación al
habilitar. Ese hecho, más que las dependencias cross-marketplace están bloqueadas
por defecto, decidió el canal: lo que parecía una cuestión de simetría con SDD era
una cuestión de cuántos marketplaces tiene que agregar quien instala.

**El canal es el marketplace de `spec-driven-dev`.** `keiron-planner` entra ahí con
`source: {source: "github", repo: "Keiron-HealthTech/keiron-planner"}`, sin
`version` y sin `ref`. Un solo `marketplace add` para el equipo, que en la mayoría
de las máquinas ya está hecho, y la dependencia sobre SDD queda intra-marketplace,
o sea que resuelve y auto-instala sin `allowCrossMarketplaceDependenciesOn`.
Descartado un marketplace propio, que dejaría a quien instala solo el planner con
un plugin deshabilitado por `dependency-unsatisfied`; descartado un marketplace
nuevo de la org, que obliga a todo el equipo a re-agregar lo que ya tiene puesto.

**La dependencia se declara de verdad**, `"dependencies": ["spec-driven-dev"]`, sin
constraint. Medido: SDD no tiene tags con la convención que Claude Code necesita
(tiene `v1.1.0` y `v1.2.0`, y su `plugin.json` dice 1.3.0 sin tag), así que un
constraint solo compraría el modo de fallo `dependency-version-unsatisfied`, que
deshabilita al planner, sin comprar protección.

**La credencial es Personal API key**, y OAuth va a la niebla. Linear no tiene
device flow, así que OAuth pide levantar un servidor de callback en un plugin cuya
regla es stdlib pelado, y sumarle refresh de 24 horas. Medido además que la key
tiene 3.000.000 de complejidad por hora contra 2.000.000 de OAuth, o sea que el
argumento de rendimiento va al revés de lo que suponíamos. Y OAuth con `actor: app`
le saca a la persona la autoría del comentario de resolución, con la que el 08 ya
contaba.

**No existe setup por repo.** El 03 sacó el caché de ids y mandó los ocho labels al
preflight; el 08 decidió que el mapa entra por URL. No queda estado por repo que
escribir. El setup es por máquina, con una sola responsabilidad, la key, y su
puerta es un comando nuevo, `/planner-setup`, que corre
`${CLAUDE_PLUGIN_ROOT}/scripts/install.sh`. No chequea la forma del workspace: ese
es el trabajo del preflight, y duplicarlo crea dos verdades.

**El repo sin Linear se disuelve.** El plugin es workspace-scoped, no repo-scoped:
no lee el repo salvo el puntero del glosario de dominio, el mapa entra por URL y la
credencial es de máquina. Los dos fallos posibles ya tienen dueño: sin key falla el
preflight, sin URL `/map-work` pregunta y para.

**El intérprete es el `python3` del sistema y `linear.py` va compatible con 3.9**,
que es lo que trae macOS (medido: `/usr/bin/python3` es 3.9.6). Es la única forma
de que PM y Diseño no tengan que instalar nada. Y el instalador pasa a chequear con
`python3 -V` en vez de `command -v python3`, porque en un Mac sin Command Line
Tools el stub existe y el chequeo actual pasaría para fallar después.

**Se publica todo, incluidos `vendor/` y `.scratch/`.** Medido con una sonda: los
`SKILL.md` anidados bajo `vendor/` no se descubren, solo los de `skills/` en la
raíz del plugin. El costo es 1 MB de disco por dev y cero tokens, contra la
atribución verificable y el único mapa trabajado que existe.

## Por qué

**Un solo `marketplace add`** es la diferencia entre que PM y Diseño instalen el
plugin y que abran un ticket pidiendo ayuda. Este plugin se instala fuera del
equipo de desarrollo por diseño, y eso ya venía decidiendo cosas desde el 01: el
instalador pide la key en vez de documentar cómo exportarla, y ahora elige el canal.

**El mecanismo antes que el párrafo.** El destino del plugin es un traspaso a SDD.
Un mapa colapsado en issues que nadie puede construir es media herramienta, así que
la presencia de SDD la garantiza `dependencies` y no una línea de `CONTEXT.md`. El
costo aceptado está nombrado: si alguien desinstala SDD, el planner queda
deshabilitado con un mensaje que dice cómo arreglarlo.

**Publicar una entrada de marketplace antes de que el plugin exista no reserva un
lugar: publica una falla.** De ahí sale el orden de publicación, que es una
consecuencia para el colapso y no una nota de proceso: la PR al repo hermano es la
última tarea del último milestone.

**Nada que instalar a mano.** El intérprete del sistema, `sh` y `curl` son lo que
ya está en la máquina. La única concesión es escribir `linear.py` sin `match` y sin
uniones `X | Y` en anotaciones, que un script que arma queries y parsea JSON no
necesita.

## Niebla graduada

Ninguna. Este ticket no vació ningún parche de "Aún no especificado": la
distribución era un tramo del camino ya trazado.

**Pero agrega uno**: OAuth contra Personal API key, que este ticket cierra para la
v1 y manda a la niebla para cuando el plugin tenga que escribir como app y no como
persona.

## Tickets nuevos

Ninguno. La resolución no abrió preguntas que no pudiera contestar ella misma.

**Queda desbloqueado el [10](10-que-chequean-los-checks.md)**, que esperaba por el
06 y por este. Era el último ticket bloqueado del mapa.

## Qué corrige o empuja

**Al 08**, dos cosas, ya bajadas a
[`research/08-los-tres-comandos.md`](../research/08-los-tres-comandos.md): el árbol
de archivos gana `commands/planner-setup.md`, `.claude-plugin/plugin.json`,
`README.md` y `LICENSE`, y su afirmación chequeable número 2 pasa de cinco archivos
en `commands/` a seis.

**A `CONTEXT.md`**, dos cosas, ya bajadas: la tabla de comandos gana
`/planner-setup`, y la sección de Dependencias deja de decir que el peer dependency
es una convención documentada para decir cómo se declara y en qué marketplace vive
el plugin.

**Al prototipo del 01**, una: `install.sh` chequea el intérprete con `python3 -V` y
no con `command -v python3`, y su mensaje de fallo nombra `xcode-select --install`.
Es el mismo modo de fallo que ese ticket quiso evitar, en un lugar que no había
mirado.

**Al ticket 10**, que hereda ocho afirmaciones chequeables nuevas, numeradas de la
14 a la 21, más un hallazgo: `claude plugin details` mete los comandos en la fila
"Skills" de su inventario, así que no sirve como chequeo estructural de cuántos
comandos hay. Hay que contar archivos.

**Al colapso**, una consecuencia de orden: la PR al repo de `spec-driven-dev` es la
última tarea del último milestone, no una tarea de infraestructura del primero.
