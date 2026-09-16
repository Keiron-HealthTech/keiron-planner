---
lang: es
---

# Plantillas del mapa

El texto que el plugin produce y que una persona lee en Linear: el overview del
Project, el cuerpo de una issue de ejecución, el comentario que resuelve un
ticket, y las dos viñetas que el mapa acumula. Va en español porque su lector
final es una persona y no el modelo.

Cada plantilla vive adentro de un bloque cercado. Los encabezados de nivel dos de
este archivo son de este archivo; los que cuentan como plantilla son los que están
adentro de la cerca. Sin esa separación los dos serían indistinguibles.

Ninguna plantilla se escribe a mano contra Linear: las escribe el adapter. Lo que
está acá es la forma que el adapter produce, para que el modelo sepa qué va en
cada argumento y la persona sepa qué va a leer.

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

`## El colapso` nace vacío con el mapa y lo llena el colapso. Las otras cinco las
llena el trabajo.

## El cuerpo de una issue de ejecución

Lo que produce un colapso o un aterrizaje. Su título es un imperativo y no una
pregunta, y la issue no lleva el label `map`: no es un ticket de decisión.

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

Una decisión ocupa una línea física y nada más: el enlace del ticket, dos puntos,
y el gist. El gist tiene tope de 120 caracteres, y el detalle vive en el
comentario de resolución del ticket, que el enlace ya alcanza. El índice con el
formato colapsable que esta forma reemplazó se comía dos tercios del documento con
diez entradas.

```
- https://linear.app/keiron/issue/CRM-3401: el tracker es Linear y el mapa vive en el overview del Project
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
