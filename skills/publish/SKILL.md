---
name: project-publish
description: Validate structured project records and regenerate consistent static HTML pages for portfolio, roadmap, work, decisions, evidence and outcomes.
---

# 生成展示

1. 先完成记录和变更日志，运行 `python3 scripts/workspace.py validate`。
2. 校验成功后运行 `python3 scripts/workspace.py build`，再打开 `site/index.html` 和受影响页面确认导航、状态与来源正确。
3. 不手工修改 `site/` 中的项目事实；样式需要修改时编辑 `templates/style.css` 或生成脚本。
4. 页面上的“无数据”和“待验证”应真实呈现，不用示例数字填充。所有项目使用同一数据来源和一致状态。
5. 返回用户可见的变化和仍未确定的事项。
