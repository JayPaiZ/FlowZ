# Host Adaptation

## Visible capabilities

On Codex CLI and the ChatGPT desktop app, use the host Plan when it is visible
and available. If it is not available, use the same-field structured contract
from `plan-policy.md`. Do not require the user to learn fixed commands; express
the workflow in the host's currently visible interaction model.

Global plugin enable/disable remains controlled by the host. A running session
does not promise hot loading or hot unloading; a new chat or CLI session is the
reliable boundary for a global change.

## Session switches

The following user controls apply from the next user turn:

- "pause FlowZ" stops FlowZ routing and assistance for subsequent turns.
- "resume FlowZ" re-enables FlowZ routing for subsequent turns.
- "open/close ChatGPT web assistance" changes only that independent switch.
- "open/close user validation suggestions" changes only that independent
  switch.

ChatGPT web assistance and user validation suggestions are off by default.
The agent still performs ordinary executable validation when suggestions are
off; enabling suggestions never transfers responsibility for safety, data
integrity, or critical regression checks.
