# Document Workflow v0.1

## Purpose

Use this workflow to help developers use existing AI coding agent capabilities in a predictable way. The first adapter targets Cline, but the principles are not limited to VS Code, Cline, or one host. This is a lightweight guidance layer, not a new agent runtime or hard security boundary.

The first version is Cline-first. It may reference project rules, project operation guides, skills, hooks, and host tools when they are available, but the core workflow must still work without any optional capability. The FlowZ repository is an installation source, not a directory to copy into every project. Bundled Skill source assets live under `.workflow/resources/skills/`; they are not project-runtime Skills. During Cline onboarding or when a required bundled Skill is missing, the Agent runs the unified installer to place selected assets in the user's Cline directories; no per-Skill confirmation is required. The core workflow still does not download or install Skills during every task.

## Global installation and first-task onboarding

When the user asks to install FlowZ, or when onboarding detects that the bundled Cline capabilities are missing, the Agent detects the host and resolves the active Cline user's actual Skills and Rules directories before running the matching installer: `.workflow/resources/skills/install-flowz-cline.ps1` on Windows, or `.workflow/resources/skills/install-flowz-cline.sh` on Ubuntu/Linux. It passes those directories explicitly to the installer. Manifest paths are only candidates; the Agent reads the active Cline or compatible fork's documentation/configuration and reuses inherited native paths. If the host or target directories cannot be identified, or more than one plausible target exists, the Agent reports the gap rather than guessing or creating an unused directory. The installer installs the global rule and the manifest's Cline defaults once, using hash verification and a no-overwrite conflict policy. It does not copy FlowZ into project directories and does not modify Cline's native or global Skills.

After installation, the global rule is applied when the Agent handles the first task in each newly created or loaded workspace. At that point the Agent reads the workspace's existing `AGENTS.md`, `.clinerules/`, `.workflow/`, relevant code, docs, tests, and runtime evidence, then preserves and reuses them. It creates project task state only when a Standard or Full task needs persistence. Opening a folder alone is not a verified trigger; if the host does not load the user rule on the first task, use the specified fallback instruction `安装 FlowZ Cline 全局工作流，并在当前工作区启用它` to rerun the installer. The Agent should not ask the user to select Skills or copy project files.

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

## Lifecycle and routing model

Use `Quick`, `Standard`, and `Full` as the only task-depth vocabulary. The lifecycle below defines the available stages and their handoff contracts; it is not a mandatory pipeline for every task.

```text
Intake / Triage
    -> Quick / Standard / Full
    -> Problem Exploration
    -> Solution Design
    -> Design Challenge
    -> Revise Design
    -> Human Approval
    -> Writing Plan
    -> Implementation
    -> Verification / Review
```

Enter only the stages whose exit conditions are not already satisfied. At most one capability may lead a stage. Skills must not call one another or automatically start the next stage. When a stage ends, emit its structured handoff, then route again from the current evidence.

Recommended stage capabilities:

| Stage | Default capability | Enter when |
| --- | --- | --- |
| Problem Exploration | `office-hours` | The problem, user, goal, current state, or evidence is unclear. |
| Solution Design | Host-preplanned design route: on Cline use native `/deep-planning`; other hosts must use their own equivalent native design capability or apply the structured design contract manually. | The goal is understood but there is no implementable design. |
| Design Challenge | `grill-me` / `grilling` | An existing design or assumption needs counterexamples, vulnerability checks, hidden-assumption review, or evidence-gap analysis. |
| Writing Plan | Host-specific planning capability | The design is approved and must be decomposed into executable steps. |
| Implementation | Cline Act or host equivalent | The required design and approval gates are complete. |
| Verification / Review | Project checks, tests, and review | Implementation is complete or a result needs independent validation. |

Stage handoff contracts:

| Handoff | Required output |
| --- | --- |
| Problem Exploration | `Problem`, `User`, `Goal`, `Non-goals`, `Evidence` |
| Solution Design | `Options`, `Recommendation`, `Architecture`, `Data Flow`, `Risks` |
| Design Challenge | `Findings`, `Hidden Assumptions`, `Missing States`, `Required Revisions` |
| Human Approval input | `Approved Design`, `Scope`, `Acceptance Criteria` |
| Writing Plan | Ordered steps, affected files or boundaries, verification commands, and rollback or recovery notes when relevant |

Tier paths are defaults, not rigid checklists:

```text
Quick:    lightweight design -> lightweight confirmation when needed -> Implement -> Verify
Standard: Solution Design -> optional Design Challenge -> Approval when a material boundary changes
          -> Writing Plan -> Implement -> Verify
Full:     Problem Exploration -> Solution Design -> Design Challenge -> Revise Design
          -> Approval -> Writing Plan -> Implement -> Review -> Verify
```

If the user enters with a concrete proposal, use the exception route `Design Challenge -> Solution Design revision -> Approval`; skip the challenge when the proposal is already clear, low-risk, and has no material unresolved boundary.

Approval scales with risk. Quick work may proceed after a lightweight confirmation or directly when the intent and scope are clear; Standard and Full work must wait when the decision changes behavior, architecture, data, permissions, external state, or another material boundary.

## Token-efficient execution and quality guardrails

The objective is to reduce redundant context and output while preserving task
completion quality. Do not impose an arbitrary per-task token ceiling until
real usage evidence supports one.

### Compact task packet

For Standard and Full work, maintain a compact task packet at stage boundaries:

```text
Goal
Scope and non-goals
Constraints
Relevant files and evidence
Confirmed decisions
Open questions
Acceptance criteria
Verification and next step
```

Pass this packet to the next stage instead of replaying the full conversation.
Do not compress away goals, constraints, decisions, risks, acceptance criteria,
or verification state. Quick work should remain session-only unless the project
already requires persistent state.

### Efficiency rules

1. Choose the smallest applicable task tier. A clear, low-risk task should not
   enter exploratory, challenge, or formal design stages merely because they
   are available.
2. Read only relevant instructions, files, tests, and runtime evidence. Expand
   the read scope only when new evidence requires it.
3. Keep stage outputs concise and non-repetitive. Expand them when the user
   requests detail or when a material risk requires it.
4. After a failure, pass only the new evidence, failure point, eliminated
   causes, and changed next step. Never restart with the entire prior context.
5. Do not automatically chain `office-hours`, `grilling`, and `/deep-planning`.
   One stage lead is enough; route again only when the current evidence leaves
   an unmet exit condition.

### Quality fallback

If the user reports an incomplete or incorrect result, an acceptance criterion
is unmet, verification fails, or the task packet conflicts with new evidence,
stop compressing and restore the detail needed to resolve the specific gap.
Escalate from Quick to Standard or Full when the risk warrants it, and preserve
the new evidence rather than restarting the whole task.

### User-verifiable checks

For low-risk, observable outcomes, prefer giving the user an exact command or
operation path, the expected result, and what to report on failure. The Agent
still performs checks that protect correctness, security, data integrity, or a
critical regression. In ordinary development tasks, the Agent must not
calculate, display, or request hashes; hash checks remain limited to installers
or other explicitly integrity-sensitive tooling.

### Measurement without premature limits

When aggregate usage evidence becomes available, compare token use with task
completion, retries, verification failures, and user-requested rework. Change
one efficiency rule at a time and revert it if completion quality deteriorates.
Do not claim a token reduction or a completion-rate improvement without
measured evidence.

### Optional conversational AI assistance

The Agent may suggest a separate user-operated conversational AI page after the
user enables this assistance, when the current request can be completed from
the user's text or one text attachment/text file without reading the project,
running commands, modifying files, or checking runtime state. This is a
lightweight suggestion, not a new workflow stage or Skill.

Suggest it only when the input or discussion is large enough that moving the
analysis out of the current task is likely to help. The user decides whether
to use the page; the Agent supplies a short prompt and accepts either the
returned result or a decision to continue locally. If the result is returned,
use it as an unverified reference and do not repeat the same analysis through
another Skill. Do not suggest the page for implementation, project-specific
debugging, command execution, or verification work.

