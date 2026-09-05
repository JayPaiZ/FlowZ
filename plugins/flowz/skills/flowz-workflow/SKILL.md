---
name: flowz-workflow
description: Route Codex work through Quick, Standard, or Full depth while coordinating host Plan capabilities, approval boundaries, and existing project rules without taking ownership of them.
---

# FlowZ Workflow

Use this skill to choose exactly one task depth: **Quick**, **Standard**, or
**Full**. Keep the decision and the resulting work within the user's request.
Read the relevant reference before applying detailed policy:

- [Plan policy](references/plan-policy.md) defines routing and the fixed context
  package.
- [Conflict policy](references/conflict-policy.md) defines precedence and the
  one-time conflict report.
- [Host adaptation](references/host-adaptation.md) defines CLI and desktop
  behavior and session switches.

## Depth routing

- **Quick** means low-risk, small-scope, and clear intent. It does not use the
  host Plan or the structured contract fallback; implement directly and run
  agent-owned validation.
- **Standard** means material uncertainty, a meaningful choice, or a local
  boundary. Use the **host Plan first**; use the **structured contract
  fallback** when the host has no Plan. Wait for approval only when behavior,
  data, permissions, architecture, or external state will materially change.
- **Full** means proactively establish design, risks, acceptance criteria, and
  an approval boundary. Prefer the host Plan; use structured design as the
  fallback. After approval, continue implementation and validation inside that
  boundary.

Reasoning effort is part of the Plan policy. Ask the host for deeper reasoning
when the selected depth warrants it, but must not modify `config.toml`, the
user's model choice, or the user's reasoning setting.

## Existing rules and conflicts

Check applicable `AGENTS.md`, existing Skills, plugins, and workflows before
adding FlowZ behavior. Those sources have priority. If a FlowZ action conflicts,
skip it, report once (including the conflicting source), and do not modify the
source. Do not copy or rename third-party Skills.

Respect Superpowers only when it is visibly loaded and active in the current
session. Superpowers is not a FlowZ dependency, and this skill does not require
any particular Superpowers lifecycle.

## Approval and continuity

State reviewable assumptions, evidence, tradeoffs, and conclusions; do not
request or expose hidden chain-of-thought. Once the user approves a plan,
continue implementation and validation within the approved boundary without
repeating approval requests. Pause for new evidence that overturns the plan,
pause for out-of-scope work, a destructive operation, a permission or external action,
an environment blocker, or a higher-priority project rule.

ChatGPT web assistance is off by default. User validation suggestions are off
by default. The controls to pause FlowZ, resume FlowZ, or change either switch
take effect from the next user turn; see the host reference for exact scope.
