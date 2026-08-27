# 14: Si el preflight corre por invocación o por sesión

**Tipo:** `map:grilling` · **Modo:** HITL (`hitl:dev`)
**Bloqueado por:** nada. Tomable ahora.
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
