# Codex 项目入口

本目录是一个通用 AI 项目工作区。处理任何用户请求前，先读 `agent/CORE.md` 和 `agent/ROUTER.md`；只读与本次意图匹配的 `skills/*/SKILL.md`。项目资料在 `workspace/projects/`，不把示例项目当成用户的真实现状。

写入时遵循 `agent/SCHEMA.md`，运行 `python3 scripts/workspace.py validate` 与 `python3 scripts/workspace.py build`。若用户要求查看源码，先确认项目的 `source_refs`、目标分支、工作区改动和分析提交；远程操作遵循现有权限，避免覆盖本地修改。

按已存在的用户授权推进工作。高影响结论必须给出证据和决定人；未有足够证据时保持 `待验证`。在最终答复说明本次修改了哪些记录、页面和仍待确认的判断。
