#!/usr/bin/env python3
"""Colapso del mapa keiron-planner v1, corrido a mano contra Linear.

El plugin todavia no existe, asi que este script hace lo que harian `map:create`,
`map:write`, `milestone:create` y `work:write`. Sigue el procedimiento del ticket
06 al pie: N milestones uno por uno, las M issues en UNA sola llamada atomica, y
el mapa como ultimo write.

Unica desviacion consciente: guarda los ids en state.json para poder correr los
pasos por separado y verificar entre uno y otro. El plugin no persiste nada; este
harness si, porque lo conduce una persona desde la shell.

Subcomandos, en orden:
  ids         Resuelve viewer, team, estados y project statuses. No escribe.
  project     Crea el Project. Escribe.
  map         Escribe el mapa en Project.content. Escribe.
  milestones  Crea los cinco cortes, uno por uno. Escribe.
  issues      Crea las veintiuna issues en una llamada atomica. Escribe.
  colapso     Llena `## El colapso` en el mapa. Escribe.
  verify      Relee todo. No escribe.
"""
import json
import os
import pathlib
import sys
import urllib.error
import urllib.request

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import plan  # noqa: E402

ENDPOINT = "https://api.linear.app/graphql"
TEAM_CRM = "267840b8-2c3e-4209-8a86-5c95f29ded19"
HERE = pathlib.Path(__file__).parent
STATE = HERE / "state.json"
PROJECT_NAME = "Plugin keiron-planner"


def api_key():
    k = os.environ.get("LINEAR_API_KEY")
    if k:
        return k.strip()
    p = pathlib.Path.home() / ".config" / "keiron-planner" / "linear.key"
    if p.exists():
        return p.read_text().strip()
    sys.exit("No hay API key.")


def gql(query, variables=None):
    req = urllib.request.Request(
        ENDPOINT,
        data=json.dumps({"query": query, "variables": variables or {}}).encode(),
        headers={"Content-Type": "application/json", "Authorization": api_key()},
    )
    try:
        with urllib.request.urlopen(req) as r:
            payload = json.load(r)
    except urllib.error.HTTPError as e:
        sys.exit("HTTP %s: %s" % (e.code, e.read().decode()[:2000]))
    if payload.get("errors"):
        print(json.dumps(payload["errors"], indent=2, ensure_ascii=False), file=sys.stderr)
        sys.exit("la API devolvio errores")
    return payload["data"]


def state():
    return json.loads(STATE.read_text()) if STATE.exists() else {}


def save(**kw):
    s = state()
    s.update(kw)
    STATE.write_text(json.dumps(s, indent=2, ensure_ascii=False))
    return s


def cmd_ids():
    d = gql(
        """query($t: String!) {
             viewer { id displayName }
             team(id: $t) {
               id key name
               states(first: 50) { nodes { id name type position } }
             }
             projectStatuses { nodes { id name type } }
           }""",
        {"t": TEAM_CRM},
    )
    states = d["team"]["states"]["nodes"]
    backlog = [s for s in states if s["type"] == "backlog"]
    backlog.sort(key=lambda s: s["position"])
    # Hay DOS project statuses tipados backlog, `Backlog` y `To Do`: el tipo no
    # alcanza para elegir, igual que el `Blocked` tipado canceled que midio el 03.
    proj_backlog = [p for p in d["projectStatuses"]["nodes"] if p["name"] == "Backlog"]
    out = {
        "viewerId": d["viewer"]["id"],
        "viewer": d["viewer"]["displayName"],
        "teamId": d["team"]["id"],
        "stateId": backlog[0]["id"],
        "stateName": backlog[0]["name"],
        "projectStatusId": proj_backlog[0]["id"],
        "projectStatusName": proj_backlog[0]["name"],
    }
    save(**out)
    print(json.dumps(out, indent=2, ensure_ascii=False))


def cmd_project():
    s = state()
    if s.get("projectId"):
        sys.exit("ya hay projectId en state.json: " + s["projectId"])
    dup = gql(
        """query($q: String!) { searchProjects(term: $q) { nodes { id name } } }""",
        {"q": PROJECT_NAME},
    )
    for n in dup["searchProjects"]["nodes"]:
        if n["name"] == PROJECT_NAME:
            sys.exit("ya existe un Project llamado asi: " + n["id"])
    d = gql(
        """mutation($input: ProjectCreateInput!) {
             projectCreate(input: $input) {
               success project { id name url slugId }
             }
           }""",
        {
            "input": {
                "name": PROJECT_NAME,
                "teamIds": [s["teamId"]],
                "leadId": s["viewerId"],
                "statusId": s["projectStatusId"],
                "description": (
                    "El plugin de planificacion que se disenio con su propio metodo. "
                    "El mapa de decisiones esta en este overview."
                ),
            }
        },
    )
    p = d["projectCreate"]["project"]
    save(projectId=p["id"], projectUrl=p["url"])
    print(json.dumps(p, indent=2, ensure_ascii=False))


def write_content(content):
    s = state()
    d = gql(
        """mutation($id: String!, $input: ProjectUpdateInput!) {
             projectUpdate(id: $id, input: $input) { success project { id updatedAt } }
           }""",
        {"id": s["projectId"], "input": {"content": content}},
    )
    return d["projectUpdate"]


def read_content():
    s = state()
    d = gql(
        """query($id: String!) { project(id: $id) { id name content updatedAt } }""",
        {"id": s["projectId"]},
    )
    return d["project"]


