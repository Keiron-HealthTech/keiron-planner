---
name: map-work
description: >
  Work one decision ticket of a Linear map: read the map and the frontier, derive the
  verdict, pick the ticket, check the role it needs and claim it.
  Trigger: Loaded by commands/map-work.md, and by nothing else.
license: MIT
metadata:
  author: Keiron-HealthTech
  version: "1.0"
  scope: [root]
  auto_invoke: Loaded by commands/map-work.md, and by nothing else
lang: en
---

CONTRACT: `${CLAUDE_PLUGIN_ROOT}/skills/_shared/map-contract.md`, read it FIRST. It owns the
closed token set, the citation form, the `$ARGUMENTS` contract, the ticket type to discipline
table, and the derivation of the verdict. Resolve all five from there rather than restating
them here.

TEMPLATES: `${CLAUDE_PLUGIN_ROOT}/skills/_shared/map-templates.md`. It owns the shape of every
piece of text a person ends up reading in Linear, and that text is in Spanish. Never type one
of those shapes from memory.

ADAPTER: `${CLAUDE_PLUGIN_ROOT}/scripts/linear.py`, invoked with Bash and written `linear.py`
below. This skill runs eight of its operations and no other: `preflight`, `map:read`,
`frontier:query`, `ticket:claim`, `ticket:create`, `ticket:block`, `ticket:resolve` and
`ticket:rule-out`. Never compose GraphQL yourself and never touch the Linear API directly.

Writing the map is not on that list, and the absence is the point: the write that adds the
line to the map happens inside the operation that resolves the ticket, so the map lands last
and exactly once by construction rather than by your discipline.

When any invocation exits non-zero, relay its stderr as it is, add nothing to it, and stop. Do
not reformulate the remediation and do not turn the failure into a token: every hard failure
already carries its own remediation, written by the operation that produced it.

One ticket per session, always. The steps below run in order. Nothing here is optional and
nothing reorders.

## Step 1, the preflight

    linear.py preflight --team CRM

Once per driver, with `--team` and no other flag. `preflight` has one more, the one that lets
it create the `map` label when the label is missing, and the only command allowed to name that
flag is the one that traces a new map. Here a missing `map` label is a hard failure, and the
remediation it prints already names where to go.

Non-zero: relay its stderr as it is and stop, with no token. No later step runs.

Its stdout is an opaque blob. Pass it along as `--ctx` to the operations that ask for one, and
never edit it, never read a value out of it to make a decision, and never resolve one of its
values on your own.

## Step 2, the map and the frontier

    linear.py map:read --project <the argument>
    linear.py frontier:query --ctx <the blob from step 1> --project <the same argument>

In that order, and neither one writes anything. Three answers stop the session here:

- `found` false in `map:read`: the argument resolved to no Project this credential can see.
  Say that and stop, with no token. None of the six says "fix the argument".
- `found` true and all six values of `sections` null: the Project resolved and carries no map.
  Emit `next_recommended: map-new` and stop, without running `frontier:query`. There is
  nothing to work yet.
- `found` false in `frontier:query` after `map:read` answered `found` true for the same
  `--project`: the Project stopped resolving between the two reads. Report that discrepancy
  and stop, with no verdict and no token.

Whether a section exists comes from `sections`, never from a search inside `content`.

## Step 3, the verdict, before picking anything

Derive it with the contract's table, cited and never copied, out of `counts` and `notTakeable`
and nothing else. Read `counts.milestones` ONLY when `counts.open` is zero: with at least one
open ticket the first two rows decide, and branching on milestones first is the natural
mistake this line exists to prevent.

`en curso` is the only verdict that continues. It goes to step 4 with no token, because this
session cannot recommend itself. The other four stop right here, each with the token the
contract gives it, and none of them asks anything:

- `trabado` with a claim holding the frontier: `next_recommended: release-claim`
- `trabado` with only blockers holding it: `next_recommended: break-cycle`
- `listo para colapsar`: `next_recommended: map-collapse`
- `colapsado`: `next_recommended: sdd-new`

## Step 4, pick the ticket

With no `$ARGUMENTS` the command already asked and stopped, per the contract. With the URL of
a ticket instead of the URL of the Project, say exactly that, ask for the URL of the Project,
and stop: the adapter resolves no Project from the URL of an issue, and that limit is the
contract's.

With the Project, take the FIRST entry of `tickets`. The adapter already ordered them by
`createdAt` ascending, so do not re-sort them and do not apply a criterion of your own. Name
which one you took and why it was first.

When `$ARGUMENTS` names one specific ticket and that ticket is not in `tickets`, say why it is
not takeable, which `notTakeable` already tells you: it is claimed, it is blocked, or it is
closed. Then stop. Never substitute another ticket for the one that was named.

## Step 5, the role check, before claiming

It fires for two labels and no other: `hitl:pm` and `hitl:design`. A ticket with neither has
`hitl:dev` as its interlocutor by default, and the check does not fire, so a session of
grilling with a developer is never interrupted by this question.

When it does fire, ask whether the person on the other side is that role, or can speak for it.
If the answer is no, stop without claiming and say which role the ticket needs.

The order is the whole point: claiming and then refusing leaves an orphan claim, and an orphan
claim is exactly the thing nobody releases. The write that is not made is the write that does
not fail.

## Step 6, the claim

    linear.py ticket:claim --ctx <the blob from step 1> --issue <the identifier from step 4>

