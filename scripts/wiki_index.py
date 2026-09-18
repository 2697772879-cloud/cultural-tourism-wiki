"""重建 wiki/index.md：按分类列出所有页面 + 一句话摘要 + 统计表。

用法：
    python wiki_index.py --root wiki
    python wiki_index.py --root wiki --dry-run   # 只打印不写入
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import (count_raw, extract_summary, iter_pages, load_config,  # noqa: E402
                     now_str, write_text)


def build_index(root):
    cfg = load_config(root)
    pages = iter_pages(root)
    labels = cfg["category_labels"]
    order = cfg["categories"]

    grouped = {c: [] for c in order}
    for cat, rel, title, meta, body in pages:
        grouped.setdefault(cat, []).append((title, rel, extract_summary(body)))
    for c in grouped:
        grouped[c].sort(key=lambda x: x[0])

    lines = ["# %s 知识库索引" % cfg["project"], "",
             "> 本文件由 `wiki_index.py` 自动重建，请勿手工编辑。",
             "> 更新时间：%s ｜ 页面 %d ｜ 原始资料 %d"
             % (now_str(), len(pages), count_raw(root)), ""]

    for cat in order:
        if cat not in grouped or not grouped[cat]:
            continue
        lines.append("## %s（%s）" % (labels.get(cat, cat), cat))
        for title, rel, summary in grouped[cat]:
            lines.append("- [%s](%s) — %s" % (title, rel, summary))
        lines.append("")

    # 未归类（目录不在配置里）
    extra = [c for c in grouped if c not in order and grouped[c]]
    if extra:
        lines.append("## 其他")
        for cat in extra:
            for title, rel, summary in grouped[cat]:
                lines.append("- [%s](%s) — %s" % (title, rel, summary))
        lines.append("")

    lens_n = len(cfg["lenses"])
    lines.append("## 统计")
    lines.append("")
    lines.append("| 分类 | 页面数 | 视角数 |")
    lines.append("|---|---|---|")
    total = 0
    for cat in order:
        n = len(grouped.get(cat, []))
        if n:
            lines.append("| %s | %d | %d |" % (labels.get(cat, cat), n, n * lens_n))
            total += n
    for cat in extra:
        n = len(grouped[cat])
        lines.append("| %s | %d | %d |" % (cat, n, n * lens_n))
        total += n
    lines.append("| **合计** | **%d** | **%d** |" % (total, total * lens_n))
    lines.append("")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default="wiki")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if not os.path.isdir(args.root):
        print("错误：目录不存在 %s（先跑 wiki_init.py）" % args.root)
        sys.exit(1)

    text = build_index(args.root)
    if args.dry_run:
        print(text)
        return
    write_text(os.path.join(args.root, "index.md"), text)
    n = len(iter_pages(args.root))
    print("index.md 已重建：%s ｜ 页面 %d 个" % (os.path.join(args.root, "index.md"), n))


if __name__ == "__main__":
    main()
