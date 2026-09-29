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
below. This skill runs eleven of its operations and no other: `preflight`, `map:read`,
`frontier:query`, `ticket:claim`, `ticket:create`, `ticket:block`, `ticket:resolve`,
`ticket:rule-out`, `map:write`, `milestone:create` and `work:write`. Never compose GraphQL
yourself and never touch the Linear API directly.

The ninth, `map:write`, belongs to the research branch of step 8 and to no other path. A
ticket of any other type still reaches the map through the operation that resolves it, and
this skill never invokes `map:write` on that path. The one other place it runs is the landing
of step 9, and only when that landing created a cut: there it runs once, with
`--append-collapse` and with nothing else, to put the cut under `## El colapso`. The tenth
and the eleventh, `milestone:create` and `work:write`, belong to step 9 alone.

The map lands last and exactly once, by construction rather than by your discipline, and
there are two constructions because there are two branches. On the normal path the write
that adds the line lives inside `ticket:resolve` or `ticket:rule-out`, so no step of this
file can reorder it or run it twice. On the research path the instance runs its resolution
with `--defer-map`, which is the adapter refusing to let it write the map at all, and the
parent runs one `map:write` after the last return. Neither construction rests on you
remembering not to write the map twice: the first puts the write out of reach inside another
operation, and the second takes it away from the instance with a flag. The landing of step 9
runs after both, and it is the one case where a session writes the map a second time: only
when it created a cut, and only for that cut.

When any invocation exits non-zero, relay its stderr as it is, add nothing to it, and stop. Do
not reformulate the remediation and do not turn the failure into a token: every hard failure
already carries its own remediation, written by the operation that produced it.

Every type worked in conversation is still one per session, and that is the rule this file is
built around. A ticket typed `map:research` is the one exception, because it is not worked in
conversation at all: it is handed to an instance of its own, and a session takes every one of
them the frontier holds rather than one. The steps below run in order. Nothing here is
optional and nothing reorders.

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

With the Project, look at `tickets` for the type label `map:research` before anything else.
When at least one carries it, take EVERY one of them: they are the fan-out of this session.
Do not apply the first by `createdAt` criterion to them, and do not take one and leave the
rest. They are the only type not worked in conversation, so several of them cost this session
one turn instead of one session each. Tickets of any other type on that same frontier are not
worked in this run and wait for a session of their own, exactly as before.

With the Project and no `map:research` on the frontier, take the FIRST entry of `tickets`. The
adapter already ordered them by `createdAt` ascending, so do not re-sort them and do not apply
a criterion of your own. Name which one you took and why it was first.

When `$ARGUMENTS` names one specific ticket, that ticket is the whole of this session, whatever
its type: a `map:research` named by the argument is dispatched alone and the rest of the
frontier is not touched. And when that ticket is not in `tickets`, say why it is not takeable,
which `notTakeable` already tells you: it is claimed, it is blocked, or it is closed. Then
stop. Never substitute another ticket for the one that was named.

## Step 5, the role check, before claiming

It fires for two labels and no other: `hitl:pm` and `hitl:design`. A ticket with neither has
`hitl:dev` as its interlocutor by default, and the check does not fire, so a session of
grilling with a developer is never interrupted by this question.

When it does fire, ask whether the person on the other side is that role, or can speak for it.
If the answer is no, stop without claiming and say which role the ticket needs.

It fires per ticket and by the label, never by the type, and that is what makes it harmless to
a fan-out. A `map:research` carries no `hitl:` role by default, because that type is AFK, so
a frontier of research asks nothing here at all. One that does carry a role is treated like
any other ticket that carries it: it is asked about, and a no leaves that one unclaimed and
undispatched while the rest of the fan-out goes on untouched.

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

When step 4 picked `map:research`, this invocation runs once per ticket it picked, all of them
here, from this session, and all of them BEFORE step 7 dispatches anything. An instance never
claims its own ticket, in either direction. Three reasons, and the third makes it obligatory:
the order
step 5 protects is the order of this file and moving the claim into step 7 would bend it for
one type only; the claim is what takes the ticket off the frontier, and the frontier was
read here, so a claim written after the dispatch leaves a window where another session reads
the same frontier and dispatches the same ticket; and a claim the parent wrote is a claim the
parent can name when an instance fails, which it could not do if an instance that died early
might or might not have claimed anything.

