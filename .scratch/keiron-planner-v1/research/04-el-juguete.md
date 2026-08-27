# 04: El mapa de juguete, y qué le hace Linear al markdown del mapa

Resolución del ticket 04. Fecha: 2026-08-27.

`map:prototype`, `hitl:dev`. La rama no es ninguna de las dos de Matt: el
artefacto no es lógica ni es UI, es un documento en una herramienta de terceros.
Se construyó a mano en el Project descartable del ticket 01 y se miró.

Va en español. Su lector es el dev leader.

---

## Por qué este ticket y no otro de la frontera

La frontera al empezar eran cuatro y las cuatro tomables: 04, 10, 11 y 12.
El 04 es **el único que puede invalidar una decisión de encuadre** sobre la que ya
se apoyan diez tickets resueltos: "el mapa es el DD vivo y vive en un Document".
Los otros tres agregan detalle sobre una apuesta que todavía nadie había mirado.

---

## Hecho medido antes de construir nada: el mapa real ya está en el volumen del ticket

El ticket se escribió pensando en un mapa hipotético de quince decisiones. El
mapa real de `keiron-planner` tiene diez, y medido, ya está donde el ticket temía:

| Sección | chars | líneas | enlaces |
| --- | --- | --- | --- |
| Destino | 208 | 6 | 0 |
| Notas | 1.506 | 32 | 0 |
| **Decisiones hasta ahora** | **8.614** | **110** | **10** |
| Aún no especificado | 2.088 | 33 | 0 |
| Fuera de alcance | 574 | 12 | 0 |
| total | 13.189 | 200 | 10 |

**El índice se come el 65% del mapa con diez entradas.** Y la plantilla del propio
mapa dice, en un comentario HTML que sigue ahí, `una línea por ticket cerrado, con
enlace al ticket que guarda el detalle`. La realidad son entradas de 5 a 14
líneas: promedio 849 chars, mínimo 449, máximo 1.256.

Peor: **las entradas están creciendo**. Las cinco resueltas el 2026-08-27
(06, 07, 09, 13, 14) promedian 1.074 chars. Las cinco anteriores (01, 02, 03, 05, 08)
promedian 625. No es una plantilla que se respeta con más disciplina: es una
plantilla que la práctica ya abandonó, y la proyección a quince entradas al ritmo
nuevo es **16.100 chars solo de índice**.

Segundo hecho medido, más chico: el mapa tiene **diez enlaces, uno por entrada**.
La niebla nombra tickets en prosa (`El 07 cerró`, `Salió al resolver el 03`) y
**no los enlaza nunca**. El ticket pedía un mapa con veinte enlaces; el mapa real
no llega ni a la mitad, y donde faltan es en la sección que más los necesita.

---

## El juguete

