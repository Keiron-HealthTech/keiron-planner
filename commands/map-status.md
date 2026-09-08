---
description: Report the map, the frontier and the verdict of a Linear Project, and write nothing
argument-hint: <linear-url>
lang: en
---

ROUTE: read-only

CONTRACT: `${CLAUDE_PLUGIN_ROOT}/skills/_shared/map-contract.md`, read it FIRST. It owns the
closed token set, the citation form and the `$ARGUMENTS` contract. Resolve the argument by its
`$ARGUMENTS` section rather than restating it here.

ADAPTER: `${CLAUDE_PLUGIN_ROOT}/scripts/linear.py`, invoked with Bash and written `linear.py`
below. This command runs three of its operations and no other, on any branch and in any mode:
`map:read`, `preflight` and `frontier:query`. The three only read, so one run leaves the
Project byte for byte as it was. Never compose GraphQL yourself.

Three invocations and not two, and that is a fact of the adapter rather than a choice:
`frontier:query` requires a `--ctx`, and `preflight` is the only operation that produces one.

When any of the three exits non-zero, relay its stderr as it is, add nothing to it, and stop.
Do not reformulate the remediation and do not turn the failure into a token: every hard
failure already carries its own, and the one for the missing `map` label already names
`/map-new`, so the routing is not lost.

## Step 1, `map:read`

    linear.py map:read --project <the argument>

This one goes first, because it needs no ctx and no preflight. The order also matters the
other way round: on a workspace where the `map` label does not exist yet, `preflight` dies
before anything is read, so leading with it would never reach the map.

- `found` false: the argument resolved to no Project this credential can see. Say that and
  stop, with no token. None of the six says "fix the argument", and recommending a new map
  would be a lie, because tracing one with that same URL fails the same way.
- `found` true and all six values of `sections` null: the Project resolved and carries no
  map. Print one block that says exactly that, name the Project, emit
  `next_recommended: map-new` and stop. Do not run step 2 or step 3, do not print a verdict,
  and do not invent a fifth verdict value. This path costs one call of network.
- Anything else: at least one anchor is there, so there is a map even if it is partial.
  Continue with step 2.

Whether a section exists comes from `sections`, never from a search inside `content`. Read
`content` only for a section whose fingerprint is not null. The rule that produces those
fingerprints lives in `scripts/LINEAR-OPERATIONS.md` and is not restated here, and no
fingerprint is ever compared against another one: this command writes nothing, so it has
nothing to protect.

## Step 2, `preflight`

    linear.py preflight --team CRM

The team key is written on that line and nowhere else in this file. Pass no other flag:
`preflight` has one more, the one that lets it create the `map` label when the label is
missing, and the only command allowed to name that flag is the one that traces a new map.

Keep the single line it writes to stdout. It is an opaque blob: pass it along and never read
inside it.

## Step 3, `frontier:query`

    linear.py frontier:query --ctx <the blob from step 2> --project <the same argument>

If this answers `found` false after step 1 answered `found` true for the same `--project`, the
Project stopped resolving between the two reads. Report that discrepancy and stop, with no
verdict and no token. Do not feed the verdict with that answer: its three counts are zero, and
the verdict derived from them would read `listo para colapsar`, which would be a lie.

## The verdict and the token

Derive both from `counts` and `notTakeable`, and from nothing else.

| Condition | Verdict | Token |
| --- | --- | --- |
| `counts.takeable` is above zero | `en curso`, with its counts | `next_recommended: map-work` |
| `counts.takeable` is zero, `counts.open` is above zero, and some entry of `notTakeable` has a non-null `assignee` | `trabado` | `next_recommended: release-claim` |
| `counts.takeable` is zero, `counts.open` is above zero, and every entry of `notTakeable` is there only for its `blockers` | `trabado` | `next_recommended: break-cycle` |
| `counts.open` is zero and `counts.milestones` is zero | `listo para colapsar` | `next_recommended: map-collapse` |
| `counts.open` is zero and `counts.milestones` is above zero | `colapsado` | `next_recommended: sdd-new` |

