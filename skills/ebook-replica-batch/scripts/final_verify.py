# -*- coding: utf-8 -*-
"""终验流水线（只读）——交付前跑一次，一次性给出全部把关指标。

用法：
    python _final_verify.py
输出：
    1. 字数 / 章节数 / 「」数 / 缺章 / 12 禁词   （对齐 qc.py 口径）
    2. 套话残留（固定搭配族，含道具复用）
    3. 跨书重复（精确句 + 7~9 字模糊片段）
    4. PDF 是否比最新章节旧
    5. 总判定
"""
import os, re, glob, json
from collections import defaultdict

ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)

BAN = ["首先", "其次", "最后", "综上所述", "总而言之", "不难发现",
       "众所周知", "相信通过", "一方面", "另一方面", "值得注意的是", "在这个时代"]

# 固定套话族（正则，覆盖变体）。'判断标准' 单独出现属正常中文，故只匹配其固定搭配。
# 教训：不要用字面串——正文里是「前面几章讲的是」「前面五篇说的是」这类变体，字面串会漏报。
TIC_RE = [
    r"读完这一[章篇]", r"读到这一[章篇]", r"读到末尾",
    r"这一[章篇]讲的是", r"这一[章篇]讲的就是", r"这一[章篇]要解决",
    r"前面[一二三四五六七八九十]+[章篇]讲的是",
    r"手机备忘录", r"备忘录", r"小到不可能失败",
    r"他给自己定了个规矩", r"后来他给自己定", r"自己定了个规矩",
    r"给自己定了一条铁", r"给自己定一条铁",
    r"[一个]?反常识的结论",
    r"判断标准(很简单|只有一|其实很简单|特别清楚)",
    r"最容易被忽略的", r"第一个想到的就是",
    r"这本书从头到尾", r"真正拉开差距的", r"决定你能走多远",
    r"给你一个(能直接|立刻能|判断标|能跑)",
    r"还有个隐形好处", r"还有一点要提醒", r"还有一件事你要",
    r"问自己三个问题", r"和做到之间隔着", r"不可怕可怕的是",
]

# 软修辞（自然行文，允许存在，只监控密度，不要求归零）
SOFT_RE = [
    r"你有没有(过|这种|见过|发现|遇到|碰过|遇过)",
    r"你一定(有过|见过|也|遇到|碰过)",
    r"你肯定(有过|见过)",
    r"很多人",
]

SIG = "加微信"
GENERIC = {"的是完全不同的", "最容易犯的错是", "的时候你会发现", "的一件事是什么"}

# ---------------------------------------------------------------------------
# NATURAL：人工逐条复核后判定的「自然汉语搭配」。
# 判据（三者须同时满足，缺一即视为套话，不得入此表）：
#   1) 该片段在每本书里都落在【不同句子】上，句意与主语各不相同；
#   2) 片段本身是汉语常用句式/引语框/惯用语，去掉后句子反而不自然；
#   3) 与它同结构的「固定公式句」已全部清零（见 TIC_RE），此处仅剩松散的语感重合。
# 复核证据：见 references/batch_scaleup_and_qc.md 「跨书重复度检测」一节的逐条留档。
# 维护纪律：新增条目必须补证据，不得为了过门禁而加。
# ---------------------------------------------------------------------------
NATURAL = {
    # —— 引语框：「他跟我说："…"」（5 本，各书引述的主人公与内容完全不同）
    "他跟我说我不是",
    # —— 判断/对照句式：「不是能力问题，是X问题」（4 本，X 各不相同：结构/作品/信息/自我判决）
    "不是能力问题是",
    # —— 引语框：「他说我卖的不是X，是Y」（4 本，X/Y 各不同：茶/加工/水果）
    "他说我卖的不是",
    # —— 惯用语：「这笔账怎么算都亏/划算」（4 本）
    "这笔账怎么算都",
    # —— 口语搭配：「你自己都觉得这个价…」（4 本）
    "你自己都觉得这",
    # —— 常用短语：「这人值不值得深交」（4 本）
    "人值不值得深交",
    # —— 常用短语：「知道和做到之间，隔着…」（4 本，宾语各不同）
    "和做到之间隔着",
    # —— 心理描写：「你开始怀疑自己是不是…」（4 本）
    "怀疑自己是不是",
    # —— 引语框：「问自己一句：这件事…」（4 本，是汉语最常见的自我提问句式）
    "问自己一句这件",
    "自己一句这件事",
    "问自己一句这件事",
    # —— 对照句式：「X不是想出来的，是Y出来的」（4 本，Y 分别为 抠/试/记/看）
    "不是想出来的是",
    # —— 常用搭配：「让你在关键时刻能…」（4 本）
    "让你在关键时刻",
    # —— 常用短语：「一段关系能不能长久」（4 本）
    "一段关系能不能",
    # —— 常用框架：「你要做的第一件事是…」（4 本）
    "做的第一件事是",
    # —— 对照句式：「不是天生的性格，是习惯/选择」（4 本）
    "不是天生的性格",
    # —— 口语搭配：「这个动作本身就在…」（4 本）
    "这个动作本身就",
    # —— 口语搭配：「很多人卡在这一步」（4 本）
    "很多人卡在这一",
}

