---
lang: en
---

# Map contract

What more than one command of `keiron-planner` has to agree on. Its only reader is the
model. It carries four things and nothing else: the closed set of `next_recommended`
tokens, the `$ARGUMENTS` contract, the ticket type to discipline table, and the derivation
of the verdict. Anything that belongs to one command alone lives in that command.

## The closed set of next_recommended tokens

Every command closes with one token from this table, and with prose never. The set is
closed: a value outside it is invalid, not an extension.

| Token | When |
| --- | --- |
| `map-new` | There is no map. |
| `map-work` | The frontier has at least one takeable ticket. |
| `map-collapse` | Zero open tickets and zero milestones. |
| `release-claim` | Zero takeable tickets, and at least one open ticket is claimed. |
| `break-cycle` | Zero takeable tickets, and every open ticket is there only because a blocker holds it. |
| `sdd-new` | Zero open tickets and at least one milestone. |

`map-collapse` needs both halves of its condition. Zero open tickets on its own also
describes a map that already collapsed, and that one is `sdd-new`.

`release-claim` and `break-cycle` split by cause and by nothing else. No numeric threshold
belongs in this table, neither a count of takeable tickets nor the age of anything: a
command that read a claim as stale after N days would be reading a constant nobody
measured, inside a contract nobody can then change without moving every command at once.

`sdd-new` is the seam with the sibling plugin, `spec-driven-dev`: a collapsed map hands the
work over to SDD.

## How a command cites a token

A command cites a token in one form only, backticked, with one space after the colon:

    `next_recommended: map-work`

and in no other form. That single form is what makes membership checkable with no false
positive over the other kebab-case words that live in `commands/*.md`, such as a `ROUTE:`
value, a file name or a flag. The bare token in the first cell of the table above is the
declaration; the form here is the citation. The two are deliberately different, and neither
one is a substitute for the other.

## The `$ARGUMENTS` contract

`$ARGUMENTS` names a map: the URL of its Project, or the URL or the identifier of any of its
decision tickets. With no argument the command asks for one and stops. It never guesses and
never searches: in a workspace where product opens Projects all the time, a command that goes
looking for the map on its own picks the wrong one silently.

`/map-new` is the declared exception. It also takes a loose idea, or nothing at all.

Pass the argument as it came to every `--project`, whichever of the two it is. The adapter
resolves a ticket's URL or identifier to the Project that ticket belongs to, before the
operation runs, so no command looks the Project up on its own. A ticket that does not carry
the `map` label, or that belongs to no Project, makes the adapter exit non-zero with its own
remediation, and the command relays it like any other hard failure. What a ticket named by
the argument means beyond finding the map is the business of the command that works it.

## Ticket type to discipline

| Label | What it invokes | The rule that is not negotiable |
| --- | --- | --- |
| `map:grilling` | grilling and domain-modeling | The agent never answers for the person. |
| `map:prototype` | prototype | The agent builds variants and never chooses. |
| `map:research` | subagents in parallel, one per ticket | The only AFK type, and the only exception to one ticket per session. |
| `map:task` | no discipline | It does instead of deciding, and it earns its place by unblocking a decision, never by delivering a piece of the destination. |

## The verdict and the token

The verdict is what a command says about the map before it proposes anything. It takes four
values and only four, and this table is the one house of its derivation: every command that
reports the map cites it and none of them restates a row. Derive both the verdict and the
token from `counts` and `notTakeable`, and from nothing else.

| Condition | Verdict | Token |
| --- | --- | --- |
| `counts.takeable` is above zero | `en curso`, with its counts | `next_recommended: map-work` |
| `counts.takeable` is zero, `counts.open` is above zero, and some entry of `notTakeable` has a non-null `assignee` | `trabado` | `next_recommended: release-claim` |
| `counts.takeable` is zero, `counts.open` is above zero, and every entry of `notTakeable` is there only for its `blockers` | `trabado` | `next_recommended: break-cycle` |
| `counts.open` is zero and `counts.milestones` is zero | `listo para colapsar` | `next_recommended: map-collapse` |
| `counts.open` is zero and `counts.milestones` is above zero | `colapsado` | `next_recommended: sdd-new` |

Four verdicts and six tokens are not a bijection, and reading four tokens out of four verdicts
is wrong: `trabado` maps to two tokens by cause, and a map that resolves and carries none at
all emits a token with no verdict behind it.

Use no numeric threshold anywhere, neither a count of takeable tickets nor the age of a claim.
The precedence between the two `trabado` rows needs no written rule of order: one existing
claim is enough for the first of them to win.

`counts.open` zero with `counts.takeable` above zero is impossible and needs no branch. The
takeable tickets are a subset of the open ones, and the two invariants the adapter publishes
guarantee it.

`counts.milestones` is read ONLY when `counts.open` is zero. With at least one open ticket the
first two rows decide and the third count takes no part. The natural mistake is to branch on
milestones first, and this line is here to prevent it.

The first row is the one place where a command that reads and a command that works part ways,
and they part in the action rather than in the derivation: a read-only command emits the token
there, and a command that works the frontier cannot recommend itself, so it works instead.
