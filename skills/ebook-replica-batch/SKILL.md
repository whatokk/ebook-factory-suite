---
name: ebook-replica-batch
description: 复刻批量化作书流水线——从「闲鱼对标店铺 / 对标商品标题+文案」批量生成可上架的多本知识付费电子书（PDF+HTML）。当用户要做「按某个店铺的想要榜批量复刻 N 本电子书、一批 20 本左右的知识付费书、多本同风格书的批量生产+去重+质检、把对标账号的高浏览商品做成书、复刻电子书（一批多本）」时使用。覆盖：标题→大纲、多 Agent/自写正文、双通道跨书去重（硬套话归零 + 软修辞分层）、结构审计、md→HTML→Edge 出 PDF、合集总览页。与 ebook-factory 协作：构建/视觉/写作规范沿用 ebook-factory，本 skill 负责「批量 + 复刻 + 跨书去重 + 收口质检」这一段。
agent_created: true
---

# ebook-replica-batch：复刻批量化作书流水线

把「一个对标店铺的想要榜 / 一组对标商品标题+文案」变成「一批排版精美、可直接上架的 PDF 电子书」。
专门解决 **一批多本** 时的两个硬问题：**跨书雷同**（买家买两本就看出撞车）和 **结构破损**（标题粘连、引号不配对）。

> 构建器、封面视觉、通用写作六段式来自 `ebook-factory`（其 `scripts/build_book.py`、`references/writing_guide.md`、`references/series_visual_guide.md`）。本 skill 聚焦「批量复刻 + 跨书去重 + 收口质检」。两者配合用。

## 何时使用

- 用户要「按某店铺想要榜复刻 N 本」「一批 20 本知识付费书」「多本同风格的批量生产」
- 用户已有一组对标标题/文案，要据此写成多本书
- 一批书写完后要「去重 + 质检 + 出总览页」再上架
- 不适用：单本书、纯翻译、营销短文

## 核心纪律（先记住这三条）

1. **字数达标 ≠ 内容不雷同**。一堆书每本都达标，但尾段套话每篇重复 18~29 次，买家买两本就退款。批量出书**必跑双通道去重**。
2. **硬套话归零，软修辞只控密度**。把「自然行文词」和「固定公式句」分开处理，前者强行替换会破坏文风。
3. **并发写 Agent 会撞车**。同一文件被两个 Agent 同时 Edit 会静默覆盖（只有一处落盘）。一本书只交给一个写入者；脚本写入时断言目标串命中数 == 1，写后 grep 自证。

## 流水线（按序执行）

### 1. 立项与目录

- 每本书一个目录：`<批名>/NN_书名/`，含 `chapters/`、`assets/`、`config.json`。
- 复制 `scripts/build_book.py`（或 ebook-factory 的 `build_book_multistyle.py`）到每本书目录，复制 `references/writing_guide.md` → `WRITING_GUIDE.md`。
- 批次根目录放 `qc.py` / `final_verify.py` / `dupcheck_fuzzy.py` / `dupcheck.py` / `gen_overview.py`，它们都基于「自身所在目录」扫描 `NN_*`，复制进批次目录即可运行。

### 2. 写大纲 `OUTLINE.md`（每本一份）

- 每本结构：**序言(00_preface) + 7 章(01~07) + 结语(08_afterword)**，共 9 个章节文件。
- 章节轨道 `toc_track` **因店而异**（见 `references/store_tracks.md` 四店轨道表），写进 `config.json`。`qc.py` 据此动态推导应有的章节清单，**不硬编码骨架**。
- 每章 6~9 小节；每节一句「认知翻转」式核心结论（多 Agent 不跑偏的关键）。

### 3. 写正文（多 Agent 或自写）

- 派 Agent：每台负责 2~4 章，prompt 自包含（角色+必须读 WRITING_GUIDE/序言/OUTLINE+每节核心结论+输出文件名）。**并发上限 2~4 路**，8 路必撞 429。
- Agent 限流失败 → 主 Agent 按规范与大纲**自己直接写**剩余章兜底，不阻塞。
- 每节按 `writing_guide.md` 六段式（结论句→痛点场景→底层逻辑→方法/话术模板→场景演练→收束），每节 ≥1 个「」话术模板。

### 4. 双通道跨书去重（批量出书的核心，必跑）