## Step 7, run the discipline the type asks for

The contract's ticket type to discipline table decides, and this file does not copy it. It
has four rows, one per type label, and each carries the rule of its own that is not
negotiable. Read it there and run what it names for the label this ticket carries.

`map:task` names no discipline, and that is not an omission: it does instead of deciding, so
there is nothing to conduct. Do the work and carry what it produced into step 8.

A ticket typed `map:research` is the one type this step does not conduct itself. It is AFK,
there is no conversation to run, and what step 7 does with it is dispatch it.

The dispatch is the irreversible batch of this branch: every instance writes a comment and
closes a ticket, and neither of those has an undo. So show which tickets are about to be
dispatched, by identifier and title, and ask for confirmation ONCE, before dispatching
anything. That is the same single confirmation step 8 asks for on the normal path, moved to
where the batch actually is. After it, do not ask again, not while they run and not before the
`map:write` of step 8.

Then dispatch one instance of
`${CLAUDE_PLUGIN_ROOT}/skills/_shared/research-subagent.md` per ticket step 6 claimed, all of
them in the same turn. Hand each one the five things that file says it receives, and nothing
else: its identifier verbatim as `frontier:query` returned it, its URL and its title, the
identifier of the Project, the fog titles that step 2 read off the map, and the team key.
Never hand it the `--ctx` blob of step 1. A preflight runs once per driver and an instance is
a driver, so it runs its own.

There is no numeric cap on how many go out at once. The bound is the frontier that step 2
read, and a cap of any other size would be a constant nobody measured, which is the one thing
the contract refuses to carry. An instance costs a preflight and at most four writes, because
`--defer-map` takes the fifth away from it.

Wait for every one of them to come back before doing anything else. Do not write the map with
the ones that already answered, do not reorder them, do not retry one, and do not abort the
ones still running because one failed.

For those tickets, do not invoke `ticket:resolve`, `ticket:rule-out`, `ticket:create` or
`ticket:block` yourself. Those are the instance's, and running one of them here would write
the resolution twice.

## Step 8, show it, confirm once, and resolve

On the normal path this is the only irreversible batch of the session. Five writes, and not
one of them has an undo: not a ticket created, not a relation, not a comment, not a close, not
a line of the map. So show the whole thing and ask for confirmation ONCE, before invoking
anything. On the research branch the batch was the dispatch and step 7 already asked, which is
the same single confirmation standing where the writes are.

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

The resolution ends here. This step neither reports nor closes with a token: step 9 lands the
decision when it applies, and step 10 reports and closes on every path.

Every type worked in conversation is still one per session, and `map:research` is the one
exception, worked by an instance of its own.

### The research branch

When step 7 dispatched a fan-out, none of the above runs. Each instance already wrote the four
writes of its own ticket: the new tickets, their wiring, the resolution comment and the close.
There is no confirmation to ask for here, because the irreversible batch of this branch was
the dispatch itself and step 7 already asked.

What is missing is the map, and only the map.

This branch never reaches step 9. A `map:research` ticket is AFK, and letting the agent decide
alone what gets built would hand it a decision that belongs to a person in a session.
Gathering the fan-out to ask for one approval at the end does not work either, because
research is AFK precisely so that nobody has to sit down.

A return is sane when, and only when, it carries a fenced block that parses as the single line
of JSON a resolution run with `--defer-map` prints, with `mapWritten` false and a `mapArgs`
that is not empty. Anything else is malformed: prose with no fenced block, JSON that does not
parse, `mapArgs` missing or empty, `mapWritten` true. A malformed return is treated exactly
like an instance that failed or never came back, and there is no second policy for it. A
return you cannot use and an invocation that never landed leave the same state behind, a
ticket whose line is not reaching the map in this session.

With every instance finished, sane or not, run exactly one invocation:

    linear.py map:write --project <the project> \
      --expect-sections <the fingerprints from step 2> \
      <the mapArgs of every instance that came back sane>

