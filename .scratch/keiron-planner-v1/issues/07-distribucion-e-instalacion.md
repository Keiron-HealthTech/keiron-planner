# 07: Distribución, instalación y setup por repo

**Tipo:** `map:grilling` · **Modo:** HITL (`hitl:dev`)
**Bloqueado por:** nada. Tomable ahora.

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
