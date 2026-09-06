# FlowZ

FlowZ 是一个面向 Codex 的本地插件：它会根据任务的风险、范围和不确定性，主动选择合适的工作深度，并协调宿主已有的 Plan 能力、批准边界和自动验证。它是工作流编排层，不替代 Codex 的 Plan，也不会要求你学习固定的内部命令。

## 安装与首次启用

本仓库提供的是本地 marketplace，不是公共插件目录。Codex 将**仓库根目录**作为 marketplace source，并从其中的 [`.agents/plugins/marketplace.json`](.agents/plugins/marketplace.json) 发现 manifest。在终端中，将 `<REPOSITORY_ROOT>` 替换为当前 FlowZ 检出的根目录后运行：

```text
codex plugin marketplace add <REPOSITORY_ROOT>
codex plugin add flowz@personal
```

安装时按宿主提示审核插件的 Skill 和 Hook；安装完成后新开一个 Codex CLI 或桌面版会话，确保插件在会话开始时被加载。

不同 Codex CLI 与桌面版的插件界面和能力可能略有差异。若当前界面没有本地 marketplace 入口，请使用该版本提供的插件管理入口，并指向同一个仓库根目录；不需要手动编辑 `config.toml` 或项目的 `AGENTS.md`。

第一次处理实际任务时，FlowZ 会检查可选第三方 Skill 是否已可用。安装或检查失败不会阻断 FlowZ 的核心路由；它会说明失败点、受影响能力和下一步。只有你明确要求“重试安装”或“查看安装诊断”时，才会再次尝试。

## FlowZ 如何选择工作深度

FlowZ 始终选择一个最小可行层级：

| 层级 | 适用情况 | Plan 与执行 |
| --- | --- | --- |
| **Quick** | 低风险、小范围、意图清晰 | 直接实施，并由 Agent 自动验证。 |
| **Standard** | 存在实质不确定性、方案选择或局部边界 | 优先使用宿主 Plan；宿主没有可用 Plan 时，用同字段的结构化契约兜底。仅在行为、数据、权限、架构或外部状态会实质改变时等待批准。 |
| **Full** | 需要先明确设计、风险、验收与边界 | 优先使用宿主 Plan；宿主没有可用 Plan 时，用同字段的结构化契约兜底；先取得设计和范围批准，再在批准边界内连续实施和验证。 |

推理投入属于这套 Plan 策略。FlowZ 可以建议宿主对 Standard 或 Full 任务使用更深入的推理，但不会暗改你的模型、推理设置或本地配置。它只呈现可审阅的假设、证据、取舍和结论，不会索取或展示内部思维过程。

## 与已有工作流协作

你的系统约束、项目规则、`AGENTS.md`、已启用的 Skill、插件和工作流优先于 FlowZ。遇到冲突时，FlowZ 会跳过冲突的自身行为、保留不冲突部分，并在同一任务中只报告一次冲突来源；它不会修改冲突来源。

FlowZ 不依赖、安装或复制 Superpowers。只有 Superpowers 或其他等价工作流已在当前会话中明确加载并生效时，FlowZ 才会尊重其主导的设计、批准和生命周期，避免启动第二套同类流程。

对于长任务，一旦 Plan 获得批准，FlowZ 会在批准边界内连续执行和自动验证，不会为普通中间进度反复索要确认。出现新证据推翻方案、需要扩大范围、破坏性操作、权限或外部状态变化、环境阻塞，或更高优先级规则要求暂停时，它才会停下重新对齐。

## 暂停、恢复与可选功能

以下控制从**下一轮用户消息**开始生效：

- 说“暂停 FlowZ”或 “pause FlowZ”，停止当前会话后续的 FlowZ 路由与辅助。
- 说“恢复 FlowZ”或 “resume FlowZ”，重新启用 FlowZ 路由。
- 说“打开/关闭 ChatGPT 网页版辅助”，只切换该独立功能。
- 说“打开/关闭用户验证建议”，只切换该独立功能。

ChatGPT 网页版辅助默认关闭，用户验证建议也默认关闭。关闭用户验证建议不会关闭 Agent 的正常自动验证；即使你打开建议，安全、数据完整性和关键回归检查的责任仍由 Agent 承担。插件的全局启用或禁用由 Codex 宿主管理，可靠的生效边界是新聊天或新的 CLI 会话，而不是承诺运行中会话热加载。

## 可选第三方 Skill

FlowZ 仅记录以下可选能力，不复制、改名、覆盖或主动更新它们：

| 用途 | 规范名 | 兼容别名 |
| --- | --- | --- |
| 中文文本处理 | `humanizer-zh` | — |
| 英文文本处理 | `humanizer` | `humanizer-en` |
| 方案质询 | `grilling` | — |
| 产品构思 | `gstack-openclaw-office-hours` | `office-hours` |

规范名或兼容别名已安装即视为满足。缺失时，FlowZ 先使用 Codex 原生 Skill Installer；若该路径失败，才按 [第三方目录](plugins/flowz/references/third-party-skills.json) 中记录的原作者 GitHub 仓库和路径回退。它不会自动替换为 Fork、同名替代项目或未记录来源，也不会把中文与英文文本处理 Skill 混用。

## 图标、作者与本地开发状态

FlowZ 由 [JayPaiZ](https://github.com/JayPaiZ) 维护，使用 MIT 许可证。插件同时提供完整水墨原图 [`logo.png`](plugins/flowz/assets/logo.png) 与透明圆角区域的圆形小图标 [`icon.png`](plugins/flowz/assets/icon.png)，后者面向插件列表和编辑器小尺寸展示。

当前版本是仓库内的本地 marketplace 开发版：尚未发布到公共目录，也不会自动发布或推送。CLI 与桌面版可见的 Plan、Hook 审核和插件管理能力由各自宿主版本决定；能力不可用时，FlowZ 保留相同的工作流语义并使用结构化契约降级。

## 隐私与项目边界

FlowZ 不会把规则或隐藏状态写入你的项目，不会修改项目 `AGENTS.md`、已有 Skill、插件或 `config.toml`。它不读取或输出凭据、`.env`、私有日志和无关运行数据；会话状态按会话隔离，不保存原始提示，并在会话结束时清理。

任何外部操作仍遵从 Codex 的权限、审核与项目规则。暂停或禁用 FlowZ 后，它不会通过遗留的项目文件继续生效。