跑 `dupcheck_fuzzy.py`（阈值 K=4）与 `final_verify.py`：

- **通道一（精确）**：同一句（≥12 字）出现在 ≥2 本 → **必然缺陷**，必须清零（署名行 `加微信…` 豁免）。
- **通道二（模糊）**：句级 **7~9 字共享片段**出现在 ≥4 本 → 必须处理（10 字以上天然为 0，说明雷同只发生在 7~9 字短搭配层）。
- **硬套话 vs 软修辞分层**（关键方法论，见 `references/store_tracks.md` 第二节）：
  - **硬套话**（固定公式，必须归零）：章节预告、道具复用、话术引导、收束套话。用正则族抓取变体（不要字面串，否则漏报「前面几章讲的是」这类）。
  - **软修辞**（自然行文，只控密度、不要求归零）：「你有没有…」「很多人」等汉语最常用词，全库几百处属正常，强行替换反而破坏自然度。
- **道具载体逐本差异化**：杜绝「手机备忘录」被 10+ 本共用。给每本分配不同载体（微信收藏/便利贴/小账本/白板…见分配表）。
- 自然汉语搭配（对照句式「不是能力问题，是…」、引语框「他跟我说："…"」等）跨 4~5 本但每处句意不同 → 列入 `NATURAL` 白名单（带证据），门禁只拦**未判定**项。

### 5. 结构审计（180 个章节文件只读，收口前必做）

逐本查 5 项，全为机械结构缺陷（见 `final_verify.py` 思路与 A2 审计口径）：
1. **标题与正文粘连**：`## x.y 标题`后无换行直接接正文 → 正文会用大字渲染，拆成「标题行+空行+正文段」。
2. **`**` 粗体未闭合**：成对计数应为偶数。
3. **「」引号不配对**：每文件「与」数相等（注意跨行引用块是正常写法）。
4. **小节编号重号/跳号**：`## N.M`，M 同章内从 1 连续、无重无跳。
5. **章名与 `config.json` 的 `toc_track` 一致**：`00_preface` + `01~07_<轨道>` + `08_afterword`。

### 6. 出 PDF + 总览页

- 改每本 `config.json` 书名/署名/`cover_style`(gold_dark/vintage/minimal/book3d)，`python build_book.py`（读 chapters→HTML→Edge headless `--print-to-pdf`）。
- 改了正文后**必须重建该本 PDF**；整批收口后全量重建。
- `python gen_overview.py` 由脚本从磁盘实算总字数/页数/话术/禁用词，生成 `<批名>合集总览.html`（**绝不手填统计**；字数口径=非空白字符数，对齐 `qc.py`）。

### 7. 提取封面图（上架用）

封面是**嵌在每本 HTML 里的 `<section class="cover …">` 区块**（纯 CSS 渐变/网格渲染，**不是独立图片文件**，`assets/` 下没有任何封面位图）。上架需要独立封面图时，跑 `extract_covers.py`：

- 逻辑：抽 `cover` 区块 + 原 `<style>` → 生成**仅含封面**的独立 HTML（白底、固定 A4 逻辑尺寸 794×1123）→ Edge headless `--force-device-scale-factor=2` 截图 → 得 1588×2246 的 A4@2x PNG。
- 输出：`<批名>/封面/NN_书名.png`，20 本一本一张。
- 兼容四风格（cv-gold / cv-vin / cv-min / cv-3d，各 5 本）：因为样式随书内嵌，抽哪本用哪本的 `<style>` 即可，无需按风格分支。
- 核验：PNG 尺寸应统一 `1588×2246`；文件大小随风格浮动（cv-gold≈1.2MB、cv-vin≈2.7MB、cv-min≈90KB、cv-3d≈1.5MB）——**cv-min 是浅底扁平设计，90KB 属正常**，不要误判为空白；可解码 IHDR 校尺寸 + 采样色数（>8 即非空白）自证。
- 暂存目录**放项目外**（如 `D:\_wb_cover_scratch`）并**全局复用单一 Edge profile**，避免在交付目录产生几百个 Edge profile 文件。

### 8. 收口终验

跑 `final_verify.py` 应全部 ✔：书籍数、无缺章、每本≥3万、12 禁词=0、套话残留=0、精确句跨书重复仅署名行、7/8 字跨书片段无未判定项、PDF 全部最新。再 `qc.py` 独立复核（20/20 达标）。

