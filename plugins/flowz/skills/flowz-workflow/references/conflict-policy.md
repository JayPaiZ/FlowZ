# Conflict Policy

## Precedence

Inspect applicable `AGENTS.md`, existing Skills, plugins, and workflows before
using FlowZ guidance. User instructions and those established project sources
take priority over this skill. Superpowers is considered only when visibly
loaded and active; it is not a dependency. An active Superpowers Skill takes
lifecycle priority for matching design, TDD, debugging, review, or delivery
work, so FlowZ skips the overlapping process and retains only non-conflicting
context and safety rules.

## Handling a conflict

If a FlowZ action conflicts with a higher-priority source, skip that action,
report once (the conflict and source) in the current task, and do not modify the source.
Continue with non-conflicting work when safe. Do not overwrite, rename, copy,
or silently reinterpret an existing Skill, plugin, workflow, or `AGENTS.md`.

The report should name the conflicting source, the skipped FlowZ action, and
the safe consequence. Do not repeat the same conflict report after compression
or during later steps of the same task.

For runtime de-duplication, derive the conflict ID as
`<source-locator>:<rule-slug>`: use the shortest stable source locator available
(for example `agents.md` or `skill:office-hours`) and a lowercase,
hyphen-separated slug for the conflicting rule or skipped FlowZ action. Omit
volatile line numbers, message wording, and step numbers. Reuse the same ID for
the same source/action pair throughout the task. Before reporting, compare the
derived ID case-insensitively with `already reported conflicts`; if present,
skip only the duplicate report, not the safe consequence.
