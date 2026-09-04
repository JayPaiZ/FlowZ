---
id: task-20260904-global-cline-installation
title: 建立一条指令安装的 Cline 全局工作流
status: completed
verification: passed
created_at: 2026-09-04T13:00:00+08:00
updated_at: 2026-09-04T13:45:00+08:00
spec: docs/superpowers/plans/2026-09-04-flowz-global-cline-installation.md
---

# Goal

让用户在 FlowZ 分发目录中向 Agent 给出一条自然语言指令，Agent 即可
安装 Cline 用户级全局规则和默认 Skill。安装完成后，用户打开或加载任意
新旧工作区时，规则在该工作区的首个任务中自动应用项目层流程；若宿主没有
在首个任务自动加载用户规则，用户可用一条指定安装指令触发同一安装动作。

# Scope

## In scope

- 创建自包含的 Cline 全局规则源文件。
- 将 Cline 默认 Skill 和全局规则安装目标统一到用户的 `.cline` 目录。
- 提供幂等、哈希校验、冲突不覆盖的统一安装器。
- 定义首个任务的项目层接入契约，保留现有项目规则和状态。
- 更新 Agent-facing 执行文档和相关任务记录。
- 在隔离目标目录中验证，不写入本机 Cline 用户目录。

## Out of scope

- 修改或删除 Cline 原生/全局 Skill。
- 自动创建、切换、归档或管理会话。
- 将 FlowZ 文件复制到每个项目或强制创建项目 `.clinerules/`。
- 本机 Cline 用户级安装、外部发布、提交或推送。

# Acceptance criteria

- [x] 全局规则安装到 `%USERPROFILE%\\.cline\\rules`，内容声明首个任务接入和指定指令降级路径。
- [x] 默认 Skill 安装到 `%USERPROFILE%\\.cline\\skills`，默认集合仅为 `humanizer-zh`、`humanizer-en`、`office-hours`、`grilling`。
- [x] 同名同哈希文件跳过；同名不同哈希文件报告冲突且不覆盖。
- [x] `grill-me` 被拒绝为 Cline 安装项，`brainstorming` 不在清单中。
- [x] 首个任务读取并保留 `AGENTS.md`、`.clinerules/`、`.workflow/` 和相关项目证据；仅在 Standard/Full 需要时创建持久任务状态。
- [x] 安装器和清单通过脚本语法、JSON、隔离安装、幂等、冲突和排除项验证。
- [x] 验证过程未修改本机 Cline 用户目录；记录项目 `scripts/flowz.ps1` 缺失时的限制。

# Verification commands

- PowerShell parser checks for both installer scripts.
- `ConvertFrom-Json` and source/hash existence checks for `manifest.json`.
- Isolated default installation with `-TargetDirectory` and rules-target override.
- Second isolated run for skip behavior; altered destination for conflict behavior.
- Explicit `grill-me` rejection and `brainstorming` absence checks.
- `git diff --check` and changed-path/scope review.

# Verification evidence

- Both PowerShell installers parsed successfully; `manifest.json` parsed with
  `ConvertFrom-Json`, and all five Skill hashes plus the global-rule hash
  matched the manifest.
- Isolated installation copied one global rule and four default Skills. A
  second run skipped all five matching destinations. Altering the isolated
  rule and `office-hours` destination produced exit code `2` and left both
  files untouched.
- Explicit `grill-me` selection was rejected as not installable for Cline;
  explicit `brainstorming` selection returned no matching entry. Optional
  installation still produced only the four defaults.
- The old `install-cline-skills.ps1` entry point remained compatible and now
  resolves its default target through the manifest's `.cline` preference.
- `%USERPROFILE%\\.cline\\skills` and `%USERPROFILE%\\.cline\\rules` were absent
  before and after the rehearsal, so no local Cline user directory was changed.
- `git diff --check` passed. `scripts/flowz.ps1` is absent, so the historical
  FlowZ check command remains unavailable.

# Transition history

- 2026-09-04T13:35:00+08:00: Created the global Cline rule, unified installer,
  Cline-only manifest targets, first-task onboarding contract, and aligned
  agent-facing documentation. Verified in isolated targets without local Cline
  installation; no commit or push was performed.

# Decisions and boundaries

- Cline engineering design uses native `/deep-planning`; the project does not
  bundle Superpowers `brainstorming`.
- Automatic behavior is best-effort at the first workspace task because Cline
  does not provide a verified “folder opened” event hook. The specified
  installation instruction is the supported fallback.
- No per-Skill confirmation is requested during Agent-managed onboarding.
- Cline user directories are external state and remain untouched in this task.
