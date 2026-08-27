#!/usr/bin/env python3
"""
Genera las cuatro variantes del mapa de juguete del ticket 04.

Las cuatro tienen el MISMO contenido: quince decisiones, la niebla real, el
fuera de alcance real y veinte enlaces. Lo unico que cambia es la forma del
indice de decisiones, que es la seccion que hoy se come el 65% del mapa.

  A  parrafo por decision, la forma de hoy, sin tocar nada
  B  una linea por decision, el detalle solo en el ticket
  C  tabla de tres columnas
  D  una linea por decision con el detalle anidado debajo

Uso: python3 variants.py <dir-de-salida>

OJO: esto se corrio contra el MAP.md en forma A, ANTES de la migracion que decidio
este mismo ticket. Hoy MAP.md esta en forma B y la variante A ya no se reproduce:
el parser de abajo busca entradas de parrafo que ya no existen. Es codigo
descartable capturado como fuente primaria, no una herramienta que se vuelva a
correr. Para reproducirlo hace falta el MAP.md del commit anterior al cierre del 04.
"""
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
MAP = (ROOT / "MAP.md").read_text()

# Los enlaces del juguete apuntan a las cinco issues reales del sandbox del
# ticket 01, cicladas. Son clicables de verdad; no son la issue que dice el texto.
SANDBOX = ["CRM-3346", "CRM-3349", "CRM-3350", "CRM-3347", "CRM-3348"]
_n = [0]


def issue_url():
    ident = SANDBOX[_n[0] % len(SANDBOX)]
    _n[0] += 1
    return ident, "https://linear.app/keiron/issue/%s" % ident


def section(name, nxt=None):
    i = MAP.index("## " + name)
    j = MAP.index("## " + nxt) if nxt else len(MAP)
    return MAP[i:j]


DEC = section("Decisiones hasta ahora", "Aún no especificado")
REAL = re.findall(r"(?m)^- \[\d+:.*?(?=\n- \[\d+:|\Z)", DEC, re.S)
REAL = [e.strip() for e in REAL]