## 关键命令（本机 Windows）

```bash
# 终验（收口前跑一次，只读）
python final_verify.py
# 双通道去重（只读，K=4）
python dupcheck_fuzzy.py 4
# 精确句去重（只读）
python dupcheck.py
# 权威质检口径（磁盘为准，不采信写手汇报）
python qc.py
# 全量重建 PDF（整批收口后）
# 把 scripts/rebuild_all.py 复制进批次目录运行，或逐本 python build_book.py
# 总览页
python gen_overview.py
# 提取封面图（上架用，批量出 20 张 A4 PNG）
python extract_covers.py
```

Edge 中文路径用正斜杠 `file:///D:/xxx/book.html`；`--headless=new` 才出图；`--user-data-dir` 给项目内独立临时目录，避免与运行中的 Edge 冲突。

## 技术坑位清单（踩过，务必规避）

1. **同一文件被多个 Agent 并发 Edit 会静默覆盖**：只有一处落盘，其余静默丢失。一本书单写入者；脚本写入 +「断言命中数==1」才写盘 + 落盘后 grep 自证。
2. **Edit 串烧陷阱**：同一消息对同一文件连发多个 Edit 互相覆盖，每个都报 Success 但只有一处生效。改用脚本批量写。
3. **硬套话字面串漏报**：正文是「前面几章讲的是」「判断标准特别清楚」等变体，字面串抓不到。改用正则族（如 `前面[一二三四五六七八九十]+[章篇]讲的是`、`判断标准(很简单|只有一|其实很简单|特别清楚)`）。
4. **总览页字数口径**：手填会差 10 万字级（579,231 vs 681,346）。必须脚本实算，口径 = 非空白字符数（对齐 `qc.py`）。
5. **PDF 页数**：无 pypdf 时用字节级 `/Type\s*/Page(?![s])` 兜底统计。
6. **标题粘连会让正文用大字渲染**：`## x.y 标题正文…` 里正文被当标题，拆行后页数也会变。修粘连用「标题行+空行+正文段」。
7. **中文路径/编码**：Windows 下 Python 脚本给含非 GBK 字段用 `\u300c` 转义或 `PYTHONUTF8=1`；检测「」用 `\u300c/\u300d`。
8. **Agent 限流 429**：并发 2~4 路，失败即主 Agent 兜底自写。
9. **署名行豁免**：`加微信…` 出现在每本结尾，去重时作为署名白名单豁免，不算跨书重复。
10. **在交付目录里删几百个临时文件会被安全钩子拦下**：Edge `--user-data-dir` 一个 profile 就有几百个文件，`shutil.rmtree` 会触发「批量删除需确认」而中断整个脚本。**根因规避**：暂存目录放项目外 + profile 全局复用一份 + 脚本内不做 rmtree（逐文件覆盖，或干脆不清理）。

## 配套脚本（scripts/）

- `qc.py` — 权威质检：字数(非空白字符)/章节数/「」数/12 禁词/PDF 新旧/缺章；章节清单由 `config.json` 的 `toc_track` 推导。
- `final_verify.py` — **收官终验**：基础指标 + 硬套话(正则族) + 软修辞密度 + 跨书重复(精确句+7~9 字片段, 含 GENERIC/NATURAL 白名单) + PDF 新旧 + 总判定。
- `dupcheck_fuzzy.py` — **双通道去重**：精确句(≥12 字) + 7~9 字共享片段(≥K 本)，只读。
- `dupcheck.py` — 精确通道句级去重，输出 `_dup_report.json`。
- `build_book.py` / `build_book_multistyle.py` — md→HTML→Edge PDF 构建器（四套封面风格），沿用 ebook-factory。
- `gen_overview.py` — 合集总览页生成器（脚本实算统计）。
- `extract_covers.py` — **封面图提取**：抽 HTML 内嵌 `.cover` 区块 → 独立 HTML → Edge headless 截图，输出 `<批名>/封面/NN_书名.png`（A4@2x，兼容四风格）。

## 配套参考（references/）

- `store_tracks.md` — 四店章节轨道表 + 道具载体分配表 + 12 禁词 + 硬套话/软修辞分层明细 + 写作六段式红线。
- `writing_six_duan.md` — 复用 ebook-factory 的写作六段式与可直抄话术模板规范（摘录版，完整版见 ebook-factory/references/writing_guide.md）。
