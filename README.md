# FlowZ

FlowZ 是一个面向 Codex 的本地插件：它会根据任务的风险、范围和不确定性，主动选择合适的工作深度，并协调宿主已有的 Plan 能力、批准边界和自动验证。它是工作流编排层，不替代 Codex 的 Plan，也不会要求你学习固定的内部命令。

## 分支与平台边界

`main` 是 Codex 与 Cline 共通工作流语义的维护基线；`FlowZ-Codex` 和 `FlowZ-Cline` 分别承载宿主专属实现。新功能先判断是否属于共通契约，再由各平台分支完成自己的接入。详细规则见 [`docs/common-boundary.md`](docs/common-boundary.md)。

## 安装与首次启用

本仓库提供的是本地 marketplace，不是公共插件目录。Codex 将**仓库根目录**作为 marketplace source，并从其中的 [`.agents/plugins/marketplace.json`](.agents/plugins/marketplace.json) 发现 manifest。在终端中，将 `<REPOSITORY_ROOT>` 替换为当前 FlowZ 检出的根目录后运行：

```text
codex plugin marketplace add <REPOSITORY_ROOT>
codex plugin add flowz@flowz-local
```

安装时按宿主提示审核插件的 Skill 和 Hook。新开一个 Codex CLI 或桌面版会话是最稳定的加载方式，但 FlowZ 不强制新会话。

不同 Codex CLI 与桌面版的插件界面和能力可能略有差异。若当前界面没有本地 marketplace 入口，请使用该版本提供的插件管理入口，并指向同一个仓库根目录；不需要手动编辑 `config.toml` 或项目的 `AGENTS.md`。

进入会话后，你可直接开始任务，也可以说“激活 FlowZ 插件”，立即运行一次完整 onboarding，检查并准备四项已登记的第三方 Skill。若你直接开始任务，FlowZ 只会在第一次识别到普通 FlowZ 任务时询问一次；选择暂缓不会中断当前任务，核心路由仍可用。

安装或检查失败不会阻断 FlowZ 的核心路由；FlowZ 会记录当前可调用的依赖，并用短诊断说明失败点和受影响能力。只有你明确要求“重试安装第三方 Skill”时才会再次尝试；“查看安装诊断”只展示已保存的结果，不会重试或重新检查。`SessionStart` 只报告加载和激活状态，不会自动安装任何 Skill。

## FlowZ 如何选择工作深度

FlowZ 会自动选择最小可行层级，不要求用户学习或选择内部深度、Plan 阶段或状态标记：

| 层级 | 适用情况 | Plan 与执行 |
| --- | --- | --- |
| **Quick** | 低风险、小范围、意图清晰 | 直接实施，并由 Agent 自动验证。 |
| **Standard** | 存在实质不确定性、方案选择或局部边界 | 优先使用宿主 Plan；宿主没有可用 Plan 时，用同字段的结构化契约兜底。仅在行为、数据、权限、架构或外部状态会实质改变时等待批准。 |
| **Full** | 需要先明确设计、风险、验收与边界 | 优先使用宿主 Plan；宿主没有可用 Plan 时，用同字段的结构化契约兜底；先取得设计和范围批准，再在批准边界内连续实施和验证。 |

推理投入属于这套 Plan 策略。FlowZ 可以建议宿主对 Standard 或 Full 任务使用更深入的推理，但不会暗改你的模型、推理设置或本地配置。它只呈现可审阅的假设、证据、取舍和结论，不会索取或展示内部思维过程。

低影响、可撤回的本地修改会连续执行。只有范围、数据、权限、架构、外部状态或不可逆操作发生实质变化时，FlowZ 才会简短说明影响并遵守宿主批准。任务结束时，它会用自然语言说明改了什么、验证了什么、剩余风险或未完成项，以及用户是否需要下一步操作；安全和关键回归验证仍由 Agent 负责。

## 与已有工作流协作

你的系统约束、项目规则、`AGENTS.md`、已启用的 Skill、插件和工作流优先于 FlowZ。遇到冲突时，FlowZ 会跳过冲突的自身行为、保留不冲突部分，并在同一任务中只报告一次冲突来源；它不会修改冲突来源。

Superpowers 是可选工作流集成，不属于 FlowZ onboarding 的四项依赖。安装不等于加载，加载也不等于在当前会话生效；FlowZ 只依据宿主可见的生效状态协作。未加载时，FlowZ 继续完成任务；只在明确有收益的 Standard/Full 任务中给出一次非阻断建议，不自动安装，也不改变 Quick 语义。已加载且在当前会话生效时，相关设计、TDD、调试、评审和交付生命周期交给 Superpowers，FlowZ 不再启动第二套同类流程。用户显式调用某个 Superpowers Skill 时，FlowZ 完整遵守该 Skill。

