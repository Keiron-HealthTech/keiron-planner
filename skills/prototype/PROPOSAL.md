---
lang: en
---

# Written proposal

The branch of a ticket that carries `hitl:design`. The label chose it, not the question, and
nobody was asked: `Diseño` decides without touching code. The session is a conversation with
`Diseño` that ends in a proposal written in prose, and nothing else gets built.

Where the design itself is drawn is not this session. It
lives in Claude Design, behind its live link, and the agent never builds variants there. The
tool belongs to `Diseño`: the agent does not draft screens in it and does not ask for a copy
of what is there.

## The four parts

The proposal is written in Spanish, because its reader is a person in Linear, and it carries
four parts, in this order:

1. `Para qué es la vista`: what the view is for, and who reaches it and when.
2. `Qué debe tener`: what has to be on it for that purpose to hold.
3. `Qué considerar`: the constraints the view lives under, including every decision of the
   map that touches it. Read those off `Decisiones hasta ahora` in the map, and name each one
   by the ticket it came from.
4. `Qué queda abierto`: what this proposal leaves for `Diseño` to settle in Claude Design.

The same four are the sections of the delivery body in
`${CLAUDE_PLUGIN_ROOT}/skills/_shared/map-templates.md`. Write them with that template and
never from memory.

## How many

One proposal is the default. The exception is to write
two or three approaches when the decision spans several views or `Diseño` asks for them, and
then `Diseño` picks one. The minimum of two variants does not apply here: that rule exists
to stop a choice slipping in unsaid between code variants, and a proposal that `Diseño`
approves out loud is already a said choice.

## What the agent does not do

- It writes no code, on any branch, not even a sketch of one.
- It builds no variants in Claude Design.
- It never chooses. It writes, `Diseño` approves or changes, and the agent rewrites until
  `Diseño` says it is approved. Without that, the ticket stays open.

## Where it goes

The approved proposal is the body of the design delivery. `/map-work` passes it in its step 8
with `--design-delivery`, as a single argument, and the delivery is born in the same first
write as the new tickets. The resolution comment names who approved it in `## La decisión`, as
on the other two branches.