# --- las cinco entradas de relleno -------------------------------------------
# No son decisiones. Son los cuatro tickets que siguen abiertos y un item de la
# niebla, puestos con SU PROPIA prosa para que la entrada pese lo que pesa una
# entrada real. Van marcadas para que nadie las lea como decididas.
FILLER = [
    ("04", "Un mapa de juguete en Linear, para ver si el Document aguanta",
     "el Document aguanta como casa del mapa a quince decisiones, con la niebla y el "
     "fuera de alcance en el mismo documento, y alguien que no estuvo en las sesiones "
     "entiende dónde va el proyecto abriéndolo solo. La forma del índice se decidió "
     "mirando cuatro variantes construidas a mano en un Project descartable, no leyendo "
     "un template. El juguete no se borra ni se promueve: queda como fuente primaria con "
     "su enlace anotado en el ticket, y la decisión validada entra al glosario. Ninguna "
     "de las dos ramas de prototipo de Matt encajaba, porque el artefacto no es lógica "
     "ni es UI sino un documento en una herramienta de terceros, así que la rama se "
     "construyó a mano."),
    ("10", "Qué chequean los checks estructurales",
     "los checks son scripts sobre el repo al estilo de los `check-*.sh` de SDD, y "
     "cuentan lo que el 08 fijó: el conjunto de tokens, los cinco archivos de comandos, "
     "los doce subcomandos del adapter, los encabezados de las plantillas y la columna de "
     "idioma. Las cuarenta y una afirmaciones chequeables ya estaban escritas al final del "
     "research de cada ticket que las produjo, repartidas 1 a 6 del 08, 7 a 13 del 06, 14 "
     "a 21 del 07, 22 a 31 del 09 y del 13, y 32 a 41 del 14, con dos reemplazadas que no "
     "se cuentan dos veces. Queda por decidir el caso del label de tipo duplicado, que se "
     "chequea contra Linear y no contra el repo, si los checks corren en CI o a mano, y si "
     "un check que falla rompe el build o solo avisa."),
    ("11", "Qué hace `/map-new` sobre un Project que ya arrancó",
     "el caso pasa de hipotético a ser el camino más probable en el CRM de hoy, porque el "
     "03 decidió que `map:create` adopta el Project si le pasan uno y el 08 decidió que "
     "`/map-new` crea siempre el DD. Queda por resolver qué pasa con las issues de "
     "ejecución que ya viven en ese Project y comparten Project con los tickets de "
     "decisión, separadas solo por el label `map`; qué pasa con las decisiones ya tomadas "
     "y no escritas, si el mapa nace con Decisiones hasta ahora vacío y miente o si hay un "
     "paso de recuperación; si el trabajo ya hecho recorta el destino y quién lo dice; y si "
     "un mapa puesto a mitad de camino se distingue de uno trazado desde cero."),
    ("12", "Qué hace el plugin cuando aparece una decisión nueva sobre un mapa colapsado",
     "para la v1 la respuesta es a mano: quien resuelve ese ticket crea la issue de "
     "ejecución él mismo. El caso existe porque el colapso es un evento único que corre "
     "con la frontera vacía y una segunda corrida se niega, pero durante la construcción "
     "aparece una pregunta que el mapa no vio, alguien crea el ticket de decisión, "
     "`/map-work` lo resuelve, la decisión entra al índice y no hay colapso que la lleve a "
     "ejecución. Queda por decidir si `/map-collapse` gana un modo incremental o si es otro "
     "comando, cómo se deduplica contra los milestones y las issues que ya existen, en qué "
     "milestone cae una decisión posterior al colapso, y si el mapa se puede descolapsar."),
    ("15", "Cuándo el plugin escribe como app y no como persona",
     "el 07 cerró Personal API key para la v1 y midió lo que cuesta OAuth: sin device flow "
     "pide un servidor de callback y refresh de veinticuatro horas. Lo que no se puede "
     "formular todavía es el disparador. El día que el mapa lo mantenga una cuenta de bot, "
     "`actor: app` le saca a la persona la autoría del comentario de resolución, y no está "
     "claro qué se pone en su lugar. El 09 le encontró el primer beneficio concreto y "
     "medible: `Document.updatedBy` existe, y con Personal API key no distingue al plugin "
     "de la persona porque son el mismo usuario."),
]

