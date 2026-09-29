---
description: Install or verify the Linear Personal API key that keiron-planner needs
argument-hint: [--verify|--remove]
lang: en
---

ROUTE: scripts/install.sh

Run `${CLAUDE_PLUGIN_ROOT}/scripts/install.sh` with `$ARGUMENTS` forwarded verbatim, and
do nothing else. There is no skill to load and no discipline to conduct.

The script needs a real TTY to read the key without echoing it, and refuses without one.
If it says it has no TTY, do not feed it the key through a pipe, a heredoc, or an
environment variable. Its message carries the exact command the person pastes into a
terminal outside Claude Code: relay it verbatim and stop. Never tell them to run
`/planner-setup` in a terminal, because it only exists inside Claude Code.

Never ask the person to paste the key into this conversation, and never read, print, or
repeat the contents of the key file. The script is the only thing that touches it.

Relay the script's output as it is. Exit code 0 means done and 1 means a failure the
script already explained in a message written for a person, so add nothing to it.
