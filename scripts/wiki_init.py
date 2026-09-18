"""初始化文旅知识库骨架。

用法：
    python wiki_init.py --root wiki --project "思豪大酒店"
    python wiki_init.py --root /home/sandbox/wiki --project "思豪大酒店" \
        --persona "思豪大酒店专属文史导游" --lenses 儿童 历史 专家
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import (DEFAULT_CATEGORIES, now_str, write_text)  # noqa: E402

DIRS = [
    "raw/images", "raw/texts", "raw/files",
    "pages/entities", "pages/events", "pages/buildings",
    "pages/people", "pages/topics",
]


def build_config(project, persona, lenses):
    return """---
project: {project}
persona: {persona}
lenses: [{lenses}]
categories: [{cats}]
created: {date}
---

# 知识库配置

本文件是**项目专属约定**，优先级高于 Skill 默认设置。

| 字段 | 值 | 说明 |
|---|---|---|
| project | {project} | 项目名称，用于视角话术 |
| persona | {persona} | 人称，如「思豪大酒店专属文史导游」 |
| lenses | {lenses} | 视角集合，决定每个页面要生成哪几个视角 |
| categories | {cats} | 页面分类目录 |

## 自定义视角

如需新增视角（如长者视角、研学任务），在此补充规范：

```markdown
### XX视角
- 目标受众：
- 语气：
- 结构：
- 开头示例：
```

## 本项目特殊约定

（由维护者在此累积，例如：年代的写法统一用公元纪年；人名首次出现必须带生卒年；
引文必须标注出处页码。）
""".format(
    project=project, persona=persona, lenses=", ".join(lenses),
    cats=", ".join(c[0] for c in DEFAULT_CATEGORIES),
    date=now_str()[:10],
)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default="wiki", help="知识库根目录")
    ap.add_argument("--project", default="文旅知识库")
    ap.add_argument("--persona", default="专属文史导游")
    ap.add_argument("--lenses", nargs="*", default=["儿童", "历史", "专家"])
    args = ap.parse_args()

    root = args.root
    created, skipped = [], []
    for d in DIRS:
        p = os.path.join(root, d)
        if os.path.isdir(p):
            skipped.append(d)
        else:
            os.makedirs(p, exist_ok=True)
            created.append(d)

    idx = os.path.join(root, "index.md")
    if not os.path.isfile(idx):
        write_text(idx, "# %s 知识库索引\n\n> 由 `wiki_index.py` 自动重建。\n\n"
                        "（暂无页面，先摄取一份资料吧）\n" % args.project)
        created.append("index.md")

    log = os.path.join(root, "log.md")
    if not os.path.isfile(log):
        write_text(log, "# 操作日志\n\n> append-only，只追加不修改。\n\n"
                        "## [%s] init | 初始化知识库\n- 项目：%s\n- 视角：%s\n"
                        % (now_str(), args.project, " / ".join(args.lenses)))
        created.append("log.md")

    cfg = os.path.join(root, "_config.md")
    if not os.path.isfile(cfg):
        write_text(cfg, build_config(args.project, args.persona, args.lenses))
        created.append("_config.md")

    print("知识库根目录：%s" % os.path.abspath(root))
    print("新建：%s" % (", ".join(created) if created else "（无）"))
    print("已存在：%s" % (", ".join(skipped) if skipped else "（无）"))
    print("下一步：把资料放进 %s/raw/，然后执行 ingest。" % root)


if __name__ == "__main__":
    main()