# --- una línea por decisión, para las variantes B, C y D ---------------------
# El gist es presentación, no decisión: el contenido ya estaba resuelto.
ONELINE = {
    "14": ("Si el preflight corre por invocación o por sesión",
           "Una vez por conductor, con la salida como blob opaco que todos reciben en `--ctx`.",
           "El preflight escribía, y `/map-status` promete no escribir."),
    "13": ("Si una pestaña abierta puede pisar una escritura del plugin",
           "No puede: `documentUpdate` mueve el estado Yjs, así que no deja rama que el cliente pueda ganar.",
           "Con markdown rancio el plugin sí borra una línea escrita en la UI."),
    "09": ("Cómo evita el plugin pisar una edición humana del mapa",
           "No detecta el conflicto, lo evita: relee justo antes de escribir y la ventana baja a 332 ms.",
           "`updatedAt` está coalescido y quedó quieto 300 s con contenido nuevo."),
    "07": ("Distribución e instalación",
           "Entra al marketplace de `spec-driven-dev` y declara la dependencia de verdad, sin constraint.",
           "El setup por repo no existe: el 03 y el 08 se lo vaciaron entero."),
    "06": ("Qué hace exactamente `/map-collapse`",
           "Es HITL y es un evento único: dos pasadas, cortes y después issues, y escribe N+2 veces.",
           "Todo lo que el plugin cree por API cae en Triage."),
    "05": ("Cómo se adaptan grilling, domain-modeling y prototype al vivir acá",
           "Model-invoked con `/grill` como única puerta, en inglés y con el frontmatter de SDD.",
           "El glosario del dominio vive en un repo central y el plugin no lo crea."),
    "02": ("Qué permite y limita la API de Documents de Linear",
           "Sirve como casa del mapa y no hay blocker: el tamaño y el rate limit son irrelevantes.",
           "No hay control de concurrencia, y eso graduó al ticket 09."),
    "01": ("Cómo lee el agente el grafo de dependencias de Linear",
           "Con GraphQL crudo en un round-trip; el SDK gasta 15 requests donde eso gasta 1.",
           "La pregunta estaba mal planteada: la API siempre expuso las relaciones."),
    "03": ("Las operaciones de wayfinding, expresadas en Linear",
           "Son ocho y no seis, todas por GraphQL crudo y sin fallbacks.",
           "Cerrado no es un test de `state.type`: `Blocked` está tipado `canceled`."),
    "08": ("Qué cambia de los dos modos de wayfinder al keironizarlos",
           "Ocho cosas: tres adaptaciones forzadas, dos endurecimientos y tres nuestras.",
           "No hay rama descartable de research: con once repos obliga a elegir uno."),
    "04": ("Un mapa de juguete en Linear, para ver si el Document aguanta",
           "[RELLENO] El Document aguanta a quince decisiones y la forma del índice se decidió mirando.",
           "Ninguna de las dos ramas de prototipo de Matt encajaba."),
    "10": ("Qué chequean los checks estructurales",
           "[RELLENO] Scripts sobre el repo que cuentan las cuarenta y una afirmaciones ya escritas.",
           "El label de tipo duplicado se chequea contra Linear, no contra el repo."),
    "11": ("Qué hace `/map-new` sobre un Project que ya arrancó",
           "[RELLENO] Adopta el Project vivo y hay un paso de recuperación de lo ya decidido.",
           "Es el camino más probable en el CRM de hoy, no el excepcional."),
    "12": ("Qué hace el plugin cuando aparece una decisión nueva sobre un mapa colapsado",
           "[RELLENO] Para la v1, a mano: quien resuelve crea la issue de ejecución él mismo.",
           "Un mapa que se reabre mucho es señal de un destino mal trazado."),
    "15": ("Cuándo el plugin escribe como app y no como persona",
           "[RELLENO] Personal API key para la v1; OAuth pide callback y refresh de 24 horas.",
           "`Document.updatedBy` no distingue al plugin de la persona."),
}

ORDER = ["14", "13", "09", "07", "06", "05", "02", "01", "03", "08",
         "04", "10", "11", "12", "15"]

BANNER = """> **JUGUETE.** No es el mapa de `keiron-planner`. Lo construyó el ticket 04 en un
> Project descartable para mirar si un Document de Linear aguanta un mapa de quince
> decisiones. Diez entradas del índice son reales, textuales, de los tickets 01, 02,
> 03, 05, 06, 07, 08, 09, 13 y 14. Las cinco marcadas `[RELLENO]` **no son
> decisiones**: son los cuatro tickets que siguen abiertos y un ítem de la niebla,
> puestos con su propia prosa para que la entrada pese lo que pesa una entrada real.
> Los veinte enlaces apuntan a las cinco issues del sandbox del ticket 01, cicladas:
> son clicables, y ninguno es la issue que dice el texto.

**Variante %s de 4: %s.** Las cuatro tienen el mismo contenido y solo cambia la forma
de la sección Decisiones hasta ahora.
"""

def fog_with_links():
    """La niebla real, pero con los tickets que nombra convertidos en enlaces.

    El mapa de hoy los nombra en prosa y no los enlaza. El juguete los enlaza
    porque el ticket 04 pregunta por un mapa con veinte enlaces, y aca es donde
    aparecen los que faltan.
    """
    fog = section("Aún no especificado", "Fuera de alcance")
    def repl(m):
        num = m.group(2)
        _, url = issue_url()
        return "%s[%s](%s)" % (m.group(1), num, url)
    return re.sub(r"(El |el |los |del |al )(0[13679]|08|06)\b", repl, fog)


def head():
    return "# DD: keiron-planner (JUGUETE del ticket 04)\n\n"


