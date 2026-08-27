# 10: Qué chequean los checks estructurales

**Tipo:** `map:grilling` · **Modo:** HITL (`hitl:dev`)
**Bloqueado por:** nada. Tomable ahora. (El 06, el 07, el 09, el 13 y el 14 se
resolvieron el 2026-08-27 y entre los cinco le dejaron **cuarenta y una**
afirmaciones chequeables, numeradas de la 1 a la 41 y repartidas por los research:
1 a 6 del [08](08-los-dos-modos-keironizados.md), 7 a 13 del
[06](06-que-hace-map-collapse.md), 14 a 21 del
[07](07-distribucion-e-instalacion.md), 22 a 31 del
[09](09-concurrencia-humano-plugin.md) y del
[13](13-pestana-abierta-pisa-al-plugin.md), y 32 a 41 del
[14](14-preflight-por-invocacion.md). Dos están reemplazadas y no se cuentan dos
veces: la 10 por la 22, y la 22 por la 32.)
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
   del comentario, con texto exacto.
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
  el 09, el 13 y el 14. Lo que queda es ordenar sus cuarenta y una afirmaciones,
  no descubrirlas.)
- Si un check que falla rompe el build o solo avisa.

## Hecho cuando

Está escrita la lista de checks con lo que verifica cada uno, y resuelto el caso
del label de tipo duplicado, aunque sea aceptando perderlo.
