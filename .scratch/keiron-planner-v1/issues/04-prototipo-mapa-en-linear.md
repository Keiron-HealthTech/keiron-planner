# 04: Un mapa de juguete en Linear, para ver si el Document aguanta

**Tipo:** `map:prototype` · **Modo:** HITL (`hitl:dev`) · **RESUELTO** el 2026-08-27
**Bloqueado por:** nada. (02 resuelto el 2026-08-26.)
**Tomado por:** Luis Felipe Jaña (`hitl:dev`), sesión del 2026-08-27.
**Research:** [`research/04-el-juguete.md`](../research/04-el-juguete.md).

## Pregunta

Decidimos que el mapa es el DD vivo y que vive en un Document. Es una apuesta
razonable en papel, pero un mapa con quince decisiones acumuladas, niebla que se
vacía y enlaces a veinte tickets no se puede juzgar leyendo un template. Hay
que verlo.

## Rama del prototipo

Ninguna de las dos de Matt encaja del todo: no es lógica ni es UI. Es un
artefacto en una herramienta de terceros. Se construye a mano, en un Project
descartable, y se mira.

## Qué tiene que responder

- Si el índice de decisiones sigue siendo legible con quince entradas.
- Si la niebla y el fuera de alcance conviven sin que el documento se vuelva un
  muro de texto.
- Si alguien que no estuvo en las sesiones entiende dónde va el proyecto
  abriendo solo el Document.

## Captura

El Project descartable queda como fuente primaria, con su enlace anotado acá.
La decisión validada entra al glosario; el juguete no se borra ni se promueve.

---

## La decisión

El Document aguanta, y la forma del índice es **una línea por decisión**: el
enlace al ticket, dos puntos, y un gist de **120 caracteres o menos**. El detalle
no entra al mapa. La niebla y el fuera de alcance **se quedan** en el mismo
Document. Y alguien que no estuvo en las sesiones entiende dónde va el proyecto
abriendo solo el Document.

Dos consecuencias que la forma arrastra:

- Las sorpresas, el "lo que se cayó al resolverlo", viven en el ticket y **nunca**
  en el mapa. El comentario de resolución pasa de cinco secciones a **seis**, y la
  que se agrega es `## Lo que se cayó`, tercera, entre `## Por qué` y
  `## Niebla graduada`.
- El markdown que el plugin le manda a Linear **no se corta a 80 columnas**.

## Por qué

Se construyeron cuatro mapas completos en el Project descartable del 01, con el
mismo contenido y cuatro formas de índice, y se miraron. B ganó por número y por
argumento. Por número: el índice pasa del 70% del documento al 34%, y la niebla
deja de empezar al 84% para empezar al 65%. Por argumento, que es el más fuerte:
`CONTEXT.md` ya define el mapa como un índice que apunta al ticket y **nunca
repite el detalle**. B no es una forma nueva. Es el mapa volviendo a su propia
definición, y A era esa definición incumplida.

El tope de 120 no es un número redondo: el gist del juguete va de 60 a 96
caracteres con mediana 84, así que 120 deja 25% de aire y aprieta. Sin número, la
regla ya falló una vez.

## Lo que se cayó

**El mapa real ya estaba en el volumen que este ticket temía, y nadie lo había
contado.** El ticket imaginaba quince decisiones como un escenario futuro. Con
diez, el índice pesaba 8.614 de 13.189 caracteres, el **65% del mapa**. Y las
entradas crecían: las cinco cerradas el 2026-08-27 promedian 1.074 caracteres
contra 625 las cinco anteriores. La plantilla decía "una línea por ticket
cerrado" y la práctica la había abandonado hacía rato.

**Y se cayó una premisa del ticket 09, del lado del formato.** Escribir por API y
releer cambia el markdown siempre, y un `**bold**` que cruza un corte de línea
vuelve partido en cuatro asteriscos. Medido: es un punto fijo y no se acumula, y
desaparece si la prosa no viene cortada a 80 columnas. El corte a 80 es una
convención para diffs de git, y el mapa no vive en git.

## Niebla graduada

Ninguna.

## Tickets nuevos

Ninguno. La migración de `MAP.md` de la forma A a la forma B se hizo en esta misma
sesión, después de verificar que cada ticket pesa entre 4 y 10 veces su entrada
del mapa y que no se perdía nada. `MAP.md` quedó en 6.900 caracteres.

## Qué corrige o empuja

- **A `CONTEXT.md`**: la fila de Map ahora fija la forma del índice y el tope de
  120; la de Resolution pasa a seis secciones.
- **A las plantillas del 08**: la sexta sección del comentario y la forma de la
  entrada del índice.
- **Al contrato del adapter**: el markdown a Linear va sin cortar a 80 columnas.
- **Al ticket 10**: las afirmaciones 42 a 46, y una corrección a la 9 del 06.

## El juguete, que queda como fuente primaria

En el Project descartable
[ZZ SANDBOX keiron-planner 01](https://linear.app/keiron/project/zz-sandbox-keiron-planner-01-3a2ec0e37ac5).
No se borra ni se promueve.

- [Mapa A](https://linear.app/keiron/document/zz-juguete-04-mapa-a-e45d707cbd6d), párrafo por decisión, la forma de hoy
- [Mapa B](https://linear.app/keiron/document/zz-juguete-04-mapa-b-b9e0aa8e86a0), **el elegido**
- [Mapa C](https://linear.app/keiron/document/zz-juguete-04-mapa-c-4cbaea6a1e45), tabla de tres columnas
- [Mapa D](https://linear.app/keiron/document/zz-juguete-04-mapa-d-dd4a82e2d036), una línea con el detalle anidado
- [Mapa B sin cortes de línea](https://linear.app/keiron/document/zz-juguete-04-mapa-b-sin-cortes-de-linea-344233bb051c), el control del hallazgo del `****`
- [Sonda de markdown](https://linear.app/keiron/document/zz-sonda-markdown-04-e309287791bb), qué sobrevive al pipeline de Linear

Harness en [`research/04-scripts/`](../research/04-scripts/): `variants.py` genera
las cuatro desde `MAP.md`, `toy.py` las escribe, las relee y corre la sonda.
