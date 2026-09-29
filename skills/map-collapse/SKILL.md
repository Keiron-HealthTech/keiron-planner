---
name: map-collapse
description: >
  Collapse a finished Linear map: check the frontier is empty, ground the cuts and the
  execution issues in conversation, then write the milestones, the work and the map.
  Trigger: Loaded by commands/map-collapse.md, and by nothing else.
license: MIT
metadata:
  author: Keiron-HealthTech
  version: "1.0"
  scope: [root]
  auto_invoke: Loaded by commands/map-collapse.md, and by nothing else
lang: en
---

CONTRACT: `${CLAUDE_PLUGIN_ROOT}/skills/_shared/map-contract.md`, read it FIRST. It owns the
closed token set, the citation form, the `$ARGUMENTS` contract and the derivation of the
verdict. Resolve all four from there rather than restating them here.

TEMPLATES: `${CLAUDE_PLUGIN_ROOT}/skills/_shared/map-templates.md`. It owns the shape of every
piece of text a person ends up reading in Linear, and that text is in Spanish. The body of an
execution issue and the sixth heading of the map are there. Never type one of those shapes
from memory.

ADAPTER: `${CLAUDE_PLUGIN_ROOT}/scripts/linear.py`, invoked with Bash and written `linear.py`
below. This skill runs six of its operations and no other: `preflight`, `map:read`,
`frontier:query`, `milestone:create`, `work:write` and `map:write`. Never compose GraphQL
yourself and never touch the Linear API directly.

The first three only read. The last three are the writes of the session, and they run in
that order and in no other: one `milestone:create` per cut, then one `work:write`, then one
`map:write`. Nothing else in this file writes, and no operation that resolves or blocks a
decision ticket applies here, because the frontier of a map that collapses is empty by
precondition.

When any invocation exits non-zero, relay its stderr as it is, add nothing to it, and stop. Do
not reformulate the remediation and do not turn the failure into a token: every hard failure
already carries its own remediation, written by the operation that produced it.

The collapse happens once per map. It is a conversation with a person, in two passes, and
nothing is written until the person has approved everything that will be written. The steps
below run in order. Nothing here is optional and nothing reorders.

## Step 1, the preflight

    linear.py preflight --team CRM

Once per driver, with `--team` and no other flag. A missing `map` label is a hard failure here,
and the remediation it prints already names where to go.

Non-zero: relay its stderr as it is and stop, with no token. No later step runs.

Its stdout is an opaque blob. Pass it along as `--ctx` to the operations that ask for one, and
never edit it, never read a value out of it to make a decision, and never resolve one of its
values on your own.

## Step 2, the map and the frontier

    linear.py map:read --project <the argument>
    linear.py frontier:query --ctx <the blob from step 1> --project <the same argument>

In that order, and neither one writes anything. This session reads the frontier with its own
invocation and never trusts what brought it here: it can be started directly, without having
passed through any other command. Three answers stop the session here:

- `found` false in `map:read`: the argument resolved to no Project this credential can see.
  Say that and stop, with no token. None of the six says "fix the argument".
- `found` true and all six values of `sections` null: the Project resolved and carries no map.
  Emit `next_recommended: map-new` and stop, without running `frontier:query`. There is
  nothing to collapse yet.
- `found` false in `frontier:query` after `map:read` answered `found` true for the same
  `--project`: the Project stopped resolving between the two reads. Report that discrepancy
  and stop, with no verdict and no token.

Whether a section exists comes from `sections`, never from a search inside `content`.

## Step 3, the verdict, and the two refusals

Derive the verdict with the contract's table, cited and never copied, out of `counts` and
`notTakeable` and nothing else. Read `counts.milestones` ONLY when `counts.open` is zero.

With `counts.open` above zero, the map still has open tickets. Say so, write nothing, and stop
with the token the contract gives that verdict:

- `next_recommended: map-work` when something is takeable
- `next_recommended: release-claim` when a claim holds the frontier
- `next_recommended: break-cycle` when only blockers hold it

When `counts.open` is zero and `truncated` names `issues`, `counts.open` is a lower bound and
the zero proves nothing. Say that and stop with no token: the collapse needs the frontier to
be verifiably empty. A lower bound above zero still proves open tickets, so it takes the
branch above.

With `counts.open` zero and `counts.milestones` zero, the verdict is `listo para colapsar`.
This session is the one that serves it, so it recommends nothing and goes to step 4.

With `counts.open` zero and `counts.milestones` above zero, the map already collapsed. Split
by `hasIssues` in the entries of `milestones`:

- Some milestone has issues. This is a second run for real: refuse, say why, write nothing,
  and close with `next_recommended: sdd-new`. The collapse is idempotent by refusal and never
  by merge. Merging two collapses is the destructive operation nobody asked for, and there is
  no uncollapse.
- No milestone has issues. A collapse died before step 7, and step 6 may have died at cut k of
  N or timed out after creating one, so the cuts that exist may be only some of the approved
  ones. Say so, show the cuts that already exist BY NAME and with no link, because
  `ProjectMilestone` does not expose a `url`, and ask the person whether those are all the cuts
  of the collapse. Take the id of each existing cut from `milestones`, as the API returned it
  in this run. If they are all, offer to resume by reusing those milestones and starting at
  step 5, and steps 4 and 6 do not run again. If some are missing, the round of step 4 runs
  only for the missing cuts, and step 6 creates only those, never one that exists, each with a
  `--sort-order` after or between the existing ones. Step 5 then covers all the cuts, the
  existing and the new.

