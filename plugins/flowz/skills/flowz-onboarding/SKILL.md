---
name: flowz-onboarding
description: Use when the user activates FlowZ, accepts its first-task onboarding offer, retries dependency setup, or views saved installation diagnostics.
---

# FlowZ dependency onboarding

Run a complete onboarding immediately when the user says "activate FlowZ plugin"
or the equivalent Chinese command. Otherwise, wait until the Hook asks the agent
to offer onboarding on the first real FlowZ task (the first real task in the
session). Ask once. If the user agrees,
finish the dependency check and installation attempts before continuing the
original task. If the user chooses to defer, continue the task and do not ask
again in this session. A later explicit activation or retry can still run it.

`SessionStart` reports state only and never installs anything. A new chat is a
recommended stable loading boundary, not a prerequisite for onboarding.

Read
[`references/third-party-skills.json`](references/third-party-skills.json)
relative to this Skill. Check the canonical name before its compatible aliases.
Any matching installation satisfies the dependency; never overwrite an
installed version.

For a missing dependency, use the native Codex Skill Installer first. Pass the
catalog's `installPath`, which is always a Skill directory, and use
`installName` as the destination name. `sourceEntry` records the upstream page
or file for provenance and source discovery; never pass a file-valued
`sourceEntry` as the Installer's `--path`.

If the Installer attempt fails, fall back to GitHub using only the original
repository and the catalog's `installPath` directory. Use `sourceEntry` only to
locate or verify the upstream entry. If that entry moved, search only inside
that same author and repository, identify the directory containing the upstream
`SKILL.md`, and retry with that directory. Never switch automatically to a
fork, a same-name substitute, or an unrecorded source.

The catalog defines exactly four optional dependencies: `humanizer-zh`,
`humanizer` (compatible alias `humanizer-en`), `grilling`, and
`gstack-openclaw-office-hours` (compatible alias `office-hours`). Keep
`humanizer` and `humanizer-zh` separate and never use one for the other. Do not
install Skills outside the catalog.

Superpowers is not part of the four catalog dependencies. It is a separate,
optional workflow plugin. Never install, enable, or diagnose Superpowers as
part of this onboarding.

A failed dependency produces a concise diagnostic containing the failure
point, new evidence, degraded capability, and next step. It does not block
core FlowZ routing or the original task; it must not block
`flowz-workflow`.
It must never report a successful install without
evidence. Do not retry installation on later turns. Retry installation only
when the user explicitly asks to retry. When the user asks to view diagnostics,
display only the diagnostics supplied by the FlowZ hook; do not run checks or
retry an installation.

After the check, record each catalog dependency in `available_dependencies`
using only its canonical `name`, the installed canonical name or compatible
alias in `satisfied_by`, `checked` or `degraded` status, and an optional short
diagnostic. Append exactly one FlowZ state marker to the final response so
the `Stop` hook can save the result. Use `checked` only when every dependency
is already available or was installed with evidence:

```text
<!-- flowz-state: {"marker_nonce":"COPY_CURRENT_NONCE","onboarding_status":"checked","available_dependencies":[{"name":"humanizer-zh","satisfied_by":"humanizer-zh","status":"checked"},{"name":"humanizer","satisfied_by":"humanizer-en","status":"checked"},{"name":"grilling","satisfied_by":"grilling","status":"checked"},{"name":"gstack-openclaw-office-hours","satisfied_by":"office-hours","status":"checked"}],"onboarding_diagnostics":[]} -->
```

Replace `COPY_CURRENT_NONCE` with the current `marker_nonce` supplied by the
FlowZ hook. A missing or stale nonce makes the Hook ignore the marker.

Use `degraded` when any dependency remains unavailable and include only short,
reviewable diagnostics. Never put the original prompt, credentials, hidden
reasoning, or full command output in the marker.

Use one marker for the entire response. If task state also changed, merge the
onboarding and task fields into that marker. Put it unindented at the absolute
end of the response, outside Markdown fences, with no text after it.

Do not copy, rename, or modify third-party Skills. Do not write to project
rules, `AGENTS.md`, or `config.toml`.