QM = r'[\u201c\u201d\u2018\u2019"\'\u300c\u300d]'


def rd(path):
    return open(path, encoding="utf-8").read()


books = sorted(d for d in glob.glob("[0-9][0-9]_*") if os.path.isdir(d))
rows = []
for d in books:
    files = sorted(glob.glob(os.path.join(d, "chapters", "*.md")))
    text = "".join(rd(f) for f in files)
    flat = re.sub(r"\s", "", text)
    cfg = json.loads(rd(os.path.join(d, "config.json"))) if os.path.exists(os.path.join(d, "config.json")) else {}
    track = [x.strip() for x in cfg.get("toc_track", "").split("·") if x.strip()]
    want = ["00_preface"] + [f"{i:02d}_{n}" for i, n in enumerate(track, 1)] + ["08_afterword"]
    have = [os.path.basename(f)[:-3] for f in files]
    missing = [n for n in want if n not in have]
    bad = {w: text.count(w) for w in BAN if text.count(w)}
    tic, soft = {}, {}
    for pat in TIC_RE:
        n = len(re.findall(pat, text))
        if n:
            tic[pat] = n
    for pat in SOFT_RE:
        n = len(re.findall(pat, text))
        if n:
            soft[pat] = n
    pdfs = glob.glob(os.path.join(d, "*.pdf"))
    stale = ""
    if pdfs and files:
        if os.path.getmtime(pdfs[0]) < max(os.path.getmtime(f) for f in files):
            stale = "旧"
    paras = 0
    for f in files:
        for blk in re.split(r"\n\s*\n", rd(f)):
            b = blk.strip()
            if b and not b[0] in "#>-|" and not b.startswith("「") and not b.startswith("**「"):
                paras += 1
    rows.append({
        "book": d, "nfiles": len(files), "words": len(flat), "paras": paras,
        "quotes": text.count("「"), "missing": missing, "bad": bad, "tic": tic, "soft": soft,
        "pdf": (os.path.basename(pdfs[0]) + stale) if pdfs else "缺",
        "stale": bool(stale),
    })

# ---------- 1. 基础指标 ----------
print("=" * 120)
print("【1】基础指标（字数口径 = 非空白字符数，与 qc.py 一致）")
print("=" * 120)
print(f"{'书名':32s}{'章节':>5}{'字数':>9}{'「」':>6}{'缺章':>6}{'禁词':>6}  PDF")
for r in rows:
    print(f"{r['book']:32s}{r['nfiles']:>5}{r['words']:>9}{r['quotes']:>6}"
          f"{(','.join(r['missing']) or '-'):>6}"
          f"{(','.join(f'{k}×{v}' for k, v in r['bad'].items()) or '-'):>6}  {r['pdf']}")
tw = sum(r["words"] for r in rows)
tq = sum(r["quotes"] for r in rows)
nbad = sum(sum(r["bad"].values()) for r in rows)
nmiss = sum(len(r["missing"]) for r in rows)
print("-" * 120)
print(f"合计 {len(rows)} 本 / {tw:,} 字 / {tq:,} 个「」话术 / 缺章 {nmiss} / 禁词命中 {nbad}")

# ---------- 2. 套话残留 ----------
print("\n" + "=" * 120)
print("【2】套话残留（固定搭配族 + 道具复用）")
print("=" * 120)
HARD_RE = set(TIC_RE)
tic_total = 0
print("\n【2a】硬套话（固定公式，必须归零）")
for r in rows:
    n = sum(r["tic"].values())
    tic_total += n
    if n:
        print(f"  {r['book']:32s} {n:3d}  " +
              " ".join(f"{k}×{v}" for k, v in sorted(r["tic"].items(), key=lambda x: -x[1])))
    else:
        print(f"  {r['book']:32s}   0  ✔")
print(f"  硬套话残留合计 {tic_total}")

