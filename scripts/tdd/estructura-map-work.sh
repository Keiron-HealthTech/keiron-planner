#!/usr/bin/env bash
# Andamio de TDD, no un check del set: vive fuera del glob scripts/check-*
# a proposito, y por eso run-checks.sh no lo corre. El contrato estructural
# de commands/map-work.md y skills/map-work/SKILL.md, escrito en rojo antes
# de que los dos archivos existieran. Se corre con scripts/tdd/correr.sh.
cd "$(dirname "$0")/../.."
fallas=0
n() { echo "FAIL - $1"; fallas=$((fallas + 1)); }

COMANDO=commands/map-work.md
SKILL=skills/map-work/SKILL.md

[ -f "$COMANDO" ] || n "no existe $COMANDO"
[ -f "$SKILL" ] || n "no existe $SKILL"
if [ "$fallas" -gt 0 ]; then echo "fallas=$fallas"; exit 1; fi

fm() { awk 'NR==1 && $0 != "---" {exit} NR==1 {next} /^---$/ {exit} {print}' "$1"; }

# --- el comando ---
claves="$(fm "$COMANDO" | grep -oE '^[a-z-]+:' | tr -d ':' | sort | tr '\n' ' ')"
[ "$claves" = "argument-hint description lang " ] || n "el frontmatter de $COMANDO declara '$claves' y tiene que declarar exactamente argument-hint, description y lang"
fm "$COMANDO" | grep -qE '^lang: en$' || n "$COMANDO no declara lang: en"
[ "$(grep -c '^ROUTE: skills/map-work/SKILL.md$' "$COMANDO")" = "1" ] || n "$COMANDO no declara exactamente un ROUTE: a skills/map-work/SKILL.md"
grep -q -- "--bootstrap" "$COMANDO" && n "$COMANDO nombra --bootstrap y la afirmación 39a lo prohíbe"
[ "$(grep -c '`next_recommended: ' "$COMANDO")" = "0" ] || n "$COMANDO cita un token, y los tokens viven en la skill"
grep -qE '^## Step ' "$COMANDO" && n "$COMANDO numera pasos y tiene que delegar sin restatearlos"

# --- la skill ---
for clave in name description license metadata lang; do
  fm "$SKILL" | grep -qE "^$clave:" || n "el frontmatter de $SKILL no declara $clave"
done
for sub in author version scope auto_invoke; do
  fm "$SKILL" | grep -qE "^  $sub:" || n "el metadata de $SKILL no declara $sub"
done
fm "$SKILL" | grep -qE '^lang: en$' || n "$SKILL no declara lang: en"
for puntero in "CONTRACT:" "TEMPLATES:" "ADAPTER:"; do
  grep -q "^$puntero" "$SKILL" || n "$SKILL no abre con el puntero $puntero"
done
for op in preflight "map:read" "frontier:query" "ticket:claim" "ticket:create" "ticket:block" "ticket:resolve" "ticket:rule-out" "map:write" "milestone:create" "work:write"; do
  grep -qF "$op" "$SKILL" || n "el puntero ADAPTER de $SKILL no nombra $op"
done
# map:write es la novena y entro por la rama de research del paso 8: el padre escribe el
# mapa porque ahi ninguna resolucion suya lo hace. En cualquier otro camino la quinta
# escritura sigue viviendo adentro de ticket:resolve, y por eso la rama se nombra aparte.
grep -qF "belongs to the research branch of step 8 and to no other path" "$SKILL" || n "$SKILL nombra map:write sin acotarlo a la rama de research"
grep -qF "map:create" "$SKILL" && n "$SKILL nombra map:create, que no es una de sus once operaciones"
for paso in 1 2 3 4 5 6 7 8 9 10; do
  grep -qE "^## Step $paso," "$SKILL" || n "$SKILL no lleva el paso $paso"
