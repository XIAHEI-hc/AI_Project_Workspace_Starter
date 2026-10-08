#!/usr/bin/env python3
"""Validate a file-based project workspace and generate static, offline HTML."""

from __future__ import annotations

import argparse
import html
import json
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROJECTS = ROOT / "workspace" / "projects"
SITE = ROOT / "site"
STYLE = ROOT / "templates" / "style.css"
SLUG = re.compile(r"^[a-z][a-z0-9-]{1,49}$")
ITEM_TYPES = {"idea", "issue", "risk", "need", "task"}
ITEM_STATUSES = {"待澄清", "后续", "待开始", "进行中", "阻塞", "待验证", "已完成", "暂缓"}
MILESTONE_STATUSES = {"后续", "进行中", "待验收", "已验收", "暂缓"}
EVIDENCE_STATUSES = {"待核实", "已核实", "不适用"}
OUTCOME_STATUSES = {"预期", "待验证", "已确认", "未达预期"}
TYPES = {"idea": "想法", "issue": "问题", "risk": "风险", "need": "需求", "task": "任务"}
NAV = [("index.html", "项目总览"), ("roadmap.html", "路线图"),
       ("work.html", "事项与执行"), ("decisions.html", "决策与变更"),
       ("evidence.html", "证据与验收"), ("outcomes.html", "收益回顾")]


def esc(value: object) -> str:
    return html.escape(str(value if value is not None else ""), quote=True)