Four verdicts and six tokens are not a bijection, and reading four tokens out of four verdicts
is wrong: `trabado` maps to two tokens by cause, and the no-map path of step 1 emits a token
and has no verdict at all.

Use no numeric threshold anywhere, neither a count of takeable tickets nor the age of a claim.
The precedence between the two `trabado` rows needs no written rule of order: one existing
claim is enough for the first of them to win.

`counts.open` zero with `counts.takeable` above zero is impossible and needs no branch. The
takeable tickets are a subset of the open ones, and the two invariants the adapter publishes
guarantee it.

## The report: six blocks and no seventh

Print these six, and not one more. The block labels are the Spanish the person reads.

1. `Destino`: the line of the map, taken from `content` only when the fingerprint of the
   `Destino` section is not null. This block also carries the fog patch count below.
2. `Veredicto`: one of the four values above, with its counts when it is `en curso`.
3. `Frontera`: the entries of `tickets`, each by name and with its link, in the order they
   arrive. That order is already `createdAt` ascending and the adapter computed it, so do not
   re-sort them.
4. `Tomados`: every entry of `notTakeable` whose `assignee` is not null, each one with the
   ticket name and its link, the value of `assignee`, which is who holds it, and its
   `createdAt` labelled for what it is. The label carries a rule of its own, below.
5. `Bloqueados`: every entry of `notTakeable` whose `blockers` is not empty, each one with its
   blockers by name and with their links.
6. `Truncado`: the names that `truncated` carries, when it carries any, relaying the stderr
   lines the adapter already wrote with their consequence. Do not reformulate a consequence:
   each one lives in the adapter and that is its only house. With `truncated` empty this block
   says nothing at all.

A ticket that is claimed AND blocked belongs in block 4 and in block 5, and choosing one of
the two is forbidden. That is the entire reason `notTakeable` is one list and not two: with
two lists something has to be chosen, and the block that loses the ticket lies.

Names are names. The Linear identifier travels inside the link and never in place of the
name, in any block: a wall of identifiers is unreadable.

There is no seventh block here. Decisions that never landed arrive with the landing, and
their predicate needs fields this query deliberately does not ask for.

### The date in block 4 is the date of the ticket

`frontier:query` returns `createdAt`, which is when the TICKET was created. There is no field
for when it was claimed, and getting one would need the history of the issue, which this
command does not read.

So the label MUST say the date is the one on which the ticket was created. Never write
"claimed N ago", and never write a Spanish construction that means it. A ticket created two
months ago and claimed five minutes ago, and one created two months ago and claimed two months
ago, carry the SAME `createdAt` and print identically. With the wrong label the first one
sends the person off to release a fresh claim: the block stops being a signal and starts
manufacturing false positives, which is worse than not having the block.

Do not estimate the age of a claim by any indirect route, and do not drop the date either. A
true date under a true label is worth more than no date.

## The fog patch count

Compute it here, over the `content` that `map:read` already returned. The adapter gains no key
for this.

- If the fingerprint of the `Aún no especificado` section is null, say the section is not there
  and search `content` for nothing.
- Otherwise find the line whose text is exactly `## Aún no especificado`, and count the
  first-level bullets that follow it, stopping at the first line that starts with `## ` or with
  `# `. A first-level bullet has no space before it; a bullet that starts with spaces is nested
  and does not count.
- Report the count and never the text of a bullet. The count is enough to notice that there
  are patches and that nobody is looking at them, without turning the report into a copy of
  the map.

The count feeds no verdict and becomes no seventh block. The fog carries a number while blocks
3, 4 and 5 carry names, and that is not an inconsistency: the fog is prose inside the map with
nothing to point at, and those are tickets with a name and a URL.