def cmd_map():
    content = (HERE / "map-linear.md").read_text()
    r = write_content(content)
    back = read_content()
    print("escrito:", r["success"])
    print("vuelven", len(back["content"].splitlines()), "lineas de", len(content.splitlines()))
    for h in [l for l in back["content"].splitlines() if l.startswith("## ")]:
        print("  ", h)


def cmd_milestones():
    s = state()
    if s.get("milestones"):
        sys.exit("ya hay milestones en state.json")
    made = {}
    for m in plan.MILESTONES:
        d = gql(
            """mutation($input: ProjectMilestoneCreateInput!) {
                 projectMilestoneCreate(input: $input) {
                   success projectMilestone { id name sortOrder targetDate status }
                 }
               }""",
            {
                "input": {
                    "projectId": s["projectId"],
                    "name": m["name"],
                    "description": m["description"],
                    "sortOrder": m["sortOrder"],
                }
            },
        )
        pm = d["projectMilestoneCreate"]["projectMilestone"]
        made[m["key"]] = pm["id"]
        print("%-6s %-8s %s  %s" % (pm["sortOrder"], pm["status"], pm["id"][:8], pm["name"]))
        if pm["targetDate"] is not None:
            sys.exit("targetDate no es nulo, y tiene que serlo")
    save(milestones=made)


def cmd_issues():
    s = state()
    if s.get("issues"):
        sys.exit("ya hay issues en state.json: el colapso es un evento unico")
    payload = []
    for it in plan.ISSUES:
        payload.append(
            {
                "teamId": s["teamId"],
                "projectId": s["projectId"],
                "projectMilestoneId": s["milestones"][it["m"]],
                "stateId": s["stateId"],
                "title": it["title"],
                "description": plan.issue_body(it),
            }
        )
    print("mandando", len(payload), "issues en una sola llamada atomica...")
    d = gql(
        """mutation($input: IssueBatchCreateInput!) {
             issueBatchCreate(input: $input) {
               success
               issues { id identifier url title estimate
                        labels { nodes { name } }
                        state { name }
                        projectMilestone { name } }
             }
           }""",
        {"input": {"issues": payload}},
    )
    res = d["issueBatchCreate"]
    made = [{"identifier": i["identifier"], "url": i["url"], "title": i["title"]} for i in res["issues"]]
    save(issues=made)
    for i in res["issues"]:
        labels = [n["name"] for n in i["labels"]["nodes"]]
        print("%-9s %-8s est=%-4s labels=%-6s %s" % (
            i["identifier"], i["state"]["name"], i["estimate"], labels or "[]", i["title"][:52]))


def cmd_colapso():
    s = state()
    proj = read_content()          # releer justo antes de escribir
    content = proj["content"]
    if "## El colapso" not in content:
        sys.exit("no esta el ancla `## El colapso`: no se escribe a ciegas")
    d = gql(
        """query($id: String!) {
             project(id: $id) {
               projectMilestones(first: 20) {
                 nodes { id name sortOrder issues { nodes { identifier } } }
               }
             }
           }""",
        {"id": s["projectId"]},
    )
    ms = sorted(d["project"]["projectMilestones"]["nodes"], key=lambda n: n["sortOrder"])
    lines = [
        "",
        "El mapa colapsó el 2026-08-28, con la frontera vacía y los catorce tickets de",
        "decisión resueltos. Cinco cortes demoables, ninguno con fecha, y veintiuna issues",
        "de ejecución adentro, creadas en una sola llamada atómica. Qué decisiones",
        "produjeron cada corte vive en la `description` del corte.",
        "",
        "`ProjectMilestone` no expone `url` en la API, así que los cortes van por nombre y",
        "se abren desde el overview.",
        "",
    ]
    for n in ms:
        k = len(n["issues"]["nodes"])
        lines.append("- **%s**: %d issues de ejecución." % (n["name"], k))
    lines.append("")
    head, _sep, _tail = content.partition("## El colapso")
    nuevo = head + "## El colapso\n" + "\n".join(lines)
    r = write_content(nuevo)
    print("escrito:", r["success"])
    print("\n".join(lines))


def cmd_verify():
    s = state()
    d = gql(
        """query($id: String!) {
             project(id: $id) {
               name url status { name } lead { displayName } scope progress content
               projectMilestones(first: 20) { nodes { name sortOrder targetDate status
                 issues { nodes { identifier } } } }
             }
           }""",
        {"id": s["projectId"]},
    )
    p = d["project"]
    print("Project :", p["name"], "|", p["status"]["name"], "| lead", p["lead"]["displayName"])
    print("URL     :", p["url"])
    print("scope   :", p["scope"], " progress:", p["progress"])
    print("mapa    :", len(p["content"].splitlines()), "lineas,",
          len([l for l in p["content"].splitlines() if l.startswith("## ")]), "encabezados")
    total = 0
    for n in sorted(p["projectMilestones"]["nodes"], key=lambda x: x["sortOrder"]):
        k = len(n["issues"]["nodes"])
        total += k
        print("  %-6s %-9s fecha=%s  %2d issues  %s" % (
            n["sortOrder"], n["status"], n["targetDate"], k, n["name"]))
    print("total   :", total, "issues de ejecucion")


CMDS = {
    "ids": cmd_ids, "project": cmd_project, "map": cmd_map,
    "milestones": cmd_milestones, "issues": cmd_issues,
    "colapso": cmd_colapso, "verify": cmd_verify,
}

if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in CMDS:
        sys.exit("uso: collapse.py {%s}" % "|".join(CMDS))
    CMDS[sys.argv[1]]()
