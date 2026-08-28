#!/usr/bin/env python3
"""
Harness del ticket 12: qué pasa cuando aparece una decisión nueva sobre un mapa
ya colapsado. Mide la ruta de escritura del aterrizaje.

Sin dependencias: solo stdlib. La API key se busca, en orden, en
$LINEAR_API_KEY y en ~/.config/keiron-planner/linear.key, igual que probe.py
del ticket 01 y collapse_probe.py del 06.

  schema   Introspection, sin autenticar: que mutaciones y que campos existen
           para borrar, mover y reordenar milestones e issues.
  order    Si un milestone se puede insertar entre dos que ya existen, y que
           sortOrder devuelve Linear. Crea y borra.
  sort0    Que 0.0 es lo unico que Linear recalcula, y que lo manda al final.
           Crea y borra.
  orphan   Que le pasa a una issue cuando se borra su milestone. Crea y borra.
  move     Si una issue existente se puede mover de milestone, y si un batch de
           una sola issue contra un milestone existente anda. Crea y borra.
  dedup    Cuanto cuesta traer, en el round-trip que /map-status ya hace, los
           milestones con description y el milestone de cada issue. Solo lee.
  relate   La relacion `related` entre un ticket de decision y una issue de
           ejecucion, y su asimetria entre relations e inverseRelations.
  fields   Que no hay atajo para escribir relaciones: ni campo en
           IssueCreateInput ni mutacion batch.
  donecut  Que un corte terminado se reabre al meterle una issue nueva, y que
           status y progress son denormalizados con lag.
  relcost  Cuanto cuesta ligar M issues de ejecucion a su ticket de decision.

Todo lo que escribe lo borra. El Project de trabajo es el sandbox.
"""
import json
import os
import pathlib
import sys
import urllib.error
import urllib.request

ENDPOINT = "https://api.linear.app/graphql"
TEAM_CRM = "267840b8-2c3e-4209-8a86-5c95f29ded19"
SANDBOX = "400e790e-67c1-4eb0-8f4b-af388fc514a1"
PREFIX = "ZZ12"


def api_key():
    k = os.environ.get("LINEAR_API_KEY")
    if k:
        return k.strip()
    p = pathlib.Path.home() / ".config" / "keiron-planner" / "linear.key"
    if p.exists():
        return p.read_text().strip()
    sys.exit("No hay API key. Ver install.sh del ticket 01.")


def gql(query, variables=None, auth=True):
    headers = {"Content-Type": "application/json"}
    if auth:
        headers["Authorization"] = api_key()
    req = urllib.request.Request(
        ENDPOINT,
        data=json.dumps({"query": query, "variables": variables or {}}).encode(),
        headers=headers,
    )
    try:
        with urllib.request.urlopen(req) as r:
            complexity = r.headers.get("x-complexity")
            payload = json.load(r)
    except urllib.error.HTTPError as e:
        sys.exit(f"HTTP {e.code}: {e.read().decode()[:2000]}")
    if payload.get("errors"):
        sys.exit("GraphQL errors: " + json.dumps(payload["errors"], indent=2)[:2000])
    return payload["data"], complexity


def backlog_state():
    q = """query($t: String!) { team(id: $t) {
      states(first: 30) { nodes { id name type } } } }"""
    d, _ = gql(q, {"t": TEAM_CRM})
    for n in d["team"]["states"]["nodes"]:
        if n["name"] == "Backlog":
            return n["id"]
    sys.exit("Sin estado Backlog")


def mk_milestone(name, sort=None, desc=None):
    inp = {"name": name, "projectId": SANDBOX}
    if sort is not None:
        inp["sortOrder"] = sort
    if desc is not None:
        inp["description"] = desc
    q = """mutation($input: ProjectMilestoneCreateInput!) {
      projectMilestoneCreate(input: $input) {
        success projectMilestone { id name sortOrder } } }"""
    d, _ = gql(q, {"input": inp})
    return d["projectMilestoneCreate"]["projectMilestone"]


def rm_milestone(mid):
    q = "mutation($id: String!) { projectMilestoneDelete(id: $id) { success } }"
    d, _ = gql(q, {"id": mid})
    return d["projectMilestoneDelete"]["success"]


