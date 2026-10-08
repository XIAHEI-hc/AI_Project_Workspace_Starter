# 记录约定（v1）

一个项目目录包含 `project.json`、`changes.jsonl` 与 `materials/`。顶层字段：`id`, `name`, `summary`, `phase`, `goal`, `scope`, `owner`, `updated_at`, `source_refs`, `milestones`, `items`, `decisions`, `evidence`, `outcomes`。

每条实体有唯一稳定 ID，格式如 `I-001`、`M-001`、`D-001`、`E-001`、`O-001`。引用使用 ID 字符串；不要用数组下标或标题链接。时间用带时区的 ISO 8601；不确定日期可省略。`source_refs` 保存可选仓库、文档或其他来源，注明核对时间和版本。

## 状态和类型

- 事项 `type`：`idea`, `issue`, `risk`, `need`, `task`；`status`：`待澄清`, `后续`, `待开始`, `进行中`, `阻塞`, `待验证`, `已完成`, `暂缓`。
- 里程碑 `status`：`后续`, `进行中`, `待验收`, `已验收`, `暂缓`。`criteria` 是可核验的完成条件；`evidence_ids` 仅表示关联，不代表已经通过。
- 证据 `status`：`待核实`, `已核实`, `不适用`；可有 `path` 或 `url` 和 `observed_at`。引用外部链接不能当作其内容已读。
- 收益 `status`：`预期`, `待验证`, `已确认`, `未达预期`；`baseline`, `observed`, `method`, `evidence_ids` 分开填写。

事项建议字段：`id`, `type`, `title`, `status`, `description`, `reason`, `owner`, `milestone_id`, `depends_on`, `evidence_ids`, `revisit_when`, `displaces`, `updated_at`。决策建议字段：`id`, `title`, `decision`, `reason`, `owner`, `date`, `item_ids`, `evidence_ids`。

## 规则

- `已完成` 的任务应有完成说明或证据；`已验收` 的里程碑应有验收决定与证据；`已确认` 的收益应有观察值与方法。校验器检查部分必需字段，AI 还须判断证据内容是否真能支持结论。
- 将不同状态分层记录：代码完成不自动改变里程碑验收，更不自动确认收益。
- 变更记录每行一个 JSON 对象：`at`, `actor`, `source`, `summary`, `entity_ids`, `reason`；修改后追加，不改写旧行。
- 页面为生成结果。原始材料与结构化数据是备份重点。
