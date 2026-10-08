# Claude 项目入口

本目录是一个通用 AI 项目工作区。先读 `agent/CORE.md`、`agent/ROUTER.md`；按请求选择 `skills/*/SKILL.md`，再读目标项目的 `project.json` 和有关材料。保持 `workspace/` 为事实来源，生成的 `site/` 不手工维护。

写入前核对事项 ID 和状态依据。写入后按 `agent/SCHEMA.md` 检查引用，运行 `python3 scripts/workspace.py validate` 与 `python3 scripts/workspace.py build`。材料不足时标注未知，重大验收和收益结论由有权决定的人确认。返回改动摘要和待确认事项。