def load_projects() -> list[tuple[Path, dict]]:
    found = []
    for file in sorted(PROJECTS.glob("*/project.json")):
        try:
            data = json.loads(file.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ValueError(f"{file}: 无法读取 JSON: {exc}") from exc
        found.append((file.parent, data))
    return found


def validate(projects: list[tuple[Path, dict]]) -> None:
    errors: list[str] = []
    project_ids: set[str] = set()
    for folder, data in projects:
        label = str(folder)
        pid = data.get("id")
        if not isinstance(pid, str) or not SLUG.fullmatch(pid) or pid != folder.name:
            errors.append(f"{label}: id 必须与安全目录名相同")
        elif pid in project_ids:
            errors.append(f"{label}: 重复项目 ID {pid}")
        project_ids.add(str(pid))
        for key in ("name", "goal", "phase", "summary"):
            if not isinstance(data.get(key), str) or not data[key].strip():
                errors.append(f"{label}: 缺少非空 {key}")
        for key in ("milestones", "items", "decisions", "evidence", "outcomes"):
            if not isinstance(data.get(key), list):
                errors.append(f"{label}: {key} 必须是数组")
        if errors and any(e.startswith(label + ":") and ("必须是数组" in e) for e in errors):
            continue
        ids: set[str] = set()
        for group, prefix in (("milestones", "M"), ("items", "I"),
                              ("decisions", "D"), ("evidence", "E"), ("outcomes", "O")):
            for record in data[group]:
                if not isinstance(record, dict):
                    errors.append(f"{label}/{group}: 记录必须是对象")
                    continue
                rid = record.get("id")
                if not isinstance(rid, str) or not re.fullmatch(prefix + r"-\d{3,}", rid):
                    errors.append(f"{label}/{group}: 无效 ID {rid!r}")
                elif rid in ids:
                    errors.append(f"{label}: 重复实体 ID {rid}")
                ids.add(str(rid))
                if not isinstance(record.get("title"), str) or not record["title"].strip():
                    errors.append(f"{label}/{group}/{rid}: 缺少标题")
        lookup = {g: {x.get("id") for x in data[g] if isinstance(x, dict)}
                  for g in ("milestones", "items", "decisions", "evidence", "outcomes")}

        def references(record: dict, field: str, group: str) -> None:
            vals = record.get(field, [])
            if not isinstance(vals, list):
                errors.append(f"{label}/{record.get('id')}: {field} 必须是数组")
            else:
                for ref in vals:
                    if ref not in lookup[group]:
                        errors.append(f"{label}/{record.get('id')}: {field} 引用不存在的 {ref}")

        for m in data["milestones"]:
            if not isinstance(m, dict):
                continue
            if m.get("status") not in MILESTONE_STATUSES:
                errors.append(f"{label}/{m.get('id')}: 无效里程碑状态")
            if not isinstance(m.get("criteria"), list) or not m["criteria"]:
                errors.append(f"{label}/{m.get('id')}: 缺少验收条件")
            references(m, "evidence_ids", "evidence")
            if m.get("status") == "已验收" and not m.get("evidence_ids"):
                errors.append(f"{label}/{m.get('id')}: 已验收缺少证据")
        for item in data["items"]:
            if not isinstance(item, dict):
                continue
            if item.get("type") not in ITEM_TYPES or item.get("status") not in ITEM_STATUSES:
                errors.append(f"{label}/{item.get('id')}: 无效事项类型或状态")
            milestone = item.get("milestone_id")
            if milestone and milestone not in lookup["milestones"]:
                errors.append(f"{label}/{item.get('id')}: 无效里程碑引用 {milestone}")
            references(item, "depends_on", "items")
            references(item, "evidence_ids", "evidence")
            if item.get("id") in item.get("depends_on", []):
                errors.append(f"{label}/{item.get('id')}: 不能依赖自身")
            if item.get("status") == "已完成" and not (item.get("evidence_ids") or item.get("completion_note")):
                errors.append(f"{label}/{item.get('id')}: 已完成缺少完成说明或证据")
        for decision in data["decisions"]:
            if isinstance(decision, dict):
                references(decision, "item_ids", "items")
                references(decision, "evidence_ids", "evidence")
        for evidence in data["evidence"]:
            if not isinstance(evidence, dict):
                continue
            if evidence.get("status") not in EVIDENCE_STATUSES:
                errors.append(f"{label}/{evidence.get('id')}: 无效证据状态")
            path = evidence.get("path", "")
            if path:
                if not isinstance(path, str) or Path(path).is_absolute() or ".." in Path(path).parts:
                    errors.append(f"{label}/{evidence.get('id')}: 不安全的证据路径")
                elif not (folder / path).is_file():
                    errors.append(f"{label}/{evidence.get('id')}: 证据文件不存在 {path}")
        for outcome in data["outcomes"]:
            if not isinstance(outcome, dict):
                continue
            if outcome.get("status") not in OUTCOME_STATUSES:
                errors.append(f"{label}/{outcome.get('id')}: 无效收益状态")
            references(outcome, "evidence_ids", "evidence")
            if outcome.get("status") == "已确认" and not all(
                outcome.get(k) for k in ("baseline", "observed", "method", "evidence_ids")
            ):
                errors.append(f"{label}/{outcome.get('id')}: 已确认收益缺少基线、观察、方法或证据")
        change_file = folder / "changes.jsonl"
        if not change_file.exists():
            errors.append(f"{label}: 缺少 changes.jsonl")
        else:
            for n, line in enumerate(change_file.read_text(encoding="utf-8").splitlines(), 1):
                try:
                    change = json.loads(line)
                    if not all(k in change for k in ("at", "actor", "source", "summary", "entity_ids", "reason")):
                        errors.append(f"{label}/changes.jsonl:{n}: 缺少变更字段")
                except json.JSONDecodeError:
                    errors.append(f"{label}/changes.jsonl:{n}: 非 JSON 行")
    if errors:
        raise ValueError("校验失败：\n- " + "\n- ".join(errors))


def badge(status: str) -> str:
    tone = "good" if status in ("已验收", "已完成", "已确认", "已核实") else (
        "warn" if status in ("阻塞", "待验证", "待验收", "待核实", "待澄清") else "neutral")
    return f'<span class="badge {tone}">{esc(status)}</span>'


def card(title: str, content: str, meta: str = "") -> str:
    return f'<section class="card"><div class="card-head"><h3>{esc(title)}</h3>{meta}</div>{content}</section>'


def empty(message: str) -> str:
    return f'<div class="empty">{esc(message)}</div>'


def list_card(records: list[dict], show) -> str:
    return '<div class="stack">' + (''.join(show(x) for x in records) if records else empty("暂无记录")) + '</div>'


def row(title: str, body: str, right: str = "", kicker: str = "") -> str:
    return (f'<article class="row"><div><small class="eyebrow">{esc(kicker)}</small>'
            f'<h3>{esc(title)}</h3><p>{esc(body)}</p></div><div class="row-right">{right}</div></article>')


def page(project: dict | None, active: str, title: str, subtitle: str, content: str) -> str:
    is_portfolio = project is None
    base = "" if is_portfolio else "../"
    menu = ([f'<a href="{base}index.html" class="{"active" if is_portfolio else ""}">项目组合</a>']
            + ([f'<a href="{target}" class="{"active" if active == target else ""}">{label}</a>'
                for target, label in NAV] if project else []))
    project_label = esc(project["name"]) if project else "所有项目"
    return f'''<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)} · AI 项目工作区</title><link rel="stylesheet" href="{base}assets/style.css"></head>
<body><div class="layout"><aside class="sidebar"><a class="brand" href="{base}index.html"><span class="brand-mark">◇</span><span>项目工作区<small>AI 辅助 · 文件驱动</small></span></a>
<div class="side-label">导航</div><nav>{''.join(menu)}</nav><div class="side-note">所有状态来自项目记录。<br>示例项目均为虚构内容。</div></aside>
<main class="main"><header class="top"><div>项目工作区 <span class="slash">/</span> {project_label}</div><span class="top-chip">静态页面 · 本地可查看</span></header>
<div class="page"><div class="hero"><div><div class="eyebrow">{project_label} / {esc(active.replace('.html',''))}</div><h1>{esc(title)}</h1><p>{esc(subtitle)}</p></div><span class="demo">示例模板</span></div>
{content}<footer>AI 项目工作区 · 页面由结构化记录生成 · 对实际项目请核对材料与决定依据</footer></div></main></div></body></html>'''


def portfolio(projects: list[tuple[Path, dict]]) -> str:
    overview = ''.join(
        f'<a class="project-card" href="{esc(p["id"])}/index.html"><div class="project-top"><span class="project-icon">▦</span>'
        f'{badge(p["phase"])}</div><h2>{esc(p["name"])}</h2><p>{esc(p["summary"])}</p>'
        f'<div class="project-foot"><span>当前目标</span><strong>{esc(p["goal"])}</strong></div></a>'
        for _, p in projects)
    content = ('<div class="metric-grid"><div class="metric"><span>项目数量</span><strong>' + str(len(projects))
               + '</strong><small>由本地项目目录生成</small></div><div class="metric"><span>管理原则</span>'
               '<strong>证据 → 决策 → 结果</strong><small>每项判断保留来源</small></div>'
               '<div class="metric"><span>当前视图</span><strong>项目组合</strong><small>进入项目查看各阶段</small></div></div>'
               '<h2 class="section-title">项目列表</h2><div class="project-grid">'
               + (overview or empty("还没有项目。运行 init 命令创建第一个项目。")) + '</div>'
               '<div class="hint">输入新材料后，先更新 workspace，再运行 validate 与 build。页面不从聊天记录自动猜测状态。</div>')
    return page(None, "portfolio", "一眼看清正在推进的项目", "从项目目标进入阶段、事项、决定、交付与收益。", content)


def overview(p: dict) -> str:
    current = [m for m in p["milestones"] if m["status"] in ("进行中", "待验收")]
    current_html = list_card(current, lambda m: row(m["title"], m.get("description", ""), badge(m["status"]), m["id"]))
    work = [x for x in p["items"] if x["status"] in ("进行中", "阻塞", "待验证")]
    deferred = [x for x in p["items"] if x["status"] in ("后续", "暂缓")]
    contents = (f'<div class="spotlight"><div class="eyebrow">项目目标</div><h2>{esc(p["goal"])}</h2>'
                f'<p>{esc(p.get("scope", ""))}</p></div><div class="metric-grid">'
                f'<div class="metric"><span>当前阶段</span><strong>{esc(p["phase"])}</strong><small>阶段名称</small></div>'
                f'<div class="metric"><span>待关注事项</span><strong>{len(work)}</strong><small>进行中 / 阻塞 / 待验证</small></div>'
                f'<div class="metric"><span>收益待核对</span><strong>{sum(o["status"] == "待验证" for o in p["outcomes"])}</strong><small>不代表收益已经实现</small></div></div>'
                '<div class="two-col">' + card("当前里程碑", current_html, '<a href="roadmap.html">查看路线图 →</a>')
                + card("正在处理", list_card(work, lambda x: row(x["title"], x.get("reason", ""), badge(x["status"]), x["id"])), '<a href="work.html">查看事项 →</a>')
                + card("留待后续", list_card(deferred, lambda x: row(x["title"], x.get("revisit_when", ""), badge(x["status"]), x["id"])))
                + card("判断依据", '<p class="readable">项目状态以记录和证据为依据。原始材料、决策、验收条件与收益分别保留；信息不足时显示待验证。</p>'
                       f'<div class="quiet">最近记录：{esc(p.get("updated_at", "未记录"))}</div>') + '</div>')
    return page(p, "index.html", p["name"], p["summary"], contents)


def roadmap(p: dict) -> str:
    body = list_card(p["milestones"], lambda m: card(m["title"],
        f'<p>{esc(m.get("description", ""))}</p><div class="divider"></div><div class="eyebrow">验收条件</div>'
        + '<ul>' + ''.join(f'<li>{esc(c)}</li>' for c in m.get("criteria", [])) + '</ul>'
        + f'<div class="quiet">关联证据：{esc(", ".join(m.get("evidence_ids", [])) or "尚无")}</div>', badge(m["status"]) + f' <small>{esc(m["id"])}</small>'))
    return page(p, "roadmap.html", "路线图与里程碑", "长期方向有启动条件，当前阶段有可核验的完成条件。", body)


def work(p: dict) -> str:
    body = list_card(p["items"], lambda x: card(x["title"],
        f'<p>{esc(x.get("description", ""))}</p><div class="detail-grid">'
        f'<div><small>安排理由</small><span>{esc(x.get("reason", "未记录"))}</span></div>'
        f'<div><small>复查条件</small><span>{esc(x.get("revisit_when", "未记录"))}</span></div>'
        f'<div><small>对应里程碑</small><span>{esc(x.get("milestone_id") or "尚未安排")}</span></div>'
        f'<div><small>依赖事项</small><span>{esc(", ".join(x.get("depends_on", [])) or "无")}</span></div>'
        f'<div><small>负责人</small><span>{esc(x.get("owner", "未定"))}</span></div>'
        f'<div><small>插队代价</small><span>{esc(x.get("displaces") or "未涉及")}</span></div></div>',
        badge(x["status"]) + f' <small>{esc(TYPES.get(x["type"], x["type"]))} · {esc(x["id"])}</small>'))
    return page(p, "work.html", "事项与当前执行", "想法、问题、风险和任务分别记录；每项都能追溯安排理由。", body)


def decisions(p: dict) -> str:
    body = list_card(p["decisions"], lambda d: card(d["title"],
        f'<p class="readable">{esc(d.get("decision", ""))}</p><div class="divider"></div>'
        f'<div class="detail-grid"><div><small>决定理由</small><span>{esc(d.get("reason", ""))}</span></div>'
        f'<div><small>相关事项</small><span>{esc(", ".join(d.get("item_ids", [])) or "无")}</span></div>'
        f'<div><small>决定人</small><span>{esc(d.get("owner", "未记录"))}</span></div>'
        f'<div><small>关联证据</small><span>{esc(", ".join(d.get("evidence_ids", [])) or "无")}</span></div></div>',
        f'<small>{esc(d.get("date", ""))} · {esc(d["id"])}</small>'))
    folder = PROJECTS / p["id"]
    changes = []
    for line in (folder / "changes.jsonl").read_text(encoding="utf-8").splitlines():
        changes.append(json.loads(line))
    log = list_card(list(reversed(changes)), lambda c: row(c.get("summary", ""), c.get("reason", ""),
                                                       f'<small>{esc(c.get("actor", ""))}</small>', c.get("at", "")))
    return page(p, "decisions.html", "决策与变更", "记住为什么调整顺序，以及变更前后发生了什么。",
                '<div class="two-col">' + card("决定记录", body) + card("修改轨迹", log) + '</div>')


def evidence(p: dict) -> str:
    body = list_card(p["evidence"], lambda e: card(e["title"],
        f'<p>{esc(e.get("note", ""))}</p><div class="detail-grid">'
        f'<div><small>来源类型</small><span>{esc(e.get("kind", "未记录"))}</span></div>'
        f'<div><small>观察时间</small><span>{esc(e.get("observed_at", "未记录"))}</span></div>'
        f'<div><small>材料位置</small><span>{esc(e.get("path") or e.get("url") or "未记录")}</span></div></div>',
        badge(e["status"]) + f' <small>{esc(e["id"])}</small>'))
    pending = [m for m in p["milestones"] if m["status"] != "已验收"]
    note = card("尚待验收的里程碑", list_card(pending, lambda m: row(m["title"],
                                    "逐条核对验收条件与证据内容", badge(m["status"]), m["id"])))
    return page(p, "evidence.html", "证据与验收", "材料有来源，验收有条件；关联证据并不自动代表验收通过。", body + note)


def outcomes(p: dict) -> str:
    body = list_card(p["outcomes"], lambda o: card(o["title"],
        f'<p>{esc(o.get("expected", ""))}</p><div class="detail-grid">'
        f'<div><small>比较前基线</small><span>{esc(o.get("baseline") or "尚未采集")}</span></div>'
        f'<div><small>实际观察</small><span>{esc(o.get("observed") or "尚无使用后数据")}</span></div>'
        f'<div><small>验证方法</small><span>{esc(o.get("method") or "尚未确定")}</span></div>'
        f'<div><small>关联证据</small><span>{esc(", ".join(o.get("evidence_ids", [])) or "尚无")}</span></div></div>',
        badge(o["status"]) + f' <small>{esc(o["id"])}</small>'))
    return page(p, "outcomes.html", "交付后的收益", "预期与观察分开，改善需要在实际使用后核对。", body)


def save(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    staged = path.with_suffix(path.suffix + ".tmp")
    staged.write_text(content, encoding="utf-8")
    staged.replace(path)


def build(projects: list[tuple[Path, dict]]) -> None:
    SITE.mkdir(exist_ok=True)
    (SITE / "assets").mkdir(exist_ok=True)
    shutil.copyfile(STYLE, SITE / "assets" / "style.css")
    save(SITE / "index.html", portfolio(projects))
    builders = {"index.html": overview, "roadmap.html": roadmap, "work.html": work,
                "decisions.html": decisions, "evidence.html": evidence, "outcomes.html": outcomes}
    for _, project in projects:
        for name, builder in builders.items():
            save(SITE / project["id"] / name, builder(project))
    print(f"已生成 {1 + len(projects) * len(builders)} 个 HTML 页面：{SITE / 'index.html'}")


def init(pid: str, name: str) -> None:
    if not SLUG.fullmatch(pid):
        raise ValueError("项目 ID 应为 2–50 位小写字母、数字、短横线，且以字母开头")
    folder = PROJECTS / pid
    if folder.exists():
        raise ValueError(f"项目已存在：{pid}")
    folder.mkdir(parents=True)
    (folder / "materials").mkdir()
    now = datetime.now().astimezone().isoformat(timespec="seconds")
    data = {"id": pid, "name": name, "summary": "待补充项目背景", "phase": "待定义",
            "goal": "待定义可验证的项目目标", "scope": "待定义范围", "owner": "未定",
            "updated_at": now, "source_refs": [], "milestones": [], "items": [],
            "decisions": [], "evidence": [], "outcomes": []}
    save(folder / "project.json", json.dumps(data, ensure_ascii=False, indent=2) + "\n")
    save(folder / "changes.jsonl", json.dumps({"at": now, "actor": "workspace-cli", "source": "init command",
        "summary": "创建项目", "entity_ids": [], "reason": "用户创建空白项目"}, ensure_ascii=False) + "\n")
    print(f"已创建：{folder}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("validate", help="校验项目记录")
    sub.add_parser("build", help="校验并生成静态 HTML")
    init_cmd = sub.add_parser("init", help="创建空项目")
    init_cmd.add_argument("id")
    init_cmd.add_argument("name")
    args = parser.parse_args()
    try:
        if args.command == "init":
            init(args.id, args.name)
            return 0
        projects = load_projects()
        validate(projects)
        if args.command == "validate":
            print(f"校验通过：{len(projects)} 个项目")
        else:
            build(projects)
        return 0
    except ValueError as exc:
        print(exc, file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
