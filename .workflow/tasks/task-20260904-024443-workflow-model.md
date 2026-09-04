---
id: task-20260904-024443-workflow-model
title: 统一 Quick Standard Full 流程模型与阶段路由
status: completed
verification: passed
created_at: 2026-09-04T02:44:43+08:00
updated_at: 2026-09-04T02:44:43+08:00
spec: none
---

# Goal

将已确认的正式主线与单阶段自动路由合并到项目执行文档，并统一使用 `Quick`、`Standard`、`Full` 作为任务深度术语。

## Scope

### In scope

- 将 Intake / Triage、Problem Exploration、Solution Design、Design Challenge、Approval、Writing Plan、Implementation、Verification / Review 定义为可选阶段。
- 明确 Quick、Standard、Full 的默认路径和按风险缩放的 Approval 规则。
- 为 Problem Exploration、Solution Design、Design Challenge 和 Approval 定义结构化交接物。
- 明确一次只允许一个阶段主导能力，Skill 不得自动互相调用或串行启动下一阶段。

### Out of scope

- 创建或安装 `.cline/skills/` 文件。
- 选择最终内置 Skill 清单、版本或依赖。
- 修改 Cline 原生或全局能力。

## Acceptance criteria

- [x] `Quick`、`Standard`、`Full` 是唯一任务深度术语，没有引入 `Level S / M / L`。
- [x] 正式主线被定义为可按出口条件裁剪的生命周期，而非所有任务必须执行的固定流水线。
- [x] 自动路由规则明确每个阶段最多一个主导能力，且 Skill 不得互相调用。
- [x] 三种任务路径、具体方案例外路径和按风险缩放的 Approval 规则已记录。
- [x] 阶段输入输出包含可供下一次路由使用的结构化交接物。

## Verification

- [x] 文档结构检查通过：执行文档正文只使用 `Quick`、`Standard`、`Full`，阶段主线、阶段能力、交接物、分级路径和例外路由均存在；任务记录保留旧术语仅用于说明迁移结果。
- [x] `git diff --check` 通过。
- [ ] 项目级 `scripts/flowz.ps1 -Command check` 未执行：该脚本当前不在仓库中。

## Knowledge feedback

- [x] 将流程层与路由层分离，作为后续 `.cline/skills/` 设计的约束。

## Transition history

- 2026-09-04T02:44:43+08:00: created and completed after user approval of the unified lifecycle and routing model.
