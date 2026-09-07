# Plan Policy

Quick, Standard, and Full are internal routing labels. Choose them automatically;
the user does not need to choose a depth or a Plan phase, and labels such as
`routing` or `awaiting_approval` are not user commands.
These internal labels stay out of user-facing commands and explanations.

## Route

Use exactly one of the three task depths:

- **Quick**: low risk, small scope, clear intent; do not use the host Plan or
  the structured contract fallback. Implement directly and run automatic agent
  validation.
- **Standard**: material uncertainty, a solution choice, or a local boundary;
  use the host Plan first and the structured contract fallback when no host Plan
  is available. Approval is needed only for material behavior, data,
  permission, architecture, or external-state change.
- **Full**: establish design, risks, acceptance, and an approval boundary before
  implementation. Prefer the host Plan; use structured design as fallback.
  After approval, implement and validate continuously inside the boundary.

## Context package

When a Plan or fallback contract is needed, keep these fields in order:

1. Goal
2. Scope and non-goals
3. Constraints
4. Evidence
5. Confirmed decisions
6. Options and tradeoffs
7. Acceptance criteria
8. Verification method
9. Approval boundary
10. Pause conditions

The structured fallback uses these same fields and is not a second planning
system. The host Plan remains preferred when visible and available.

## Reasoning and approvals

Reasoning investment belongs to this Plan policy. It may request more careful
host reasoning for a Standard or Full task, but it never changes the selected
model, reasoning setting, or `config.toml`. Report only reviewable assumptions,
evidence, tradeoffs, and conclusions.

Approval authorizes continuous work only inside the stated boundary. Pause when
new evidence overturns the plan, scope expands, a destructive or permissioned
operation is needed, an external state change is required, the environment is
blocked, or a higher-priority rule requires a pause.

For low-impact local and reversible edits, continue without an extra permission
preface. For behavior, data, permission, architecture, external-state, or
irreversible changes, briefly state the action, impact, reversibility, and host
approval needed. One approval boundary covers its ordinary intermediate steps;
do not ask repeatedly.

## Completion summary

Use a concise natural-language completion summary containing what changed, what
was verified, remaining risk or unfinished work, and the next user step. An
unfinished task must not be described as complete. Agent-owned safety, data
integrity, and critical regression checks remain required even when optional
user validation suggestions are disabled.
