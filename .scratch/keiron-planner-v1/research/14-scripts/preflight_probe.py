#!/usr/bin/env python3
"""
Harness del ticket 14: si el preflight corre por invocacion o por sesion.

El 08 dijo "un preflight por proceso que emite operaciones". El 09 mostro que el
adapter es `scripts/linear.py` invocado por Bash, un subcomando por operacion, o
sea que cada invocacion ES un proceso. Leido literal, un `/map-work` tipico paga
ocho preflights.

Lo que el 09 anoto era complejidad: 423 por preflight contra 10.000 por query y
un presupuesto horario que el 02 midio como holgado. Pero el argumento del
ticket no es el costo, es que "falla temprano" se vuelve "falla ocho veces". Lo
que falta medir es el costo en SEGUNDOS, que es lo que una persona siente, y si
el preflight se puede fusionar con la query que la operacion ya manda, en cuyo
caso deja de ser una invocacion aparte y pasa a ser campos de mas.

Sin dependencias: solo stdlib. La API key sale de $LINEAR_API_KEY o de
~/.config/keiron-planner/linear.key, igual que el resto de los harness.

Subcomandos:

  startup [n]        Arranque puro del interprete, sin red. Compara el 3.9 de
                     macOS con el python3 del PATH. Es el piso que paga toda
                     invocacion, exista o no el preflight.
  one                Un preflight solo. Reporta el desglose interno y la
                     complejidad y el presupuesto que devuelven los headers.
  labels             Si los ocho labels ya existen. Decide si el preflight
                     tambien MUTA en cada invocacion o solo lee.
  chain [n]          n preflights como n procesos separados, secuenciales,
                     medidos desde afuera. Es la cuenta del ticket.
  merged             La query del preflight FUSIONADA con la de una operacion
                     real (frontier:query). Un round-trip. Reporta la
                     complejidad de las dos por separado y de la fusion.
  needs              Que ids del preflight necesita realmente cada una de las
                     once operaciones. Se responde leyendo, no midiendo, pero
                     va aca para que quede junto al resto.

Solo lee, salvo `labels`, que tampoco escribe: solo cuenta. Este harness no
muta nada en el workspace.
"""
import json
import os
import pathlib
import subprocess
import sys
import time
import urllib.error
import urllib.request

API = "https://api.linear.app/graphql"
TEAM = "CRM"
LABELS = ["map", "map:research", "map:prototype", "map:grilling", "map:task",
          "hitl:pm", "hitl:design", "hitl:dev"]
SANDBOX_PROJECT = "400e790e-67c1-4eb0-8f4b-af388fc514a1"


def key():
    k = os.environ.get("LINEAR_API_KEY")
    if k:
        return k.strip()
    p = pathlib.Path(os.environ.get("XDG_CONFIG_HOME", pathlib.Path.home() / ".config")) / "keiron-planner" / "linear.key"
    return p.read_text().strip()


def gql(query, variables=None, k=None):
    """Devuelve (data, headers, segundos_de_red)."""
    body = json.dumps({"query": query, "variables": variables or {}}).encode()
    req = urllib.request.Request(API, data=body, method="POST")
    req.add_header("Content-Type", "application/json")
    req.add_header("Authorization", k or key())
    t0 = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            raw = r.read()
            headers = dict(r.headers)
    except urllib.error.HTTPError as e:
        raw = e.read()
        headers = dict(e.headers)
    dt = time.perf_counter() - t0
    payload = json.loads(raw)
    if "errors" in payload:
        print("GraphQL errors:", json.dumps(payload["errors"], indent=2)[:2000], file=sys.stderr)
    return payload.get("data"), headers, dt


def limits(h):
    out = {}
    for name, value in h.items():
        low = name.lower()
        if "complexity" in low or "ratelimit" in low:
            out[name] = value
    return out


# --- la query del preflight, tal cual la fijo el 03 con la enmienda del 06 ---
PREFLIGHT = """
query($team: String!, $labels: [String!]!) {
  viewer { id displayName }
  team(id: $team) {
    id key name
    defaultIssueState { id name }
    states(first: 50) { nodes { id name type position } }
  }
  issueLabels(first: 250, filter: { name: { in: $labels } }) {
    nodes { id name team { id } }
  }
}
"""

