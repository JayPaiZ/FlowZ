# Document Workflow v0.1

## Purpose

Use this workflow to help developers use existing AI coding agent capabilities in a predictable way. The first adapter targets Cline, but the principles are not limited to VS Code, Cline, or one host. This is a lightweight guidance layer, not a new agent runtime or hard security boundary.

The first version is Cline-first. It may reference project rules, project operation guides, skills, hooks, and host tools when they are available, but the core workflow must still work without any optional capability.

## Operating principles

1. Read the repository instructions and relevant project context before changing files.
2. Classify the request before choosing a process. Do not force every request through the full workflow.
3. Keep the user experience simple. The user should describe the outcome; do not require internal state names or slash commands unless Cline needs them.
4. Keep the scope explicit. Do not expand the change because a nearby improvement is interesting.
5. Verification is part of the work. Do not claim completion from an explanation alone.
6. If a plan no longer fits the evidence, stop, explain the change, and revise the plan before continuing.
7. Treat rules as guidance. Use a script or hook for a rule only when the check is deterministic and repeated violations justify the extra mechanism.

## Task triage

Choose the smallest tier that fits. These tiers describe the depth of the working loop, not a file-count checklist. Use judgment, and escalate when ambiguity, risk, or scope grows.

### Quick

Use when the Agent can quickly understand the intent, make a small low-risk change, and verify it directly. A Quick task may still need a small clarification.

Process:

1. Restate the requested outcome and inspect the relevant file or failure.
2. Make the smallest change that solves the request.
3. Run the narrowest useful verification.
4. Report the change and evidence.

Do not create a persistent task or separate spec unless the project already requires one or the work expands.

### Standard

Use when the task needs some investigation or a short plan, but not a formal design. It may involve one file or several files.

Process:

1. Clarify the outcome, constraints, and acceptance conditions.
2. Read the relevant code, documents, and tests.
3. Present a short plan when the change has meaningful choices or risk; get confirmation when a decision changes behavior, architecture, or external state.
4. Implement within the agreed scope.
5. Verify with relevant tests, lint, type checks, build checks, or runtime checks.
6. Report evidence, remaining risk, and any useful durable lesson.

### Full

Use when the task needs a formal design, careful confirmation, or multiple implementation phases because its uncertainty or impact is material.

Process:

1. Define the problem, users, constraints, and acceptance criteria.
2. Produce a spec or design and identify the affected boundaries.
3. Review the design with the user before implementation.
4. Create an implementation plan and execute it in small, reviewable steps.
5. Verify behavior and inspect the final diff.
6. Review whether a stable lesson belongs in project rules, a procedure, a skill, or a hook.

Internal task states such as `planning`, `in_progress`, and `verifying` may be used by project records or scripts. Do not make the user manage those states unless the user asks to see them.

## Cline adapter

This section tells Cline how to apply the host-neutral workflow. It is an execution guide, not a list of commands the user must learn.

- Treat the user's natural-language outcome as the primary input. Do not require the user to know Plan/Act names, file-mention syntax, or internal task states.
- Map Quick work to Act mode.
- Map Standard work to Plan mode for the short investigation and plan, then Act mode for implementation. Wait for user confirmation only when the decision changes behavior, architecture, data, permissions, external state, or another material boundary.
- Map Full work to `/deep-planning` or an equivalent Cline planning pass that produces a reviewable design or specification before Act mode.
- Collect relevant workspace context yourself: inspect the applicable instructions, code, documents, tests, and runtime evidence. If context is missing, ask the user in plain language; do not make them learn a file-mention syntax.
- Treat `AGENTS.md` and `.clinerules/` as instruction sources. Use conditional rules when their file scope matches the current work.
- Invoke an enabled Skill only when its trigger matches the task. If an applicable Skill is unavailable or incompatible, continue with the core workflow when possible and state the gap.
- Use `/smol` or `/compact` only as a context-management action when needed or requested. It does not replace the handoff contract.
- After a handoff is recommended and the user confirms, generate the handoff prompt. The user decides whether to use Cline's `/newtask` or start another blank session.
- A Checkpoint may be created before Act mode for Standard or Full work when it helps recovery. It does not replace verification or handoff.

## Choosing capabilities

Select capabilities after triage. Do not call or install something merely because it exists.

| Capability | Use it when | Default behavior |
| --- | --- | --- |
| Project operation guide | The project has a stable operation documented in a README, runbook, script, or command. | Reuse the project source of truth; do not assume a universal operation-guide mechanism. |
| Skill | The task needs reusable judgment, analysis, review, or a domain-specific method. | Use a relevant enabled skill when its trigger matches. |
| Hook | A check or action must happen at a lifecycle point and can be judged mechanically. | Keep it out of the core workflow until repeated evidence justifies automation. |

Selection rules:

1. Prefer host-native and project-owned capabilities over host-specific assumptions.
2. Reuse the project's existing operation guide, script, or command when it is the source of truth.
3. Use a Skill when judgment is the main part of the work. If the matching Skill is unavailable, use the requirements or review checklist manually.
4. Use a Hook only for deterministic enforcement, not as a substitute for thinking or review.
5. Do not assume a Skill, Rule, Workflow, or Hook from one agent can run on another agent without adaptation.
6. Keep installation and host integration outside the core workflow. Ask before installing or enabling anything.
7. If no available capability materially improves the task, continue without one.

