---
name: project-source
description: Inspect an optional code repository or versioned source for a project, recording branches and exact versions without conflating commits and deployment.
---

# 源码与版本

1. 先确认目标仓库、分支、分析目的和访问权限；看本地是否有未提交改动。
2. 核对远程更新时用只读获取；查看其他分支用独立检出或等价安全方式，保留用户现有工作区。
3. 记录分析依据的提交、检查远程的时间、测试包与实际部署包；后三者不相互推断。
4. 提交记录只证明代码历史，不证明测试、验收和收益。没有仓库的项目跳过本技能。
5. 若远程不可访问，说明最后一次可核实的版本与未知部分，继续分析已有本地材料。
