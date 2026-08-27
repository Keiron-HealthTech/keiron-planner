# 08: Qué cambia de los dos modos de wayfinder al keironizarlos

**Tipo:** `map:grilling` · **Modo:** HITL (`hitl:dev`)
**Bloqueado por:** nada. Tomable ahora. (03 y 05 resueltos.)

## Pregunta

Wayfinder ya especifica sus dos modos con detalle: chart y work. Nuestro trabajo
es adaptarlos, no inventarlos. ¿Qué cambia?

Está bloqueado por 03 porque los pasos que tocan el tracker dependen de las seis
operaciones, y por 05 porque los pasos que invocan disciplinas dependen de cómo
queden escritas.

Preguntas que cuelgan de esta:

- Qué hace `/map-new` que wayfinder no hace, dado que crea un Project y un
  Document en vez de un issue padre.
- Cómo entra el multi-rol en `/map-work`: si el ticket lleva `hitl:design`, qué
  hace la sesión cuando esa persona no está.
- Qué hace `/map-status` exactamente, que es nuestro y no de Matt.
- Cómo se gradúa la niebla en la práctica, que es el paso que más fácil se
  saltea.
- **Agregado por el ticket 05**: grilling ahora crea tickets, porque una
  pregunta de otro rol sale como ticket HITL. Deja de ser una skill pura de
  conversación y toca el adapter, así que su punto de contacto con las seis
  operaciones hay que definirlo acá.

## Agregado por el ticket 03

Las ocho operaciones ya están escritas en
[`research/03-operaciones-en-linear.md`](../research/03-operaciones-en-linear.md).
Lo que este ticket tiene que hacer es repartirlas entre los cuatro comandos, no
inventarlas.

Y `/map-status` dejó de estar vacío. Tiene tres cosas concretas que reportar, que
salieron de la resolución del 03:

- Los tickets **tomados**, con su antigüedad. Una toma huérfana no se libera sola,
  a propósito, así que la única forma de que se vea es que `/map-status` la muestre.
- **Frontera vacía con tickets abiertos**, que significa mapa trabado, contra
  frontera vacía sin tickets abiertos, que significa listo para colapsar. Son
  opuestos y se ven igual.
- El aviso de **truncado**, si el mapa pasó los cincuenta tickets.

## Hecho cuando

Los cuatro comandos tienen su procedimiento escrito y los checks estructurales
del ticket de verificación tienen algo concreto que chequear.
