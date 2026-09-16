---
name: domain-modeling
description: >
  Build and sharpen the domain model of the CRM while a decision is being made: challenge
  terms, invent edge-case scenarios, and settle the vocabulary the moment it crystallises.
  Trigger: Sharpening the domain vocabulary while a decision is being made.
license: MIT
metadata:
  author: Keiron-HealthTech
  version: "1.0"
  scope: [root]
  auto_invoke: Sharpening the domain vocabulary while a decision is being made
lang: en
---

# Domain Modeling

Actively build and sharpen the domain model as you design. This is the *active* discipline:
challenging terms, inventing edge-case scenarios, and writing the glossary and the decisions
down the moment they crystallise. Merely *reading* a glossary for vocabulary is not this
skill: that's a one-line habit any skill can do. This skill is for when you're changing the
model, not just consuming it.

It is reached from a `map:grilling` ticket, alongside grilling.

## The glossary this skill sharpens, and the one it must not touch

Two different files are called `CONTEXT.md`, and confusing them is the expensive mistake here.

- The glossary this discipline sharpens is the **domain glossary of the CRM**. It lives in a
  central domain repository, and each repository of the CRM reaches it through a one-line
  pointer in its own `CLAUDE.md`. Shared terms have a single definition; terms belonging to one
  repository are added in its own section.
- The `CONTEXT.md` of `keiron-planner` is something else entirely: it is the glossary of this
  tool. This skill **never** edits it, on any branch, for any reason.

Do not write the path or the name of the central repository here. None has been measured, and
an invented path is a broken pointer carrying authority. The name arrives in the `CLAUDE.md`
of the repository being worked on, and that is its only house.

If the pointer is not there, proceed in silence. Do not offer to create the glossary, the
central repository, a `CONTEXT.md` inside the repository being worked on, or a directory for
decision records.

**This discipline writes no files.** What it produces lands on the decision ticket, and
nowhere else. That is what makes proceeding in silence a fact rather than a promise.

## During the session

### Challenge against the glossary

When the person uses a term that conflicts with the existing language of the domain glossary,
call it out immediately. "Your glossary defines 'cancellation' as X, but you seem to mean Y.
Which is it?" Reach the glossary through the pointer, never through a fixed path.

### Sharpen fuzzy language

When the person uses vague or overloaded terms, propose a precise canonical term. "You're
saying 'account': do you mean the Customer or the User? Those are different things."

The example is deliberately generic. Writing it with two real terms of the CRM would state a
domain fact no phase of this work verified, inside the file whose whole job is to be right
about the domain, and the next reader would take it for a definition.

### Discuss concrete scenarios

When domain relationships are being discussed, stress-test them with specific scenarios.
Invent scenarios that probe edge cases and force the person to be precise about the boundaries
between concepts.

### Cross-reference with code

When the person states how something works, check whether the code agrees. If you find a
contradiction, surface it: "Your code cancels entire Orders, but you just said partial
cancellation is possible. Which is right?"

"The code" is not one repository. A project of the CRM crosses repositories by default, and
the ones in play are named by the decision ticket or by the person. So:

- a contradiction leaves **with its repository named**, because otherwise the person cannot go
  and look at it;
- if a repository is not available to read, say so and carry on. Never state what its code
  does. A cross-reference against code nobody read is an invention wearing the shape of
  evidence.

### Settle terms as they resolve

When a term is resolved, settle it right there, in the words the session will carry. Don't
batch these up: capture them as they happen.

A domain glossary is totally devoid of implementation details. Do not treat it as a spec, a
scratch pad, or a repository for implementation decisions. It is a glossary and nothing else.

### Where the decision is recorded

A decision that crystallises in the session is recorded where the map records, and never in a
file of the repository being worked on.

## What replaced the two format satellites of the original

The original carried two satellite files, one specifying how to write the glossary and one
specifying the artefact of a decision. Neither travelled here, and this is what took their
place:

| Satellite of the original | What replaces it here |
| --- | --- |
| The one specifying how to write the glossary | Nothing in this plugin. The glossary lives in the central domain repository, which this plugin neither creates nor populates, so its format is not this tool's business. This skill reads that glossary through the pointer and imposes no shape on it. |
| The one specifying the artefact of a decision | The resolution comment of the decision ticket, and its line in the `Decisiones hasta ahora` section of the map. |

The resolution comment has a fixed set of sections with exact text. They are not listed here:
they belong to the shared templates of the map, and a second copy of them would be a future
contradiction.

The original also carried a three-part test for when a decision earns a record: hard to
reverse, surprising without context, the result of a real trade-off. It is gone. Here the
record is not optional and is not offered: every decision ticket that resolves writes its
resolution comment and its line in the index. The criterion moved upstream, to whether a
question earns a decision ticket at all, and that is the work of `/map-new` and `/map-work`.

---

Adapted from mattpocock/skills (github.com/mattpocock/skills), MIT, at commit 6654f6b.
Adapted, not ported: the glossary and the decision record live outside the repo being worked on,
so the two format satellites of the original are gone and this file names what replaced them.
