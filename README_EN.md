# Cultural Tourism Wiki — Ingest & Multi-Lens Generation Skill

[中文](../README.md) | **English** | [Operations Manual](docs/OPERATIONS.md)

Compile scattered cultural-heritage material — old photographs, guide maps, document scans, oral history, PDFs, web pages — into a **Markdown wiki that keeps growing**, and generate **three lenses** for every entry: **Child · History · Expert**.

The method comes from Andrej Karpathy's [LLM Wiki](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f#llm-wiki):

> Knowledge is compiled once and then kept up to date, rather than being re-derived on every query.
> Obsidian is the IDE, the LLM is the programmer, the wiki is the codebase.

Conventional RAG re-assembles an answer from raw documents on every question. An LLM Wiki instead has the model **incrementally maintain one persistent structured knowledge base** — cross-references, contradictions and syntheses are already resolved — so each new source makes the whole thing thicker rather than starting over.

Built for historical hotels, museums, heritage streets and similar cultural-tourism projects. Designed for long-running, high-volume, incremental ingestion.

---

## What it solves

| Problem | How this skill handles it |
|---|---|
| Manual entry of photo/text material is slow | Drop-in archiving; OCR / vision extracts text and architectural features; raw files stay read-only and traceable |
| The same source has to be written three times | Compile once, emit Child / History / Expert automatically |
| The three versions contradict each other | Lenses are forced to derive from one shared **fact base** — they may not add facts |
| Models invent things | Every fact carries a `<!-- src: raw/... -->` provenance anchor; unsourced content cannot pass lint |
| The wiki rots as it grows | Merge-first policy, alias de-duplication, script-rebuilt index, periodic lint |
| Images never show up in answers | Pages embed `![caption](URL)`, which the front end renders |

## Quick start

```bash
# 1. Scaffold the wiki
python scripts/wiki_init.py --root wiki --project "Sihao Hotel" \
    --persona "Sihao Hotel resident history guide"

# 2. Drop sources into wiki/raw/ — images, texts, files

# 3. Let the agent ingest it (or just say "archive this source")
#    archive -> extract -> fact base -> three lenses -> index + log

# 4. Rebuild the index
python scripts/wiki_index.py --root wiki

# 5. Health check
python scripts/wiki_lint.py --root wiki --out wiki/lint-report.md
```

The scripts use the **standard library only** — no dependencies, runs as-is on Windows, Linux and the Dify sandbox.

## Layout

```
wiki/
├── _config.md      # project name, persona, lens set, categories
├── index.md        # index (script-regenerated)
├── log.md          # operation log (append-only)
├── raw/            # raw sources (read-only)
│   ├── images/  ├── texts/  └── files/
├── pages/
│   ├── entities/  events/  buildings/  people/  topics/
└── lint-report.md
```

A page is structured as: `Summary → Fact base (with src anchors) → Body → Lenses → Images → Related → Sources → Revision history`. Full template: `assets/page-template.md`.

## Commands

| Command | What it does |
|---|---|
| `/wiki init` | Scaffold a new wiki |
| `/wiki ingest` | Ingest one source |
| `/wiki lens <page>` | Rewrite one lens only, leaving the fact base untouched |
| `/wiki query <question>` | Answer from the wiki; good answers can be saved back as pages |
| `/wiki lint` | Health check |

Natural phrasing works too: “archive this photo”, “write a kids version of the clock tower”, “check the knowledge base”.

## Use with Dify

`SKILL.md` at the repo root follows the Anthropic Skills spec, so it can be zipped and uploaded directly:

```bash
zip -r cultural-tourism-wiki-skill.zip SKILL.md references/ assets/ scripts/ docs/
```

Upload at Dify → Agent → Skills, then add a trigger sentence to the agent's system prompt. Full details — image handling, sandbox persistence, Chatflow wiring, cost control, pilot checklist — are in [`references/dify-integration.md`](references/dify-integration.md) and [`docs/OPERATIONS.md`](docs/OPERATIONS.md).

## Repository contents

| Path | Contents |
|---|---|
| `SKILL.md` | Main entry point: three-layer architecture, command routing, ingest flow, seven hard rules |
| `README.md` / `README_EN.md` | Chinese / English introduction |
| `docs/OPERATIONS.md` | **English operations manual**: install, ingest procedure, merge rules, scripts, Dify notes, troubleshooting |
| `references/schema.md` | Page schema, frontmatter fields, taxonomy, naming, provenance discipline |
| `references/lenses.md` | Lens generation rules and consistency self-check |
| `references/ingest-workflow.md` | The seven ingest steps, merge decision tree, idempotency, batch strategy |
| `references/lint.md` | Health-check list and report format |
| `references/dify-integration.md` | Dify integration guide |
| `assets/` | `page` / `index` / `log` templates |
| `scripts/` | `wiki_init.py`, `wiki_index.py`, `wiki_lint.py` (pure standard library) |

## Customising

Project-specific conventions — project name, persona, lens set, categories, house style — go into `wiki/_config.md`, **not** into the skill. One skill then serves many projects. Need a fourth lens (senior visitors, study tasks)? Add it to `lenses` in `_config.md` and document it under “自定义视角”.

## License

MIT — see [`LICENSE`](LICENSE).
