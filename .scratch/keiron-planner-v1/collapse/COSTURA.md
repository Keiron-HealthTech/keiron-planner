---
lang: es
---

# La costura con `/sdd-new`

CRM-3407, corrida el 2026-09-29 sobre `main` en `cbdd9f2`, con `spec-driven-dev` 1.5.0.

## Qué se corrió

`/sdd-new crm-3408-afirmaciones-vivas` sobre CRM-3408, "Pasar a viva las cuarenta y
nueve afirmaciones no retiradas", una issue de ejecución nacida del colapso del
2026-08-28. Se eligió porque su sección `Lo que ya está decidido` es la más cargada
del Project: el research 10 y dos correcciones de CRM-3391. Corrió hasta el proposal,
que es donde termina `/sdd-new`.

La issue se le pasó a `sdd-explore` tal cual la devuelve Linear, sin contexto
agregado por quien conducía. Si se le hubiera sumado lo que el conductor ya sabía, la
prueba habría dejado de medir si el cuerpo alcanza.

Los artefactos quedaron en engram, proyecto `keiron-planner`:

- `sdd/crm-3408-afirmaciones-vivas/explore`, observación 14129.
- `sdd/crm-3408-afirmaciones-vivas/brainstorm`, observación 14130.
- `sdd/crm-3408-afirmaciones-vivas/proposal`, observación 14131.

## Las tres verificaciones

**El orchestrator trae la issue y se la pasa a `sdd-explore`.** Cierra. La traída es
un `get_issue` y devuelve las tres secciones completas. Los links de `Lo que ya está
decidido` apuntan a `research/*.md` en `main` y resuelven. Hay algo que anotar del
lado de SDD, sin arreglarlo porque ese repo queda fuera: toda la puerta es una línea
del orchestrator ("fetches it with the Linear MCP tools and passes the issue context
to sdd-explore"). `sdd-explore` no nombra Linear ni issues, y el proyecto no tenía
`sdd-init`. Lo que explore sabe de la issue depende de qué ponga el orchestrator en el
prompt, y nada obliga a que pase el cuerpo entero y no un resumen.

**El discovery no vuelve a litigar lo decidido.** Cierra. Explore no discutió nada de
lo enlazado. Del research 10 leyó tres filas con `grep` y no abrió CRM-3391: le
alcanzó con `scripts/CHECKS.md`, que es autocontenido. Trajo una sola pregunta de
diseño, si el check de `name:` extiende la afirmación 14 o acuña un número nuevo, y él
mismo avisó que su respuesta estaba implícita en la regla del research 10 de no
escribir dos veces un número. El conductor no la preguntó. El discovery tuvo una
pregunta de verdad, qué exige exactamente el `name:`, y el gate.

**El cuerpo alcanza sin tener forma de proposal.** Cierra, con un hallazgo. El
proposal salió en una iteración, y salió porque explore midió en vez de confiar en el
cuerpo. Y lo que midió contradice al cuerpo en casi todo:

- El título dice cuarenta y nueve no retiradas y `CHECKS.md` dice sesenta y tres.
- Dice siete scripts y `run-checks.sh` corre ocho.
- Pasar a viva todo lo que tiene check y dejar CI en verde ya estaban hechos: los
  cortes 1 a 4 los fueron cumpliendo al ejecutarse.

El cuerpo mismo dice que "el conteo vive en `scripts/CHECKS.md` y en ningún otro
lado", y el título igual lo copia. Lo que funcionó es justo lo que el research 06
buscaba: como el cuerpo no es un proposal, SDD no lo tomó como verdad y midió. Pero la
issue llega con dos de sus cuatro puntos vencidos, y el alcance real fue mucho más
chico que el escrito.

## El arreglo

De este lado de la costura, en la plantilla. `skills/_shared/map-templates.md` gana
una regla en `El cuerpo de una issue de ejecución`: ni el título ni el cuerpo copian un
número o un estado que otra issue del mismo colapso puede mover, y nombran el archivo
donde vive. `Qué hay que construir` dice qué tiene que ser cierto al terminar, no
cuánto falta. No lleva check: detectar un conteo en prosa es verificar contenido
conversacional, y el encuadre del mapa lo descarta.

Las issues ya creadas no se tocan. Corregir una issue de ejecución que se escribió mal
es trabajo del equipo sobre su tracker, que es lo que el mapa dejó fuera de alcance al
resolver el 12. El proposal de CRM-3408 ya manda sobre su cuerpo.