def mk_issue(title, state, milestone=None):
    inp = {"teamId": TEAM_CRM, "projectId": SANDBOX, "stateId": state, "title": title}
    if milestone:
        inp["projectMilestoneId"] = milestone
    q = """mutation($input: IssueCreateInput!) { issueCreate(input: $input) {
      success issue { id identifier title projectMilestone { id name } } } }"""
    d, _ = gql(q, {"input": inp})
    return d["issueCreate"]["issue"]


def rm_issue(iid):
    q = "mutation($id: String!) { issueDelete(id: $id) { success } }"
    d, _ = gql(q, {"id": iid})
    return d["issueDelete"]["success"]


def milestones():
    q = """query($p: String!) { project(id: $p) {
      projectMilestones(first: 50) { nodes { id name sortOrder description
        issues(first: 5) { nodes { identifier } } } } } }"""
    d, c = gql(q, {"p": SANDBOX})
    return d["project"]["projectMilestones"]["nodes"], c


# ---------------------------------------------------------------- schema

def cmd_schema():
    q = """query {
      __type(name: "Mutation") { fields { name } }
    }"""
    d, _ = gql(q, auth=False)
    names = [f["name"] for f in d["__type"]["fields"]]
    print("== Mutaciones relevantes ==")
    for pat in ("projectMilestone", "issueBatch", "issueRelation", "issueUpdate", "issueDelete", "issueArchive"):
        hits = sorted(n for n in names if pat.lower() in n.lower())
        print(f"  {pat:20s} -> {hits}")

    for t in ("ProjectMilestoneUpdateInput", "IssueUpdateInput", "IssueCreateInput"):
        q2 = """query($n: String!) { __type(name: $n) { inputFields { name } } }"""
        d2, _ = gql(q2, {"n": t}, auth=False)
        f = sorted(x["name"] for x in d2["__type"]["inputFields"])
        interesting = [x for x in f if any(k in x.lower() for k in
                       ("milestone", "sortorder", "project", "state", "estimate"))]
        print(f"\n== {t} ({len(f)} campos) ==\n  {interesting}")

    q3 = """query { __type(name: "IssueRelationType") { enumValues { name } } }"""
    d3, _ = gql(q3, auth=False)
    print("\n== IssueRelationType ==\n  ",
          [v["name"] for v in d3["__type"]["enumValues"]])

    q4 = """query { __type(name: "ProjectMilestone") { fields { name } } }"""
    d4, _ = gql(q4, auth=False)
    print("\n== ProjectMilestone fields ==\n  ",
          sorted(f["name"] for f in d4["__type"]["fields"]))


# ---------------------------------------------------------------- order

def cmd_order():
    print("Estado inicial de milestones en el sandbox:")
    before, _ = milestones()
    for m in before:
        print(f"  {m['sortOrder']:>10} {m['name']}")
    created = []
    try:
        a = mk_milestone(f"{PREFIX} A", sort=0.0)
        b = mk_milestone(f"{PREFIX} B", sort=1.0)
        c = mk_milestone(f"{PREFIX} C", sort=2.0)
        created += [a, b, c]
        print("\nTres milestones pedidos con sortOrder 0.0 / 1.0 / 2.0:")
        for m in (a, b, c):
            print(f"  pedido -> devuelto: {m['name']} = {m['sortOrder']}")

        mid = (a["sortOrder"] + b["sortOrder"]) / 2
        d = mk_milestone(f"{PREFIX} D-entre-A-y-B", sort=mid)
        created.append(d)
        print(f"\nCuarto, pedido con sortOrder {mid} (entre A y B):")
        print(f"  devuelto = {d['sortOrder']}")

        after, _ = milestones()
        print("\nOrden resultante (solo los ZZ12):")
        for m in sorted([x for x in after if x["name"].startswith(PREFIX)],
                        key=lambda x: x["sortOrder"]):
            print(f"  {m['sortOrder']:>12} {m['name']}")

        # ¿se puede reordenar uno existente?
        q = """mutation($id: String!, $input: ProjectMilestoneUpdateInput!) {
          projectMilestoneUpdate(id: $id, input: $input) {
            success projectMilestone { id name sortOrder } } }"""
        try:
            dd, _ = gql(q, {"id": a["id"], "input": {"sortOrder": 99.0}})
            print("\nprojectMilestoneUpdate con sortOrder 99.0 sobre A:")
            print("  ", dd["projectMilestoneUpdate"]["projectMilestone"])
        except SystemExit as e:
            print("\nprojectMilestoneUpdate falló:", e)
    finally:
        for m in created:
            print("  cleanup milestone", m["name"], rm_milestone(m["id"]))


