---
name: flowz-onboarding
description: Use when FlowZ is first used in a Codex session and its optional third-party Skills need availability checks or installation diagnostics.
---

# FlowZ dependency onboarding

On the first real task after the plugin is enabled, read
`references/third-party-skills.json` from the plugin and check each optional
dependency once. Check the canonical name before its compatible aliases. Any
matching installation satisfies the dependency; never overwrite an installed
version.

Install a missing dependency with the native Codex Skill Installer first. If
that fails, fall back to GitHub using only the original repository and path in
the catalog. If the recorded path moved, search only inside that same author
and repository. Never switch automatically to a fork, a same-name substitute,
or an unrecorded source.

The catalog defines exactly four optional dependencies: `humanizer-zh`,
`humanizer` (compatible alias `humanizer-en`), `grilling`, and
`gstack-openclaw-office-hours` (compatible alias `office-hours`). Keep
`humanizer` and `humanizer-zh` separate and never use one for the other. Do not
install Skills outside the catalog.

A failed dependency produces a concise diagnostic containing the failure
point, new evidence, degraded capability, and next step. It must not block
`flowz-workflow`, and it must never report a successful install without
evidence. Do not retry installation on every turn and do not proactively check
for third-party updates. Retry installation only when the user explicitly asks
to retry. Show saved installation diagnostics without retrying when the user
asks to view diagnostics.

Do not copy, rename, or modify third-party Skills. Do not write to project
rules, `AGENTS.md`, or `config.toml`.
