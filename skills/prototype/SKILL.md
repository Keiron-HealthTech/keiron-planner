---
name: prototype
description: >
  Build throwaway code that answers the question a decision ticket asks: a driveable logic
  demo, or several radically different UI variants for the person to choose between; or, for
  a `hitl:design` ticket, a written proposal with no code.
  Trigger: Building throwaway variants to answer a design question.
license: MIT
metadata:
  author: Keiron-HealthTech
  version: "1.0"
  scope: [root]
  auto_invoke: Building throwaway variants to answer a design question
lang: en
---

# Prototype

A prototype is **throwaway code that answers a question**. The question decides the shape.

It is reached from a `map:prototype` ticket, which is HITL: the person is there by definition
of the type.

## Pick a branch

The label decides before the question does. A ticket that carries `hitl:design` takes the
written-proposal branch, [PROPOSAL.md](PROPOSAL.md), and nobody is asked whether they want
code: `Diseño` decides without touching code, and the design itself lives in Claude Design.
The two code branches below are for every ticket without `hitl:design`.

The question being answered is **the body of the decision ticket**, which is a question and
not a task. Do not reformulate it into something easier to prototype. If the question does not
say enough to pick a branch, ask: the person is in the room.

- **"Does this logic / state model feel right?"** → [LOGIC.md](LOGIC.md). Build a single
  shareable HTML file (free-play buttons plus tabbed guided walkthroughs) that pushes the state
  machine through cases that are hard to reason about on paper, and that a non-developer can
  drive.
- **"What should this look like?"** → [UI.md](UI.md). Generate several radically different UI
  variations on a single route, switchable via a URL search param and a floating bottom bar.

The two branches produce very different artifacts, so getting this wrong wastes the whole
prototype. State the question and the branch you picked at the top of the prototype.

There is no default to fall back on when the answer does not come. Ask and wait. A rule written
for a state that cannot exist is exactly the rule an agent reaches for when it wants to move
alone, and this file carries the opposite hardening.

## Rules that apply to the two code branches

1. **Throwaway from day one, and clearly marked as such.** There is no single place for it: the
   polyrepo already settled that. The artifact lives where its nature asks for. A throwaway
   Linear Project if it is a Linear artifact, a branch if it is code. The ticket **links** to
   it and never pastes it inside. When it is code, name it so a casual reader can see it's a
   prototype, not production, and obey whatever routing convention the project already uses;
   don't invent a new top-level structure.
2. **Trivial to run.** A UI prototype starts from one command in the project's task runner:
   `pnpm <name>`, `python <path>`, `bun <path>`, etc. A logic demo is a single HTML file the
   person double-clicks. Either way, no thinking required to start it.
3. **No persistence by default.** State lives in memory. Persistence is the thing the prototype
   is _checking_, not something it should depend on. If the question explicitly involves a
   database, hit a scratch DB or a local file with a clear "PROTOTYPE, wipe me" name.
4. **Skip the polish.** No tests, no error handling beyond what makes the prototype _runnable_,
   no abstractions. The point is to learn something fast.
5. **Surface the state.** After every action (logic) or on every variant switch (UI), print or
   render the full relevant state so the person can see what changed.
6. **Capture it when done.** The prototype is a **primary source** and is not thrown away: it
   goes to a throwaway branch, out of the main branch, and the answer is captured together with
   the question it settled. The pointer to that branch goes on the **decision ticket**, and the
   answer goes in its resolution comment. There is no implementation issue to point at: the
   issues of execution are born in the collapse. Fold nothing into real code, on any branch. A
   map decides and does not build, and code written under prototype constraints, with no tests
   and no error handling, has no business in a main branch.

## The agent builds and never chooses

1. **The agent builds. The person chooses.** Never state which variant won, nor whether a model
   works, neither by implication nor by presenting a recommendation as a conclusion.
2. **A `map:prototype` ticket does not resolve without a choice said by the person.** Without
   it the session ends with the prototype delivered and the ticket open.
3. **The `## La decisión` section of the resolution comment has to name who chose.**
4. **What counts as that choice is different in each branch**, and only one of the three is
   about variants:

| Branch | What counts as the person's choice |
| --- | --- |
| UI | Which variant wins, said by the person. With fewer than two variants built, the ticket does not resolve: one variant is not a prototype, it is a proposal, and it is how the choice slips in without being said. |
| Logic | The verdict on the model, said by the person after driving the demo: whether it works, and what changes if it does not. Show what happened; never declare the verdict. |
| Written proposal | The proposal, or one of the approaches, approved by `Diseño`, said by the person. The minimum of two variants does not apply here: one proposal is the default. |

---

Adapted from mattpocock/skills (github.com/mattpocock/skills), MIT, at commit 6654f6b.
Adapted, not ported: the agent builds the variants and never chooses, and nothing is folded into
real code here, because a map decides and does not build.
