---
lang: en
---

# Map contract

What more than one command of `keiron-planner` has to agree on. Its only reader is the
model. It carries three things and nothing else: the closed set of `next_recommended`
tokens, the `$ARGUMENTS` contract, and the ticket type to discipline table. Anything that
belongs to one command alone lives in that command.

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

`$ARGUMENTS` is a Linear URL: the Project's, or any decision ticket of the map. With no
argument the command asks for one and stops. It never guesses and never searches: in a
workspace where product opens Projects all the time, a command that goes looking for the
map on its own picks the wrong one silently.

`/map-new` is the declared exception. It also takes a loose idea, or nothing at all.

**The limit as of today.** The adapter resolves `--project` from a UUID, a slugId or the URL
of a Project, and no operation of the adapter resolves the Project from the URL of an issue.
So a command handed a ticket URL says exactly that, asks for the URL of the Project, and
stops. It does not guess the Project and does not go looking for the one the ticket belongs
to. This paragraph is stale the day the adapter gains that resolution, and the change that
adds it deletes the paragraph.

## Ticket type to discipline

| Label | What it invokes | The rule that is not negotiable |
| --- | --- | --- |
| `map:grilling` | grilling and domain-modeling | The agent never answers for the person. |
| `map:prototype` | prototype | The agent builds variants and never chooses. |
| `map:research` | subagents in parallel, one per ticket | The only AFK type, and the only exception to one ticket per session. |
| `map:task` | no discipline | It does instead of deciding, and it earns its place by unblocking a decision, never by delivering a piece of the destination. |
