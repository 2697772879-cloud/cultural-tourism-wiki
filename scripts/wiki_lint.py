"""知识库体检：断链 / 孤儿页 / 缺视角 / 缺溯源 / 重复 / 索引漂移 / 未引用资料 / 复核队列。

用法：
    python wiki_lint.py --root wiki
    python wiki_lint.py --root wiki --out wiki/lint-report.md
    python wiki_lint.py --root wiki --stale-days 30
"""

import argparse
import difflib
import os
import re
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import (LINK_RE, REQUIRED_FIELDS, SRC_RE, count_raw, get_list,  # noqa: E402
                     iter_pages, load_config, now_str, read_text, write_text)

NON_PAGE_DOCS = {"index.md", "log.md", "_config.md", "lint-report.md", "overview.md"}


def norm(s):
    return re.sub(r"\s+", "", str(s)).lower()


def date_diff_days(d):
    try:
        return (datetime.now() - datetime.strptime(str(d)[:10], "%Y-%m-%d")).days
    except Exception:
        return -1


def lint(root, stale_days=30):
    cfg = load_config(root)
    lenses = cfg["lenses"]
    pages = iter_pages(root)

    # 建立 title/alias/stem -> rel 的解析表
    resolver = {}
    for cat, rel, title, meta, body in pages:
        stem = os.path.splitext(os.path.basename(rel))[0]
        for key in [title, stem] + get_list(meta, "aliases"):
            k = norm(key)
            if k:
                resolver.setdefault(k, rel)

    issues = {k: [] for k in
              ["frontmatter", "lens", "broken_link", "orphan", "no_source",
               "duplicate", "index_drift", "raw_unused", "stale_draft"]}
    review_queue = []

    bodies = {}
    for cat, rel, title, meta, body in pages:
        bodies[rel] = body

        # 1. frontmatter 缺字段
        missing = [f for f in REQUIRED_FIELDS
                   if f not in meta or meta.get(f) in ("", [], None)]
        if missing:
            issues["frontmatter"].append((rel, "缺字段：%s" % ", ".join(missing)))

        # 2. 缺视角章节
        heads = re.findall(r"^###\s*(.+?)\s*$", body, re.M)
        miss_lens = [l for l in lenses if not any(l in h for h in heads)]
        if miss_lens:
            issues["lens"].append((rel, "缺视角：%s" % "、".join(miss_lens)))

        # 3. 断链（index/log 之外的页面链接）
        for m in LINK_RE.finditer(body):
            target = m.group(1).strip()
            if norm(target) not in resolver:
                issues["broken_link"].append((rel, "断链 → [[%s]]" % target))

        # 4. 无溯源锚点
        if not SRC_RE.search(body):
            issues["no_source"].append((rel, "事实底座缺少 <!-- src: raw/... --> 锚点"))

        # 5. 长期 draft
        if str(meta.get("status", "")).strip() == "draft":
            d = date_diff_days(meta.get("updated") or meta.get("created"))
            if d >= stale_days:
                issues["stale_draft"].append((rel, "draft 已 %d 天未复核" % d))

        # 复核队列
        for line in body.splitlines():
            if "[需人工复核]" in line:
                review_queue.append((rel, line.strip()[:100]))
                break
        if re.search(r"⚠️\s*冲突", body):
            review_queue.append((rel, "页面标记为事实冲突"))

    # 6. 孤儿页（无其他页面入链）
    inbound = {rel: 0 for rel in bodies}
    for rel, body in bodies.items():
        for m in LINK_RE.finditer(body):
            t = norm(m.group(1).strip())
            tgt = resolver.get(t)
            if tgt and tgt != rel:
                inbound[tgt] += 1
    for rel, n in inbound.items():
        if n == 0:
            issues["orphan"].append((rel, "无入链（孤儿页）"))

    # 7. 疑似重复（标题相似度）
    titles = [(rel, title) for _, rel, title, _, _ in pages]
    for i in range(len(titles)):
        for j in range(i + 1, len(titles)):
            r = difflib.SequenceMatcher(None, titles[i][1], titles[j][1]).ratio()
            if r >= 0.85 and titles[i][1] != titles[j][1]:
                issues["duplicate"].append(
                    (titles[i][0], "与《%s》(%s) 标题相似度 %.2f"
                     % (titles[j][1], titles[j][0], r)))

    # 8. 索引漂移
    idx_path = os.path.join(root, "index.md")
    if os.path.isfile(idx_path):
        idx_text = read_text(idx_path)
        in_index = set(re.findall(r"\]\((pages/[^)]+\.md)\)", idx_text))
        actual = set(bodies.keys())
        for rel in sorted(actual - in_index):
            issues["index_drift"].append((rel, "页面存在但不在 index.md 中"))
        for rel in sorted(in_index - actual):
            issues["index_drift"].append((rel, "index.md 中有链接但页面不存在"))
    else:
        issues["index_drift"].append(("index.md", "索引文件缺失"))

    # 9. raw 未被引用
    all_text = "\n".join(bodies.values())
    if os.path.isfile(idx_path):
        all_text += read_text(idx_path)
    raw_dir = os.path.join(root, "raw")
    for sub in ("images", "texts", "files"):
        d = os.path.join(raw_dir, sub)
        if not os.path.isdir(d):
            continue
        for f in sorted(os.listdir(d)):
            if not os.path.isfile(os.path.join(d, f)):
                continue
            if os.path.basename(f) not in all_text:
                issues["raw_unused"].append(
                    ("raw/%s/%s" % (sub, f), "已存档但未被任何页面引用"))

    return cfg, pages, issues, review_queue