def body_after_index():
    return "\n" + fog_with_links() + section("Fuera de alcance")


def relink(entry):
    """Cambia el link local del ticket por una issue real del sandbox."""
    ident, url = issue_url()
    return re.sub(r"\]\(issues/[^)]+\)", "](%s)" % url, entry, count=1)


def variant_a():
    out = [head(), BANNER % ("A", "párrafo por decisión, la forma de hoy"), "\n"]
    out.append(section("Destino", "Notas"))
    out.append(section("Notas", "Decisiones hasta ahora"))
    out.append("## Decisiones hasta ahora\n\n")
    for e in REAL:
        out.append(relink(e) + "\n\n")
    for num, title, gist in FILLER:
        ident, url = issue_url()
        out.append("- [%s: %s](%s): **[RELLENO, no es una decision]** %s\n\n"
                   % (num, title, url, gist))
    out.append(body_after_index())
    return "".join(out)


def variant_b():
    out = [head(), BANNER % ("B", "una línea por decisión, el detalle solo en el ticket"), "\n"]
    out.append(section("Destino", "Notas"))
    out.append(section("Notas", "Decisiones hasta ahora"))
    out.append("## Decisiones hasta ahora\n\n")
    for num in ORDER:
        title, gist, _ = ONELINE[num]
        ident, url = issue_url()
        out.append("- [%s: %s](%s): %s\n" % (num, title, url, gist))
    out.append("\n")
    out.append(body_after_index())
    return "".join(out)


def variant_c():
    out = [head(), BANNER % ("C", "tabla de tres columnas"), "\n"]
    out.append(section("Destino", "Notas"))
    out.append(section("Notas", "Decisiones hasta ahora"))
    out.append("## Decisiones hasta ahora\n\n")
    out.append("| Ticket | La decision | Lo que se cayo al resolverlo |\n")
    out.append("| --- | --- | --- |\n")
    for num in ORDER:
        title, gist, fell = ONELINE[num]
        ident, url = issue_url()
        out.append("| [%s](%s) | **%s.** %s | %s |\n" % (num, url, title, gist, fell))
    out.append("\n")
    out.append(body_after_index())
    return "".join(out)


def variant_d():
    out = [head(), BANNER % ("D", "una línea por decisión con el detalle anidado"), "\n"]
    out.append(section("Destino", "Notas"))
    out.append(section("Notas", "Decisiones hasta ahora"))
    out.append("## Decisiones hasta ahora\n\n")
    real_by_num = {re.match(r"- \[(\d+):", e).group(1): e for e in REAL}
    filler_by_num = {n: g for n, t, g in FILLER}
    for num in ORDER:
        title, gist, _ = ONELINE[num]
        ident, url = issue_url()
        out.append("- [%s: %s](%s): %s\n" % (num, title, url, gist))
        if num in real_by_num:
            detail = real_by_num[num]
            detail = re.sub(r"^- \[\d+:[^\]]*\]\([^)]*\):\s*", "", detail, flags=re.S)
        else:
            detail = "**[RELLENO, no es una decision]** " + filler_by_num[num]
        detail = " ".join(detail.split())
        out.append("  - %s\n" % detail)
    out.append("\n")
    out.append(body_after_index())
    return "".join(out)


def main():
    outdir = pathlib.Path(sys.argv[1])
    outdir.mkdir(parents=True, exist_ok=True)
    for letter, fn in (("A", variant_a), ("B", variant_b), ("C", variant_c), ("D", variant_d)):
        _n[0] = 0
        text = fn()
        p = outdir / ("variant-%s.md" % letter)
        p.write_text(text)
        links = len(re.findall(r"\]\(", text))
        idx = text[text.index("## Decisiones hasta ahora"):text.index("## Aún no especificado")]
        print("%s  %6d chars  %4d lineas  %3d enlaces  |  indice: %5d chars, %3d lineas (%d%% del doc)"
              % (letter, len(text), text.count("\n"), links, len(idx), idx.count("\n"),
                 round(100 * len(idx) / len(text))))


if __name__ == "__main__":
    main()
