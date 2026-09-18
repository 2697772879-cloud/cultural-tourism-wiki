# 文旅知识库摄取与多视角生成 Skill

[中文](README.md) ｜ [English](README_EN.md) ｜ [English Operations Manual](docs/OPERATIONS.md)

把零散的文旅史料（老照片 / 导览图 / 文献截图 / 口述史 / PDF / 网页）**编译**成一份可持续生长的 Markdown Wiki，并为每条知识生成 **儿童 / 历史 / 专家** 三种视角的解读。

方法论来自 Andrej Karpathy 的 [LLM Wiki](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f#llm-wiki)：

> 知识被编译一次，然后保持更新，而不是每次查询时重新推导。
> Obsidian 是 IDE，LLM 是程序员，Wiki 是代码库。

传统 RAG 每次问答都从原始文档重新拼凑；LLM Wiki 则是让 LLM **增量维护一份持久的结构化知识库**，交叉引用、矛盾标注、综合判断都已提前完成，随每份新资料持续变厚。

## 它解决什么问题

| 痛点 | 本 Skill 的做法 |
|---|---|---|
| 图文资料人工录入慢 | 落盘即归档，OCR / 视觉识别提取文字与建筑特征，原始资料只读可追溯 |
| 同一史料要写三个版本 | 一次编译，自动产出儿童 / 历史 / 专家三视角 |
| 三视角各说各话 | 强制「事实底座 → 视角」顺序，视角只能从底座生成 |
| 容易编造 | 每条事实挂 `<!-- src: raw/... -->` 溯源锚点，无出处的写不进去 |
| 知识库越用越乱 | 合并优先、别名去重、脚本重建索引、周期性体检 |
| 图片无法在问答中展示 | 页面内嵌 `![描述](URL)`，前端自动渲染 |

## 快速开始

```bash
# 1. 初始化知识库骨架
python scripts/wiki_init.py --root wiki --project "思豪大酒店" \
    --persona "思豪大酒店专属文史导游"

# 2. 把史料放进 wiki/raw/（图片 / 文本 / PDF 分别入 images、texts、files）

# 3. 让 Agent 摄取（或直接对 Agent 说「收录这份资料」）
#    → 落盘 → 识别 → 写事实底座 → 生成三视角 → 更新索引与日志

# 4. 重建索引
python scripts/wiki_index.py --root wiki

# 5. 体检
python scripts/wiki_lint.py --root wiki --out wiki/lint-report.md
```

脚本为**纯标准库**，Windows / Linux / Dify 沙箱均可直接运行，无需安装依赖。

## 目录结构

```
wiki/
├── _config.md          # 项目配置：项目名、人称、视角集合、分类
├── index.md            # 内容索引（脚本重建）
├── log.md              # 操作日志（append-only）
├── raw/                # 原始资料（只读）
│   ├── images/  ├── texts/  └── files/
├── pages/
│   ├── entities/   events/   buildings/   people/   topics/
└── lint-report.md      # 体检报告
```

页面结构：`摘要 → 事实底座（带 src 锚点）→ 正文 → 多视角解读 → 图片 → 关联条目 → 原始资料 → 修订记录`。

完整模板见 `assets/page-template.md`。

## 命令

| 命令 | 作用 |
|---|---|---|
| `/wiki init` | 初始化知识库 |
| `/wiki ingest` | 摄取一份资料 |
| `/wiki lens <页面>` | 只重写某个视角 |
| `/wiki query <问题>` | 基于知识库作答（好答案可回存为新页面） |
| `/wiki lint` | 知识库体检 |

也接受自然语言：「收录这张照片」「给钟楼写个儿童版」「检查下知识库」。

## 用于 Dify

根目录的 `SKILL.md` 符合 Anthropic Skills 规范，可直接打包上传：

```bash
zip -r 文旅知识库摄取与多视角生成-Skill.zip SKILL.md references/ assets/ scripts/ docs/
```

上传至 Dify → Agent → 技能，并在系统提示词中加入触发语。细节见 `references/dify-integration.md`（含图片方案、沙箱持久化、Chatflow 衔接、成本控制、试点验收清单）。

## 文件说明

| 路径 | 内容 |
|---|---|---|
| `SKILL.md` | 主入口：三层架构、命令路由、摄取流程、七条硬规则 |
| `README.md` / `README_EN.md` | 中文 / 英文介绍 |
| `docs/OPERATIONS.md` | **英文操作手册**：安装、摄取流程、合并规则、脚本、Dify 集成、故障排查 |
| `references/schema.md` | 分类法、frontmatter 字段、命名、溯源纪律、图片与链接规范 |
| `references/lenses.md` | 三视角生成规范与一致性自检 |
| `references/ingest-workflow.md` | 摄取七步、合并决策树、幂等、批量策略 |
| `references/lint.md` | 体检清单与报告格式 |
| `references/dify-integration.md` | Dify 集成指南 |
| `assets/` | page / index / log 三个模板 |
| `scripts/` | `wiki_init.py` `wiki_index.py` `wiki_lint.py`（纯标准库） |

## 自定义

项目专属约定（项目名、人称、视角集合、分类、特殊写法）写在 `wiki/_config.md`，**不要改 Skill 本身**。这样同一个 Skill 可以服务多个文旅项目。

## License

MIT
