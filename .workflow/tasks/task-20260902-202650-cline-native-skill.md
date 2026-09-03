---
id: task-20260902-202650-cline-native-skill
title: 评估 Cline 原生 Skill 与 Lite 文档的冲突处理
status: planning
verification: pending
created_at: 2026-09-02T20:26:50+08:00
updated_at: 2026-09-02T20:26:50+08:00
spec: none
---

# Goal

在整理随文档分发的 Skill 时，检查 Cline 原生 Skill 与 Lite 执行文档之间是否存在冲突，并确定冲突的处理方式。

## Scope

### In scope

- 盘点与候选内置 Skill 相关的 Cline 原生 Skill、触发条件和行为边界。
- 识别原生 Skill 与 Lite 执行文档、路由规则或分发约定之间的冲突。
- 为每项冲突确定处理策略：兼容现有行为、调整 Lite 文档约定，或在文档中明确记录需要修改原生 Skill。
- 明确冲突处理后的验证方式和兼容性限制。

### Out of scope

- 在本任务记录阶段不创建、安装或修改任何 Skill。
- 直接修改 Cline 原生 Skill。
- 现在修改 Lite 执行文档或开始编写面向开发者的说明文档。

## Acceptance criteria

- [ ] 候选内置 Skill 的原生 Skill 依赖和行为边界有清单。
- [ ] 已识别的冲突均有证据、影响范围和处理决定。
- [ ] 若需要修改原生 Skill，Lite 文档明确记录修改对象、原因、替代方案和风险。
- [ ] 处理方案不把 Cline 专属行为未经说明地当成跨宿主保证。

## Verification

- [ ] 完成原生 Skill 与 Lite 文档的逐项对照检查，并记录未能验证的宿主行为。

## Knowledge feedback

- [ ] 检查是否有长期有效的兼容性规则应写入 Lite 文档、Skill 或任务记录。

## Transition history

- 2026-09-02T20:26:50+08:00: created in planning.
