# FlowZ Global Cline Installation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:executing-plans` to implement this plan task-by-task with review checkpoints.

**Goal:** Turn the FlowZ repository into a one-instruction Cline global-workflow installer that installs user-level Cline rules and Skills, then applies the project layer automatically on the first task in each workspace.

**Architecture:** The repository remains the distribution source and is opened once in Cline for onboarding. A global installer copies a self-contained FlowZ rule into Cline's user rules directory and selected Skill files into Cline's user Skill directory. The global rule performs idempotent first-task workspace onboarding: it reads existing project instructions and state, preserves them, and creates project task state only when the current task requires it; it does not copy the distribution repository into every project.

**Tech Stack:** PowerShell 7, JSON manifest, Markdown Cline rule and Skill files, SHA-256 verification, Cline 4.1.x user-level directories.

**Trigger boundary:** Cline does not expose a verified folder-open lifecycle
trigger. The first Agent task is the automatic onboarding path; when the host
does not load user rules automatically, the specified instruction `安装 FlowZ
Cline 全局工作流，并在当前工作区启用它` is the fallback from the FlowZ
distribution source.

**Spec:** `.workflow/tasks/task-20260904-global-cline-installation.md`

## Global Constraints

- Cline global rules target `%USERPROFILE%\\.cline\\rules` and global Skills target `%USERPROFILE%\\.cline\\skills` by default; do not use `%USERPROFILE%\\.agents` for Cline-only installation.
- The user gives one natural-language onboarding instruction; the Agent runs the installer without asking for per-Skill confirmation.
- Existing same-name global rules or Skills are never overwritten automatically; identical SHA-256 content is skipped, and differing content is reported as a conflict.
- Project-local `.clinerules`, `AGENTS.md`, `.workflow`, source code, tests, and runtime state are preserved and read before project-layer actions.
- `brainstorming` is not a project resource or Cline installation entry. Cline Solution Design uses native `/deep-planning`.
- `grill-me` remains a Codex wrapper and is not directly installable to Cline; Cline installs `grilling`.
- No Cline user directory is modified while implementing or testing this plan; tests use an isolated target directory.

---

### Task 1: Define the global Cline rule and first-task project-layer contract

**Files:**
- Create: `.workflow/resources/cline/rules/flowz-global.md`
- Create: `.workflow/tasks/task-20260904-global-cline-installation.md`

**Interfaces:**
- Consumes: Existing `.clinerules/workflows/document-workflow-v0.1.md` lifecycle, routing, Skill, and verification rules.
- Produces: A self-contained global rule that can run after the repository is no longer open and a task record with acceptance criteria.

- [ ] **Step 1: Write the global rule source**

  Include these executable rules:

  - On the first task in a new or loaded workspace, read the workspace `AGENTS.md`, `.clinerules/`, `.workflow/`, relevant code, docs, tests, and runtime evidence before changing anything.
  - Preserve existing project instructions and state. If project FlowZ state exists, use it; if it does not, apply the global contract in the current session and create `.workflow/tasks/` only when a Standard or Full task needs persistent state.
  - Route by `Quick`, `Standard`, and `Full`; use `office-hours` only for unclear problem context, `grilling` only for an existing design that needs challenge, and Cline `/deep-planning` for engineering design.
  - Use one stage lead at a time, structured handoffs, risk-scaled approval, Act for implementation, and evidence-based verification.
  - Do not require users to select Skills, copy project files, or learn internal slash commands.
  - Treat first-task onboarding as the automatic best-effort path; support the specified installation instruction as the fallback when user rules are not loaded automatically.

- [ ] **Step 2: Write the task acceptance record**

  Record the global rule target, first-task onboarding behavior, preservation rules, and verification commands. Mark local Cline installation as out of scope for this implementation.

- [ ] **Step 3: Self-review the rule**

  Check for references to deleted `brainstorming` resources, project-template instructions, per-install confirmation, and `%USERPROFILE%\\.agents` Cline targets. Remove any such claim.

### Task 2: Update the manifest for global Cline installation

**Files:**
- Modify: `.workflow/resources/skills/manifest.json`

**Interfaces:**
- Consumes: The global rule source from Task 1 and the existing five Skill entries.
- Produces: A manifest with global rule entries, Cline-only user targets, default Skill list, collision policy, and installer entry point.

- [ ] **Step 1: Add global rule metadata**

  Add a Cline rules target `%USERPROFILE%/.cline/rules`, a `globalRules` list containing `flowz-global.md`, its SHA-256, and a `projectIntegration` mode of `first-task-idempotent`.

- [ ] **Step 2: Change Skill target metadata**

  Set the preferred Cline Skill target to `%USERPROFILE%/.cline/skills`. Keep `%USERPROFILE%/.agents/skills` only as a documented non-default compatibility candidate if needed; never select it for Cline-only installation.

- [ ] **Step 3: Keep the Cline default list narrow**

  Keep `humanizer-zh`, `humanizer-en`, `office-hours`, and `grilling` as defaults. Keep `grill-me` non-installable and do not add `brainstorming` back to the manifest.

