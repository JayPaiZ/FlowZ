# FlowZ Bounded Common Boundary Design

**Status:** Implemented on `main` in commits `8c788fc`, `3401080`, `06d916e`, and `b1d30ea`

**Date:** 2026-09-08

## Goal

Keep `main` as the source of truth for stable Codex/Cline workflow semantics
without turning it into a third platform implementation or allowing the cost
of maintaining the two platform branches to grow without a control point.

## Context and evidence

The current repository has two materially different platform trees. `main`
contains the Codex plugin, Hook state machine, Codex Skills, and Codex tests;
`FlowZ-Cline` contains Cline rules, Plan/Act guidance, Windows and Ubuntu
installers, and bundled Skill sources. The two branches share concepts but no
runtime files. Their common ancestor is `657f3e1`; a direct merge would not
create useful code sharing and could reintroduce retired platform files or
conflicting README/package contracts.

The common concepts that are stable enough to govern both platforms are:

- Quick / Standard / Full task-depth semantics;
- lifecycle stages and the single-stage-lead rule;
- compact context packets and incremental failure evidence;
- risk-based approval boundaries and low-impact continuity;
- conflict precedence and preservation of user instructions;
- verification evidence and completion-summary fields;
- optional capability and dependency naming/alias semantics; and
- context-health and handoff principles.

Host event protocols, installation paths, native Plan/Act controls, and
platform UI remain platform-specific.

## Chosen architecture

`main` is a **common contract and integration baseline**, not a third adapter
implementation. It owns a small, host-neutral contract and conformance tests.
The two long-lived platform branches own their host-facing implementations and
consume the common changes by ordinary merge or cherry-pick.

```text
main (stable common contract + conformance tests)
├── FlowZ-Codex (Codex Hook, plugin manifest, Codex Skills)
└── FlowZ-Cline (Cline rules, installers, Cline Skill bundle)
```

No mandatory `adapters/` abstraction layer is introduced in this phase. The
existing host entry points remain intact so a structural migration does not
become a prerequisite for every future feature.

### Common boundary

The common boundary contains only artifacts that can be stated without a
Codex- or Cline-specific command, event name, path, or UI assumption:

- a versioned workflow contract with tier, lifecycle, risk, approval,
  verification, completion, and handoff fields;
- one canonical third-party dependency catalog with aliases and purposes;
- platform-neutral test vectors for the contract; and
- a short boundary/synchronization policy for contributors.

The common boundary does **not** contain:

- Codex `hook_event_name`, `PLUGIN_DATA`, nonce handling, or plugin manifest;
- Cline Plan/Act, `/deep-planning`, global-rule paths, or installer commands;
- vendored third-party Skill payloads;
- host-specific README installation instructions; or
- a second copy of either platform's runtime state machine.

### Promotion rule

New behavior is presumed platform-specific. It enters the common boundary
only when both platforms need the same externally observable semantics and the
semantics are stable enough to version. Experimental behavior remains in the
owning platform branch until that condition is met.

### Extraction trigger

This design deliberately accepts small duplicated host glue. Extract a shared
runtime module only when at least one of these signals is observed:

1. the same logic is manually synchronized in two consecutive feature changes;
2. the same defect is fixed independently in both branches; or
3. a common field or state transition must be maintained in three or more
   locations.

The trigger creates a new design decision; it does not authorize speculative
abstraction in advance.

## Change and synchronization flow

1. Start every cross-platform feature in `main` with a short classification:
   common contract, Codex-only, Cline-only, or experimental.
2. Keep common-contract edits in a separate commit from platform edits.
3. Before starting a dependent feature, apply the common commit to both
   platform branches and run each branch's adapter tests.
4. Platform-specific commits stay on their platform branch unless a later
   decision promotes their behavior to the common boundary.
5. Record intentional platform differences in the relevant adapter document or
   test; do not encode them as silent exceptions in the common contract.

The normal direction is `main -> FlowZ-Codex` and `main -> FlowZ-Cline`.
Platform branches do not become sources of common semantics merely because a
platform implementation was completed first.

## Data flow

```text
common contract + catalog
          │
          ├── Codex branch: map contract to Hook/Skill/session behavior
          │
          └── Cline branch: map contract to rule/installer/Skill behavior
```

The contract is normative for names, defaults, and observable outcomes. Each
adapter is free to choose its host-native mechanism and wording as long as its
conformance tests preserve those outcomes.

## Error handling and compatibility

- A platform may degrade when its host lacks a native capability, but it must
  preserve the common semantic outcome or report the specific gap.
- A common contract change is versioned when it changes a field meaning,
  default, required state, or acceptance condition.
- Unknown common fields are ignored by an older adapter when safe; removal or
  semantic narrowing requires an explicit compatibility note and adapter
  updates.
- A dependency source or alias is never silently renamed on only one branch.

## Testing strategy

The first implementation slice adds:

- a machine-readable common contract and canonical catalog;
- core tests for tier names, lifecycle fields, approval/risk semantics,
  completion summary fields, and dependency aliases;
- conformance checks that each platform branch can run against the same test
  vectors when it incorporates the common commit; and
- a lightweight synchronization/boundary check that rejects platform commands,
  paths, or host event names from the common contract.

Existing Codex tests remain the authority for Codex Hook/plugin behavior.
Cline installer and rule tests remain platform-specific and are added or
updated on `FlowZ-Cline` when its adapter consumes the common contract. No
real host installation, external Skill installation, or deployment is part of
this design.

## Non-goals

- merging the complete Cline tree into the Codex plugin;
- making the two platforms use identical prose or identical event handling;
- introducing a permissions system, model router, or new workflow engine;
- vendoring more third-party repositories into the common branch; and
- guaranteeing zero adaptation work for future platform-specific features.

## Success criteria

The approach is successful when:

1. a contributor can decide whether a change belongs in `main` without reading
   both platform implementations;
2. a common semantic change has one normative definition and one conformance
   test set;
3. platform branches can adapt independently without silently changing common
   meanings; and
4. the repository has a visible trigger for when duplicated logic has become
   expensive enough to extract.
