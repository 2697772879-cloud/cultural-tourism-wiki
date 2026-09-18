"""文旅知识库 Skill 公共工具（纯标准库，Windows / Dify 沙箱均可运行）。"""

import os
import re
import sys
from datetime import datetime

try:  # Windows 控制台中文输出
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

# 默认分类（目录名 -> 中文名 + frontmatter type）
DEFAULT_CATEGORIES = [
    ("entities", "实体", "entity"),
    ("events", "事件", "event"),
    ("buildings", "建筑", "building"),
    ("people", "人物", "person"),
    ("topics", "主题", "topic"),
]

DEFAULT_LENSES = ["儿童", "历史", "专家"]
DEFAULT_PERSONA = "专属文史导游"

REQUIRED_FIELDS = ["title", "type", "tags", "status", "confidence", "sources",
                   "created", "updated"]

FM_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.S)
LINK_RE = re.compile(r"\[\[([^\]|]+?)(?:\|([^\]]+?))?\]\]")
SRC_RE = re.compile(r"<!--\s*src:\s*([^\s>]+?)\s*-->")


def read_text(path):
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        return f.read()


def write_text(path, text):
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def parse_frontmatter(text):
    """极简 YAML frontmatter 解析：支持 key: value、key: [a, b]、key: + '- item' 列表。"""
    m = FM_RE.match(text)
    if not m:
        return {}, text
    raw = m.group(1)
    body = text[m.end():]
    data = {}
    cur_key = None
    for line in raw.splitlines():
        if not line.strip() or line.strip().startswith("#"):
            continue
        if re.match(r"^\s*-\s+", line):
            if cur_key:
                data.setdefault(cur_key, [])
                if isinstance(data[cur_key], list):
                    data[cur_key].append(re.sub(r"^\s*-\s+", "", line).strip())
            continue
        if ":" in line:
            k, v = line.split(":", 1)
            k = k.strip()
            v = v.strip()
            cur_key = k
            if v.startswith("[") and v.endswith("]"):
                inner = v[1:-1].strip()
                data[k] = [x.strip() for x in inner.split(",") if x.strip()]
            elif v == "":
                data[k] = []
            else:
                data[k] = v
    return data, body


def get_list(meta, key):
    v = meta.get(key, [])
    if isinstance(v, list):
        return v
    return [v] if v else []


def extract_summary(body, limit=60):
    """取 ## 摘要 下第一段；没有摘要节则取第一个非空段落。"""
    m = re.search(r"^##\s*摘要\s*$\s*\n(.*?)(?=^##\s|\Z)", body, re.S | re.M)
    chunk = m.group(1) if m else body
    for para in chunk.splitlines():
        p = para.strip()
        if not p or p.startswith(">") or p.startswith("#") or p.startswith("---"):
            continue
        p = re.sub(r"\[\[([^\]|]+?)(?:\|([^\]]+?))?\]\]", r"\1", p)
        p = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", p).strip()
        if not p:
            continue
        return (p[:limit] + "…") if len(p) > limit else p
    return "（暂无摘要）"


def iter_pages(root):
    """返回 [(category_dir, rel_path_from_root, title, meta, body)]"""
    pages_dir = os.path.join(root, "pages")
    out = []
    if not os.path.isdir(pages_dir):
        return out
    for cat in sorted(os.listdir(pages_dir)):
        cat_dir = os.path.join(pages_dir, cat)
        if not os.path.isdir(cat_dir):
            continue
        for name in sorted(os.listdir(cat_dir)):
            if not name.lower().endswith(".md"):
                continue
            full = os.path.join(cat_dir, name)
            text = read_text(full)
            meta, body = parse_frontmatter(text)
            title = meta.get("title") or os.path.splitext(name)[0]
            rel = "pages/%s/%s" % (cat, name)
            out.append((cat, rel, title, meta, body))
    return out


def load_config(root):
    """读 wiki/_config.md，缺项用默认值。"""
    cfg_path = os.path.join(root, "_config.md")
    cfg = {
        "project": "文旅知识库",
        "persona": DEFAULT_PERSONA,
        "lenses": list(DEFAULT_LENSES),
        "categories": [c[0] for c in DEFAULT_CATEGORIES],
        "category_labels": {c[0]: c[1] for c in DEFAULT_CATEGORIES},
        "category_types": {c[0]: c[2] for c in DEFAULT_CATEGORIES},
    }
    if os.path.isfile(cfg_path):
        meta, _ = parse_frontmatter(read_text(cfg_path))
        if meta.get("project"):
            cfg["project"] = meta["project"]
        if meta.get("persona"):
            cfg["persona"] = meta["persona"]
        lenses = get_list(meta, "lenses")
        if lenses:
            cfg["lenses"] = [str(x) for x in lenses]
        cats = get_list(meta, "categories")
        if cats:
            cfg["categories"] = [str(x) for x in cats]
    return cfg


def count_raw(root):
    total = 0
    raw_dir = os.path.join(root, "raw")
    for sub in ("images", "texts", "files"):
        d = os.path.join(raw_dir, sub)
        if os.path.isdir(d):
            total += len([f for f in os.listdir(d)
                          if os.path.isfile(os.path.join(d, f))])
    return total


def now_str():
    return datetime.now().strftime("%Y-%m-%d %H:%M")
