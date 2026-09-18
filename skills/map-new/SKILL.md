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
`linear.py` below. This skill runs eight of its operations and no other: `preflight`,
`map:create`, `ticket:create`, `ticket:block`, `ticket:claim`, `ticket:resolve`,
`map:write` and `frontier:query`. Never compose GraphQL yourself and never touch the
Linear API directly.

Two of the eight belong to step 6 and to no other step, and they reach Linear from two
different places. `ticket:claim` runs from this session, once per research ticket, before
anything is dispatched. `ticket:resolve` never runs from this session at all: it runs
inside each instance that step 6 dispatches, and it is on the list because step 6 is what
puts it there.

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

Every ticket step 5 just created carrying the type label `map:research` is answered here,
in this same run, by an instance of its own. A run that created none skips this step
whole: no claim, no dispatch, straight to step 7, exactly as before.

Claim them all first, one invocation per ticket, before anything is dispatched:

    linear.py ticket:claim --ctx <blob> --issue <the identifier of the research ticket>

The identifier is the one `ticket:create` returned in this same run, copied verbatim and
never typed from memory. The claim is this session's and never the instance's: it is what
takes the ticket off the frontier, and a claim this session wrote is a claim this session
can name when an instance fails.

Then dispatch one instance of
`${CLAUDE_PLUGIN_ROOT}/skills/_shared/research-subagent.md` per ticket, all of them in the
same turn, and wait for every one to come back. Hand each one the five things that file
says it receives, and nothing else: its identifier verbatim, its URL and its title, the
identifier of the Project, the fog titles currently on the map, and the team key. Never
hand it the `--ctx` blob of step 1. A preflight runs once per driver and an instance is a
driver, so it runs its own.

There is no numeric cap on how many go out at once, and inventing one would be reading a
constant nobody measured. The bound is the frontier itself, which here is what step 5 just
created. Do not ask before dispatching either: this command asks exactly once, in step 4,
and the questions these tickets carry are the ones the person dictated in step 3, minutes
ago.

Wait for all of them before doing anything else. Do not write the map with the ones that
already answered, do not reorder them, do not retry one, and do not abort the ones still
running because one failed.

A return is sane when, and only when, it carries a fenced block that parses as the single
line of JSON a resolution run with `--defer-map` prints, with `mapWritten` false and a
`mapArgs` that is not empty. Anything else is malformed: prose with no fenced block, JSON
that does not parse, `mapArgs` missing or empty, `mapWritten` true. A malformed return is
treated exactly like an instance that failed or never came back, and there is no second
policy for it.

Keep the `mapArgs` of every sane return, in the order you dispatched. Step 7 is what
writes them. Never rebuild that line yourself, never deduce it from the prose an instance
wrote around its block, and never ask an instance to repeat it: the adapter is the one
house of that format, which is why an instance returns argv and not markdown.

Of a ticket whose instance failed or came back malformed: do not release its claim, do not
resolve it in its name, and write no line of its own in the map. It stays claimed, open
and off the frontier, and step 8 is where it gets named.

## Step 7, write the map

One single write, at the end:

    linear.py map:write --project <project id> \
      --append-decision <ticket url> <gist> \
      --append-fog <bullet> --append-out-of-scope <bullet> \
      <the mapArgs of every instance that came back sane>

The `mapArgs` of step 6 travel inside this same invocation, concatenated token by token in
the order the instances were dispatched, and they are the reason a research answered in
this run reaches the map without a second write. There is still exactly one write of the
map in the whole session, and this is it.

When this pass has no edit at all to make, no decision, no fog, no out of scope bullet and
no `mapArgs` that came back sane, do not invoke `map:write`. The adapter refuses an
invocation that carries no edit, and a failure the session manufactured for itself is
worse than a write that had nothing to do.

Every flag repeats, and they repeat for exactly this reason: the whole pass lands in one
invocation. Take the shape of each value from the templates. A fog bullet and an out of
scope bullet both start with their title in bold, and that title is their unique key. A gist
is capped at 120 characters, and the detail lives in the ticket the link already reaches.

Decisions that the session settled get a line each. Fog gets a bullet each. Anything the
person put beyond the destination goes to out of scope, which never graduates.

## Step 8, the frontier and the closing report

    linear.py frontier:query --ctx <blob> --project <project id>

Report, in one block: the destination, how many decision tickets were opened, which ones are
takeable now, and what stayed as fog. When step 6 dispatched anything, the same block names
which research answered and what line each one left in the map, and then, by identifier,
which ones did not: each of those is still claimed by you and unreleased, open and off the
frontier until its research is completed or the claim is handed back. Say how to finish one
by hand, which is to run `/map-work` on that ticket, or to release it with
`ticket:claim --release` if it is being left.

Then close with exactly one token from the contract's closed set, in its citation form:

- at least one research that did not come back: `next_recommended: map-work`
- at least one takeable ticket on the frontier: `next_recommended: map-work`
- zero open tickets and zero milestones, which is the map that was born with no fog:
  `next_recommended: map-collapse`

One token, never two, and never prose in its place.
