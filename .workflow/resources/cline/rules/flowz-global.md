# FlowZ global workflow for Cline

This is a user-level Cline rule installed by the FlowZ onboarding installer. It
is the runtime contract for any workspace after installation. The FlowZ
repository is an installation source; do not copy it into each project and do
not treat this rule as permission to overwrite a project's own instructions.

## First task in a workspace

When a workspace is newly created or loaded, apply this rule when handling the
first user task in that workspace:

1. Read the applicable `AGENTS.md` files, `.clinerules/` files, and any
   existing `.workflow/` task or plan state. Read the relevant source, docs,
   tests, and runtime evidence before changing anything.
2. Preserve existing instructions, project state, source files, and tests. If
   the project already has a workflow or task record, use it rather than
   replacing it. Do not create project files merely because FlowZ is installed.
3. If no project workflow exists, apply the routing and verification contract
   below in the current session. Create `.workflow/tasks/` only when a
   Standard or Full task needs persistent state; a Quick task may remain
   session-only.

First-task detection is intentionally idempotent. Prefer the current Cline
session's onboarding state or an existing project task record when available.
If no reliable marker exists, perform the read-only onboarding check again
rather than creating a marker solely for a Quick task; never overwrite an
existing project record just to mark onboarding complete.

The rule is triggered by the first task, not by opening a folder alone. If the
host does not apply user rules automatically, the supported fallback is for the
user to issue one instruction such as: `安装 FlowZ Cline 全局工作流，并在当前工作区启用它`.
Before installing, detect the host operating system and resolve the active
Cline user's actual Skills and Rules directories. On Windows run
`.workflow/resources/skills/install-flowz-cline.ps1`; on Ubuntu or another Linux
host run `.workflow/resources/skills/install-flowz-cline.sh`. Pass the resolved
directories explicitly with the installer's target arguments. The manifest's
Windows and Ubuntu paths are hints, not guaranteed locations. Read the active
Cline or compatible fork's documentation/configuration and reuse its native
paths when the fork inherits them. If the host or target directories cannot be
identified, or more than one plausible target exists, report the gap instead of
guessing or creating an unused directory.
Do not ask for separate confirmation for each bundled Skill. Do not claim that
project onboarding happened before a workspace task actually runs.

## Task routing

Use only `Quick`, `Standard`, and `Full` as task-depth labels.

- **Quick**: understand the intent quickly, make a small low-risk change, and
  verify it directly.
- **Standard**: investigate and make a short plan; use a design challenge only
  when an existing proposal or assumption needs counterexamples or evidence
  checks. Wait for approval only when a material boundary changes.
- **Full**: establish the problem and constraints, produce an implementable
  design, challenge it, revise it, obtain approval, plan the implementation,
  then implement and verify.

Choose the smallest route whose exit conditions are not already satisfied. At
most one capability leads a stage; Skills do not call one another or start the
next stage automatically.

### Capability triggers

- Use `office-hours` only when the problem, user, goal, current state, or
  evidence is unclear.
- Use `grilling` only when an existing design, plan, or assumption needs
  counterexamples, vulnerability checks, hidden-assumption review, or evidence
  gap analysis.
- For engineering design on Cline, use the native `/deep-planning` route. Do
  not chain a second design Skill automatically.
- Use Cline Plan for investigation and a reviewable plan, and Act for approved
  implementation. The Agent may recommend the mode, but cannot switch or
  approve it on the user's behalf.

Do not force `office-hours`, `grilling`, and `/deep-planning` into a serial
pipeline. Route again from the current evidence after each stage. Pass a
structured handoff (`Problem`, `Goal`, `Evidence`; `Options`, `Recommendation`,
`Risks`; or `Findings`, `Required Revisions`) instead of replaying the whole
conversation.

## Token-efficient execution and quality guardrails

Reduce redundant context and output without weakening task completion quality.
Do not impose an arbitrary per-task token ceiling without real usage evidence.

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

Pass the packet forward instead of replaying the full conversation. Never
compress away goals, constraints, decisions, risks, acceptance criteria, or
verification state. Read only relevant files and expand the scope when new
evidence requires it. Keep normal outputs concise and non-repetitive.

After a failure, carry only the new evidence, failure point, eliminated causes,
and changed next step. Do not restart with the complete prior context. If the
user reports an incomplete or incorrect result, an acceptance criterion is
unmet, verification fails, or new evidence conflicts with the task packet,
stop compressing and restore the detail needed for that specific gap. Escalate
the task tier when risk warrants it.

For low-risk, observable outcomes, give the user an exact verification command
or operation path, expected result, and failure-report instruction. Keep
correctness, security, data-integrity, and critical-regression checks with the
Agent. During ordinary development tasks, do not calculate, display, or request
hashes; hash checks belong only to installers or explicitly integrity-sensitive
tooling.

## Optional external chat assistance

When a request can be completed from the user's text or one text attachment or
text file, without reading the project, running commands, modifying files, or
checking runtime state, you may suggest that the user use a separate chat page
for the analysis. This is only a lightweight suggestion, not a workflow stage
or Skill.

Suggest it only when the input or discussion is large enough for moving the
analysis out of the current task to be useful. Give the user a short prompt and
let them choose. If they bring back a result, treat it as an unverified
reference and do not repeat the same analysis through another Skill. Do not
suggest it for implementation, project-specific debugging, command execution,
or verification.

These suggestions are enabled by default. An explicit user request to enable
or disable them takes precedence for the applicable conversation or workspace
scope.

## Scope and verification

Reuse project README files, runbooks, scripts, and commands as the source of
truth. Keep changes within the approved scope, preserve unrelated user edits,
and never read or expose secrets without a task-specific need and authorization.
Verify with the narrowest useful tests, static checks, build checks, runtime
checks, or review evidence. Report checks that were not run and any remaining
risk; do not describe an unrun check as passed.

Use `@` Problems or other diagnostic context as an input signal only. Inspect
the referenced files and reproduce or verify the issue independently.

## Project-layer boundary

This global rule supplies the workflow when a project has no equivalent local
contract. It does not copy FlowZ files into the project, overwrite
`.clinerules/`, `AGENTS.md`, `.workflow/`, or modify Cline's native/global
Skills. Project-specific rules remain authoritative when they are applicable;
record any compatibility difference instead of silently replacing them.
