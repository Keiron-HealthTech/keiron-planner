#!/usr/bin/env python3
"""
Harness del ticket 06: la ruta de escritura de `/map-collapse`, medida.

Sin dependencias: solo stdlib. La API key se busca, en orden, en
$LINEAR_API_KEY y en ~/.config/keiron-planner/linear.key, igual que probe.py
del ticket 01.

Reproduce los cuatro hechos que la resolucion del 06 usa:

  settings      Los settings del team que deciden si el mapa ensucia el sprint:
                cycles, auto-assign, estimacion, triage.
  pollution     Que le hace un ticket de decision al scope del Project, y que
                pasa con `estimate: 0`. Escribe y restaura.
  triage        Que estado le toca a una issue creada por API, con y sin
                `stateId` explicito. Crea y borra.
  collapse      Un colapso de juguete entero: N milestones mas un
                `issueBatchCreate` atomico. Crea y borra.

Todo lo que escribe lo borra. El Project de trabajo se pasa por argumento y
tiene que ser un sandbox: este script no distingue.
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
        print(json.dumps(payload["errors"], indent=2, ensure_ascii=False), file=sys.stderr)
    return payload.get("data"), complexity


def label_id(name):
    d, _ = gql("{ issueLabels(first: 200) { nodes { id name } } }")
    for n in d["issueLabels"]["nodes"]:
        if n["name"] == name:
            return n["id"]
    sys.exit(f"no existe el label {name}")


def cmd_settings(team=TEAM_CRM):
    """Los settings que deciden si el mapa ensucia el sprint review."""
    d, _ = gql(
        """query($t: String!) { team(id: $t) {
             key name
             cyclesEnabled cycleDuration cycleStartDay
             cycleIssueAutoAssignStarted cycleIssueAutoAssignCompleted cycleLockToActive
             triageEnabled triageIssueState { name }
             issueEstimationType issueEstimationAllowZero defaultIssueEstimate
             defaultIssueState { id name type }
             activeCycle { number startsAt endsAt }
             states(first: 30) { nodes { name type position } }
           } }""",
        {"t": team},
    )
    t = d["team"]
    states = sorted(t.pop("states")["nodes"], key=lambda s: s["position"])
    print(json.dumps(t, indent=2, ensure_ascii=False))
    print("\nestados del team:")
    for s in states:
        print(f'  {s["position"]:7.1f}  {s["type"]:<12} {s["name"]}')


def cmd_pollution(project=SANDBOX):
    """Que le hace un ticket de decision al scope, y que hace `estimate: 0`."""
    d, _ = gql(
        """query($id: String!) { project(id: $id) {
             name scope progress
             issues(first: 50) { nodes { id identifier estimate state { name type } cycle { number } } }
           } }""",
        {"id": project},
    )
    p = d["project"]
    print(f'{p["name"]}: scope={p["scope"]} progress={p["progress"]}')
    for i in p["issues"]["nodes"]:
        print(f'  {i["identifier"]} est={i["estimate"]} {i["state"]["name"]} '
              f'cycle={i["cycle"] and i["cycle"]["number"]}')

    victim = next((i for i in p["issues"]["nodes"] if i["estimate"] is None), None)
    if not victim:
        return
    print(f'\nponiendo estimate 0 en {victim["identifier"]}...')
    gql("""mutation($id: String!, $in: IssueUpdateInput!) {
             issueUpdate(id: $id, input: $in) { success } }""",
        {"id": victim["id"], "in": {"estimate": 0}})
    # scope es denormalizado: la relectura inmediata puede venir con lag.
    for _ in range(2):
        d, _ = gql("query($id: String!) { project(id: $id) { scope progress } }", {"id": project})
        print("  ->", d["project"])
    gql("""mutation($id: String!, $in: IssueUpdateInput!) {
             issueUpdate(id: $id, input: $in) { success } }""",
        {"id": victim["id"], "in": {"estimate": None}})
    print("  restaurado")


def cmd_triage(project=SANDBOX, team=TEAM_CRM):
    """Que estado le toca a una issue creada por API, con y sin stateId."""
    d, _ = gql("query($t: String!) { team(id: $t) { defaultIssueState { id name type } } }",
               {"t": team})
    default = d["team"]["defaultIssueState"]
    print("Team.defaultIssueState =", default)
    lbl = label_id("zz-sandbox-map")
    base = {"teamId": team, "projectId": project, "labelIds": [lbl], "description": "control"}
    d, _ = gql(
        """mutation($in: IssueBatchCreateInput!) { issueBatchCreate(input: $in) {
             success issues { id identifier title state { name type } } } }""",
        {"in": {"issues": [
            dict(base, title="ZZ control SIN stateId"),
            dict(base, title="ZZ control CON stateId", stateId=default["id"]),
        ]}},
    )
    created = d["issueBatchCreate"]["issues"]
    for i in created:
        print(f'  {i["title"]:<26} {i["identifier"]} -> '
              f'{i["state"]["name"]} ({i["state"]["type"]})')
    for i in created:
        gql("mutation($id: String!) { issueDelete(id: $id) { success } }", {"id": i["id"]})
    print("  borrados")


def cmd_collapse(project=SANDBOX, team=TEAM_CRM):
    """Un colapso de juguete: N milestones mas un issueBatchCreate atomico."""
    lbl = label_id("zz-sandbox-map")
    d, _ = gql("query($t: String!) { team(id: $t) { defaultIssueState { id } } }", {"t": team})
    state = d["team"]["defaultIssueState"]["id"]

    milestones = []
    for i, (name, desc) in enumerate([
        ("ZZ Tracer bullet del sandbox", "Sale de las decisiones A y D."),
        ("ZZ Segundo corte demoable", "Sale de la decision B."),
    ]):
        d, c = gql(
            """mutation($in: ProjectMilestoneCreateInput!) {
                 projectMilestoneCreate(input: $in) { success projectMilestone {
                   id name sortOrder targetDate status } } }""",
            {"in": {"name": name, "projectId": project, "description": desc,
                    "sortOrder": float(i)}},
        )
        m = d["projectMilestoneCreate"]["projectMilestone"]
        milestones.append(m)
        print(f'milestone [complejidad {c}] sortOrder pedido={float(i)} '
              f'devuelto={m["sortOrder"]} status={m["status"]} targetDate={m["targetDate"]}')

    issues = [
        {"teamId": team, "projectId": project, "stateId": state, "labelIds": [lbl],
         "projectMilestoneId": milestones[0]["id"],
         "title": "ZZ Construir el esqueleto del adapter",
         "description": "## Que hay que construir\ncuerpo de prueba"},
        {"teamId": team, "projectId": project, "stateId": state, "labelIds": [lbl],
         "projectMilestoneId": milestones[0]["id"],
         "title": "ZZ Cablear el comando a la skill",
         "description": "## Que hay que construir\ncuerpo de prueba"},
        {"teamId": team, "projectId": project, "stateId": state, "labelIds": [lbl],
         "projectMilestoneId": milestones[1]["id"],
         "title": "ZZ Agregar el segundo subcomando",
         "description": "## Que hay que construir\ncuerpo de prueba"},
    ]
    d, c = gql(
        """mutation($in: IssueBatchCreateInput!) { issueBatchCreate(input: $in) {
             success issues { id identifier estimate state { name type }
               cycle { number } projectMilestone { name } } } }""",
        {"in": {"issues": issues}},
    )
    batch = d["issueBatchCreate"]
    print(f'\nissueBatchCreate [complejidad {c}] {len(issues)} issues success={batch["success"]}')
    for i in batch["issues"]:
        print(f'  {i["identifier"]} est={i["estimate"]} {i["state"]["name"]} '
              f'cycle={i["cycle"]} milestone={i["projectMilestone"]["name"]}')

    for i in batch["issues"]:
        gql("mutation($id: String!) { issueDelete(id: $id) { success } }", {"id": i["id"]})
    for m in milestones:
        gql("mutation($id: String!) { projectMilestoneDelete(id: $id) { success } }", {"id": m["id"]})
    print("  colapso de juguete borrado")


COMMANDS = {"settings": cmd_settings, "pollution": cmd_pollution,
            "triage": cmd_triage, "collapse": cmd_collapse}

if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in COMMANDS:
        sys.exit(__doc__)
    COMMANDS[sys.argv[1]](*sys.argv[2:])