# ---------------------------------------------------------------- orphan

def cmd_orphan():
    state = backlog_state()
    m = mk_milestone(f"{PREFIX} orphan-host")
    i = mk_issue(f"{PREFIX} issue que vive en el milestone", state, m["id"])
    print("Creados:")
    print("  milestone", m["id"], m["name"])
    print("  issue    ", i["identifier"], "->", i["projectMilestone"])
    try:
        print("\nBorrando el milestone:", rm_milestone(m["id"]))
        q = """query($id: String!) { issue(id: $id) {
          identifier title state { name } project { name }
          projectMilestone { id name } } }"""
        d, _ = gql(q, {"id": i["id"]})
        print("La issue después de borrar su milestone:")
        print("  ", json.dumps(d["issue"], ensure_ascii=False))
    finally:
        print("  cleanup issue", rm_issue(i["id"]))


# ---------------------------------------------------------------- move

def cmd_move():
    state = backlog_state()
    m1 = mk_milestone(f"{PREFIX} origen")
    m2 = mk_milestone(f"{PREFIX} destino")
    i = mk_issue(f"{PREFIX} issue a mover", state, m1["id"])
    print("Antes:", i["identifier"], "->", i["projectMilestone"])
    try:
        q = """mutation($id: String!, $input: IssueUpdateInput!) {
          issueUpdate(id: $id, input: $input) {
            success issue { identifier projectMilestone { id name } } } }"""
        d, _ = gql(q, {"id": i["id"], "input": {"projectMilestoneId": m2["id"]}})
        print("Después de issueUpdate:", d["issueUpdate"]["issue"])

        d2, _ = gql(q, {"id": i["id"], "input": {"projectMilestoneId": None}})
        print("Después de mandarlo a null:", d2["issueUpdate"]["issue"])

        # y una segunda issue por batch, apuntando a un milestone que ya existe
        qb = """mutation($input: IssueBatchCreateInput!) {
          issueBatchCreate(input: $input) { success issues {
            identifier projectMilestone { name } } } }"""
        db, cb = gql(qb, {"input": {"issues": [{
            "teamId": TEAM_CRM, "projectId": SANDBOX,
            "projectMilestoneId": m2["id"], "stateId": state,
            "title": f"{PREFIX} issue incremental por batch"}]}})
        extra = db["issueBatchCreate"]["issues"]
        print(f"issueBatchCreate de UNA sola issue a un milestone existente "
              f"(complejidad {cb}):", extra)
        for e in extra:
            pass
        # cleanup del extra
        qq = """query($p: String!) { project(id: $p) { issues(first: 50) {
          nodes { id identifier title } } } }"""
        dq, _ = gql(qq, {"p": SANDBOX})
        for n in dq["project"]["issues"]["nodes"]:
            if n["title"].startswith(f"{PREFIX} issue incremental"):
                print("  cleanup issue extra", n["identifier"], rm_issue(n["id"]))
    finally:
        print("  cleanup issue", rm_issue(i["id"]))
        print("  cleanup m1", rm_milestone(m1["id"]))
        print("  cleanup m2", rm_milestone(m2["id"]))


# ---------------------------------------------------------------- dedup

