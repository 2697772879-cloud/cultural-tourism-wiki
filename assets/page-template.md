# 页面模板（复制后填写）

````markdown
---
title: 页面标题
type: entity
tags: [标签1, 标签2]
status: draft
confidence: medium
aliases: []
sources:
  - raw/images/YYYYMMDD-HHMMSS-xxx.jpg
created: YYYY-MM-DD
updated: YYYY-MM-DD
---

# 页面标题

## 摘要
一句话概括（index.md 会抓这一段）。

## 事实底座
> 本页全部内容的唯一证据来源。先写这里，再写正文和视角。

- 事实一，细节照抄原文 <!-- src: raw/texts/xxxx.md -->
- 事实二 <!-- src: raw/images/xxxx.jpg --> `[需人工复核]`

推断（非事实，属 LLM 拼接/常识补全）：
- [推断] ……

## 正文
分点或分段展开，保留全部细节：年代、地址、人名、构件、尺寸、价格、引文。

## 多视角解读

### 儿童视角
小朋友，你好呀！下面为你讲讲……

1. ……
2. ……
3. ……

### 历史视角
你好，我是{persona}，下面为你从历史角度解答：

- ……

### 专家视角
你好，我是{persona}，下面为你提供专业分析：

- ……

**边界与局限**：……

## 图片
![画面描述](https://.../xxx.jpg)

## 关联条目
- [[相关页面1]]
- [[相关页面2]]

## 原始资料
- raw/images/YYYYMMDD-HHMMSS-xxx.jpg（用户上传，YYYY-MM-DD）

## 修订记录
- YYYY-MM-DD 创建，来源 raw/images/xxxx.jpg
````

## 填写要点

1. `{persona}` 替换为 `_config.md` 中的人设（默认「思豪大酒店专属文史导游」）。
2. `type` 取 `entity | event | building | person | topic` 之一，决定落哪个目录。
3. **先写事实底座再写正文**，视角最后写。
4. 无图片时删掉 `## 图片` 整节，不要留空节。
5. 每条事实挂 `<!-- src: raw/... -->` 锚点，推断单独列并标 `[推断]`。
