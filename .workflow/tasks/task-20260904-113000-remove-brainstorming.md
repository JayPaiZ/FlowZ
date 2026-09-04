---
id: task-20260904-113000-remove-brainstorming
title: 从项目预置资源中移除 brainstorming
status: completed
verification: passed
created_at: 2026-09-04T11:30:00+08:00
updated_at: 2026-09-04T12:05:00+08:00
spec: none
---

# Goal

从项目预置资源和当前有效路由中彻底移除 Superpowers `brainstorming`，保留 Cline 原生 `/deep-planning` 作为工程设计入口。

## Scope

### In scope

- 删除 `.workflow/resources/skills/sources/brainstorming/`。
- 删除 manifest 中的 `brainstorming` 条目和其他宿主 fallback 路由。
- 从当前有效执行文档中移除 `brainstorming` 作为项目能力的引用。
- 保留历史任务记录中对该 Skill 的事实性决策记录。

### Out of scope

- 删除或修改 Codex 本机 Superpowers 缓存。
- 删除或修改其他项目或用户级 Skill。
- 修改 Cline 原生 `/deep-planning`。

## Acceptance criteria

- [x] 项目资源目录不再包含 `brainstorming` 源包。
- [x] manifest 不再声明 `brainstorming` 资源或 Cline 安装项。
- [x] 当前有效执行文档不再把 `brainstorming` 作为项目 fallback Skill。
- [x] 历史任务记录未被伪造重写，仅保留必要审计信息。

## Verification

- [x] 资源目录、manifest 和有效文档检查通过。
- [x] 安装器回归测试通过：默认和可选安装均未恢复已删除的 `brainstorming`，也未安装 Cline 不兼容的 `grill-me`。
- [x] `git diff --check` 通过。
- [ ] 项目级 `scripts/flowz.ps1 -Command check` 未执行：该脚本当前不在仓库中。

## Knowledge feedback

- [x] Cline 适配采用原生 `/deep-planning`；其他宿主需提供自己的设计入口，不再由本项目提供 `brainstorming` fallback。

## Transition history

- 2026-09-04T11:30:00+08:00: created and completed after the user approved removing `brainstorming` from the project.
- 2026-09-04T12:05:00+08:00: post-removal installer regression passed; Codex cache was preserved.
