# Conflict Policy

## Precedence

Inspect applicable `AGENTS.md`, existing Skills, plugins, and workflows before
using FlowZ guidance. User instructions and those established project sources
take priority over this skill. Superpowers is considered only when visibly
loaded and active; it is not a dependency.

## Handling a conflict

If a FlowZ action conflicts with a higher-priority source, skip that action,
report once (the conflict and source) in the current task, and do not modify the source.
Continue with non-conflicting work when safe. Do not overwrite, rename, copy,
or silently reinterpret an existing Skill, plugin, workflow, or `AGENTS.md`.

The report should name the conflicting source, the skipped FlowZ action, and
the safe consequence. Do not repeat the same conflict report after compression
or during later steps of the same task.
