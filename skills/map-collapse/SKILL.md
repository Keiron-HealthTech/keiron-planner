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
