# 10: Qué chequean los checks estructurales

**Tipo:** `map:grilling` · **Modo:** HITL (`hitl:dev`) · **RESUELTO** el 2026-08-27
**Tomado por:** Luis Felipe Jaña (`hitl:dev`), sesión del 2026-08-27.
**Bloqueado por:** nada. Tomable ahora. (El 04, el 06, el 07, el 09, el 13 y el 14
se resolvieron el 2026-08-27 y entre los seis le dejaron **cuarenta y seis**
afirmaciones chequeables, numeradas de la 1 a la 46 y repartidas por los research:
1 a 6 del [08](08-los-dos-modos-keironizados.md), 7 a 13 del
[06](06-que-hace-map-collapse.md), 14 a 21 del
[07](07-distribucion-e-instalacion.md), 22 a 31 del
[09](09-concurrencia-humano-plugin.md) y del
[13](13-pestana-abierta-pisa-al-plugin.md), 32 a 41 del
[14](14-preflight-por-invocacion.md), y 42 a 46 del
[04](04-prototipo-mapa-en-linear.md). Tres están reemplazadas y no se cuentan dos
veces: la 10 por la 22, la 22 por la 32, y la 9 por la 43.)
**Origen:** graduado desde la niebla al resolver el [08](08-los-dos-modos-keironizados.md).

## Pregunta

La decisión de encuadre del mapa dice que la verificación son checks
estructurales sobre el repo, al estilo de los `scripts/check-*.sh` de SDD, y nada
de verificar comportamiento conversacional. Hasta ahora eso no se podía
precisar, porque no existía la estructura del plugin. El 08 la fijó.

## Por qué graduó de la niebla

El parche decía literal que dependía de que existiera la estructura del plugin.
El 08 escribió el árbol de archivos completo, el contrato de tokens, las dos
plantillas y el reparto de las ocho operaciones, así que ahora hay algo que
contar.

## Lo que otros tickets ya dejaron listo, y este no re-deriva

Las cuarenta y una afirmaciones viven al final del research de cada ticket que las
escribió. Las seis primeras, del 08, van acá como muestra de la forma; las demás se
leen en su lugar y no se copian.

Seis afirmaciones chequeables, en
[`research/08-los-tres-comandos.md`](../research/08-los-tres-comandos.md):

1. El conjunto de tokens de `map-contract.md` es exactamente el que emiten los
   comandos. Cinco, ni uno más.
2. `commands/` tiene cinco archivos, y los tres que rutean apuntan a una skill
   que existe.
3. `map-status.md` dice `ROUTE: read-only` y no existe `skills/map-status/`.
4. `map-templates.md` tiene los cinco encabezados del DD y las cinco secciones
   del comentario, con texto exacto. (Reemplazada dos veces: el 06 la llevó a seis
   encabezados y le sumó las tres secciones de la issue de ejecución, y el 04 llevó
   el comentario a **seis** secciones. Ver la afirmación 43.)
5. `scripts/linear.py` tiene un subcomando por cada una de las ocho operaciones
   nombradas en `LINEAR-OPERATIONS.md`, y ninguno de más. (Reemplazada dos veces:
   el 09 la llevó a once y el 14 a **doce**, con `preflight` adentro. Ver la
   afirmación 32.)
6. Los archivos de la columna inglés no tienen prosa en español, y al revés.

## Preguntas que cuelgan de esta

- **La que el 08 no pudo contestar**: que ningún ticket lleve dos labels
  `map:<tipo>` es la exclusividad que se perdió al elegir labels planos en vez de
  label groups. Se chequea contra Linear y no contra el repo, así que no es un
  check estructural en el sentido de la decisión de encuadre. Hay que decidir si
  entra igual, si vive en otro lado, o si se acepta perderla.
- Si los checks corren en CI, en un hook, o a mano.
- Qué agrega el 06 al árbol cuando escriba `/map-collapse`, y qué agrega el 07
  con la instalación. (Contestada: los dos se resolvieron el 2026-08-27, y también
  el 04, el 09, el 13 y el 14. Lo que queda es ordenar sus cuarenta y seis
  afirmaciones, no descubrirlas.)
- Si un check que falla rompe el build o solo avisa.

## Hecho cuando

Está escrita la lista de checks con lo que verifica cada uno, y resuelto el caso
del label de tipo duplicado, aunque sea aceptando perderlo.

---

# Resolución

Cinco rondas de grilling, veinticinco preguntas, frontera del árbol vacía.
Deliverable: [`research/10-los-checks.md`](../research/10-los-checks.md).

## La decisión

**Seis scripts, un job de CI, y cuarenta y cuatro afirmaciones vivas de cincuenta
acuñadas.** La tabla completa, con qué verifica cada check y qué brecha deja, está
en la sección 5 del deliverable.