One invocation for the whole fan-out and never one per instance, with the `mapArgs`
concatenated token by token in the order you dispatched. Every token arrives raw: the
adapter never quotes it, and a gist or a fog bullet can carry any character a shell
reads specially, `;` and `|` included. Quote each token yourself before pasting it into
the line, no exception even for a token that is a flag name: wrap it in single quotes,
and if it already contains one, close the quote, write `'\''`, and reopen it.
`--expect-sections` carries the fingerprints that the `map:read` of step 2 already
returned. Step 7 did not read the map again, so those are the ones that belong here.

When no instance came back sane, do not run `map:write` at all. The adapter aborts when it
receives no edit, so an empty invocation is a failure this session would have manufactured
for itself.

Never rebuild the line yourself, never deduce it from the prose an instance wrote around the
block, and never ask an instance to repeat it. The adapter is the one house of that format,
which is why an instance returns argv and not markdown.

Of a ticket whose instance failed or came back malformed, three things are done by not doing
them. Do not run `ticket:claim --release`: handing the claim back erases the evidence that
this research was attempted and returns the ticket to the frontier looking fresh. Do not run
`ticket:resolve` or `ticket:rule-out` in its name: this session did not do the research and
has nothing to put in the six sections. And write no line of its own in the map: a decision
with no resolution has no line.

Then go to step 10, which reports the fan-out and closes.

### The other-role branch

While resolving, a question can come up that belongs to a different role, `hitl:pm` or
`hitl:design`. This is not the check of step 5, which was about the chosen ticket itself;
this is about a question that working it just produced.

This branch never reaches step 9 either. It resolves nothing: the pause is deliberate, the
current ticket stays open and blocked, and there is no decision to land.

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

Then go to step 10, which reports the pause and closes.

## Step 9, the landing

The landing hangs the execution work of a decision taken after the collapse. It runs only
when all three conditions hold at once:

1. the session is HITL: a person is on the other side and just approved a resolution;
2. the ticket that step 8 resolved or ruled out is typed `map:grilling` or `map:prototype`,
   never `map:research` and never `map:task`;
3. `counts.milestones` in the `frontier:query` that step 2 read is above zero.

With any of the three false, this step does not run and the session goes straight to step 10.
`map:task` is out by definition: it earns its place by unblocking a decision and never by
delivering a piece of the destination, so a task has nothing to land. The research branch and
the other-role branch of step 8 never get here.

It runs after `ticket:resolve` or `ticket:rule-out` has written, never before and never in
place of it. A session that dies halfway through the landing then leaves the decision
resolved, the map up to date and no issue, which is exactly the state `/map-status` shows in
its block of decisions that never landed. With the landing first, a death would leave
execution issues that the map does not mention and that nobody reports.

There are four sub-steps.

### The round

Propose exactly one of three outcomes, and the person approves it or changes it. Nothing is
written yet.

- New issues: the decision adds work.
- Tie it to an execution issue that already exists: zero new issues, one relation. It is
  probably the most common outcome, and without it every one of those decisions would sit in
  the report as pending until nobody looks at it.
- Nothing: the decision touches nothing of what is being built. It is recorded with the label
  `map:no-landing`, because a report that can never reach zero gets ignored all the same.

The cut where new issues land comes from `milestones`, the key of the `frontier:query` of
step 2, shown by name and with its `status`. Never a cut with `status: done`: adding an issue
to a finished milestone reopens it, and a late decision that un-finishes a cut the team
already demoed breaks an instrument of the team to save one milestone. Read the `status`
before writing and never read it again to verify a write: it is denormalized and lags, and
the lag returns the previous state.

When every cut is `done` and the decision asks for a cut, the cut is born anyway and the
session says so out loud: all the cuts were finished, this reopens the project, and it may be
a sign that the destination was drawn wrong. That is the one place where "there is no
uncollapse" becomes observable.

### The cut, only when the outcome needs one that does not exist

    linear.py milestone:create --project <the project> --name <the cut in prose> \
      --description <the decision that produced it, by name and with its link> \
      --sort-order <the order>

