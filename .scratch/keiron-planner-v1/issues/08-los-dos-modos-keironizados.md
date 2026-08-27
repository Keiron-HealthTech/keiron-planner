# 08: Qué cambia de los dos modos de wayfinder al keironizarlos

**Tipo:** `map:grilling` · **Modo:** HITL (`hitl:dev`)
**Estado:** **RESUELTO** el 2026-08-27.
**Tomado por:** Luis Felipe Jaña (`hitl:dev`), sesión del 2026-08-27.

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

> **Corregido al resolver.** El criterio pedía el procedimiento de los **cuatro**
> comandos. `/map-collapse` es la pregunta del ticket 06, que sigue abierto:
> escribirlo acá resolvía dos tickets en una sesión y dejaba al 06 sin objeto.
> El criterio correcto es tres procedimientos más la costura del cuarto.

`/map-new`, `/map-work` y `/map-status` tienen su procedimiento escrito, la
costura con `/map-collapse` está nombrada, y los checks estructurales tienen una
lista concreta de afirmaciones que chequear.

---

## La decisión

El documento completo es
[`research/08-los-tres-comandos.md`](../research/08-los-tres-comandos.md), 520
líneas. A diferencia del reference del 03, que se copia entero al plugin, este se
**reparte**: cada procedimiento termina en su `SKILL.md`, el contrato en
`skills/_shared/map-contract.md` y las plantillas en `map-templates.md`.

Seis rondas de grilling, veinticinco preguntas, frontera del árbol vacía.

**Ocho cosas cambian de wayfinder.** Tres son adaptaciones forzadas: el mapa no es
un issue padre, así que el parentesco se reemplaza por Project más label `map`; no
hay rama descartable de research, porque con once repos obliga a elegir uno, así
que los hallazgos van a un Document hermano del DD; y no hay skill de research,
porque el Tier B está fuera de alcance, así que el prompt del subagente vive en
`skills/_shared/`.

**Dos son endurecimientos**, y los dos salen de fallas que el propio doc de
wayfinder reporta. Las Notas del mapa dejan de poder anular el "plan, don't do",
porque la restricción y su exención vivían en el mismo archivo que controla el
restringido. Y en un ticket de prototipo el agente construye variantes y nunca
elige: sin una elección dicha por la persona, el ticket no se resuelve.

**Tres son nuestras.** Se saca el corte de "sin niebla no hace falta mapa", porque
en Keiron el DD lo tiene todo proyecto igual y ese corte deja a la persona sin
nada; `/map-new` crea siempre el Project y el DD, y sin niebla el mapa nace listo
para colapsar. El multi-rol sale como ticket HITL creado al resolver, que es el
punto de contacto que el 05 dejó anotado. Y existe `/map-status`, que en wayfinder
no existe, porque tres cosas que decidimos en el 03 quedan invisibles en la UI de
Linear.

**Las ocho operaciones repartidas.** La tabla completa está en el documento. Lo que
el reparto obligó a decidir: `map:create` tiene una variante que usa solo su
segunda mitad, el Document de research; `ticket:resolve` es la única operación que
se parte entre procesos, con el subagente escribiendo comentario y estado y el
padre escribiendo el mapa; y `frontier:query` cierra `/map-new` además de abrir
`/map-work`, porque el plugin relee en vez de reportar de memoria.

**El adapter es un script**, `scripts/linear.py`, stdlib pelado, un subcomando por
operación. El modelo no compone GraphQL. El árbol de archivos completo está en el
documento y sigue la forma real de `../spec-driven-dev`.

**Medido**: traer el mapa entero en la misma query que la frontera cuesta 25 de
complejidad, 3.847 contra 3.872. `/map-status` es un round-trip y el aire contra
el techo sigue en 61%. Script en
[`research/08-scripts/status_cost.py`](../research/08-scripts/status_cost.py).

## Por qué

Lo descartado que más costó.

**Un mapa de roles en config**, para saber quién está del otro lado de un ticket
`hitl:design`. Descartado: le deja creer al agente que verificó algo que no
verificó, y toda la disciplina HITL se apoya en que el agente nunca habla por la
persona. En su lugar pregunta y le cree a la respuesta, y solo cuando el label no
es `hitl:dev`.

**Que los subagentes de research escriban el mapa cada uno.** Descartado: son N
read-modify-write sobre el mismo Document desde una sola sesión, y la decisión de
encuadre del conductor único no lo cubre, porque acá el conductor único genera N
escritores.

**Traer la skill `research` de Matt.** Descartado: correr el límite de alcance por
comodidad. Un subagente común con el prompt escrito alcanza, y es lo que hicimos a
mano para el 02.

**Un solo archivo en `skills/_shared/`.** Descartado: la regla de idioma los parte
por lector, y meter una plantilla en español adentro del contrato en inglés es
exactamente la clase de archivo que se pudre.

**Que el modelo componga el GraphQL** leyendo el reference. Descartado: el 03 dice
que el predicado de frontera es lo que más fácil se implementa mal, y un script lo
implementa una vez en vez de una vez por sesión.

## Niebla graduada

Dos parches, los dos vaciados del mapa.

- **La forma exacta de los checks estructurales** decía explícito que dependía de
  que existiera la estructura del plugin. Esta sesión la fija. Gradúa al
  [ticket 10](10-que-chequean-los-checks.md).
- **Proyectos del CRM que ya arrancaron sin mapa** se destrabó al decidir que
  `/map-new` adopta un Project vivo, que ya tiene issues de ejecución adentro.
  Gradúa al [ticket 11](11-map-new-sobre-project-vivo.md).

Y uno que no gradúa pero se achicó: **qué pasa con un ticket HITL de un rol que no
entra a Linear**. `/map-status` ahora lo muestra en la frontera con su antigüedad,
así que deja de ser invisible. Lo que sigue difuso es cómo se le avisa a esa
persona.

## Tickets nuevos

- [10: Qué chequean los checks estructurales](10-que-chequean-los-checks.md),
  bloqueado por el 06 y el 07, que son los dos que todavía agregan archivos al
  árbol.
- [11: Qué hace `/map-new` sobre un Project que ya arrancó](11-map-new-sobre-project-vivo.md),
  sin bloqueantes.

## Qué corrige o empuja

**Al reference del 03**, tres cosas, ya bajadas a
[`research/03-operaciones-en-linear.md`](../research/03-operaciones-en-linear.md):
`ticket:resolve` son cinco escrituras y no tres, porque los tickets nuevos se
crean y se cablean antes del comentario que los enlaza; `map:create` tiene una
variante que usa solo su segunda mitad; y el preflight es uno por proceso que
emite operaciones, no uno por sesión, porque con subagentes en paralelo sesión y
proceso dejan de ser lo mismo.

**A `CONTEXT.md`**, tres cosas. `Discovery` deja de ser "el label que marca el DD",
que era falso desde que el 03 midió que un Document no acepta labels. La regla de
idioma pasa a distinguir por lector. Y se agregan `next_recommended` y el
comentario de resolución al glosario.

**Al ticket 09**, a favor: `/map-new` y `/map-work` escriben el mapa exactamente
una vez cada uno, así que la superficie que el 09 tiene que proteger es la mínima
posible.

**Al ticket 06**, la precondición: `/map-collapse` corre solo con cero tickets de
decisión abiertos, que es el veredicto que `/map-status` ya reporta.
