# AI 项目工作区 · 通用模板

这是一个“对话输入 → 项目记录 → 多页 HTML”的本地项目包。它适用于开发、研究、课程建设、活动等项目；示例项目是虚构的“资料交付流程优化”，只用于演示页面和记录关系。

## 五分钟开始

1. 解压包，先读 `AGENTS.md`（Codex）、`CLAUDE.md`（Claude）或 `DSH.md`（DSH）。这些入口都指向同一个 `agent/CORE.md`。
2. 直接打开 `site/index.html` 查看初版页面。页面为预生成静态文件，浏览器可用 `file://` 打开，无需 Docker、Node 或服务器。
3. 给 AI 一条指令：`请按本项目 AGENTS.md / CLAUDE.md / DSH.md 工作。把下面这条想法录入示例项目，说明现在是否做、依赖和复查条件；更新 HTML：……`。
4. AI 修改 `workspace/projects/<项目 ID>/project.json`，保留材料于 `materials/`，追加 `changes.jsonl`，再运行 `python3 scripts/workspace.py validate` 和 `python3 scripts/workspace.py build`。
5. 新项目：`python3 scripts/workspace.py init your-project-id "项目名称"`，再用 AI 补齐项目目标、材料和事项。项目 ID 使用小写英文字母、数字和短横线。

## 文件分工

| 位置 | 用途 |
| --- | --- |
| `agent/CORE.md` | 全部 AI 的共同约定，来源、权限、更新顺序 |
| `agent/ROUTER.md` | 请求意图到具体项目技能的路由 |
| `skills/*/SKILL.md` | 各类任务的项目内技能说明；是随压缩包携带的本地流程文件，不会自动安装为个人技能 |
| `workspace/projects/*/project.json` | 项目的结构化事实记录；HTML 的唯一数据来源 |
| `workspace/projects/*/materials/` | 用户输入的原始文字、日志和材料引用；不自动当作已核实事实 |
| `workspace/projects/*/changes.jsonl` | 记录每次变更的原因、来源及影响范围 |
| `scripts/workspace.py` | 校验、初始化、生成静态页面；仅需 Python 3.10+ 标准库 |
| `site/` | 已生成的多页 HTML，直接打开 `index.html` |

## 真实工作方式

AI 可直接整理材料、补充候选关系、更新普通事项和生成页面。涉及项目目标改变、里程碑验收、实际收益认定、删除、发布或对外通知时，AI 先写清证据和建议，由具有决定权的人确认。用户在对话中明确授权时，无需重复询问。

示例 JSON、截图和页面中的事项均为虚构；`待验证` 不得渲染成 `已完成`。页面不会从代码提交数计算完成率。

## 接入其他工具

源码仓库、聊天、日历、网盘、测试系统都是可选的证据来源。接入时只记录明确的来源、采集时间、版本或链接；没有连接权限时不推测其内容。使用 ZIP 部署的软件项目要分别记录“分析提交、测试包、实际部署包”，不要将远程最新提交等同于上线版本。

DSH 的部署形态各不相同，本包没有假定它自带文件写入工具或自动发现 `SKILL.md`。需要在 DSH 工作区授予本目录的读写和本地脚本运行能力，并把 `DSH.md` 作为入口；具体权限按实际运行环境配置。

## 扩展顺序

先验证录入、去重、状态依据、变更记录和 HTML 一致性，再扩展多用户审批、外部消息、仓库同步、自动定时任务。所有自动生成页面都可以重建；请长期保存 `workspace/` 和原始材料。