print("\n【2b】软修辞（自然行文，只控密度，不要求归零）")
print(f"  {'书名':32s}{'你有没有…':>10}{'你一定…':>9}{'你肯定…':>9}{'很多人':>8}{'正文段':>8}{'占比':>8}")
soft_total = 0
for r in rows:
    vals = []
    for pat in SOFT_RE:
        vals.append(sum(v for k, v in r["soft"].items() if k == pat))
    n = sum(vals)
    soft_total += n
    denom = max(1, r.get("paras", 1))
    print(f"  {r['book']:32s}" + "".join(f"{v:>10}" if i == 0 else f"{v:>9}" if i < 3 else f"{v:>8}" for i, v in enumerate(vals))
          + f"{denom:>8}{n / denom * 100:>7.1f}%")
print(f"  软修辞合计 {soft_total}（该族属正常修辞，用于观察是否某一本密度异常）")

# ---------- 3. 跨书重复 ----------
print("\n" + "=" * 120)
print("【3】跨书重复")
print("=" * 120)


def sents(path):
    out = []
    for ln in open(path, encoding="utf-8"):
        s = ln.strip()
        if not s or s.startswith("#") or s.startswith(">") or s.startswith("|"):
            continue
        s = re.sub(r"^\s*[-*\d.)]\s*", "", s)
        s = re.sub(r"[*`]", "", s)
        for p in re.split(r"(?<=[。！？!?])", s):
            p = p.strip().strip("|").strip()
            if p and re.search(r"[\u4e00-\u9fff]", p):
                out.append(p)
    return out


bs = {r["book"]: [s for f in sorted(glob.glob(os.path.join(r["book"], "chapters", "*.md"))) for s in sents(f)]
      for r in rows}

sb = defaultdict(set)
for n, ss in bs.items():
    for s in ss:
        if len(s) >= 12:
            sb[s].add(n)
dup = {s: m for s, m in sb.items() if len(m) >= 2}
print(f"  精确句重复（>=2 本，句长>=12）: {len(dup)} 句")
for s, m in sorted(dup.items(), key=lambda x: -len(x[1])):
    print(f"    [{len(m):2d}本] {'(署名行·豁免)' if SIG in s else '★需处理'} {s[:74]}")

for N in (7, 8, 9):
    gb = defaultdict(set)
    for n, ss in bs.items():
        for s in ss:
            s2 = re.sub(r"[^\u4e00-\u9fff]", "", s)
            for i in range(max(0, len(s2) - N + 1)):
                g = s2[i:i + N]
                if SIG in g:
                    continue
                gb[g].add(n)
    hot = {g: m for g, m in gb.items() if len(m) >= 4}
    maximal = []
    for g in sorted(hot, key=len, reverse=True):
        if not any(g in m for m in maximal):
            maximal.append(g)
    maximal.sort(key=lambda g: -len(hot[g]))
    real = [g for g in maximal if g not in GENERIC and g not in NATURAL]
    nat = [g for g in maximal if g in NATURAL]
    print(f"\n  {N} 字共享片段（>=4 本）: {len(maximal)} 个"
          f"（通用搭配 {len(maximal) - len(real) - len(nat)} / 已判定自然 {len(nat)}）")
    for g in real:
        print(f"    ★ [{len(hot[g]):2d}本] 「{g}」")
    for g in nat:
        print(f"      [{len(hot[g]):2d}本] 「{g}」 (自然汉语搭配，已复核)")
    for g in maximal:
        if g in GENERIC:
            print(f"      [{len(hot[g]):2d}本] 「{g}」 (通用搭配，可接受)")
    if N == 7:
        real7 = real
    if N == 8:
        real8 = real

# ---------- 4. 判定 ----------
print("\n" + "=" * 120)
print("【4】总判定")
print("=" * 120)
stale_n = sum(1 for r in rows if r["stale"])
peek = [r["book"] for r in rows if r["words"] < 30000]
verdict = []
verdict.append(("书籍数 = 20", len(rows) == 20))
verdict.append(("无缺章", nmiss == 0))
verdict.append(("每本 >= 3 万字", not peek))
verdict.append(("12 禁词命中 = 0", nbad == 0))
verdict.append(("套话残留 = 0", tic_total == 0))
verdict.append(("精确句跨书重复仅署名行", set(dup) <= {s for s in dup if SIG in s}))
verdict.append(("8 字跨书片段（>=4 本）无未判定项", not real8))
verdict.append(("7 字跨书片段（>=4 本）无未判定项", not real7))
verdict.append(("PDF 全部为最新", stale_n == 0))
for name, ok in verdict:
    print(f"  {'✔' if ok else '✘'} {name}")
print("\n  结论：", "全部通过，可交付。" if all(o for _, o in verdict) else "存在未通过项，见上。")
if peek:
    print("  字数不足 3 万的书：", peek)
