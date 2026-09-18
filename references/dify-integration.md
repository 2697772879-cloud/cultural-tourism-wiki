# Dify 集成指南

## 1. 打包上传

Dify 的 Agent Skill 遵循 Anthropic Skills 规范：**zip 包根目录必须含 `SKILL.md`**。

```bash
cd ~/.workbuddy/skills/cultural-tourism-wiki
zip -r 文旅知识库摄取与多视角生成-Skill.zip SKILL.md references/ assets/ scripts/
```

- 上传位置：Dify → Agent 应用 → 技能 → 上传（< 50MB）。
- 上传后在 Agent 系统提示词里加一句：
  > 当用户上传文旅资料（图片 / 文本 / PDF / 链接）或要求整理知识库、生成多视角解读时，使用「文旅知识库摄取与多视角生成」技能。
- **渐进式披露**：SKILL.md 保持精简，细节放 `references/`。若发现 Dify 侧不会自动读子文件，在 SKILL.md 顶部补一句「执行 ingest 前先读 `references/ingest-workflow.md` 与 `references/schema.md`」。
- **沙箱**：`scripts/` 里的 Python 脚本在 Dify 沙箱内可用（纯标准库，无第三方依赖）；若沙箱无 Python，退化到 `mkdir` / `cat` / `echo >>` 的 shell 写法，索引与体检改由 LLM 手工维护（此时务必每次 ingest 后同步 `index.md`）。

## 2. 知识库存放位置

- **沙箱内路径**：建议 `/home/sandbox/wiki/`（Dify 沙箱默认可写），通过环境变量或 Agent 提示词固定。
- **持久化**：Dify 沙箱约 20GB，但**实例重建可能丢数据**。两个保险：
  1. 每次 ingest 后把 `wiki/` 打成 tar 上传 Dify 文件存储；
  2. 定期导出 `wiki/` 到本地或用 Git 做版本管理（推荐，改动可 diff、可回滚）。
- **不要在 Skill 里写绝对路径**，路径统一从 `wiki/_config.md` 或用户当次指令读取。

## 3. 图片方案（关键）

Skill 不能直接「推送」图片，但生成的 Markdown 图片链接会被前端渲染。

**推荐：Dify 内置文件服务（方案一）**

1. 管理员把实拍图嵌入 Word（.docx），上传 Dify 知识库；
2. Dify 自动抽取 JPG/PNG（单张 < 2MB）并生成可访问 URL；
3. 这些 URL 以 `![描述](URL)` 形式留在分段文本里；
4. 知识库启用**多模态嵌入模型**（带 Vision 图标）后，图片本身也被向量化，支持以图搜图。

**备选：外部对象存储（MinIO / OSS）**——图片大、量多、需独立管理时迁移。

**处理流程**：原图入 `raw/images/`（只读）→ 压缩（长边 ≤1600px、100–350KB）→ 上传取 URL → 页面 `## 图片` 节引用 → Chatflow 检索到该页时前端自动渲染。

> 注意：Wiki 页面里同时保留 `raw/images/` 的**相对路径**（用于本地可追溯）与 **HTTP URL**（用于线上渲染）。Dify 只认后者。

## 4. 与多视角问答 Chatflow 的衔接

分工：**Skill 负责生产，Chatflow 负责消费。**

| 环节 | 负责方 | 产物 |
|---|---|---|
| 摄取、编译、建页、生成三视角 | Skill（Agent） | `wiki/pages/*.md` |
| 索引与日志 | Skill + 脚本 | `index.md` / `log.md` |
| 用户选择视角、检索、作答、展示图片 | Chatflow | 对话输出 |

**入库建议**：把 `wiki/pages/` 下的 md 按「页面」为单位上传 Dify 知识库（一页一段，不要整库一个文件），这样检索命中粒度 = 一个条目，且三视角同处一段，用户选视角时不会被切散。

**回存闭环**：Chatflow 里产生的好答案（对比分析、新发现的时间线）应回存为新的 Wiki 页面——这正是 LLM Wiki「探索也复利」的要点。可在 Chatflow 末尾加一个分支，把用户点赞/标记为有价值的回答写入 `pages/topics/`。

## 5. 成本控制

| 措施 | 做法 |
|---|---|
| 分阶段 | 先用轻量模型出「原始内容摘要 + 分类建议」，确认后再用高质量模型生成页面与三视角 |
| 批量降配 | 批量时视角长度减半（儿童 100 / 历史 300 / 专家 400 字），重点条目事后精修 |
| 图片压缩 | 上传前压到长边 ≤1600px，减少视觉模型成本 |
| 缓存 | 重复意图/重复查询启用缓存 |
| 上下文裁剪 | Agent 开启对话历史摘要，避免全量历史反复入参 |
| 配额 | 为 Agent 配置 Token 配额，防意外超支 |
| 抽检 | OCR 结果与历史年代采用抽检而非全检，标 `[需人工复核]` 交人工 |
| 审计 | 每月统计调用量与费用，跑一次 lint 清掉重复页面 |

## 6. 试点检查清单（一期 2 周）

- [ ] Skill 上传成功，Agent 能正确识别「收录这张照片」意图
- [ ] 图片落盘命名规范，`raw/` 未被修改
- [ ] 一份资料能触发 5+ 页面更新，而非只建一页
- [ ] 三视角内容事实一致、无编造
- [ ] `index.md` 与实际文件一致（跑 `wiki_index.py` 验证）
- [ ] 图片能在 Chatflow 前端渲染出来
- [ ] `log.md` 可 grep，`[需人工复核]` 项被正确标记
- [ ] 跑一次 `wiki_lint.py`，问题数可接受