def cmd_dedup():
    base = """query($id: String!, $label: String!) {
      project(id: $id) {
        name content
        issues(first: 50, filter: { labels: { some: { name: { eq: $label } } } }) {
          nodes { id identifier title state { id name type } assignee { name } } }
      } }"""
    _, c1 = gql(base, {"id": SANDBOX, "label": "map"})
    print(f"frontera + mapa (lo que /map-status ya hace): complejidad {c1}")

    plus = """query($id: String!, $label: String!) {
      project(id: $id) {
        name content
        projectMilestones(first: 50) { nodes { id name sortOrder } }
        issues(first: 50, filter: { labels: { some: { name: { eq: $label } } } }) {
          nodes { id identifier title state { id name type } assignee { name } } }
      } }"""
    _, c2 = gql(plus, {"id": SANDBOX, "label": "map"})
    print(f"+ projectMilestones sin description:      complejidad {c2}")

    full = """query($id: String!, $label: String!) {
      project(id: $id) {
        name content
        projectMilestones(first: 50) { nodes { id name sortOrder description } }
        issues(first: 50, filter: { labels: { some: { name: { eq: $label } } } }) {
          nodes { id identifier title state { id name type } assignee { name }
                  projectMilestone { id name } } }
      } }"""
    _, c3 = gql(full, {"id": SANDBOX, "label": "map"})
    print(f"+ description + projectMilestone por issue: complejidad {c3}")

    allissues = """query($id: String!) {
      project(id: $id) {
        projectMilestones(first: 50) { nodes { id name description
          issues(first: 50) { nodes { identifier title } } } } } }"""
    d4, c4 = gql(allissues, {"id": SANDBOX})
    print(f"milestones con TODAS sus issues adentro:   complejidad {c4}")
    print("  ", json.dumps(d4["project"]["projectMilestones"]["nodes"],
                           ensure_ascii=False)[:400])


CMDS = {"schema": cmd_schema, "order": cmd_order, "orphan": cmd_orphan,
        "move": cmd_move, "dedup": cmd_dedup}



# ---------------------------------------------------------------- extras

def cmd_sort0():
    """Si sortOrder 0.0 es 'poneme donde quieras' y cualquier otro se respeta."""
    created = []
    try:
        a = mk_milestone(f"{PREFIX} s1", sort=10.0)
        b = mk_milestone(f"{PREFIX} s2", sort=20.0)
        created += [a, b]
        print(f"pedido 10.0 -> {a['sortOrder']}, pedido 20.0 -> {b['sortOrder']}")
        z = mk_milestone(f"{PREFIX} s-cero", sort=0.0)
        created.append(z)
        print(f"pedido 0.0 con dos milestones ya existentes -> {z['sortOrder']}")
        n = mk_milestone(f"{PREFIX} s-sin-campo")
        created.append(n)
        print(f"sin pasar sortOrder -> {n['sortOrder']}")
        h = mk_milestone(f"{PREFIX} s-entre", sort=15.0)
        created.append(h)
        print(f"pedido 15.0 (entre 10 y 20) -> {h['sortOrder']}")
        after, _ = milestones()
        print("orden final:")
        for m in sorted([x for x in after if x["name"].startswith(PREFIX)],
                        key=lambda x: x["sortOrder"]):
            print(f"  {m['sortOrder']:>8} {m['name']}")
    finally:
        for m in created:
            rm_milestone(m["id"])
        print("cleanup ok")


def cmd_relate():
    """Si una issue de ejecucion puede quedar ligada a su ticket de decision."""
    state = backlog_state()
    dec = mk_issue(f"{PREFIX} ticket de decision (pregunta)", state)
    exe = mk_issue(f"{PREFIX} issue de ejecucion (imperativo)", state)
    print("decision:", dec["identifier"], " ejecucion:", exe["identifier"])
    try:
        q = """mutation($input: IssueRelationCreateInput!) {
          issueRelationCreate(input: $input) { success issueRelation {
            id type issue { identifier } relatedIssue { identifier } } } }"""
        d, c = gql(q, {"input": {"issueId": exe["id"], "relatedIssueId": dec["id"],
                                 "type": "related"}})
        print(f"issueRelationCreate (complejidad {c}):",
              json.dumps(d["issueRelationCreate"], ensure_ascii=False))

        q2 = """query($id: String!) { issue(id: $id) {
          identifier
          relations(first: 10) { nodes { type relatedIssue { identifier title } } }
          inverseRelations(first: 10) { nodes { type issue { identifier title } } } } }"""
        d2, c2 = gql(q2, {"id": dec["id"]})
        print(f"\nleido desde el ticket de decision (complejidad {c2}):")
        print("  ", json.dumps(d2["issue"], ensure_ascii=False))

        flat = """query($id: String!, $label: String!) {
          project(id: $id) {
            issues(first: 50, filter: { labels: { some: { name: { eq: $label } } } }) {
              nodes { id identifier title state { id name type } assignee { name }
                relations(first: 5) { nodes { type relatedIssue { identifier } } } } } } }"""
        _, c3 = gql(flat, {"id": SANDBOX, "label": "map"})
        print(f"\nfrontera + relations por ticket: complejidad {c3}")
    finally:
        print("cleanup:", rm_issue(dec["id"]), rm_issue(exe["id"]))


