---
lang: es
---

# Plantillas del mapa

El texto que el plugin produce y que una persona lee en Linear: el overview del
Project, el cuerpo de una issue de ejecución, el comentario que resuelve un
ticket, las dos viñetas que el mapa acumula, y la entrega de diseño con el
comentario que la cierra. Va en español porque su lector
final es una persona y no el modelo.

Cada plantilla vive adentro de un bloque cercado. Los encabezados de nivel dos de
este archivo son de este archivo; los que cuentan como plantilla son los que están
adentro de la cerca. Sin esa separación los dos serían indistinguibles.

Ninguna plantilla se escribe a mano contra Linear salvo una: las escribe el
adapter. Lo que está acá es la forma que el adapter produce, para que el modelo
sepa qué va en cada argumento y la persona sepa qué va a leer. La excepción es el
comentario que cierra una entrega de diseño, que escribe Diseño a mano.

## El DD

El overview del Project. Las seis secciones son las anclas de lectura, en este
orden, y el adapter las escribe desde una sola constante: si el orden o el texto
de una cambian allá, cambian acá. Lo que ya había en el overview sobrevive
verbatim debajo, bajo `## Antes del mapa`, que no es un ancla de lectura y por eso
no aparece en el bloque.

```
## Destino

La frase que dictó la persona, la que dice adónde va este mapa.

## Notas

## Decisiones hasta ahora

## Aún no especificado

## Fuera de alcance

## El colapso
```

`## El colapso` nace vacío con el mapa, lo llena el colapso, y después
el aterrizaje le agrega una línea por cada corte que crea. Las otras cinco las llena el
trabajo.

## El cuerpo de una issue de ejecución

Lo que produce un colapso o un aterrizaje. Su título es un imperativo y no una
pregunta, y la issue no lleva el label `map`: no es un ticket de decisión.

Ni el título ni el cuerpo copian un número o un estado que otra issue del mismo
colapso puede mover: nombran el archivo donde vive. La issue se toma semanas después
de escrita, con los cortes anteriores ya ejecutados, y un conteo copiado llega
vencido. `Qué hay que construir` dice qué tiene que ser cierto al terminar, no
cuánto falta para llegar.

```
## Qué hay que construir

## Lo que ya está decidido

## Qué queda fuera
```

## El comentario de resolución

Lo que se escribe al cerrar un ticket de decisión. Las seis secciones van en este
orden, y `## Lo que se cayó` va tercera, entre `## Por qué` y `## Niebla
graduada`: primero la decisión, después su razón, y recién ahí lo que la decisión
descartó. Una alternativa descartada leída antes de la razón no se entiende.

```
## La decisión

## Por qué

## Lo que se cayó

## Niebla graduada

## Tickets nuevos

## Qué corrige o empuja
```

## Decisiones hasta ahora (ejemplo)

Una decisión ocupa una línea física y nada más: el identificador del ticket
enlazado a su url entre ángulos, dos puntos fuera del enlace, y el gist. Hay una
sola línea por ticket. El gist tiene tope de 120 caracteres, y el detalle vive en el
comentario de resolución del ticket, que el enlace ya alcanza. El índice con el
formato colapsable que esta forma reemplazó se comía dos tercios del documento con
diez entradas.

```
- [CRM-3401](<https://linear.app/keiron/issue/CRM-3401>): el tracker es Linear y el mapa vive en el overview del Project
```

## La niebla (ejemplo)

Una viñeta de niebla empieza con su título entre dobles asteriscos, un espacio, y
el cuerpo. El título en negrita es la clave única de una viñeta de niebla: dos
viñetas con el mismo título son la misma entrada, aunque el cuerpo haya cambiado,
y es el título lo que se pasa para graduarla.

```
- **Los reportes del equipo clínico.** Todavía no sabemos cuáles pide, así que no
  se puede enunciar la pregunta con precisión.
- **La migración de los datos históricos.** Falta medir cuántos registros hay
  antes de poder decidir si entra al alcance.
```

Una entrada de `## Fuera de alcance` lleva la misma forma, con su título en
negrita, y su título es también su clave única.

## El cuerpo de una entrega de diseño

La issue `Diseño terminado: <la vista>` que nace al cerrar un ticket de decisión
con `hitl:design`, en la misma escritura que los tickets nuevos. Lleva
`hitl:design` y `map:design-delivery`, no lleva `map` y la asigna el adapter a
quien cerró la decisión. Su cuerpo es la propuesta escrita que Diseño aprobó en la
rama de propuesta escrita de prototype, con sus cuatro partes, y abre con el
enlace al ticket de decisión: la entrega no tiene relación con él, así que el
enlace es lo único que las une.

```
Decisión: <enlace al ticket de decisión>

## Para qué es la vista

## Qué debe tener

## Qué considerar

## Qué queda abierto
```

## El comentario que cierra una entrega de diseño

La única plantilla que no escribe el adapter: la escribe Diseño a mano en Linear al
cerrar la entrega, y ningún comando la cierra. El diseño vive en Claude Design, así
que el comentario lleva su link vivo y nunca una copia congelada.

```
## Quién eligió

## El diseño

El link vivo de Claude Design.

## Por qué así

## A quién se mostró

## Alternativas

Cuáles hubo y cuál ganó.
```