- [ ] **Step 4: Validate JSON and references**

  Parse the manifest and verify every global rule and Skill source path exists with the recorded hash.

### Task 3: Implement the one-instruction FlowZ Cline installer

**Files:**
- Create: `.workflow/resources/skills/install-flowz-cline.ps1`
- Modify: `.workflow/resources/skills/install-cline-skills.ps1`
- Modify: `.workflow/resources/skills/manifest.json`

**Interfaces:**
- Consumes: Manifest, global rule source, Skill source directories, and optional `-TargetDirectory` test override.
- Produces: A PowerShell entry point that installs global rules and Skills into Cline user directories and emits installed, skipped, and conflict results.

- [ ] **Step 1: Define installer arguments and path guards**

  Support `-ProjectRoot`, `-TargetDirectory` for isolated Skill tests, and an internal rules target override. Resolve environment variables, reject paths outside their intended roots, and never use recursive deletion or overwrite operations on user directories.

- [ ] **Step 2: Implement idempotent rule installation**

  Copy each manifest `globalRules` file to `%USERPROFILE%\\.cline\\rules`. Skip matching hashes, report differing same-name files as conflicts, and verify the destination hash after copying.

- [ ] **Step 3: Reuse or delegate Skill installation**

  Make the orchestrator install the manifest's Cline defaults using `%USERPROFILE%\\.cline\\skills` and the existing collision/hash rules. Explicitly reject `grill-me` and any removed entry.

- [ ] **Step 4: Emit onboarding guidance**

  Report the installed rule and Skill names, conflicts, and the required Cline refresh. Do not claim that the project layer was initialized before a workspace task runs.

- [ ] **Step 5: Keep the old entry point compatible**

  Update `install-cline-skills.ps1` to use the Cline-only preferred target or delegate to the new orchestrator without changing its safe collision behavior.

### Task 4: Align the active Cline documentation

**Files:**
- Modify: `.clinerules/workflows/document-workflow-v0.1.md`
- Modify: `.workflow/tasks/task-20260902-202650-cline-native-skill.md`
- Modify: `.workflow/tasks/task-20260904-025500-skill-bundle.md`

**Interfaces:**
- Consumes: Global rule and manifest behavior from Tasks 1–3.
- Produces: Consistent agent-facing instructions for one-instruction global installation and first-task project onboarding.

- [ ] **Step 1: Replace project-template wording**

  State that the FlowZ repository is an installation source, not a directory users copy into every project. Global rules and Skills are installed once; project state is read or created on demand in each workspace.

- [ ] **Step 2: Document the global installation trigger**

  Instruct the Agent to run `install-flowz-cline.ps1` when the user asks to install FlowZ or when onboarding detects missing bundled Cline capabilities. No per-Skill confirmation is required.

- [ ] **Step 3: Document first-task onboarding**

  State that the project layer runs on the first task after a workspace is created or loaded, not necessarily at the instant the workspace opens. Preserve existing project files and state.

- [ ] **Step 4: Record the Cline-only design route**

  Keep `/deep-planning` as the Cline design entry point and remove any suggestion that a bundled `brainstorming` fallback exists.

### Task 5: Verify the global installer without changing local Cline state

**Files:**
- Test: `.workflow/resources/skills/install-flowz-cline.ps1`
- Test: `.workflow/resources/skills/install-cline-skills.ps1`
- Test: `.workflow/resources/skills/manifest.json`

**Interfaces:**
- Consumes: Final installer and manifest.
- Produces: Fresh evidence for syntax, manifest integrity, isolated installation, collision handling, excluded entries, and scope.

- [ ] **Step 1: Parse scripts and JSON**

  Run PowerShell parser checks and `ConvertFrom-Json`; expected result is no parse error.

- [ ] **Step 2: Run isolated default installation**

  Use `-TargetDirectory` under a validated temporary project path. Expected result: four default Skills plus one global-rule copy when the rules target override is provided.

- [ ] **Step 3: Run isolated idempotence and conflict checks**

  Run twice to confirm matching files are skipped. Alter one isolated destination file and confirm the installer reports a conflict without overwriting it.

- [ ] **Step 4: Check excluded entries**

  Confirm `grill-me` is rejected and `brainstorming` is absent from the manifest and cannot be installed through optional selection.

- [ ] **Step 5: Review scope and evidence**

  Run `git diff --check`, inspect changed paths, verify no local Cline user directory timestamps changed, and record that the project `scripts/flowz.ps1` check remains unavailable if the file is still absent.

---

## Plan self-review

- **Coverage:** Tasks 1–5 cover global rule installation, user-level Skill installation, first-task project onboarding, Cline route selection, collision safety, and verification.
- **No placeholders:** All steps name exact files, arguments, outputs, and expected results.
- **Consistency:** The manifest, installer, active workflow, and task records all use `%USERPROFILE%\\.cline` as the Cline-only target and exclude `brainstorming`.