对于长任务，一旦 Plan 获得批准，FlowZ 会在批准边界内连续执行和自动验证，不会为普通中间进度反复索要确认。出现新证据推翻方案、需要扩大范围、破坏性操作、权限或外部状态变化、环境阻塞，或更高优先级规则要求暂停时，它才会停下重新对齐。

## 暂停、恢复与可选功能

以下控制从**下一轮用户消息**开始生效：

- 说“暂停 FlowZ”或 “pause FlowZ”，停止当前会话后续的 FlowZ 路由与辅助。
- 说“恢复 FlowZ”或 “resume FlowZ”，重新启用 FlowZ 路由。
- 说“打开/关闭 ChatGPT 网页版辅助”，只切换该独立功能。
- 说“打开/关闭用户验证建议”，只切换该独立功能。
- 说“使用简洁回答”或“使用详细回答”，设置本会话的回答详略偏好。
- 说“隐藏计划摘要”或“显示简短计划摘要”，设置本会话的计划摘要偏好。

ChatGPT 网页版辅助默认关闭，用户验证建议也默认关闭。打开 ChatGPT 网页版辅助后，FlowZ 只会在独立对话确有价值且宿主具有可见浏览器能力时提出或使用它，并会说明共享内容与结果如何并入当前任务；没有浏览器能力时只提供可复制的提示词，不会声称已经访问网页。

关闭用户验证建议不会关闭 Agent 的正常自动验证。打开后，FlowZ 可以建议用户完成非关键、明显耗 token 或环境相关的检查，例如浏览器视觉效果、硬件行为或私有账号集成；安全、数据完整性和关键回归检查仍由 Agent 承担。插件的全局启用或禁用由 Codex 宿主管理，可靠的生效边界是新聊天或新的 CLI 会话，而不是承诺运行中会话热加载。

## 可选第三方 Skill

FlowZ 仅记录以下可选能力，不复制、改名或覆盖它们：

| 用途 | 规范名 | 兼容别名 |
| --- | --- | --- |
| 中文文本处理 | `humanizer-zh` | — |
| 英文文本处理 | `humanizer` | `humanizer-en` |
| 方案质询 | `grilling` | — |
| 产品构思 | `gstack-openclaw-office-hours` | `office-hours` |

规范名或兼容别名已安装即视为满足。缺失时，FlowZ 先使用 Codex 原生 Skill Installer；若该路径失败，才按 [第三方目录](plugins/flowz/skills/flowz-onboarding/references/third-party-skills.json) 中记录的原作者 GitHub 仓库和路径回退。目录分别记录供 Installer 使用的 Skill 目录和供来源定位使用的入口文件，根目录 Skill 不会再把 `SKILL.md` 当作安装目录。它不会自动替换为 Fork、同名替代项目或未记录来源，也不会把中文与英文文本处理 Skill 混用。

## 作者与本地开发状态

FlowZ 由 [JayPaiZ](https://github.com/JayPaiZ) 维护，使用 MIT 许可证。

主页与仓库：[github.com/JayPaiZ/FlowZ/tree/FlowZ-Codex](https://github.com/JayPaiZ/FlowZ/tree/FlowZ-Codex)。

当前版本是仓库内的本地 marketplace 开发版：尚未发布到公共目录，也不会自动发布或推送。CLI 与桌面版可见的 Plan、Hook 审核和插件管理能力由各自宿主版本决定；能力不可用时，FlowZ 保留相同的工作流语义并使用结构化契约降级。

## 隐私与项目边界

FlowZ 不会把规则或隐藏状态写入你的项目，也不会修改项目 `AGENTS.md`、已有 Skill、插件或 `config.toml`。FlowZ 执行规则要求 Agent 不读取或输出凭据、`.env`、私有日志和无关运行数据。Hook 只读取当前提示来匹配明确的会话命令，不保存原始提示；`Stop` 只保存答复末尾标记中的白名单、限长摘要，不保存完整答复。规则也禁止把原始提示、隐藏推理或凭据放入该标记，Hook 还会过滤明显的凭据形态。会话状态按会话隔离，并在会话结束时清理。

任何外部操作仍遵从 Codex 的权限、审核与项目规则。暂停或禁用 FlowZ 后，它不会通过遗留的项目文件继续生效。