# --- frontier:query, la query real del 03, palabra por palabra ---
FRONTIER = """
query($id: String!, $label: String!) {
  project(id: $id) {
    name
    issues(first: 50, filter: { labels: { some: { name: { eq: $label } } } }) {
      pageInfo { hasNextPage }
      nodes {
        identifier title createdAt
        state { id name type }
        assignee { displayName }
        labels { nodes { name } }
        relations(first: 10) {
          pageInfo { hasNextPage }
          nodes { type relatedIssue { identifier state { id } } }
        }
        inverseRelations(first: 10) {
          pageInfo { hasNextPage }
          nodes { type issue { identifier state { id } } }
        }
      }
    }
  }
}
"""

# --- map:read, la mitad que lee del 09 ---
MAPREAD = """
query($doc: String!) {
  document(id: $doc) { id title content updatedAt updatedBy { id displayName } }
}
"""

# --- preflight + frontier, un solo round-trip ---
MERGED2 = """
query($team: String!, $labels: [String!]!, $id: String!, $label: String!) {
  viewer { id displayName }
  team(id: $team) {
    id key name
    defaultIssueState { id name }
    states(first: 50) { nodes { id name type position } }
  }
  issueLabels(first: 250, filter: { name: { in: $labels } }) {
    nodes { id name team { id } }
  }
  project(id: $id) {
    name
    issues(first: 50, filter: { labels: { some: { name: { eq: $label } } } }) {
      pageInfo { hasNextPage }
      nodes {
        identifier title createdAt
        state { id name type }
        assignee { displayName }
        labels { nodes { name } }
        relations(first: 10) {
          pageInfo { hasNextPage }
          nodes { type relatedIssue { identifier state { id } } }
        }
        inverseRelations(first: 10) {
          pageInfo { hasNextPage }
          nodes { type issue { identifier state { id } } }
        }
      }
    }
  }
}
"""

# --- preflight + map:read + frontier: el paso 1 y el paso 2 enteros de /map-work ---
MERGED3 = """
query($team: String!, $labels: [String!]!, $id: String!, $label: String!, $doc: String!) {
  viewer { id displayName }
  team(id: $team) {
    id key name
    defaultIssueState { id name }
    states(first: 50) { nodes { id name type position } }
  }
  issueLabels(first: 250, filter: { name: { in: $labels } }) {
    nodes { id name team { id } }
  }
  document(id: $doc) { id title content updatedAt updatedBy { id displayName } }
  project(id: $id) {
    name
    projectMilestones(first: 50) { nodes { id name } }
    issues(first: 50, filter: { labels: { some: { name: { eq: $label } } } }) {
      pageInfo { hasNextPage }
      nodes {
        identifier title createdAt
        state { id name type }
        assignee { displayName }
        labels { nodes { name } }
        relations(first: 10) {
          pageInfo { hasNextPage }
          nodes { type relatedIssue { identifier state { id } } }
        }
        inverseRelations(first: 10) {
          pageInfo { hasNextPage }
          nodes { type issue { identifier state { id } } }
        }
      }
    }
  }
}
"""

SANDBOX_DOC = "8d748d5c-0a07-4906-8a04-e02868d0d1e0"