TITLES = {
    "frontmatter": "frontmatter 字段缺失",
    "lens": "视角章节缺失",
    "broken_link": "断链",
    "orphan": "孤儿页（无入链）",
    "no_source": "缺溯源锚点",
    "duplicate": "疑似重复条目",
    "index_drift": "索引漂移",
    "raw_unused": "原始资料未引用",
    "stale_draft": "长期未复核的 draft",
}
HIGH = {"broken_link", "no_source", "duplicate", "index_drift"}


def render_report(root, cfg, pages, issues, review_queue):
    total_issues = sum(len(v) for v in issues.values())
    lines = ["# 知识库体检报告", "",
             "- 时间：%s" % now_str(),
             "- 知识库：%s" % os.path.abspath(root),
             "- 页面总数：%d ｜ 原始资料：%d ｜ 视角配置：%s"
             % (len(pages), count_raw(root), " / ".join(cfg["lenses"])),
             "- 结论：%s" % ("✅ 未发现问题" if total_issues == 0
                            else "⚠️ 共 %d 项需处理" % total_issues), ""]

    lines.append("## 必须处理")
    lines.append("")
    lines.append("| 级别 | 问题 | 位置 | 说明 |")
    lines.append("|---|---|---|---|")
    any_high = False
    for key in ["broken_link", "no_source", "duplicate", "index_drift", "lens",
                "frontmatter"]:
        for rel, msg in issues[key]:
            any_high = True
            lvl = "高" if key in HIGH else "中"
            lines.append("| %s | %s | %s | %s |" % (lvl, TITLES[key], rel, msg))
    if not any_high:
        lines.append("| — | 无 | — | — |")
    lines.append("")

    lines.append("## 建议处理")
    lines.append("")
    for key in ["orphan", "raw_unused", "stale_draft"]:
        if issues[key]:
            lines.append("**%s（%d）**" % (TITLES[key], len(issues[key])))
            for rel, msg in issues[key][:50]:
                lines.append("- %s — %s" % (rel, msg))
            lines.append("")
    lines.append("")

    lines.append("## 待人工复核队列")
    lines.append("")
    if review_queue:
        for rel, msg in review_queue:
            lines.append("- [ ] %s — %s" % (rel, msg))
    else:
        lines.append("- （无）")
    lines.append("")

    lines.append("## 备注")
    lines.append("")
    lines.append("- 语义层问题（跨页事实冲突、摘要失真、视角超出事实底座、知识缺口）"
                 "需由 LLM 读页面判断，本报告只覆盖结构问题。")
    lines.append("- 修复后请重跑：`python wiki_lint.py --root %s`" % root)
    lines.append("")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default="wiki")
    ap.add_argument("--out", default=None, help="报告写入路径")
    ap.add_argument("--stale-days", type=int, default=30)
    args = ap.parse_args()

    if not os.path.isdir(args.root):
        print("错误：目录不存在 %s（先跑 wiki_init.py）" % args.root)
        sys.exit(1)

    cfg, pages, issues, review_queue = lint(args.root, args.stale_days)
    report = render_report(args.root, cfg, pages, issues, review_queue)
    print(report)
    if args.out:
        write_text(args.out, report)
        print("\n报告已写入：%s" % args.out)


if __name__ == "__main__":
    main()