El reparto es `check-roster.sh` (igualdades de conjuntos sobre el árbol),
`check-templates.sh` (texto exacto), `check-adapter.py` (el AST de `linear.py`),
`check-packaging.sh` (manifiesto, instalador y repo), `check-language.sh` (la
columna de idioma) y `check-py39.sh`. Más `check-common.sh`, que los seis sourcean,
y `check-all.sh`, que los corre desde un glob.

Cuatro decisiones le dan forma al resto:

1. **`check-adapter` no es bash.** Seis afirmaciones no hablan del archivo sino de
   la *ruta de ejecución*, que un grep no puede expresar, y otras cuatro estaban
   dadas por irreducibles. Sobre un AST las diez son exactas.
2. **Ningún número que ya viva en el repo se escribe dos veces.** Donde dos
   archivos cargan el mismo conjunto, el check compara conjuntos y el número
   desaparece del script. Donde el número es la única copia, se hardcodea con el
   número de afirmación al lado.
3. **Un solo job**, que corre `check-all.sh`, que saca la lista de un glob. Un job
   por script escribiría la lista dos veces, en el YAML y en el script.
4. **Verde local y verde en CI significan lo mismo.** Por eso
   `claude plugin validate --strict` corre adentro de `check-packaging.sh` y la 19
   es un script y no un job de CI.

Todas rompen con código distinto de cero, todas acumulan y reportan juntas, todas
fallan cuando su fuente falta, y la salida nombra el número de afirmación. Cada
check nace en la misma task de SDD que construye lo que chequea, y ahí su fila pasa
de `pendiente` a `viva`.

**Las dos afirmaciones que se chequeaban contra Linear no se pierden: se mueven al
adapter.** `ticket:create` rechaza dos labels `map:<tipo>` y `issue:create` no tiene
ruta que agregue `map`, así que las dos pasan a ser afirmaciones sobre `linear.py`,
las nuevas 47 y 48. Es el mismo movimiento de la 45 con el tope de 120 caracteres:
convertir una invariante de datos en una invariante de código.

## Por qué

Porque la única forma de que cuarenta afirmaciones sobrevivan a la construcción es
que existan en un solo lugar con estado. Estaban repartidas en seis documentos con
tres cadenas de reemplazo cruzándolas, y nadie las había recontado: seis están
retiradas y dos más lo están a medias, que es peor, porque leerlas enteras da mitad
verdad.

Y porque un check que no puede decir lo que la afirmación dice no es un check, es
una coartada. Ahí sale el AST: escribir veintidós afirmaciones en un lenguaje que no
puede expresar seis de ellas obligaba a una columna de brechas que no serían del
problema sino de la herramienta.

## Lo que se cayó

**`CONTEXT.md` decía que once operaciones reciben el `--ctx`. Son siete.** El 14 lo
tenía medido en su propia tabla, con cuatro operaciones que no lo usan, y su sección
8 acota la regla a los subcomandos *consumidores*. La contradicción sobrevivió al
cierre del 14 y solo se vio acá, al escribir la afirmación 35, que dice siete: de no
corregirse, el glosario y el check se contradecían. Ya está bajado.

**Y se cayó la idea de que `claude plugin validate` alcanza para algo.** Medido: sin
`--strict` sale 0 aunque haya warnings, así que la afirmación 14 tal como estaba
escrita pasaba con un manifiesto sin `description`. Y aun con `--strict`, un
`SKILL.md` **sin `name:` lo pasa limpio**. El comando es un piso, no un check.

## Niebla graduada

Ninguna graduó. Se abre una nueva: **cómo se prueba que el adapter hace lo que dice,
y no solo que está escrito como dice.** Los checks son estructurales por decisión de
encuadre, y esa decisión ruled out el comportamiento *conversacional*, no el del
adapter, que nunca se conversó. Recién ahora se ve el costo, porque la columna de
brechas lo hace contable: la 11, la 23, la 28, la 34, la 44 y la 47 solo se cierran
con tests de verdad, y la 18 es la cara, porque su modo de falla es una credencial
en un log.

## Tickets nuevos

Ninguno.

## Qué corrige o empuja

**A `CONTEXT.md`**, dos cosas, ya bajadas: las siete operaciones que consumen el
ctx, y la regla de idioma, que gana el frontmatter `lang:` como forma verificable de
la columna y manda `README.md` a español.

**Al ticket 08**, dos: su árbol dice `scripts/check-*.sh` y pasa a `scripts/check-*`,
con dos extensiones; y su tabla de idioma por archivo deja de ser la fuente, que
ahora es el frontmatter, y queda como el razonamiento de por qué cada archivo cae
donde cae.

**Al ticket 07**, una: su `README.md` nace con `lang: es`.

**A los tickets 06, 08 y 09**, la contabilidad de las retiradas. Sus documentos no
se reescriben, y por eso la tabla del deliverable las mantiene visibles con el
puntero a la que las reemplazó.

**A quien escriba `check-roster.sh`**: cerrar lo que `--strict` no atrapa, un
`SKILL.md` sin `name:`, sale casi gratis porque ese script ya camina `skills/`.
