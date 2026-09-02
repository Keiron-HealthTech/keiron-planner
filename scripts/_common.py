"""Gemelo de _common.sh. Se importa, nunca se ejecuta: sin shebang y sin bit de
ejecución, igual que su gemelo, y su nombre no matchea el glob check-*."""
import os
import sys

MANIFEST = ".claude-plugin/plugin.json"
SCRIPTS = "scripts"
CHECKS_MD = "scripts/CHECKS.md"

# Derivado del archivo que se ejecuta, para que el nombre del mensaje no se pueda
# separar del nombre del archivo. Sobrevive al re-exec porque el argumento del script
# es una ruta absoluta y no un nombre inventado.
CHECK_NAME = os.path.basename(sys.argv[0])
if CHECK_NAME.endswith(".sh"):
    CHECK_NAME = CHECK_NAME[:-3]
if CHECK_NAME.endswith(".py"):
    CHECK_NAME = CHECK_NAME[:-3]

# Las fallas se acumulan en vez de salir en la primera, así que una corrida nombra todo
# lo que está roto y no solo lo primero.
FAILURES = []


def fail(mensaje):
    # La neutralización va acá y no en cada aserción: el separador de report es el salto
    # de línea, y un valor leído del artefacto chequeado puede traerlo adentro y
    # fabricarse una línea propia. El [N] va embebido en el string, nunca como argumento
    # aparte: es lo que permite extraerlo con la misma expresión de un .sh y de un .py.
    FAILURES.append(str(mensaje).replace("\r", " ").replace("\n", " "))


def report():
    if not FAILURES:
        return
    sys.stderr.write("%s: FAIL - %s\n" % (CHECK_NAME, FAILURES[0]))
    for mensaje in FAILURES[1:]:
        sys.stderr.write("  also: %s\n" % mensaje)
    sys.exit(1)


def bail(mensaje):
    """El tercer tier: reporta y sale ahí mismo, porque las fallas derivadas de una
    fuente ausente sepultan el mensaje que importa."""
    fail(mensaje)
    report()
    sys.exit(1)


def require_nonempty(valor, mensaje):
    # Se usa sobre el conjunto y nunca sobre un conteo: 0 es falsy, así que un conteo
    # legítimamente cero cortaría la corrida como si la fuente se hubiera movido.
    if not valor:
        bail(mensaje)