CMDS["sort0"] = cmd_sort0
CMDS["relate"] = cmd_relate




# ---------------------------------------------------------------- ronda 2

def cmd_fields():
    """Todos los campos de IssueCreateInput, buscando un atajo para relaciones."""
    for t in ("IssueCreateInput", "IssueBatchCreateInput", "ProjectMilestoneUpdateInput"):
        q = """query($n: String!) { __type(name: $n) { inputFields { name
          type { name kind ofType { name kind } } } } }"""
        d, _ = gql(q, {"n": t}, auth=False)
        print(f"== {t} ==")
        for f in sorted(d["__type"]["inputFields"], key=lambda x: x["name"]):
            print("  ", f["name"])
        print()
    q2 = """query { __type(name: "Mutation") { fields { name } } }"""
    d2, _ = gql(q2, auth=False)
    names = [f["name"] for f in d2["__type"]["fields"]]
    print("mutaciones con 'batch':", sorted(n for n in names if "batch" in n.lower()))
    print("mutaciones con 'relation':", sorted(n for n in names if "relation" in n.lower()))


def cmd_donecut():
    """Si un corte ya terminado acepta una issue nueva, y que le pasa al status."""
    q = """query($t: String!) { team(id: $t) {
      states(first: 30) { nodes { id name type } } } }"""
    d, _ = gql(q, {"t": TEAM_CRM})
    st = {n["name"]: n["id"] for n in d["team"]["states"]["nodes"]}
    backlog, done = st["Backlog"], st.get("Done")
    m = mk_milestone(f"{PREFIX} corte terminado")
    i1 = mk_issue(f"{PREFIX} unica issue del corte", done, m["id"])
    created = [i1]
    try:
        qs = """query($id: String!) { projectMilestone(id: $id) {
          name status progress } }"""
        d1, _ = gql(qs, {"id": m["id"]})
        print("corte con su unica issue en Done:", d1["projectMilestone"])

        i2 = mk_issue(f"{PREFIX} issue tardia", backlog, m["id"])
        created.append(i2)
        d2, _ = gql(qs, {"id": m["id"]})
        print("el mismo corte despues de meterle una issue en Backlog:",
              d2["projectMilestone"])
    finally:
        for i in created:
            rm_issue(i["id"])
        rm_milestone(m["id"])
        print("cleanup ok")


def cmd_relcost():
    """Cuanto cuesta ligar M issues de ejecucion a sus tickets de decision."""
    import time
    state = backlog_state()
    dec = mk_issue(f"{PREFIX} decision madre", state)
    exes = [mk_issue(f"{PREFIX} ejecucion {n}", state) for n in range(5)]
    try:
        q = """mutation($input: IssueRelationCreateInput!) {
          issueRelationCreate(input: $input) { success issueRelation { id } } }"""
        t0 = time.time()
        total = 0
        for e in exes:
            _, c = gql(q, {"input": {"issueId": e["id"], "relatedIssueId": dec["id"],
                                     "type": "related"}})
            total += int(c or 0)
        dt = time.time() - t0
        print(f"5 issueRelationCreate secuenciales: {dt*1000:.0f} ms, "
              f"complejidad acumulada {total}, {dt*1000/5:.0f} ms por llamada")

        q2 = """query($id: String!) { issue(id: $id) {
          identifier
          inverseRelations(first: 10) { pageInfo { hasNextPage }
            nodes { type issue { identifier } } } } }"""
        d2, c2 = gql(q2, {"id": dec["id"]})
        n = d2["issue"]["inverseRelations"]["nodes"]
        print(f"leido desde la decision (complejidad {c2}): {len(n)} relaciones, "
              f"hasNextPage={d2['issue']['inverseRelations']['pageInfo']['hasNextPage']}")
    finally:
        for i in [dec] + exes:
            rm_issue(i["id"])
        print("cleanup ok")


CMDS["fields"] = cmd_fields
CMDS["donecut"] = cmd_donecut
CMDS["relcost"] = cmd_relcost


if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in CMDS:
        sys.exit("uso: reopen_probe.py " + "|".join(CMDS))
    CMDS[sys.argv[1]]()