When `hasIssues` is missing from the entries, or `truncated` names `projectMilestones` so the
list is a lower bound, do not decide alone. Show the cuts that are there by name and ask the
person whether any of them already holds execution issues. Yes is the refusal above, and no
is the offer to resume.

## Step 4, first pass: the cuts

A grilling session with domain-modeling, the discipline the contract gives to a `map:grilling`
ticket, over the index under `## Decisiones hasta ahora` that step 2 read. The agent proposes
the milestones and the person approves them or redraws them. The agent never answers for the
person. NOTHING IS WRITTEN YET.

The first cut is always the tracer bullet of the project, and it is grilled, never derived
from the map: no decision ticket answers which is the smallest vertical slice that proves the
architecture works. A milestone is a demoable cut and never a slice of time. How many there are
comes out of the round and is not fixed beforehand.

The name of a cut is the cut in prose, with no numeric prefix. Its description names the
decisions that produced the cut, each by name and with the link to its ticket, and that is all
the traceability the collapse leaves. Name and description are text a person reads in Linear,
so they are in Spanish.

## Step 5, second pass: the execution issues

Only when every cut is approved. Inside each cut the agent proposes the issues and the person
approves them. The two passes are one session and the second does not start before the first is
approved: mixing them makes redrawing a cut throw away the issues already proposed for it, and
redrawing cuts is exactly what step 4 asks of the person.

The title of an execution issue inverts the title of the decision: the question becomes an
imperative. The body is the three-section shape of `map-templates.md`, in Spanish, and it is
never typed from memory. The `Fuera de alcance` of the map is not copied into any body. This
is not a proposal, and that is deliberate.

Then show the whole batch, the cuts by name and in order, and ask for confirmation ONCE. After
the yes, nothing is asked again before the writes end.

## Step 6, the milestones, one call per cut, in order

    linear.py milestone:create --project <the project> --name <the cut in prose> \
      --description <the decisions that produced it> --sort-order <the order>

One invocation per cut, in the order of the round, one at a time and never together: there is
no batch mutation for milestones, and the order of the calls is the order of the cuts. The
`--sort-order` values are explicit, ascending and nonzero, and the adapter refuses zero. No
call passes a date.

Keep the `id` each invocation prints. It is what step 7 puts in the third value of each
`--issue`, and it comes from the payload of the mutation and never from what you believe you
typed. This is the first write of the session, and nothing wrote before it.

A resumed run whose cuts are all there skips this step: the ids are the ones step 3 took from
`milestones`. A resumed run with missing cuts creates only the missing ones and takes the ids
of the existing cuts from step 3.

## Step 7, the work, one atomic call

    linear.py work:write --ctx <the blob from step 1> --project <the project> \
      --issue <title> <body> <cut id> [--issue <title> <body> <cut id> ...]

ONE invocation, with every issue of every cut, because the batch creates them atomically. List
the issues of the first cut first, so the first issue the adapter prints is the first issue of
the first cut. Pass no `--relate` and no `--no-landing`: the collapse does not backfill the
decisions taken before it, and the block of decisions that never landed in `/map-status`
separates them by date for exactly that reason. No block is wired between execution issues:
the order of execution belongs to the team, and the milestone with its `sortOrder` already
gives the coarse order.

When it fails, relay its stderr and stop, and do not rerun the `work:write`: a rejection and
a lost response look the same, so the issues may exist. Tell the person to check Linear. A new
run of `/map-collapse` reads step 3: with no issues in any cut it lands in the resume offer,
and with issues already there it refuses, in which case only the step 8 `map:write` is left
and it can be run on its own, because step 8 explains its rerun is safe.

## Step 8, the map, once, under the sixth heading

    linear.py map:write --project <the project> \
      --append-collapse "**<name of the cut>.** <one sentence>" \
      [--append-collapse "..." ...]

ONE invocation and never one per cut: one `--append-collapse` per cut, in the order of the
round. The bold title is the name of the cut exactly as it was passed to `milestone:create`,
followed by a period. The sentence is in Spanish, and you condense it from the description the
milestone was created with, which the person already approved in the first pass, so nothing
is shown before this write beyond what the flow already shows and nothing new is asked. In a
resumed run the description is not in the read, so condense the sentence from what the person
approved for that cut in step 5. The line carries the name and the sentence and nothing else,
and no link, because `ProjectMilestone` does not expose a `url`.

The fingerprints that step 2 read may go along as `--expect-sections`. It is optional, and a
drift it reports goes to stderr and never aborts the write.

This is the last write and the only one to the map. When it fails, relay its stderr and stop:
rerunning `/map-collapse` does not help, because a new run refuses once issues exist. Offer to
rerun that same `map:write` invocation, unchanged. It is safe: if the first write never landed,
the rerun writes the lines; if it landed and only the answer was lost, the rerun aborts because
the bold title of each cut is its uniqueness key, which confirms the lines are there. Only when
the rerun fails for any other reason are the lines the person's to add by hand.

## Step 9, the closing report and its token

Report, in this order: the cuts that were created, in order; the issues each one holds; and
the first issue of the first cut with its URL, which is where someone starts. The URL is the
one `work:write` printed, copied verbatim.

Close with `next_recommended: sdd-new` and nothing inside the token but the token. The name of
the sibling plugin, if you say it, goes in the prose. Then stop.
