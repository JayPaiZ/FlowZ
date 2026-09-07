# Superpowers Integration

Superpowers is an optional workflow integration, never a required FlowZ
dependency. FlowZ distinguishes installation, loading, and activation:
installation only places a plugin on disk, loading makes its Skills visible to
the host, and activation means a Skill is loaded and active for the current
task. Only that last state is usable. FlowZ does not infer it from files or a
past session, install or enable Superpowers, or promise hot loading.

## Arbitration

- When Superpowers is not visible, FlowZ keeps routing the task itself. For a
  Standard or Full task with a clear benefit, make one optional recommendation
  when not loaded and continue the task. A Quick task stays Quick.
- When Superpowers is loaded and active, it owns that part of the lifecycle.
  FlowZ does not start a second workflow for design, TDD, debugging, review,
  or delivery. Keep only non-conflicting task context, conflict protection,
  and the validation floor.
- An explicit invocation of a Superpowers Skill means following all of that
  Skill's entry conditions, required steps, and completion gates. FlowZ must
  not shorten or bypass it.

Use stable recommendation IDs:

| Situation | Optional Skill |
| --- | --- |
| New feature, architecture, or unclear requirements | `superpowers:brainstorming` |
| Bug, failing test, or unexpected behavior | `superpowers:systematic-debugging` |
| Feature, fix, or refactor | `superpowers:test-driven-development` |
| Before a completion, commit, or release claim | `superpowers:verification-before-completion` |

Recommend `superpowers:dispatching-parallel-agents` or
`superpowers:subagent-driven-development` only when multiple genuinely
independent tasks justify parallel work. A Skill is a host-loaded instruction,
not a FlowZ programmable function; FlowZ can recommend an ID but cannot call
the Skill as an internal API.

The Hook stores at most eight valid `superpowers:<slug>` IDs for the current
task. It appends and de-duplicates marker updates, restores the IDs after
compaction, and clears them when the next real task begins. Never store the
prompt, response, installation output, credentials, or private logs.
