---
name: flowz-workflow
description: Route Codex work through Quick, Standard, or Full depth while coordinating host Plan capabilities, approval boundaries, and existing project rules without taking ownership of them.
---

# FlowZ Workflow

Use this skill to choose exactly one task depth: **Quick**, **Standard**, or
**Full**. Keep the decision and the resulting work within the user's request.
Quick, Standard, and Full are internal routing labels. The user does not need
to choose a depth, a Plan phase, or an internal state name; select the smallest
appropriate depth automatically and describe only a real decision in natural
language.
Read the relevant reference before applying detailed policy:

- [Plan policy](references/plan-policy.md) defines routing and the fixed context
  package.
- [Conflict policy](references/conflict-policy.md) defines precedence and the
  one-time conflict report.
- [Host adaptation](references/host-adaptation.md) defines CLI and desktop
  behavior and session switches.
- [Runtime state](references/runtime-state.md) defines the compact state marker
  used for task continuity and conflict de-duplication.
- [Superpowers integration](references/superpowers-integration.md) defines
  optional recommendations and lifecycle arbitration.

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
session. When active, let its relevant lifecycle rules lead instead of starting
a second design, TDD, debugging, review, or delivery process. When it is not
loaded, FlowZ remains fully usable and may make one non-blocking optional
recommendation for a clearly beneficial Standard or Full task. Follow an
explicit Superpowers Skill invocation in full. See the integration reference;
Superpowers is not a FlowZ dependency and is never installed by FlowZ.

## Humanizer routing

When a task calls for humanization and the matching optional Skill is installed,
route Chinese output only to `humanizer-zh`. Route English output to
`humanizer`, or to its installed compatible alias `humanizer-en`. Never
substitute either language Skill for the other, infer routing from the shared
word "humanizer", or apply both Skills to the same passage. For a bilingual
deliverable, keep the language sections separate. For a mixed-language passage,
split it at clear paragraph or segment boundaries and route each segment to its
matching Skill; never apply both Skills to the same paragraph. If it cannot be
split without changing the meaning, preserve the passage or ask which single
language treatment should govern. If the user explicitly requests both Skills
for one rewriting request, follow their shared upstream contract: ask once
whether to process separate sections with both, use only `humanizer-zh`, or use
only `humanizer`/`humanizer-en`, then wait before rewriting.

## Approval and continuity

State reviewable assumptions, evidence, tradeoffs, and conclusions; do not
request or expose hidden chain-of-thought. Once the user approves a plan,
continue implementation and validation within the approved boundary without
repeating approval requests. Pause for new evidence that overturns the plan,
pause for out-of-scope work, a destructive operation, a permission or external action,
an environment blocker, or a higher-priority project rule.

Keep low-impact, local, reversible edits continuous inside the approved
boundary. Changes with substantive scope, permission, external-state, or
irreversible impact require a user decision, including material data or
architecture changes. A concise risk note says what will happen, its impact,
whether it can be undone, and what
host approval is needed. Do not repeat ordinary intermediate confirmations
inside one approved boundary, and never replace the host's permission system.

When resuming after compaction, use the existing Codex context package first:
goal, scope and non-goals, decisions, acceptance criteria, validation, and
approval boundary. Check the named files or tests for fresh evidence, then
continue the nearest unfinished action. Do not repeat completed work or ask
the user to restate information that is present. Ask only for a minimal missing
field or when evidence is stale; a missing marker never implies approval.

At completion, give one short summary with four items: what changed, what was
verified, remaining risk or unfinished work, and the next user step (including
whether the user must act). If the host already supplies an equivalent summary,
fill only missing evidence instead of emitting a second long report. Never
expose internal phase names, marker details, or hidden reasoning.

The Hook supports only lightweight, session-scoped preferences: `response_detail`
(`concise`, `normal`, or `detailed`) and `plan_summary` (`hidden` or `brief`).
An explicit user instruction overrides a preference. Preferences do not change
host permissions, model or reasoning settings, critical validation ownership,
or project rules, and they never persist the original prompt.

When durable task state changes, append the compact, reviewable marker from
`references/runtime-state.md`. The Hook uses it to restore the approved boundary
after compaction and to avoid repeating a conflict report. Append exactly one
unindented marker at the absolute end of the response and outside Markdown
fences, copy the current Hook-supplied `marker_nonce`, and do not reuse a nonce.
The marker is state, not a substitute for a user-facing conclusion.

ChatGPT web assistance is off by default. User validation suggestions are off
by default. The controls to pause FlowZ, resume FlowZ, or change either switch
take effect from the next user turn; see the host reference for exact scope.