done
# La ausencia de un paso once no se puede afirmar por nombre; el conteo exacto si.
step_count="$(grep -cE '^## Step [0-9]+,' "$SKILL" || true)"
[ "$step_count" = "10" ] || n "$SKILL lleva $step_count pasos y tiene que llevar exactamente diez"
# El paso 7 despacha el fan-out de research, y esa es la unica excepcion a uno por sesion.
# Las dos mitades se afirman por separado a proposito: que la regla sigue valiendo para todo
# lo que se trabaja en conversacion, y cual es el unico tipo que la rompe. Afirmar solo la
# primera dejaria pasar un archivo que borro la excepcion; solo la segunda, uno que aflojo
# la regla para todos.
grep -qF "map:research" "$SKILL" || n "$SKILL no nombra map:research en su rama de fan-out"
grep -qF "one per session" "$SKILL" || n "$SKILL no dice que cada tipo trabajado en conversacion sigue siendo uno por sesion"
grep -qF "is the one exception" "$SKILL" || n "$SKILL no nombra a map:research como la excepcion a uno por sesion"
# El paso 8 pide confirmacion UNA vez y nombra el negativo explicito de la niebla.
grep -qF '`ninguna`' "$SKILL" || n "$SKILL no nombra el negativo explicito de la seccion de niebla"
grep -qF "ticket:resolve --ctx" "$SKILL" || n "$SKILL no invoca ticket:resolve en su paso 8"
grep -qF "ticket:rule-out" "$SKILL" || n "$SKILL no nombra ticket:rule-out en su paso 8"
# La rama de otro rol suelta la toma y NUNCA resuelve.
grep -qF "ticket:claim --ctx <the blob from step 1> --issue <the chosen ticket> --release" "$SKILL" || n "$SKILL no suelta la toma en la rama de otro rol"
# Ninguna de las tres escrituras reintenta a las otras, asi que una falla en cualquiera
# deja la toma sin soltar: la rama tiene que decir eso y prohibir soltarla fuera de orden.
grep -qF "the claim from step 6 is still yours to release until the third one" "$SKILL" || n "$SKILL no dice que una falla en la secuencia de tres deja la toma sin soltar"
grep -qF "Never run the release out of order" "$SKILL" || n "$SKILL no prohibe soltar la toma antes de que ticket:block aterrice"
grep -q -- "--bootstrap" "$SKILL" && n "$SKILL nombra --bootstrap"
grep -qF "skills/_shared/research-subagent.md" "$SKILL" || n "$SKILL no nombra por su ruta el prompt del subagente de research que su paso 7 despacha"
grep -qF "| Condition | Verdict | Token |" "$SKILL" && n "$SKILL repite la tabla del veredicto en vez de citarla"
for tok in map-new release-claim break-cycle map-collapse sdd-new; do
  grep -qF "\`next_recommended: $tok\`" "$SKILL" || n "$SKILL no cita el token $tok que sus pasos 2 y 3 emiten"
done
# El paso 3 no puede emitir map-work: un veredicto que se recomienda a si mismo es un
# bucle, porque la sesion volveria a derivar el mismo veredicto sin haber trabajado nada.
# El paso 10 SI lo emite, y es legitimo: ahi ya se resolvio un ticket y la frontera cambio.
paso3="$(awk '/^## Step 3,/{f=1} /^## Step 4,/{f=0} f' "$SKILL")"
printf '%s\n' "$paso3" | grep -qF '`next_recommended: map-work`' && n "el paso 3 de $SKILL se recomienda a si mismo, y eso es un bucle"
# El paso 8 resuelve y no cierra: el token vive en el paso 10 y en ningun otro. Cada rango se
# acota en el encabezado siguiente; sin el corte, awk leeria hasta el final y un literal del
# paso 10 daria verde sobre el paso equivocado.
step8="$(awk '/^## Step 8,/{f=1} /^## Step 9,/{f=0} f' "$SKILL")"
printf '%s\n' "$step8" | grep -qF 'ticket:resolve --ctx' || n "el paso 8 de $SKILL no invoca ticket:resolve"
# Con hitl:design el paso 8 pasa la entrega, y el paso 10 la nombra en el reporte.
printf '%s\n' "$step8" | grep -qF -- '--design-delivery' || n "el paso 8 de $SKILL no pasa --design-delivery a ticket:resolve"
step9="$(awk '/^## Step 9,/{f=1} /^## Step 10,/{f=0} f' "$SKILL")"
for op in "milestone:create" "work:write"; do
  printf '%s\n' "$step9" | grep -qF "$op" || n "el paso 9 de $SKILL no nombra $op, que es lo que el aterrizaje escribe"
done
printf '%s\n' "$step9" | grep -qF 'status: done' || n "el paso 9 de $SKILL no prohibe aterrizar en un corte terminado"
for tipo in "map:grilling" "map:prototype"; do
  printf '%s\n' "$step9" | grep -qF "$tipo" || n "el paso 9 de $SKILL no acota el aterrizaje al tipo $tipo"
done
printf '%s\n' "$step9" | grep -qF -- '--append-collapse' || n "el paso 9 de $SKILL no nombra --append-collapse, que es como el corte nuevo llega al mapa"
step10="$(awk '/^## Step 10,/{f=1} f' "$SKILL")"
# El puntero ADAPTER del preámbulo nombra las once operaciones a propósito, por eso el
# rango de antes del aterrizaje arranca en el paso 1 y no en la primera línea del archivo.
before_landing="$(awk '/^## Step 1,/{f=1} /^## Step 9,/{f=0} f' "$SKILL")"
for op in "milestone:create" "work:write"; do
  printf '%s\n' "$before_landing" | grep -qF "$op" && n "$SKILL nombra $op antes del paso 9, y solo el aterrizaje puede escribirlo"
  printf '%s\n' "$step10" | grep -qF "$op" && n "$SKILL nombra $op después del paso 9, y solo el aterrizaje puede escribirlo"
done
printf '%s\n' "$step10" | grep -qF 'design delivery' || n "el paso 10 de $SKILL no nombra la entrega de diseño en el reporte"
printf '%s\n' "$step10" | grep -qF '`next_recommended: map-work`' || n "el paso 10 de $SKILL no cierra con ningun token"
grep -qF "ticket:claim --ctx" "$SKILL" || n "$SKILL no invoca ticket:claim en su paso 6"
grep -qF 'Pass no `--release` here' "$SKILL" || n "$SKILL no dice que el paso 6 va sin --release"

if [ "$fallas" -gt 0 ]; then echo "fallas=$fallas"; exit 1; fi
echo "OK - la estructura del comando y de la skill de /map-work"
