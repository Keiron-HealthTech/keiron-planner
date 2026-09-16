---
description: Trace the map of a project on Linear, from naming the destination to the first tickets
argument-hint: [linear project url, a loose idea, or nothing]
lang: en
---

ROUTE: skills/map-new/SKILL.md

Load `${CLAUDE_PLUGIN_ROOT}/skills/map-new/SKILL.md`, trace the map of whatever
`$ARGUMENTS` names, and stop. The eight steps live in that file and are not restated here.

`$ARGUMENTS` is the declared exception to the contract: the URL of a Linear Project, a
loose idea, or nothing at all. With nothing, ask what the map is for and stop.

This command, and only this one, runs its preflight in bootstrap mode:

    linear.py preflight --team CRM --bootstrap

It is the only command that can run on a workspace where the `map` label does not exist
yet, so here a missing `map` label is not a hard failure. Everywhere else it is.

The session closes with one next recommended, and the skill is where that choice lives.