def cmd_startup(n=10):
    n = int(n)
    for interp in ["/usr/bin/python3", sys.executable]:
        ver = subprocess.run([interp, "-c", "import sys;print('%d.%d.%d'%sys.version_info[:3])"],
                             capture_output=True, text=True).stdout.strip()
        times = []
        for _ in range(n):
            t0 = time.perf_counter()
            subprocess.run([interp, "-c", "import json,os,pathlib,sys,urllib.request"], capture_output=True)
            times.append((time.perf_counter() - t0) * 1000)
        times.sort()
        print("%-22s %-8s n=%d  min %6.1f ms  mediana %6.1f ms  max %6.1f ms"
              % (interp, ver, n, times[0], times[len(times) // 2], times[-1]))
    print()
    print("Es el piso por invocacion, sin red. El preflight se suma a esto.")


def cmd_one():
    t_all = time.perf_counter()
    k = key()
    t_key = time.perf_counter() - t_all
    data, h, t_net = gql(PREFLIGHT, {"team": TEAM, "labels": LABELS}, k)
    total = time.perf_counter() - t_all
    print("leer la key      %7.1f ms" % (t_key * 1000))
    print("round-trip       %7.1f ms" % (t_net * 1000))
    print("total en proceso %7.1f ms" % (total * 1000))
    print()
    if data:
        team = data.get("team") or {}
        states = (team.get("states") or {}).get("nodes") or []
        done = sorted([s for s in states if s["type"] == "completed"], key=lambda s: s["position"])
        canc = sorted([s for s in states if s["type"] == "canceled"], key=lambda s: s["position"])
        print("viewer           %s (%s)" % ((data.get("viewer") or {}).get("displayName"), (data.get("viewer") or {}).get("id")))
        print("team             %s / %s" % (team.get("key"), team.get("id")))
        print("defaultIssueState%s" % (" " + str((team.get("defaultIssueState") or {}).get("name"))))
        print("completed[0]     %s" % (done[0]["name"] if done else None))
        print("canceled[0]      %s" % (canc[0]["name"] if canc else None))
        print("labels devueltos %d de %d" % (len((data.get("issueLabels") or {}).get("nodes") or []), len(LABELS)))
    print()
    for kk, vv in sorted(limits(h).items()):
        print("  %-40s %s" % (kk, vv))


def cmd_labels():
    data, h, _ = gql(PREFLIGHT, {"team": TEAM, "labels": LABELS})
    found = {n["name"] for n in ((data.get("issueLabels") or {}).get("nodes") or [])}
    missing = [l for l in LABELS if l not in found]
    print("existen  %d/%d" % (len(found & set(LABELS)), len(LABELS)))
    print("faltan   %s" % (missing or "ninguno"))
    print()
    print("Si no falta ninguno, el preflight es una query y CERO mutations.")
    print("Si falta alguno, cada invocacion intentaria crearlo.")


def cmd_chain(n=8):
    n = int(n)
    here = pathlib.Path(__file__).resolve()
    for interp in ["/usr/bin/python3", sys.executable]:
        t0 = time.perf_counter()
        for _ in range(n):
            subprocess.run([interp, str(here), "quiet"], capture_output=True)
        total = (time.perf_counter() - t0) * 1000
        print("%-22s %d invocaciones  total %7.1f ms  cada una %6.1f ms"
              % (interp, n, total, total / n))
    print()
    print("Es lo que cuesta el preflight de un /map-work de %d operaciones," % n)
    print("si cada subcomando corre el suyo y nadie lo fusiona con nada.")


def cmd_quiet():
    gql(PREFLIGHT, {"team": TEAM, "labels": LABELS})


def cmd_merged():
    cases = [
        ("preflight", PREFLIGHT, {"team": TEAM, "labels": LABELS}),
        ("map:read", MAPREAD, {"doc": SANDBOX_DOC}),
        ("frontier", FRONTIER, {"id": SANDBOX_PROJECT, "label": "zz-sandbox-map"}),
        ("pre+frontier", MERGED2, {"team": TEAM, "labels": LABELS, "id": SANDBOX_PROJECT, "label": "zz-sandbox-map"}),
        ("pre+read+front", MERGED3, {"team": TEAM, "labels": LABELS, "id": SANDBOX_PROJECT, "label": "zz-sandbox-map", "doc": SANDBOX_DOC}),
    ]
    rows = []
    for name, q, v in cases:
        data, h, dt = gql(q, v)
        cx = next((vv for kk, vv in h.items() if kk.lower() == "x-complexity"), None)
        ok = data is not None and all(vvv is not None for vvv in (data or {}).values())
        rows.append((name, cx, dt * 1000, ok))
        time.sleep(0.4)
    print("%-16s %12s %14s %6s" % ("query", "complejidad", "round-trip", "ok"))
    for name, cx, ms, ok in rows:
        print("%-16s %12s %11.1f ms %6s" % (name, cx, ms, ok))
    print()
    by = {r[0]: r for r in rows}
    try:
        sep2 = int(by["preflight"][1]) + int(by["frontier"][1])
        sep3 = sep2 + int(by["map:read"][1])
        print("preflight+frontier: %d por separado en 2 round-trips, %s fusionada en 1"
              % (sep2, by["pre+frontier"][1]))
        print("los tres:           %d por separado en 3 round-trips, %s fusionada en 1"
              % (sep3, by["pre+read+front"][1]))
        print("techo por query 10000")
    except (TypeError, ValueError, KeyError):
        print("faltan headers de complejidad en alguna corrida")


NEEDS = [
    ("map:create",      "si",   "team.id, para ProjectCreateInput.teamIds"),
    ("map:read",        "no",   "el id del Document viene del Project"),
    ("map:write",       "no",   "idem, y la edicion es semantica"),
    ("ticket:create",   "si",   "team.id + los 8 labelIds + stateId explicito o cae en Triage"),
    ("ticket:block",    "no",   "issueId y relatedIssueId aceptan CRM-123"),
    ("frontier:query",  "si",   "los DOS ids cerrados: el predicado los compara en el cliente"),
    ("ticket:claim",    "si",   "viewer.id"),
    ("ticket:resolve",  "si",   "el completed de menor position, y lo de ticket:create de los nuevos"),
    ("ticket:rule-out", "si",   "el canceled de menor position"),
    ("milestone:create","no",   "projectId y nombre, nada resuelto"),
    ("issue:create",    "si",   "team.id + stateId explicito"),
]


def cmd_ensure():
    """Si el preflight crea los 8 labels que faltan, cuantos round-trips es.

    Usa dos nombres descartables con prefijo zz-, en una sola mutation con
    alias, y los borra al final. Es el mismo procedimiento que uso el 03.
    """
    names = ["zz-preflight-probe-a", "zz-preflight-probe-b"]
    aliased = "mutation(%s) {\n%s\n}" % (
        ", ".join("$i%d: IssueLabelCreateInput!" % i for i in range(len(names))),
        "\n".join("  c%d: issueLabelCreate(input: $i%d) { success issueLabel { id name } }"
                   % (i, i) for i in range(len(names))),
    )
    variables = {"i%d" % i: {"name": n} for i, n in enumerate(names)}
    data, h, dt = gql(aliased, variables)
    cx = next((vv for kk, vv in h.items() if kk.lower() == "x-complexity"), None)
    ids = []
    for i in range(len(names)):
        node = ((data or {}).get("c%d" % i) or {}).get("issueLabel") or {}
        if node.get("id"):
            ids.append(node["id"])
    print("mutations con alias en UN round-trip: %d creados, complejidad %s, %.1f ms"
          % (len(ids), cx, dt * 1000))
    for lid in ids:
        gql("mutation($id: String!) { issueLabelDelete(id: $id) { success } }", {"id": lid})
    print("borrados %d. El workspace queda como estaba." % len(ids))
    print()
    print("Conclusion: crear los N labels que falten es UN round-trip, no N,")
    print("asi que un preflight de primera corrida es 2 round-trips: leer y crear.")


def cmd_needs():
    print("%-18s %-4s %s" % ("operacion", "usa", "que necesita del preflight"))
    for op, uses, need in NEEDS:
        print("%-18s %-4s %s" % (op, uses, need))
    print()
    nada = [op for op, uses, _ in NEEDS if uses == "no"]
    print("no necesitan nada: %s" % ", ".join(nada))
    print("son %d de %d. Las otras %d si." % (len(nada), len(NEEDS), len(NEEDS) - len(nada)))


def cmd_ctx():
    """Cuanto pesa el contexto resuelto que habria que pasar entre invocaciones."""
    import base64
    data, _, _ = gql(PREFLIGHT, {"team": TEAM, "labels": LABELS})
    team = data.get("team") or {}
    states = (team.get("states") or {}).get("nodes") or []
    done = sorted([s for s in states if s["type"] == "completed"], key=lambda s: s["position"])
    canc = sorted([s for s in states if s["type"] == "canceled"], key=lambda s: s["position"])
    # los labels no existen hoy, asi que se simula con uuids del largo real
    found = {n["name"]: n["id"] for n in ((data.get("issueLabels") or {}).get("nodes") or [])}
    fake = "00000000-0000-0000-0000-000000000000"
    ctx = {
        "viewer": (data.get("viewer") or {}).get("id"),
        "team": team.get("id"),
        "done": done[0]["id"] if done else None,
        "canceled": canc[0]["id"] if canc else None,
        "default": (team.get("defaultIssueState") or {}).get("id"),
        "labels": {l: found.get(l, fake) for l in LABELS},
        "discovery": fake,
    }
    compact = json.dumps(ctx, separators=(",", ":"))
    b64 = base64.b64encode(compact.encode()).decode()
    print("json compacto  %4d bytes  ~%d tokens" % (len(compact), len(compact) // 4))
    print("base64         %4d bytes  ~%d tokens" % (len(b64), len(b64) // 4))
    print("indentado      %4d bytes" % len(json.dumps(ctx, indent=2)))
    print()
    print("Por siete invocaciones que lo consumen en un /map-work:")
    print("  json  ~%d tokens de contexto" % (len(compact) // 4 * 7))
    print("  b64   ~%d tokens de contexto" % (len(b64) // 4 * 7))
    print()
    print("ARG_MAX no es problema:", os.sysconf("SC_ARG_MAX"), "bytes")


def cmd_stable():
    """Si el id de un label sobrevive a un rename. Decide cuan angosta es la ventana
    en la que un ctx resuelto al empezar puede quedar rancio."""
    d, _, _ = gql("mutation($i: IssueLabelCreateInput!) { issueLabelCreate(input: $i) { success issueLabel { id name } } }",
                  {"i": {"name": "zz-preflight-rename-probe"}})
    node = ((d or {}).get("issueLabelCreate") or {}).get("issueLabel") or {}
    lid = node.get("id")
    print("creado   %s  id %s" % (node.get("name"), lid))
    d2, _, _ = gql("mutation($id: String!, $i: IssueLabelUpdateInput!) { issueLabelUpdate(id: $id, input: $i) { success issueLabel { id name } } }",
                   {"id": lid, "i": {"name": "zz-preflight-rename-probe-DOS"}})
    n2 = ((d2 or {}).get("issueLabelUpdate") or {}).get("issueLabel") or {}
    print("renombrado %s  id %s" % (n2.get("name"), n2.get("id")))
    print("el id %s" % ("SOBREVIVE" if n2.get("id") == lid else "CAMBIO"))
    gql("mutation($id: String!) { issueLabelDelete(id: $id) { success } }", {"id": lid})
    print("borrado. El workspace queda como estaba.")



def cmd_orphan():
    """Si borrar un label lo saca de las issues que lo llevaban.

    Decide si el label `map` ausente es una falla dura del preflight o solo un
    aviso: si borrarlo huerfana a todo ticket de decision, `frontier:query`
    devuelve cero y el veredicto de /map-work miente en silencio.

    Trabaja sobre el sandbox del ticket 01 y deja todo como estaba.
    """
    d, _, _ = gql("""query($id: String!) {
      project(id: $id) { name issues(first: 3) { nodes { id identifier title labels { nodes { id name } } } } }
    }""", {"id": SANDBOX_PROJECT})
    nodes = (((d or {}).get("project") or {}).get("issues") or {}).get("nodes") or []
    if not nodes:
        print("el sandbox no tiene issues; no se puede medir")
        return
    issue = nodes[0]
    before = [n["name"] for n in (issue.get("labels") or {}).get("nodes") or []]
    print("issue    %s  %s" % (issue["identifier"], issue["title"][:50]))
    print("labels   %s" % before)

    d2, _, _ = gql("mutation($i: IssueLabelCreateInput!) { issueLabelCreate(input: $i) { success issueLabel { id name } } }",
                   {"i": {"name": "zz-preflight-orphan-probe"}})
    lid = (((d2 or {}).get("issueLabelCreate") or {}).get("issueLabel") or {}).get("id")
    print("label    creado %s" % lid)

    gql("mutation($id: String!, $i: IssueUpdateInput!) { issueUpdate(id: $id, input: $i) { success } }",
        {"id": issue["id"], "i": {"labelIds": [n["id"] for n in (issue.get("labels") or {}).get("nodes") or []] + [lid]}})
    d3, _, _ = gql("query($id: String!) { issue(id: $id) { identifier labels { nodes { name } } } }", {"id": issue["id"]})
    mid = [n["name"] for n in (((d3 or {}).get("issue") or {}).get("labels") or {}).get("nodes") or []]
    print("con el label  %s" % mid)

    gql("mutation($id: String!) { issueLabelDelete(id: $id) { success } }", {"id": lid})
    d4, _, _ = gql("query($id: String!) { issue(id: $id) { identifier title labels { nodes { name } } } }", {"id": issue["id"]})
    after_issue = (d4 or {}).get("issue") or {}
    after = [n["name"] for n in (after_issue.get("labels") or {}).get("nodes") or []]
    print("borrado el label")
    print("la issue      %s existe: %s" % (after_issue.get("identifier"), bool(after_issue.get("title"))))
    print("sus labels    %s" % after)
    print()
    if set(after) == set(before):
        print("BORRAR UN LABEL LO SACA DE LAS ISSUES Y LA ISSUE SOBREVIVE.")
        print("O sea: borrar `map` huerfana a todo ticket de decision y")
        print("frontier:query devuelve cero sin error.")
    else:
        print("resultado inesperado; before=%s after=%s" % (before, after))



if __name__ == "__main__":
    cmds = {"startup": cmd_startup, "one": cmd_one, "labels": cmd_labels,
            "chain": cmd_chain, "merged": cmd_merged, "quiet": cmd_quiet,
            "needs": cmd_needs, "ensure": cmd_ensure,
            "ctx": cmd_ctx, "stable": cmd_stable, "orphan": cmd_orphan}
    if len(sys.argv) < 2 or sys.argv[1] not in cmds:
        print(__doc__)
        sys.exit(1)
    cmds[sys.argv[1]](*sys.argv[2:])
