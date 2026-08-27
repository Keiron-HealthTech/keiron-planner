# 14: Si el preflight corre por invocación o por sesión

**Tipo:** `map:grilling` · **Modo:** HITL (`hitl:dev`) · **RESUELTO** el 2026-08-27
**Bloqueado por:** nada.
**Tomado por:** Luis Felipe Jaña, sesión 2026-08-27.
**Origen:** creado al resolver el [09](09-concurrencia-humano-plugin.md).

## Pregunta

El 08 decidió que el preflight es **uno por proceso que emite operaciones**, no
uno por sesión de usuario. La razón era buena: con subagentes de research en
paralelo, sesión y proceso dejan de ser lo mismo, y un subagente no puede
heredar los ids del padre sin que alguien se los pase.

El 09 volvió esa regla visible desde otro ángulo. El adapter es
`scripts/linear.py` y el modelo lo llama por Bash, un subcomando por operación.
**Cada invocación es un proceso.** Leído literal, un `/map-work` que hace claim,
lee la frontera, crea dos tickets, los cablea, comenta, cambia el estado y
escribe el mapa paga **ocho preflights**, no uno.

Son 423 de complejidad medidos por preflight, contra un presupuesto horario que
el 02 midió como holgado, así que no es urgente por costo. Lo que molesta es
otra cosa: el preflight existe para fallar temprano y claro, y un preflight que
corre ocho veces por sesión ya no falla temprano, falla ocho veces.

## Preguntas que cuelgan de esta

- Si la regla del 08 quiso decir "por proceso" en el sentido de proceso del
  sistema operativo, o "por conductor" en el sentido de una sesión de modelo,
  que es lo que resuelve el caso de los subagentes sin multiplicar por ocho.
- Si el preflight se puede pasar de padre a hijo por argumentos sin volver a
  crear el acoplamiento que el 03 quiso evitar al decidir no cachear.
- Si conviene un subcomando `preflight` explícito que el comando corra una vez
  al empezar, y que los demás subcomandos asuman hecho.
- Qué pasa cuando el preflight de la invocación siete falla y las seis
  anteriores ya escribieron.

## Hecho cuando

Está decidido cuántas veces corre el preflight en un `/map-work` típico, y cómo
se lo pasa un padre a sus subagentes sin cachear estado.

---

# Resolución

Cinco rondas de grilling, diecisiete preguntas, frontera del árbol vacía.
Deliverable: [`research/14-el-preflight.md`](../research/14-el-preflight.md).
Harness: [`research/14-scripts/preflight_probe.py`](../research/14-scripts/preflight_probe.py).

## La decisión

**Corre una vez por conductor, y un `/map-work` típico son cinco invocaciones y un
preflight.** La regla del 08 sobrevive entera; lo que estaba mal era una palabra.
Decía "por proceso que emite operaciones" y su razonamiento era todo sobre contexto
de modelo, así que se lee **por conductor**: la sesión es uno, cada subagente de
research es uno, un subcomando no.

Para que eso sea mecánico, el `preflight` pasa a ser un subcomando de verdad, la
operación **doce**. Imprime por stdout un blob opaco de 712 bytes y nada más, y
todo consumidor lo recibe como `--ctx`. **Un consumidor sin `--ctx` falla**: ningún
subcomando consumidor sabe hacer un preflight, así que pagar dos es imposible por
construcción y no por disciplina. Eso se chequea con un grep.

La regla de no cachear del 03 queda acotada a lo que su razón decía: **lo prohibido
es persistir entre corridas**. Pasar ids resueltos hace tres segundos adentro de la
misma corrida no envejece, y era el 08 leyendo la regla de la manera ancha lo que
había convertido esto en un problema.

**La premisa del ticket se cayó.** Este ticket decía que un preflight por invocación
rompe la promesa de fallar temprano porque falla ocho veces. Es falso: con el
preflight adentro de cada subcomando, la primera invocación es la que falla, y esa
es exactamente la falla temprana que se quería. Y el costo tampoco alcanzaba: el
techo por hora no es 10.000 sino **3.000.000 de complejidad y 2.500 requests**, así
que ocho preflights son el 0,11% del presupuesto. Lo que quedaba era latencia,
**3.197 ms medidos** por `/map-work`, que sobre una sesión de grilling no decide
nada.

**Lo que decidió el ticket apareció midiendo, y es peor: el preflight escribía.**
Creaba los labels que faltaran, y el 08 lo puso a correr dentro de `/map-status`,
que promete dejar Linear byte a byte como estaba. Medido, hoy no existe ninguno de
los ocho labels, así que sobre el workspace de hoy `/map-status` crearía ocho. El
preflight pasa a ser **de solo lectura** y la creación se muda a `ticket:create`,
su único consumidor real, que además cubre el caso que `map:create` no cubría:
alguien borrando `hitl:pm` tres semanas después.

Las fallas duras quedan en **cuatro**: la key ausente o rechazada, el team no
encontrado, que falte algún estado de tipo `completed` o `canceled`, y que no
exista el label `map`. La cuarta rompe la simetría de los ocho labels a propósito,
y la medición dice por qué: **borrar un label lo saca de las issues y las issues
sobreviven**, así que sin `map` todo ticket de decisión queda huérfano,
`frontier:query` devuelve cero sin error y `/map-work` emite `map-collapse` sobre
un mapa lleno de preguntas abiertas. Los otros siete solo bloquean una escritura;
este hace mentir a una lectura. `/map-new` la apaga con `--bootstrap`, porque es el
único comando que nunca lee una frontera preexistente.

De paso se resolvió una ambigüedad que nunca se había nombrado: **`ticket:resolve`
es una invocación, no cinco.** Hace sus cinco escrituras adentro, y el orden lo
garantiza el adapter y no el modelo. Es el mismo argumento del 09 para `map:write`.

## Por qué

Porque la regla del 08 no era el problema y el costo tampoco. El problema era que
la regla no tenía cómo hacerse cumplir: un preflight escondido adentro de cada
subcomando corre las veces que corra el subcomando, y nadie se entera. La forma de
volverla verdadera no fue escribirla mejor, fue sacarle a los consumidores la
capacidad de hacer un preflight.

Y la parte que no se veía desde el enunciado es que el preflight escribía. Un paso
de arranque que además muta el workspace es exactamente la clase de cosa que se
vuelve invisible cuando corre ocho veces por sesión, y solo se ve cuando alguien
pregunta cuántas veces corre.

## Niebla graduada

Ninguna. Este ticket no vació ningún parche del mapa y no abrió ninguno nuevo.

## Tickets nuevos

Ninguno.

## Qué corrige o empuja

**Al ticket 08**, la regla del preflight: "por proceso que emite operaciones" se
lee "por conductor". El razonamiento no cambia, cambia la palabra. Y la fila
`preflight` de la columna `/map-status` de su tabla de reparto deja de ser una
escritura.

**Al ticket 03**, tres cosas. El preflight ya no crea labels: resuelve acá, crea en
`ticket:create`. Su lista de fallas duras se reescribe en cuatro. Y su regla de no
cachear queda acotada explícitamente a no persistir entre corridas.

**A `CONTEXT.md`**, cuatro cosas. Las operaciones pasan de once a doce. Las que no
escriben pasan de dos a tres. La fila `Preflight` se reescribe entera. Y
`ticket:create` gana la creación de los labels que falten.

**Al ticket 10**, la corrección de la afirmación 22 y las afirmaciones 32 a 41.
