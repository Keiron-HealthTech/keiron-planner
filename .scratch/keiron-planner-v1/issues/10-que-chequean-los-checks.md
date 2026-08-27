# 10: Qué chequean los checks estructurales

**Tipo:** `map:grilling` · **Modo:** HITL (`hitl:dev`)
**Bloqueado por:** [06](06-que-hace-map-collapse.md) y [07](07-distribucion-e-instalacion.md).
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

## Lo que el 08 ya dejó listo, y este ticket no re-deriva

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
   nombradas en `LINEAR-OPERATIONS.md`, y ninguno de más.
6. Los archivos de la columna inglés no tienen prosa en español, y al revés.

## Preguntas que cuelgan de esta

- **La que el 08 no pudo contestar**: que ningún ticket lleve dos labels
  `map:<tipo>` es la exclusividad que se perdió al elegir labels planos en vez de
  label groups. Se chequea contra Linear y no contra el repo, así que no es un
  check estructural en el sentido de la decisión de encuadre. Hay que decidir si
  entra igual, si vive en otro lado, o si se acepta perderla.
- Si los checks corren en CI, en un hook, o a mano.
- Qué agrega el 06 al árbol cuando escriba `/map-collapse`, y qué agrega el 07
  con la instalación.
- Si un check que falla rompe el build o solo avisa.

## Hecho cuando

Está escrita la lista de checks con lo que verifica cada uno, y resuelto el caso
del label de tipo duplicado, aunque sea aceptando perderlo.
