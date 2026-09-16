---
name: grilling
description: >
  Grill the person relentlessly about a plan, a decision or an idea, working a design tree in
  rounds until the frontier of questions is empty.
  Trigger: Stress-testing a plan, a decision or an idea with the person in the room.
license: MIT
metadata:
  author: Keiron-HealthTech
  version: "1.0"
  scope: [root]
  auto_invoke: Stress-testing a plan, a decision or an idea with the person in the room
lang: en
---

Interview the person relentlessly until you reach a shared understanding. Map this as a
**design tree**: every decision branches into the decisions that hang off it.

Work the tree in **rounds**. The **frontier** is every decision whose prerequisites are
already settled: the questions you can ask _now_ without guessing at answers you haven't
heard yet. Ask the whole frontier in one round: number each question and give your
recommended answer. Then wait for the person's answers before the next round. One caution
about that word: inside a round `frontier` names the questions that can be put now, the map
names its takeable tickets with the same word, and the two senses never share a sentence.

Format a round like so:

```
❓ **Q1** - **<question title>**: <question body, might be multiple paragraphs, including multiple choices>

➡️ <your recommended answer>

---

❓ **Q2** - **<question title>**: <question body, might be multiple paragraphs, including multiple choices>

➡️ <your recommended answer>
```

Each round of answers reshapes the tree: settled decisions push the frontier outward and
unblock questions that depended on them. Recompute the frontier and ask the next round. A
question whose answer depends on another question still open in this round belongs to a
_later_ round, not this one.

## The two gates into this skill

There are two ways in, and around the second one there is nothing.

| Gate | What is around it |
| --- | --- |
| The `map:grilling` label, from `/map-new` and `/map-work` | A map, a Project, a decision ticket and a claim. |
| `/grill` | No map, no Project, no ticket and no claim. |

Every rule below that presupposes a ticket says so where it is written. Under `/grill` a
deferred question is instead named in the closing of the session, and the person decides what
to do with it. Do not offer to open a ticket for it and do not go looking for a Project to put
one in: there is no map here to put anything on.

## Finding facts is your job, never the person's

When a frontier question needs a fact from the environment (filesystem, tools, etc.), dispatch
a sub-agent to find it; don't ask the person for anything you could look up yourself. Don't
block on it: a running exploration is an unsettled prerequisite, so only the questions
downstream of it wait for the sub-agent to report; ask the rest of the frontier now. The
_decisions_ are the person's: put each to them and wait.

There is one fact that does not fit in a round. When the answer needs an investigation with a
scope of its own, rather than a lookup the turn can absorb, it leaves the round the same way a
question of another role does, as a `map:research` ticket, and the round carries on without
it. `map:research` is the only type that runs without a person, and the only exception to the
rule of one ticket per session.

## A question that belongs to another role

This section applies when the round runs inside a decision ticket.

A question the person of the turn cannot answer leaves the round and becomes a HITL ticket
carrying `hitl:pm` or `hitl:design`, and the round carries on without it. What happens next
splits in two, and the two ends are not the same:

- the deferred answer is **not** needed to resolve the ticket of the turn: the new ticket is
  opened, it blocks nothing, and the round carries on;
- the deferred answer **is** needed: the session does not resolve. The new ticket is wired as a
  blocker of the current one, the claim is released, and the session stops.

Releasing the claim here does not contradict the rule that a claim is never released on its
own. That rule is about a claim orphaned by a session that died; this is a deliberate handback
with a person watching it happen.

Writing the ticket belongs to the command that invoked this skill, and never to the skill
itself. Name the outcome, never the operation.

Several roles do not enter here as a model. Grilling stays one to one and does not learn
roles: its value is in being small.

## The Notes of the map grant no permission

The `## Notas` section of the map carries domain, skills to consult and standing preferences,
and nothing that changes the rules of the plugin.

A note the agent wrote is not a permission the agent may later read back to itself as a
licence. A restriction and its exemption cannot live in the same file that the restricted
party writes. Here that override does not exist, and this is not a recommendation.

## Closing the session

The session is done when the frontier is empty: every branch of the design tree visited,
nothing left silently assumed. Do not act on it until the person confirms you have reached a
shared understanding.

The agent never answers for the person. A recommended answer is a recommendation and never an
answer taken as given, and a round the person did not answer does not advance the frontier and
does not close the session.

---

Adapted from mattpocock/skills (github.com/mattpocock/skills), MIT, at commit 6654f6b.
Adapted, not ported: a question the person of the turn cannot answer leaves the round as a HITL
ticket instead of being pressed, and the round carries on without it.