Cuatro Documents completos en el Project descartable
[ZZ SANDBOX keiron-planner 01](https://linear.app/keiron/project/zz-sandbox-keiron-planner-01-3a2ec0e37ac5).
Los cuatro tienen **el mismo contenido**: quince entradas, la niebla real, el
fuera de alcance real y veinte enlaces clicables. Lo único que cambia es la forma
de la sección Decisiones hasta ahora.

| | Variante | Documento | chars | índice | dónde empieza la niebla |
| --- | --- | --- | --- | --- | --- |
| A | párrafo por decisión, la forma de hoy | [Mapa A](https://linear.app/keiron/document/zz-juguete-04-mapa-a-e45d707cbd6d) | 17.976 | 70% del doc | al 84% |
| B | una línea por decisión, el detalle solo en el ticket | [Mapa B](https://linear.app/keiron/document/zz-juguete-04-mapa-b-b9e0aa8e86a0) | 8.363 | 34% | al 65% |
| C | tabla de tres columnas | [Mapa C](https://linear.app/keiron/document/zz-juguete-04-mapa-c-4cbaea6a1e45) | 9.525 | 43% | al 70% |
| D | una línea por decisión con el detalle anidado debajo | [Mapa D](https://linear.app/keiron/document/zz-juguete-04-mapa-d-dd4a82e2d036) | 19.121 | 71% | al 85% |

Honestidad del juguete, escrita en un banner arriba de los cuatro documentos:
diez entradas son reales y textuales, de los tickets 01, 02, 03, 05, 06, 07, 08,
09, 13 y 14. Las cinco marcadas `[RELLENO]` **no son decisiones**: son los cuatro
tickets que siguen abiertos y un ítem de la niebla, puestos con su propia prosa
para que la entrada pese lo que pesa una entrada real. Los veinte enlaces apuntan
a las cinco issues del sandbox del 01, cicladas: son clicables y ninguno es la
issue que dice el texto.

Harness: [`04-scripts/variants.py`](04-scripts/variants.py) genera las cuatro
desde `MAP.md`, y [`04-scripts/toy.py`](04-scripts/toy.py) las escribe, las relee
y corre la sonda de markdown. Solo stdlib.

---

## Lo que el juguete encontró y nadie había mirado: qué le hace Linear al markdown

Esto no era la pregunta del ticket. Salió de escribir el mapa de verdad, y toca
directo al contrato de `map:write` que fijó el 09.

Escribir por API y releer por API cambia el markdown **siempre**. Cuatro
transformaciones, medidas sobre los cuatro documentos:

| Escrito | Devuelto | Ya lo sabíamos |
| --- | --- | --- |
| viñeta `- ` | viñeta `* ` | sí, el 09 |
| `[t](url)` | `[t](<url>)` | sí, el 09 |
| `\| --- \|` de tabla | `\| -- \|` | no, es nuevo y es inofensivo |
| línea en blanco entre ítems de lista | **se borra** | no, y en la variante A borró **quince** |

Y un defecto de verdad:

**Un `**bold**` que cruza un corte de línea vuelve partido en cuatro asteriscos.**

```
escrito:   ... `[RELLENO]` **no son
           decisiones**: son los cuatro tickets ...

devuelto:  ... `[RELLENO]` **no son****
           ****decisiones**: son los cuatro tickets ...
```

Aparece seis veces en la variante A y cuatro en las otras tres. Dos cosas lo
acotan, las dos medidas:

1. **Es un punto fijo, no una degradación que se acumula.** Cuatro ciclos de
   releer y volver a escribir lo leído, que es exactamente lo que hace
   `map:write`: 17.976 chars y seis `****` en el ciclo 0, y los mismos 17.976
   chars y los mismos seis `****` en los ciclos 1, 2, 3 y 4. Byte a byte estable.
   Y el render no se rompe, justamente porque es estable: si Linear reparseara
   ese texto a un estado distinto, el ciclo 2 no sería idéntico al 1.
2. **Desaparece si la prosa no viene cortada a 80 columnas.** El mismo mapa B con
   cada párrafo y cada ítem en una sola línea baja de cuatro `****` a dos, y los
   dos que quedan son del banner, que mi reflow no tocó porque es una cita.
   Documento de control:
   [Mapa B sin cortes de línea](https://linear.app/keiron/document/zz-juguete-04-mapa-b-sin-cortes-de-linea-344233bb051c).

Consecuencia para el plugin: **el markdown que `map:write` le manda a Linear no se
corta a 80 columnas.** El corte a 80 es una convención del repo, para diffs de git
legibles; el mapa no vive en git, vive en un editor que envuelve solo. Cortarlo no
compra nada y ensucia lo que se lee de vuelta, que es de donde el 09 decidió que
salen las anclas.

Un quinto hallazgo, chico y solo de la variante C: dentro de una celda de tabla,
`**Qué hace exactamente `/map-collapse`.**` vuelve como
`**Qué hace exactamente** `/map-collapse`**.**`. Linear parte el bold alrededor
del código inline. Es cosmético y estable, pero si el índice fuera una tabla, sus
celdas serían el lugar del mapa con más churn de markdown.

---

## La sonda de markdown: qué se puede usar y qué no

[Documento de la sonda](https://linear.app/keiron/document/zz-sonda-markdown-04-e309287791bb).
Escrito y releído por API.

| Forma | Sobrevive el round-trip | Nota |
| --- | --- | --- |
| viñeta anidada a tres niveles | sí | habilita la variante D |
| tabla | sí | `---` se normaliza a `--` |
| checkbox `- [ ]` / `- [x]` | sí | la `x` vuelve `X` |
| encabezado de nivel 3 | sí | |
| bloque de código y código inline | sí | |
| separador `---` y cita `>` | sí | |
| `<details>` / `<summary>` | sobrevive como **texto** | ver abajo |
| URL pelada | se convierte en `[CRM-3346](url)` | autolink |

El `<details>` es el que importaba, porque plegar el detalle disolvería la tensión
entera del índice sin tener que acortar nada. Sobrevive el round-trip **como
texto literal**, que es la firma de algo que el pipeline no parseó a un nodo. Si
se renderiza como un bloque plegable, la variante D es innecesaria; si se
renderiza como los caracteres `<details>` a la vista, el HTML queda descartado.
Eso se mira, no se mide por API, y va en la lista de abajo.

---

## El veredicto

Miró los cuatro documentos y eligió, en dos tandas de preguntas.

**La forma es B: una línea por decisión.** El enlace al ticket, dos puntos, y el
gist. El detalle no entra al mapa.

**La niebla y el fuera de alcance se quedan en el mismo Document.** No se mudan a
ninguna parte. Con B el índice baja al 34% del documento y la niebla empieza al
65%, así que el muro de texto que el ticket temía era del índice, no de las otras
dos secciones.

**Alguien que no estuvo en las sesiones entiende dónde va el proyecto abriendo
solo el Document.** Es la tercera pregunta del ticket y la única que no se podía
medir. Contestada mirando el Mapa B.

**Las sorpresas viven en el ticket, nunca en el mapa.** Es lo más denso de cada
entrada de hoy, y es lo que B saca. La variante C las conservaba en una tercera
columna y perdió por eso. El argumento que la cerró: `CONTEXT.md` ya define el
mapa como un índice que apunta al ticket y **nunca repite el detalle**. B no es
una forma nueva, es el mapa volviendo a su propia definición, y A era la
definición incumplida.

**El gist tiene tope duro: 120 caracteres.** Medido sobre el juguete, el gist va
de 60 a 96 con mediana 84, así que 120 deja 25% de aire y aprieta de verdad. El
número que se propuso primero, 200, estaba mal: era el largo de la línea entera
con enlace y título adentro, no el del gist, y no habría apretado nunca. El tope
es lo único que impide que B se degrade a A una entrada por vez, que es
exactamente lo que ya pasó una vez con "una línea por ticket cerrado" escrito sin
número.

**El comentario de resolución pasa de cinco secciones a seis.** Si las sorpresas
se mudan al ticket, el ticket necesita dónde ponerlas, y ninguna de las cinco que
fijó el 08 era ese lugar. La que se agrega es `## Lo que se cayó`, o "ninguna",
y va tercera, después de `## Por qué`. Hoy esa
sección existe de hecho en varios tickets cerrados, con nombres distintos cada
vez: sobrevivía por costumbre y ahora es contrato.

Las preguntas 4 y 5 de la lista que se le llevó se caen solas al elegir B: sin
detalle largo en el mapa no hay nada que plegar con `<details>`, y no hay ítems de
párrafo que se vean pegados por las líneas en blanco que Linear borra.

## La migración, hecha en esta sesión

`MAP.md` estaba en forma A y quedó en forma B. No se perdió nada: se verificó
antes de tocar el archivo que cada ticket pesa entre 4 y 10 veces su entrada del
mapa, y que el vocabulario de la entrada está contenido en el ticket más su
research.

| | antes | después |
| --- | --- | --- |
| MAP.md entero | 13.189 chars | 6.900 chars |
| Decisiones hasta ahora | 8.614 chars, 110 líneas | 2.325 chars, 11 líneas |
| el índice, como parte del mapa | 65% | 34% |
| gist más largo | 1.256 chars | 104 chars |

El comentario HTML de la sección también se reescribió. Decía "una línea por
ticket cerrado" sin número, que es la regla que la práctica abandonó; ahora dice
el tope y dice dónde vive el detalle.

## Captura

El juguete no se borra ni se promueve, como pide el ticket. Los seis documentos
quedan en el Project descartable como fuente primaria, con sus enlaces en este
documento y en el ticket. `MAP.md` y `CONTEXT.md` se quedan solo con la decisión
validada.

---

## Lo que este documento corrige o empuja

**A `CONTEXT.md`**, dos filas. La de Map ahora dice que el índice es una línea por
decisión con gist de 120 caracteres o menos. La de Resolution pasa de "secciones
fijas" a "seis secciones fijas" y nombra la sexta.

**Al contrato del mapa**, la regla de que el markdown que va a Linear **no se
corta a 80 columnas**. Es el hallazgo del `****`, y es la única de estas líneas
que cambia código en vez de prosa.

**A las plantillas que fijó el 08**, la sexta sección del comentario de
resolución y la forma de la entrada del índice.

**Al ticket 10**, las afirmaciones 42 a 46, y una corrección a la 9.

**A la niebla, nada.** Este ticket no vació ningún parche y no abrió ninguno. La
frontera al cerrar son tres: 10, 11 y 12.

---

## Las afirmaciones chequeables, para el ticket 10

Siguen la numeración: 1 a 6 del 08, 7 a 13 del 06, 14 a 21 del 07, 22 a 31 del 09
y del 13, 32 a 41 del 14.

42. `map-templates.md` describe la entrada de Decisiones hasta ahora como **una
    línea**: enlace al ticket, dos puntos, y un gist. No hay ninguna plantilla que
    muestre una entrada de más de una línea.
43. `map-templates.md` tiene las **seis** secciones del comentario de resolución
    con texto exacto, y la que se agregó es `## Lo que se cayó`, tercera, entre
    `## Por qué` y `## Niebla graduada`. **Corrige la afirmación 9
    del ticket 06**, que decía cinco. Los seis encabezados del DD y las tres
    secciones de la issue de ejecución que esa misma afirmación fija no cambian.
44. El adapter **no envuelve texto**. Grep de `textwrap`, `\n`.join sobre líneas
    cortadas, o cualquier `wrap` en la ruta de `map:write`: cero coincidencias. Lo
    que se manda a Linear va sin cortes de línea adentro de un párrafo.
45. El flag de `map:write` que agrega una decisión recibe el gist como argumento
    propio, separado del número y del título, y **rechaza un gist de más de 120
    caracteres** con código distinto de cero. Es el tope, hecho mecánico.
46. Ninguna plantilla ni ningún comando contiene `<details>` ni `<summary>`. El
    HTML no se parsea a nodo en el pipeline de Linear y el mapa no lo necesita.
