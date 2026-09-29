# 电子书工厂套件

> WorkBuddy Skill · 屋里涛说

从「一句主题」或「一个对标店铺」批量生产可上架的知识付费电子书（PDF + HTML 原稿）。两个技能是**配合**关系：一个造引擎，一个跑批量。

## 技能清单

| 技能 | 说明 |
|---|---|
| **ebook-factory** · 电子书工厂（引擎） | 主题 / 卖点文案 / 章节大纲 → 排版精美的 PDF 电子书。含系列骨架、写作规范、全书大纲、多 Agent 并行写长稿、质检、md→HTML→Edge 打印 PDF、视觉验证。自带「××开窍」系列统一视觉。 |
| **ebook-replica-batch** · 复刻批量（产线） | 从对标店铺想要榜 / 对标商品标题批量生成 N 本，专治两个硬问题：**跨书雷同**（双通道去重：硬套话归零 + 软修辞分层）和**结构破损**（标题粘连、引号不配对）。 |

## 工作流

```
ebook-factory（构建器 + 视觉 + 写作规范）
        │  提供 build_book.py / 六段式 / series_visual_guide
        ▼
ebook-replica-batch（批量 + 复刻 + 跨书去重 + 收口质检）
        │
        ▼
一批可上架的 PDF 电子书
```


## 安装

把 `skills/` 下的技能目录拷贝到 WorkBuddy 的技能目录：

```bash
cp -r skills/* ~/.workbuddy/skills/
```

Windows PowerShell：

```powershell
Copy-Item .\skills\* "$env:USERPROFILE\.workbuddy\skills\" -Recurse -Force
```

重启 WorkBuddy 后，技能列表即可看到。

## 使用要点

- `ebook-replica-batch` 复用 `ebook-factory` 的构建器与写作规范，所以两者放同一仓库。
- 首次做系列时先用 `ebook-factory` 确立视觉与规范，之后批量走 `ebook-replica-batch`。

## 环境依赖

- Python 3.13
- Microsoft Edge（PDF 打印）

## 目录规范

```
ebook-factory-suite/
└── skills/
    ├── ebook-factory/
    ├── ebook-replica-batch/
```

每个技能遵循统一结构：`SKILL.md`（必需，含 name/description frontmatter）+ `scripts/`（可选）+ `references/`（可选）。

---

## License

MIT — 随意取用、修改、二次分发。
