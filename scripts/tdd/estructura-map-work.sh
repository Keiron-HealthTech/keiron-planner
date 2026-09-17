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
grep -qF 'status: done' "$COMANDO" || n "$COMANDO no lleva la frase de la fila 55 sobre aterrizar en un corte con status: done"
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
for op in preflight "map:read" "frontier:query" "ticket:claim" "ticket:create" "ticket:block" "ticket:resolve" "ticket:rule-out"; do
  grep -qF "$op" "$SKILL" || n "el puntero ADAPTER de $SKILL no nombra $op"
done
for prohibida in "map:write" "map:create" "milestone:create" "work:write"; do
  grep -qF "$prohibida" "$SKILL" && n "$SKILL nombra $prohibida, que no es una de sus ocho operaciones"
done
for paso in 1 2 3 4 5 6 7 8; do
  grep -qE "^## Step $paso," "$SKILL" || n "$SKILL no lleva el paso $paso"
done
for paso in 9 10; do
  grep -qE "^## Step $paso," "$SKILL" && n "$SKILL lleva el paso $paso, que es de un corte posterior"
done
# El paso 7 no rechaza un map:research y dice por que la excepcion todavia no licencia nada.
grep -qF "map:research" "$SKILL" || n "$SKILL no nombra map:research en su paso 7"
grep -qF "one per session" "$SKILL" || n "$SKILL no dice que un map:research se trabaja uno por sesion"
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
grep -qF "research-subagent.md" "$SKILL" && n "$SKILL nombra un archivo que no existe"
grep -qF "| Condition | Verdict | Token |" "$SKILL" && n "$SKILL repite la tabla del veredicto en vez de citarla"
for tok in map-new release-claim break-cycle map-collapse sdd-new; do
  grep -qF "\`next_recommended: $tok\`" "$SKILL" || n "$SKILL no cita el token $tok que sus pasos 2 y 3 emiten"
done
# El paso 3 no puede emitir map-work: un veredicto que se recomienda a si mismo es un
# bucle, porque la sesion volveria a derivar el mismo veredicto sin haber trabajado nada.
# El paso 8 SI lo emite, y es legitimo: ahi ya se resolvio un ticket y la frontera cambio.
paso3="$(awk '/^## Step 3,/{f=1} /^## Step 4,/{f=0} f' "$SKILL")"
printf '%s\n' "$paso3" | grep -qF '`next_recommended: map-work`' && n "el paso 3 de $SKILL se recomienda a si mismo, y eso es un bucle"
paso8="$(awk '/^## Step 8,/{f=1} f' "$SKILL")"
printf '%s\n' "$paso8" | grep -qF '`next_recommended: map-work`' || n "el paso 8 de $SKILL no cierra con ningun token"
grep -qF "ticket:claim --ctx" "$SKILL" || n "$SKILL no invoca ticket:claim en su paso 6"
grep -qF 'Pass no `--release` here' "$SKILL" || n "$SKILL no dice que el paso 6 va sin --release"

if [ "$fallas" -gt 0 ]; then echo "fallas=$fallas"; exit 1; fi
echo "OK - la estructura del comando y de la skill de /map-work"
