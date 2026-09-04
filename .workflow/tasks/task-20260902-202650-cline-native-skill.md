---
id: task-20260902-202650-cline-native-skill
title: 评估 Cline 原生能力与项目文档的冲突处理
status: completed
verification: passed
created_at: 2026-09-02T20:26:50+08:00
updated_at: 2026-09-04T11:27:53+08:00
spec: none
---

# Goal

在整理随文档分发的 Skill 时，检查 Cline 原生能力与项目执行文档之间是否存在冲突，并确定冲突的处理方式。

## Scope

### In scope

- 盘点与候选内置 Skill 相关的 Cline 原生能力、触发条件和行为边界。
- 识别原生能力与项目执行文档、路由规则或分发约定之间的冲突。
- 为每项冲突确定处理策略：兼容现有行为、调整项目文档约定，或在文档中明确记录需要修改原生 Skill。
- 明确冲突处理后的验证方式和兼容性限制。

### Out of scope

- 下载、安装或修改任何 Skill；这些属于后续 Skill 分发与 Cline 集成任务。
- 直接修改 Cline 原生 Skill。
- 开始编写面向开发者的说明文档。

## Acceptance criteria

- [x] 候选内置 Skill 的原生能力依赖和行为边界有清单。
- [x] 已识别的冲突均有证据、影响范围和处理决定。
- [x] 未授权修改 Cline 原生 Skill；项目文档记录了保持原生行为或使用项目级适配的策略。
- [x] 处理方案不把 Cline 专属行为未经说明地当成跨宿主保证。

## Verification

- [x] 完成原生能力与项目文档的逐项对照检查，并记录未能验证的宿主行为。
- [x] 针对性结构检查通过：项目级 Skill 分发、原生 Skill 不修改、Plan/Act 边界、`/deep-planning`、`@问题` 独立验证、候选 Skill 分工和任务完成状态均已核对。
- [x] `git diff --check` 通过，且变更范围仅为本任务记录和 Cline 执行文档。
- [ ] 项目级 `scripts/flowz.ps1 -Command check` 未执行：该脚本在重基线后已不位于当前仓库，无法以当前路径运行。

## Knowledge feedback

- [x] 将长期有效的兼容性规则写入 Cline 执行文档；具体内置 Skill 清单和文件仍留待后续设计任务。

## Native capability inventory and decisions

| Cline capability | Observed boundary | Project decision | Evidence or limitation |
| --- | --- | --- | --- |
| Project Rules (`.clinerules/`) | Workspace rules are merged and can be scoped by path. | Keep project routing and execution rules here. | Cline documentation review; exact precedence can vary by host version. |
| Project Skill source assets (`.workflow/resources/skills/`) | Cline can load project Skills from `.cline/skills/`, while its global scanner also checks user-level Skill directories. | Keep bundled source assets outside project runtime paths. During onboarding or when a required Skill is missing, the Agent automatically installs selected entries into the user's supported global directory; do not globally modify native Skills. | Cline 4.1.x extension inspection: global scan includes `%USERPROFILE%\\.agents\\skills` and `%USERPROFILE%\\.cline\\skills`; exact behavior remains host/version dependent. |
| Plan / Act | Plan is for inspection and planning; Act performs changes and commands. | Agent recommends a mode; user/host controls the actual switch. | Cline documentation review; project rules cannot reliably switch modes. |
| `/deep-planning` | Native engineering-planning entry point for a reviewable design. | Use as the Cline mapping of the Full-task design gate; do not automatically chain a separate `brainstorming` Skill. | Cline documentation review. |
| `@` context and Problems (`@问题`) | Can provide workspace or diagnostic context; public docs do not fully establish the screenshot's exact Problems entry. | Use as an input signal, then inspect and verify independently. | Screenshot and public-documentation limitation. |
| Workflows | Visible in the host UI, but storage and trigger semantics were not verified. | Keep optional and version-dependent until a real Cline task confirms the contract. | Not verified in the current environment. |
| Hooks | Public material reviewed here points mainly to SDK/plugin integration. | Keep outside the core workflow until a deterministic project need and host implementation are verified. | Not verified as a stable project-level contract. |

## Conflict handling rule

Follow-up integration decision (2026-09-04): the FlowZ Agent-managed installer
uses `%USERPROFILE%\\.cline\\skills` and `%USERPROFILE%\\.cline\\rules` as its
preferred Cline-only targets. `%USERPROFILE%\\.agents\\skills` remains a host
compatibility candidate only. Installation is idempotent and hash-verified;
same-name differences are reported without overwrite. The global rule applies
on the first task in each workspace, with a specified installation instruction
as the fallback when the host does not load user rules automatically.

Project-bundled Skill source assets are an explicit project adaptation layer, not a replacement for Cline's global or built-in Skills. Keep the source assets outside project runtime Skill paths, and install selected assets into the user's supported Cline Skill directory during onboarding or when a required bundled Skill is missing; this is a project-defined Agent behavior and does not require per-install user confirmation. When a project Skill overlaps a native Skill, preserve the native behavior unless the project explicitly declares the project Skill authoritative for that task. Record the difference and test the host integration; do not edit Cline's built-in installation to resolve a project-local conflict.

## Candidate Skill boundaries

| Candidate | Host dependency or overlap | Project decision |
| --- | --- | --- |
| `humanizer-zh` / `humanizer-en` | No required Cline-native dependency; the main risk is language overlap between the two Skills. | Keep separate language routes. One passage is handled by one language Skill only; do not run both on the same passage. |
| `grilling` / `grill-me` | The current `grill-me` source is a Codex wrapper that calls a `Skill tool` and delegates to `grilling`; Cline does not provide that wrapper contract. | Bundle both sources for provenance, install `grilling` to Cline by default, and keep `grill-me` out of the Cline install list until a Cline-specific adapter is reviewed. Treat finding vulnerabilities, counterexamples, or evidence gaps as an explicit trigger. Do not automatically chain it with `office-hours` or engineering design. |
| `office-hours` | No required Cline-native dependency; its diagnostic questioning can overlap with general planning. | Use only when the problem, user, goal, or current situation is unclear. Pass a structured problem statement onward instead of the whole transcript. |
| `session-handoff` | It is a user-local Skill and depends on personal session conventions, not on the project. | Keep it outside the project's built-in Skill set. The project workflow documents the handoff contract without requiring this Skill. |
| Superpowers plugin collection | A plugin is not a portable Cline project dependency, and the full collection may duplicate native or project capabilities. | Do not require or bundle the plugin. The project uses host-native design planning and keeps only the selected non-Superpowers Skill resources. |

## Upstream verification

- `grill-me` upstream file: https://github.com/mattpocock/skills/blob/main/skills/productivity/grill-me/SKILL.md
- Fetched upstream content is the same wrapper as the copied source: `Call the Skill tool with "grilling".`
- `grilling` upstream file: https://github.com/mattpocock/skills/blob/main/skills/productivity/grilling/SKILL.md
- Therefore `grill-me` is a user-facing entry point only where the host exposes a compatible Skill-calling tool; `grilling` is the self-contained interview logic used by the Cline default route.

## Transition history

- 2026-09-02T20:26:50+08:00: created in planning.
- 2026-09-04T00:00:00+08:00: Cline native capability review completed; project-bundled Skill source assets approved outside project runtime paths for later Agent-managed Cline integration, with native/global Skill modification excluded.
