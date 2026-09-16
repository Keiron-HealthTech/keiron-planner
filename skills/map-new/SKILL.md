---
name: map-new
description: >
  Trace the map of a project on Linear: name the destination, map the frontier breadth
  first, adopt or create the Project, write the map into its overview, and open the first
  decision tickets.
  Trigger: Loaded by commands/map-new.md, and by nothing else.
license: MIT
metadata:
  author: Keiron-HealthTech
  version: "1.0"
  scope: [root]
  auto_invoke: Loaded by commands/map-new.md, and by nothing else
lang: en
---

CONTRACT: `${CLAUDE_PLUGIN_ROOT}/skills/_shared/map-contract.md`, read it FIRST. It owns the
closed token set, the citation form, the `$ARGUMENTS` contract and the ticket type to
discipline table. Resolve all four from there rather than restating them here.

TEMPLATES: `${CLAUDE_PLUGIN_ROOT}/skills/_shared/map-templates.md`. It owns the shape of
every piece of text a person ends up reading in Linear, and that text is in Spanish. Never
type one of those shapes from memory.

ADAPTER: `${CLAUDE_PLUGIN_ROOT}/scripts/linear.py`, invoked with Bash and written
`linear.py` below. This skill runs six of its operations and no other: `preflight`,
`map:create`, `ticket:create`, `ticket:block`, `map:write` and `frontier:query`. Never
compose GraphQL yourself and never touch the Linear API directly.

When any invocation exits non-zero, relay its stderr as it is, add nothing to it, and stop.
Do not reformulate the remediation and do not turn the failure into a token: every hard
failure already carries its own remediation, written by the operation that produced it.

The eight steps below run in order. Nothing here is optional and nothing reorders.

## Step 1, the preflight

Run the preflight once, for the team `CRM`, in bootstrap mode. The flag that turns bootstrap
mode on is named in `commands/map-new.md` and only there, so take it from the command that
routed you here: a second copy in this file is a copy nothing compares against.

The preflight runs once per driver. Its stdout is an opaque blob. Pass it along as `--ctx`
to the operations that ask for one, and never edit it, never read a value out of it to make
a decision, and never resolve one of its values on your own.

## Step 2, name the destination

Load grilling and domain-modeling. Work with the person until the destination is one
sentence that says what arriving means.

The destination is what fixes the scope, so it closes before a single ticket exists. The
person names it, always. Never propose one, never infer one from the argument, and never
fill it in to keep the session moving.

## Step 3, map the frontier

Keep grilling, breadth first: across, not deep. Ask every question that can be asked now,
in this one session.

There is no cut here, and that is the one place this method departs from wayfinder: fog
does not stop the mapping. A question you cannot yet state with precision is fog, and fog
is a bullet in the map, never a reason to stop early. The test is whether you can state the
question, not whether you can answer it.

With no fog and no question left, the map is still created. It is born ready to collapse,
and step 8 says so.

## Step 4, adopt or create the Project

    linear.py map:create --ctx <blob> --destino <the sentence from step 2> --project <url>

with `--project` when the argument named a Project, and `--name <project name>` instead when
it did not. Exactly one of the two.

When the adopted Project already has prose in its overview, show that prose to the person
and ask for confirmation ONCE, before going on. Never refuse a Project because it already
has content, never rewrite it and never summarise it: the operation preserves it verbatim
under its own heading, below the frontier. Asking again at every later step is noise.

## Step 5, the tickets and their blocks

One invocation of `ticket:create` with every ticket of this pass, and then one invocation of
`ticket:block` with every pair. Two invocations in total, never one per ticket: the
preflight ran once and the blob is immutable, so a second `ticket:create` would read the
same unresolved labels and try to create them again.

    linear.py ticket:create --ctx <blob> --project <project id> \
      --ticket <title> <body> <labels> --ticket <title> <body> <labels>

The title is the question in prose, with no numeric prefix. The body is that same question
and nothing else: no heading, no template, no text you add. `<labels>` is a comma separated
list with at most one type from the contract's table, plus the `hitl:` role when the type is
HITL and the interlocutor is known. Pass an empty string when the ticket carries neither:
that absence is the signal for AFK. The `map` label, and `Discovery` when the workspace has
it, are added by the operation and are never passed here.

Blocks run in a second pass because a ticket cannot be referenced before it has an id. Take
the ids from the stdout of `ticket:create` in this same run, and pass the blocker first:

    linear.py ticket:block --block <blocker id> <blocked id>

## Step 6, the research subagents

Out of scope for now. This step does not exist yet, and the tickets typed `map:research`
simply wait on the frontier: they are open, unassigned and unblocked, so `frontier:query` in
step 8 returns them as takeable and the closing report names them with the rest. The person
resolves them through the normal path, one per session. Say nothing else about this step and
do not improvise it.

## Step 7, write the map

One single write, at the end:

    linear.py map:write --project <project id> \
      --append-decision <ticket url> <gist> \
      --append-fog <bullet> --append-out-of-scope <bullet>

Every flag repeats, and they repeat for exactly this reason: the whole pass lands in one
invocation. Take the shape of each value from the templates. A fog bullet and an out of
scope bullet both start with their title in bold, and that title is their unique key. A gist
is capped at 120 characters, and the detail lives in the ticket the link already reaches.

Decisions that the session settled get a line each. Fog gets a bullet each. Anything the
person put beyond the destination goes to out of scope, which never graduates.

## Step 8, the frontier and the closing report

    linear.py frontier:query --ctx <blob> --project <project id>

Report, in one block: the destination, how many decision tickets were opened, which ones are
takeable now, and what stayed as fog. Then close with exactly one token from the contract's
closed set, in its citation form:

- at least one takeable ticket on the frontier: `next_recommended: map-work`
- zero open tickets and zero milestones, which is the map that was born with no fog:
  `next_recommended: map-collapse`

One token, never two, and never prose in its place.