`--sort-order` is a value you compute, strictly between the `sortOrder` of the two neighbours,
taken from `milestones` exactly as the API returned them in step 2. At either end there is
one neighbour only, so pick a nonzero value on the correct side of it. The adapter never
computes it and refuses zero. When `truncated` names `projectMilestones`, the list is a lower
bound and the neighbour you need may not be in it: say that and ask the person for the
neighbouring cuts rather than computing from a partial list.

The `id` it prints is the cut id that the next sub-step passes.

### The work

    linear.py work:write --ctx <the blob from step 1> --project <the project> \
      [--issue <title> <body> <cut id>] [--relate <ticket> <target>] [--no-landing <ticket>]

One invocation, with the shape of the outcome, and `<ticket>` is the identifier of the
resolved ticket, copied verbatim from what `frontier:query` returned:

- new issues: one `--issue` per issue, with the id of the cut it belongs to, plus one
  `--relate <ticket> <position>` per issue, where the position is the 1-based place of that
  `--issue` inside this same invocation;
- tie: no `--issue`, and one `--relate <ticket> <id of the existing execution issue>`;
- nothing: `--no-landing <ticket>` alone.

The title of an execution issue inverts the title of the decision: the question becomes an
imperative. The body is the three-section shape of `map-templates.md`, in Spanish, and it is
never typed from memory. The `Fuera de alcance` of the map is not copied into any body.

### The map, only when a cut was born

`map:write` runs once, with a single
`--append-collapse "**<name of the cut>.** <one sentence>"`. The bold title is the name of
the cut exactly as it was passed to `milestone:create`, final period included. You condense
the sentence from the `description` the milestone was created with, which the person already
saw in the round, so nothing new is shown before the write. The line carries no link,
because `ProjectMilestone` does not expose a `url`. The sentence is in Spanish, like the rest
of the map. When no cut was born, the map is not touched again.

A landing that dies halfway is named and not repaired. When a cut was born and `work:write`
then failed, what is left is an empty milestone and an unlanded decision, and both are
visible: the empty cut in Linear, the decision in the report of `/map-status`. Never try to
delete the cut, because no operation of this plugin does that.

## Step 10, the report and the token

The one home of the closing report and of the token, for the three paths. Which one applies
depends on what step 8 did.

On the normal path, report what the resolution wrote: the comment, the new tickets, the
state, and the line that reached the map. When step 9 ran, also say what it produced: which
of the three outcomes was chosen, which cut received the work, which issues were born with
their URL, or that the decision was marked as having no work. When the frontier that step 2
read held more than the one ticket just resolved, close with `next_recommended: map-work`.

### Reporting a research fan-out

Report, naming these in this order:

1. which research came back well, and what line each one left in the map;
2. which ones did not, by identifier;
3. that each of those is still claimed by you and unreleased;
4. that whether the ticket is actually still open cannot be told from here: a malformed
   or missing return most often means the four writes of its own ticket already landed
   and only the relay back to you, or the `--defer-map` flag itself, is what failed, so
   the ticket is probably already Done or Canceled with its six-section resolution
   comment posted;
5. what to do about it, which is to open that ticket and read its resolution comment
   first: the url and the gist the missing `map:write --append-decision` needs are
   already sitting there, so the one call can be rebuilt by hand from the comment. Only
   when the comment itself never landed either is the ticket genuinely unresolved, and
   then `/map-work` on it, or `ticket:claim --release` to hand the claim back, is what
   applies.

That is the same policy the other-role branch of step 8 already follows when one of its three
writes fails: name what landed, name the claim, do not release it, and say how to finish by
hand. It is not a second policy for the same problem.

With at least one research that did not land, close with `next_recommended: map-work`: that
ticket is open and it is what there is to work. With every one of them landed, report what
landed and close with one token, the same way the normal path does.

### Reporting an other-role pause

Report which of the three writes landed and which did not, and that the claim from step 6 is
still yours until the third one runs. Then close with `next_recommended: map-work`: the ticket
that was just opened is born takeable.