These suggestions are disabled by default. The Agent must not proactively
suggest them until the user explicitly asks to enable or open conversational
AI assistance. An explicit request to disable the assistance takes precedence
and remains in effect for the applicable conversation or workspace scope.

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
- Treat `.workflow/resources/skills/manifest.json` and its source directories as the package manifest and source of truth for bundled Skill assets. Do not load these files as project-runtime Skills from `.cline/skills/`.
- During Cline onboarding or when a required bundled Skill is missing, the Agent detects the host, resolves the active Cline user's actual Skills and Rules directories, and passes them explicitly to the matching installer: `install-flowz-cline.ps1` on Windows or `install-flowz-cline.sh` on Ubuntu/Linux. Manifest paths are candidates only. Reuse the native paths of a compatible fork that inherits Cline's configuration; if the target is ambiguous, stop and report rather than guessing. No per-install user confirmation is required. `%USERPROFILE%\\.agents\\skills` remains a compatibility candidate only and is never selected without host evidence. Preserve existing installations, verify hashes, report differing same-name conflicts without overwriting, and reload or refresh Cline after installation.
- Use the bundled source first. If a listed source is missing, use the manifest's recorded public source only when retrieval is authorized and safe; if retrieval fails, report the gap instead of silently substituting another Skill.
- Invoke an enabled Skill only when its trigger matches the task. If an applicable Skill is unavailable or incompatible, continue with the core workflow when possible and state the gap.
- Prefer a project-bundled Skill over a same-purpose host-native Skill only when the project explicitly defines the project Skill as the authoritative adaptation. Otherwise preserve the native Skill behavior and document any compatibility difference; do not modify Cline's built-in or global Skills as part of a project task.
- Cline's native `/deep-planning` is the Full-task engineering-design entry point. Do not automatically chain a second design Skill with it; choose one design lead for a phase.
- Use Plan and Act as host controls: the Agent may recommend the appropriate mode, but project rules cannot reliably switch modes or approve actions on the user's behalf.
- Use `@问题` or an equivalent Problems diagnostic context only as an input signal. Inspect the referenced files, reproduce or verify the issue, and do not treat the Problems view as the sole source of truth.
- Treat Cline Workflows and Hooks as version-dependent unless the current host has been verified. Do not make them mandatory for the core workflow based on screenshots or unverified host behavior.
- Apply the token-efficiency guardrails: use compact task packets, avoid repeated context, restore detail when quality signals deteriorate, prefer user-verifiable low-risk checks, and do not calculate hashes during ordinary development tasks.
- Use `/smol` or `/compact` only as a context-management action when needed or requested. It does not replace the handoff contract.
- After a handoff is recommended and the user confirms, generate the handoff prompt. The user decides whether to use Cline's `/newtask` or start another blank session.
- A Checkpoint may be created before Act mode for Standard or Full work when it helps recovery. It does not replace verification or handoff.

## Choosing capabilities

Select capabilities after triage. Do not call or install something merely because it exists.

| Capability | Use it when | Default behavior |
| --- | --- | --- |
| Project operation guide | The project has a stable operation documented in a README, runbook, script, or command. | Reuse the project source of truth; do not assume a universal operation-guide mechanism. |
| Skill | The task needs reusable judgment, analysis, review, or a domain-specific method. | Use a relevant enabled Skill when its trigger matches. Project-bundled source assets are installed into the host's user-level Skill directory during Cline onboarding or when the required bundled Skill is missing. |
| Hook | A check or action must happen at a lifecycle point and can be judged mechanically. | Keep it out of the core workflow until repeated evidence justifies automation. |

Selection rules:

1. Prefer host-native and project-owned capabilities over host-specific assumptions.
2. Reuse the project's existing operation guide, script, or command when it is the source of truth.
3. Use a Skill when judgment is the main part of the work. If the matching Skill is unavailable, use the requirements or review checklist manually.
4. Use a Hook only for deterministic enforcement, not as a substitute for thinking or review.
5. Do not assume a Skill, Rule, Workflow, or Hook from one agent can run on another agent without adaptation.
6. Keep Skill installation and host integration outside the core task loop. During Cline onboarding or when a required bundled Skill is missing, detect the host, resolve the active Cline user-level directories, and pass explicit targets to `.workflow/resources/skills/install-flowz-cline.ps1` on Windows or `.workflow/resources/skills/install-flowz-cline.sh` on Ubuntu/Linux. The selected installer installs the global rule and manifest entries into those resolved directories and verifies the result; do not place them in the project `.cline/skills/` directory by default.
7. If no available capability materially improves the task, continue without one.

Capability availability is distinct from task applicability: an enabled capability that does not match the task should remain unused, while a missing or incompatible capability is a reported gap rather than a reason to invent a substitute.

Design-entry routing is host-planned, not user-selected:

- Cline uses native `/deep-planning` for Solution Design and the Full-task design gate.
- Other hosts must use their own equivalent native design capability or apply the structured design handoff manually; this project does not bundle a fallback design Skill.
- A combined native-plus-second-design-Skill route is not enabled in the Cline adapter v0.1. A future adapter may define one only when it specifies a single stage lead, structured handoff fields, and no automatic mutual invocation.
- The Agent decides the route from the detected host and task tier; ordinary users are not asked to choose between these design mechanisms.

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
