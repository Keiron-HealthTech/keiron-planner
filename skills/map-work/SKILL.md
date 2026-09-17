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
branch that pauses a ticket rather than to the one that takes it.

Steps 7 and 8, the discipline that the ticket type asks for and the resolution that closes it,
are not written in this file yet. Until they are, stop after the claim, report which ticket you
took and who now holds it, and say plainly that the resolution is not wired yet.
