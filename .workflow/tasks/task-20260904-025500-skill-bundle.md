---
id: task-20260904-025500-skill-bundle
title: 建立内置 Skill 预置资源与 Cline 用户级安装清单
status: completed
verification: passed
created_at: 2026-09-04T02:55:00+08:00
updated_at: 2026-09-04T11:35:00+08:00
spec: none
---

# Goal

将当前 Codex 已安装或缓存的候选 Skill 复制为项目预置资源，并为后续 Agent 自动安装到 Cline 用户级 Skill 目录建立清单。

## Scope

### In scope

- 从当前 Codex Skill 安装位置复制 `humanizer-zh`、`humanizer-en`、`office-hours`、`grilling`、`grill-me` 和 Superpowers `brainstorming` 源包。
- 创建机器可读清单，记录来源、资源路径、入口文件、哈希、依赖和 Cline 默认安装标记。
- 创建 Agent 可执行的 PowerShell 安装器，读取清单并执行用户级安装。
- 明确资源目录不属于当前项目的运行时 Skill 搜索路径。
- 明确 Cline 集成由 Agent 自动在用户级目录执行，优先使用 `%USERPROFILE%/.cline/skills`，不在本机执行该安装；`.agents/skills` 仅作为兼容候选。

### Out of scope

- 本机 Cline 用户目录安装或修改。
- 修改 Cline 原生或全局 Skill 内容。
- 将 `brainstorming` 作为 Cline 默认 Skill 安装。
- 将 `session-handoff` 纳入项目资源。

## Acceptance criteria

- [x] 候选源包已复制到 `.workflow/resources/skills/sources/`。
- [x] 清单记录每个资源的入口、哈希、依赖和 Cline 默认安装状态。
- [x] Cline 安装规则允许 Agent 在需要时自动执行且无需逐次用户确认，但禁止覆盖同名现有 Skill。
- [x] `grill-me` 的 Codex-only wrapper 限制已记录，Cline 默认安装使用 `grilling`。
- [x] `brainstorming` 与 Cline `/deep-planning` 的默认分工已记录。
- [x] Agent 安装器已创建，支持默认项、显式项和可选项，且不会覆盖同名 Skill。
- [x] 安装器拒绝将不兼容 Cline 的 `grill-me` wrapper 当作可安装 Skill。

## Verification

- [x] 源文件清单与清单哈希核对通过。
- [x] JSON 清单可解析，所有声明的入口文件存在。
- [x] 安装器语法检查和临时目标目录安装演练通过，未写入本机 Cline 目录。
- [x] `git diff --check` 通过。
- [ ] 项目级 `scripts/flowz.ps1 -Command check` 未执行：该脚本当前不在仓库中。
- [x] Cline 用户级安装未执行；这是按本任务边界保留的后续 Agent 行为，本机 Cline 运行行为仍未验证。

## Knowledge feedback

- [ ] 根据后续 Cline 安装实测，确认 `%USERPROFILE%/.agents/skills` 与 `%USERPROFILE%/.cline/skills` 的宿主优先级和刷新方式；当前项目安装器固定选择 `.cline`。

## Transition history

- 2026-09-04T02:55:00+08:00: created in progress after the user clarified that installation is an Agent action for future onboarding, not a local installation in this task.
- 2026-09-04T03:18:00+08:00: source bundles copied and manifest verified; Cline default installation behavior recorded without local Cline installation.
- 2026-09-04T11:27:53+08:00: Agent installer added and verified with default, optional, matching, conflicting, and incompatible-entry rehearsals; no local Cline installation performed.
- 2026-09-04T11:35:00+08:00: Cline design-entry routing fixed as host-planned: `/deep-planning` on Cline, `brainstorming` only on hosts without an equivalent native entry point; upstream `grill-me` delegation confirmed.
- 2026-09-04T12:00:00+08:00: `brainstorming` was removed from the project resource bundle and manifest by a later user decision; the remaining five source packages stay available for Cline integration.
- 2026-09-04T13:00:00+08:00: The bundle became a global Cline installation source: `install-flowz-cline.ps1` installs the global rule and four defaults into `.cline`, with first-task project onboarding and a specified-instruction fallback. Existing user files are never overwritten.
