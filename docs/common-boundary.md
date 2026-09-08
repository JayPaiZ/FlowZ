# FlowZ Common Branch Boundary

This document is the contributor-facing rule for maintaining `main` as the
shared FlowZ baseline for Codex and Cline. It complements the host-specific
implementation documents; it does not replace them.

## What belongs in `main`

Put a change in the common boundary only when both platforms need the same
stable, externally observable behavior. The common boundary may define:

- the Quick / Standard / Full task tiers;
- lifecycle stage names and the single-stage-lead rule;
- compact context-package fields and failure updates that carry new evidence;
- risk, approval, verification, completion-summary, and handoff semantics;
- conflict precedence and preservation of higher-priority user instructions;
- canonical optional-capability IDs, aliases, purposes, and source metadata; and
- privacy requirements such as not persisting full prompts, responses, hidden
  reasoning, credentials, private logs, or unrelated runtime data.

The common files must remain host-neutral. They must not contain a host event
name, platform command, installation path, UI assumption, or a second copy of a
platform runtime state machine.

## What stays on a platform branch

Classify work before implementation as one of these four categories:

1. **common contract** — stable behavior required by both platforms;
2. **Codex-only** — Codex plugin, Hook, Skill, marketplace, or session protocol;
3. **Cline-only** — Cline rules, Plan/Act behavior, installer, or user-global
   resource layout; or
4. **experimental** — a platform trial that has not yet proved a shared need.

Codex-only and Cline-only behavior stays on its own branch. In particular,
host events, host commands, host paths, UI wording, installers, and vendored
Skill payloads do not enter the common contract merely because both platforms
offer a superficially similar feature.

## Promotion and extraction rules

New behavior is presumed platform-specific. Promote it to `main` only after:

- both platforms require the same observable outcome;
- the behavior and field meanings are stable enough to version; and
- a platform-neutral conformance case can describe it without host details.

Small duplicated host glue is intentional. Consider extracting shared runtime
code only when one of these signals is present:

- the same logic is manually synchronized in two consecutive changes;
- the same defect is fixed independently in both branches; or
- one common field or state transition is maintained in three or more locations.

An extraction signal starts a new design decision. It does not authorize a
speculative abstraction or create a third implementation of the workflow.

## Synchronization flow

The normal direction is:

```text
main -> FlowZ-Codex
main -> FlowZ-Cline
```

For a cross-platform feature:

1. Define or update the common contract on `main`.
2. Keep common and platform commits separate: one commit for the common
   contract/tests, followed by one or more platform-specific implementation
   commits.
3. Apply the common commit to both platform branches before starting dependent
   work.
4. Run the native adapter tests on each branch and record intentional
   differences in that branch's adapter documentation or tests.
5. Keep platform-specific commits on their own branch unless a later promotion
   decision changes their classification.

Platform-specific commits remain on their branch.

The platform branches consume common semantics; they do not silently redefine
them. A platform may degrade when its host lacks a capability, but it must
preserve the common outcome or report the precise gap.

## Pre-merge checklist

- [ ] The change is classified as common contract, Codex-only, Cline-only, or
      experimental.
- [ ] Common files contain no host command, event name, path, UI term, or
      installer detail.
- [ ] Common and platform commits stay separate.
- [ ] The common contract has a platform-neutral conformance test or vector.
- [ ] Both platform branches have a recorded adaptation and native test plan.
- [ ] Any intentional difference is documented rather than hidden in an
      exception.
- [ ] No plan files, credentials, private logs, or unrelated runtime data are
      added to the repository.
