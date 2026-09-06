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

The following user controls apply from the next user turn. Treat the quoted
phrases as explicit commands (English `open`/`close` and `enable`/`disable` are
equivalent); a polite prefix or suffix does not turn unrelated prose into a
control command:

- "pause FlowZ" stops FlowZ routing and assistance for subsequent turns.
- "resume FlowZ" re-enables FlowZ routing for subsequent turns.
- "open/close ChatGPT web assistance" changes only that independent switch.
- "open/close user validation suggestions" changes only that independent
  switch.

If the user requests an onboarding retry while FlowZ is paused, queue that
one retry and run it only after an explicit resume. Viewing saved diagnostics
remains display-only even while paused.

ChatGPT web assistance and user validation suggestions are off by default.

When ChatGPT web assistance is off, do not propose or use a separate ChatGPT
web conversation as part of FlowZ. When ChatGPT web assistance is on, use it
only when an independent conversational pass would materially help the current
task and a visible browser capability is available. State what information will
be shared and how its result will be reconciled with repository evidence. Do
not send credentials, private logs, or unrelated project content. If no browser
capability is available, offer a compact paste-ready prompt instead of claiming
that a web conversation occurred.

When user validation suggestions are off, the agent performs every feasible
ordinary validation itself and does not offload work merely to save tokens.
When user validation suggestions are on, the agent may suggest clearly optional
checks that are non-critical, unusually token-intensive, or environment-specific,
such as browser appearance, hardware behavior, or private-account integration.
Explain why the user is better placed to run each suggested check. Safety, data
integrity, and critical regression checks always remain agent-owned and must be
run whenever the environment permits.
