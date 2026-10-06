---
description: Collapse a finished map into the milestones and the execution work it implies
argument-hint: <linear-url>
lang: en
---

ROUTE: skills/map-collapse/SKILL.md

Load `${CLAUDE_PLUGIN_ROOT}/skills/map-collapse/SKILL.md`, collapse whatever `$ARGUMENTS`
names, and stop. The nine steps live in that file and are not restated here.

`$ARGUMENTS` follows the general contract and not the exception that `/map-new` declares: the
URL of a Linear Project, or the URL or identifier of one decision ticket of its map. With no
argument, ask which map and stop.

This command runs once per map and refuses a second run. It also refuses while a design
delivery of the map is still open. It is where the plugin ends: after it the work is in Linear
and the sibling plugin takes over.

The session closes with one next recommended, and the skill is where that choice lives.