The first write of the session, and nothing may have written before it. The identifier is the
`identifier` value that `frontier:query` returned in this same run, copied verbatim and never
typed from memory.

Pass no `--release` here. That flag hands a claim back on purpose, and it belongs to the
branch of step 8 that pauses a ticket rather than to the one that takes it.

## Step 7, run the discipline the type asks for

The contract's ticket type to discipline table decides, and this file does not copy it. It
has four rows, one per type label, and each carries the rule of its own that is not
negotiable. Read it there and run what it names for the label this ticket carries.

`map:task` names no discipline, and that is not an omission: it does instead of deciding, so
there is nothing to conduct. Do the work and carry what it produced into step 8.

A ticket typed `map:research` is worked here **exactly like any other AFK ticket, one per
session, by the normal path**. Do not dispatch a subagent, do not run anything in parallel,
and above all do not refuse the ticket. Dispatching every research ticket of the frontier at
once is a later cut and does not exist yet; what that cut adds is the parallelism, never the
ability to resolve one, because resolving is what step 8 already does and step 8 does not
look at the type. The tickets typed `map:research` simply wait on the frontier, and the
person resolves them through the normal path, one per session.

So the rule that says research is the one exception to one ticket per session is describing
a **future** exception. Until the parallel dispatch exists there is nothing for it to
license, and in this cut one ticket per session holds with no exception at all.

## Step 8, show it, confirm once, and write

This is the only irreversible batch of the session. Five writes, and not one of them has an
undo: not a ticket created, not a relation, not a comment, not a close, not a line of the
map. So show the whole thing and ask for confirmation ONCE, before invoking anything.

Show five things, and show them as they will read rather than as a summary:

1. the six sections of the resolution comment, already written out;
2. the new tickets, each with the type label it will carry;
3. the wiring between them, if any;
4. the fog this resolution graduates;
5. the gist of the line that goes to the map, or the bullet that goes to `Fuera de alcance`.

The `Niebla graduada` section carries `ninguna` when this resolution graduated no patch, and
names every graduated title when it did. Writing that negative by hand is not ceremony: the
adapter refuses a comment with any section left empty, so the section cannot be skipped, and
a silent omission becomes a non-zero exit instead of a gap nobody sees.

After the confirmation, invoke once and do not ask again:

    linear.py ticket:resolve --ctx <the blob from step 1> --project <the project> \
      --issue <the chosen ticket> --section <NOMBRE> <LINEA> [--section ...] \
      --gist <gist> [--new-ticket <title> <body> <labels>] \
      [--block <blocker title> <blocked title>] [--append-fog <bullet>] \
      [--remove-fog <title>]

or `linear.py ticket:rule-out`, the same shape with `--out-of-scope <bullet>` in place of
`--gist`, when the discipline concludes the ticket ended up beyond the destination. Its line
goes to `Fuera de alcance` and never to `Decisiones hasta ahora`.

The order of the five writes, and the guarantee that they all travel inside one invocation,
belong to the adapter and are not restated here. There is no flag that reorders them.

Then report what landed and stop with one token. When the frontier that step 2 read held more
than the one ticket just resolved, that token is `next_recommended: map-work`. Reading the
frontier again, landing the decision and reporting the close are steps 9 and 10, and they
belong to a later cut.

One ticket per session, always, `map:research` included.

### The other-role branch

While resolving, a question can come up that belongs to a different role, `hitl:pm` or
`hitl:design`. This is not the check of step 5, which was about the chosen ticket itself;
this is about a question that working it just produced.

**When the answer is not needed to close the current ticket**, there is no branch at all: the
new ticket is one more `--new-ticket` of the normal resolution, with its `hitl:` label and no
`--block`, and it gets named in `Tickets nuevos`.

**When the answer is needed**, do not invoke `ticket:resolve` or `ticket:rule-out` at all.
Run these three, in this order, and stop:

    linear.py ticket:create --ctx <the blob from step 1> --project <the project> \
      --ticket <the question> <the question again as body> <hitl label>
    linear.py ticket:block --block <the new ticket id> <the current ticket id>
    linear.py ticket:claim --ctx <the blob from step 1> --issue <the chosen ticket> --release

No comment, no state change, no line in the map for the current ticket. This is not a
resolution, it is a deliberate pause: the current ticket ends the session open, unassigned
and blocked, which is to say off the frontier until the blocker is resolved. Handing the
claim back is what `--release` exists for, and it is the difference between a pause and the
orphan claim that nobody ever releases.

None of the three retries the other two, and `ticket:block`'s own failure message only
knows about missing pairs, never about this sequence: it cannot tell you the release is
still outstanding, because it is shared with a standalone `ticket:block` that never
promised one. So when any of the three exits non-zero, relay its stderr as step 1 of this
file already says, but before stopping add, in your own words, which of the three landed
and which did not: the claim from step 6 is still yours to release until the third one
actually runs, and an unreleased claim here is exactly the orphan claim step 5 exists to
prevent. Never run the release out of order to close that gap early: releasing before
`ticket:block` lands sends the ticket back to the frontier looking freely takeable, with
the question that blocks it invisible, because nothing yet says it is blocked. Finish the
sequence by hand instead, in order, starting from whichever of the three is still missing.

Close with `next_recommended: map-work`: the ticket that was just opened is born takeable.
