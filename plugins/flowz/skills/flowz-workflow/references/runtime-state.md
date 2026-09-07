# Runtime state

The Hook persists deterministic session controls itself. FlowZ supplies only
compact, reviewable workflow decisions through a marker in the last assistant
message; the `Stop hook` reads that marker without saving the surrounding
message.

## Recovery order

On a new turn or after compaction, the agent first uses the saved context
package (`goal`, `scope_and_non_goals`, `confirmed_decisions`,
`acceptance_criteria`, `validation`, and `approval_boundary`). It then checks
the relevant actual files and tests for fresh evidence and continues the next
unfinished action. Do not repeat completed work or ask the user to restate a
field already present. Ask only for a minimal missing field or stale evidence;
a missing marker never creates an approved boundary.

Append one single-line marker after the user-facing response whenever one of
these values changes:

- `marker_nonce`: copy the current 32-character nonce supplied by the Hook
  context exactly; it authenticates this turn's marker and is rotated after use;
- `task_depth`: `Quick`, `Standard`, or `Full`;
- `plan_phase`: `routing`, `planning`, `awaiting_approval`, `approved`,
  `executing`, `validating`, `complete`, or `blocked`;
- `context_package`: a compact object containing only relevant fields from
  `goal`, `scope_and_non_goals`, `constraints`, `evidence`,
  `confirmed_decisions`, `options_and_tradeoffs`, `acceptance_criteria`,
  `validation`, `approval_boundary`, and `pause_conditions`;
- `reported_conflict_ids`: short stable identifiers for conflicts already
  reported in this task, derived as `<source-locator>:<rule-slug>` according to
  `conflict-policy.md`;
- `recommended_optional_workflows`: newly recommended, stable
  IDs from the integration reference (for example
  `superpowers:brainstorming` or `superpowers:systematic-debugging`). The Hook
  rejects unknown slugs, appends valid IDs, ignores an empty list, restores
  them after compaction, and clears them for the next real task;
- `onboarding_status`: `pending`, `prompted`, `deferred`, `requested`, `checked`,
  or `degraded`; state moves forward from `pending`/`prompted` to a requested or completed
  result; a stale marker cannot downgrade `checked` or `degraded` to a prompt;
- `onboarding_prompted` and `onboarding_activation_requested`: Hook-controlled
  flags for the one-time offer and explicit activation; markers cannot set them
  directly;
- `available_dependencies`: at most the four catalog dependencies, with a
  canonical name, checked/degraded status, compatible-alias result, and an
  optional bounded diagnostic;
- `response_detail`: optional `concise`, `normal`, or `detailed` session
  preference;
- `plan_summary`: optional `hidden` or `brief` session preference. These
  preferences are ignorable and cannot change permissions, model settings,
  validation ownership, or project rules;
- `onboarding_diagnostics`: short saved diagnostics when relevant.

Use valid JSON and include only fields that changed. For example:

```text
<!-- flowz-state: {"marker_nonce":"COPY_CURRENT_NONCE","task_depth":"Standard","plan_phase":"approved","context_package":{"goal":"Add local plugin validation","approval_boundary":"Edit and test the plugin without installing it"}} -->
```

Replace `COPY_CURRENT_NONCE` with the exact nonce in the current Hook context.
Never reuse a nonce from an earlier response. A missing, stale, or mismatched
nonce causes the entire marker to be ignored.

Set `plan_phase` to `complete` after the requested task and its required
validation are complete. The next real user task then gets a fresh task state.
Do not emit a marker merely to restate unchanged values.
If onboarding and workflow state both change in the same response, combine all
changed fields into this one marker.

Each `context_package` value must be a short string or a small list/map that
can be flattened into a reviewable string. Use `{}` to clear the whole context
package and an empty value to remove one stale field. Append only newly
reported conflict or optional-workflow IDs; omit either field when there are
none. The Hook preserves both histories for the current task and clears them
only when the next real task starts. Put the single-line marker block unindented at the
absolute end of the answer, outside Markdown fences, with no text after it.
Text that merely quotes or demonstrates a marker is not runtime state.

Every value must be a concise summary the user could review. Never include the
original user prompt, full assistant response, hidden chain-of-thought,
credentials, environment values, raw logs, or unrelated project content. A
marker cannot change FlowZ's switches or schema version; those are controlled
by the Hook's explicit user commands. The Hook also rejects obvious
secret-shaped values, but this is defense in depth rather than permission to
place sensitive content in a marker.