Capability availability is distinct from task applicability: an enabled capability that does not match the task should remain unused, while a missing or incompatible capability is a reported gap rather than a reason to invent a substitute.

## Scope and safety

- Read only the files and systems needed to understand the task.
- Preserve existing user changes.
- Do not read secrets or sensitive files unless the task explicitly requires it and the user has authorized that access.
- Ask before installing software, changing permissions, writing to external systems, publishing, deploying, or performing another high-impact action.
- If a requested action would delete or overwrite material data, identify the exact target and obtain confirmation immediately before doing it.

## Verification

Choose evidence proportional to risk. Prefer, in order as applicable:

1. Focused tests for the changed behavior.
2. Type, lint, format, or static checks.
3. Integration, build, or packaging checks.
4. Runtime or user-visible checks.
5. Final diff and scope review.

When verification fails:

1. Record the failure and the command or observation that produced it.
2. Diagnose the cause before changing code or tests.
3. Return to implementation, revise the smallest necessary change, and verify again.
4. Never weaken or delete a test only to make the result pass.

## Context health and handoff

Long sessions can accumulate stale, irrelevant, or conflicting context. Describe this as context quality risk, not as a claim that the model has literally become less intelligent.

The Agent may mark `HANDOFF_RECOMMENDED` when clear context-quality risk appears, such as repeated loss of confirmed constraints, unresolved work after repeated revisions, a host-reported context event, or a user report that response quality is declining. The exact compression threshold is maintained as a separate design decision and is not part of this workflow contract.

The marker is advisory. Do not automatically create a handoff, start a new session, or copy conversation history. First tell the user why a new session may improve reliability and ask whether to generate a handoff prompt.

When the marker is raised, do not start another feature or widen the scope. Finish the current smallest safe unit first: complete in-progress writes, finish validation already required for that unit, and inspect the current state. Defer the recommendation if a write is incomplete, validation is still running, or the actual state is unknown.

Only after the user confirms, generate a compact, self-contained prompt for a new blank session containing:

Use this fixed order:

1. Handoff reason and whether the current safe unit is complete.
2. Project identity and state: absolute project path, current branch, `HEAD`, and uncommitted changes.
3. Task goal, current phase, and completed work.
4. Confirmed decisions and constraints.
5. Files or systems changed.
6. Verification evidence, including checks not run.
7. Remaining risks and unverified items.
8. Unresolved questions.
9. The next action for the new session.
10. Files the new session should read first.
11. Environment and external operations: current model and API state when known, local/runtime data and privacy boundaries, and commits, pushes, deployments, publications, or other external operations performed or not performed.

The user copies that prompt into a new blank task or session and decides whether to switch. Host behavior may differ: a Cline checkpoint preserves workspace state but is not a portable conversation summary, while Codex may provide its own session recovery or context compaction. The workflow keeps the handoff contract host-neutral.

## Completion report

Use the shortest report that still gives the user reliable evidence:

### Quick

- what changed;
- verification result.

### Standard

- what changed;
- verification result, including checks not run;
- remaining risk or limitation.

### Full

- completed outcome and affected areas;
- relevant design or task state;
- verification evidence, including checks not run;
- remaining risks and unverified items;
- durable knowledge or document updates;
- whether `HANDOFF_RECOMMENDED` was raised and whether the user accepted it.

Every report should include a concrete next step when one exists and state any user decision that is still needed. Do not claim completion from an explanation alone.


Only call the task complete when the requested outcome and its verification condition are both satisfied, or when the user explicitly accepts the remaining limitation.

## Project experience feedback

After a task or a repeated correction, the Agent may identify a project-specific experience that could help future work. A candidate should be specific to the project, supported by an observed task or explicit user decision, actionable as a future instruction, likely to remain valid, and not already covered by existing documents.

Use these evidence thresholds before making a suggestion:

- the same kind of issue appeared in at least two tasks; or
- the user explicitly confirmed it as a long-term project rule; or
- it is a significant architecture or data boundary that the user explicitly wants preserved after one occurrence.

Suggest the smallest suitable carrier:

- project `AGENTS.md` for stable collaboration constraints;
- architecture documentation for system boundaries;
- README, Runbook, or scripts for fixed operations;
- a project Skill for repeated judgment-heavy methods;
- a script or Hook for deterministic enforcement only after the need repeats.

Before writing, show the candidate experience, its evidence, proposed carrier, expected impact, and maintenance cost. Ask the user to accept it, revise it, keep it only in the task record, or reject it. Do not write it automatically.

## Escalation

Escalate from Quick to Standard or Full when any of these appears:

- the request affects multiple unrelated areas;
- the requirement has more than one materially different interpretation;
- the change alters architecture, data, permissions, or external behavior;
- verification exposes an unknown root cause;
- a new reusable rule or automation is being proposed;
- the task needs a capability that is missing or incompatible with the current host;
- the session shows context-quality risk and a handoff is recommended.
