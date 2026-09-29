# -*- coding: utf-8 -*-
"""跨书套话检测 v2（双通道）——批量出书的必跑项。

通道一：精确句重复（同一句出现在 >=2 本书）
通道二：模糊片段重复（句级 7-9 字共享搭配，出现在 >=K 本书）——抓"措辞微调但同一套模板"

用法：
    python dupcheck.py                 # 默认 K=4
    python dupcheck.py 5               # 阈值 K=5
只读，不改任何稿件。
"""
import os, re, glob, sys, json
from collections import defaultdict

ROOT = os.path.dirname(os.path.abspath(__file__))
K = int(sys.argv[1]) if len(sys.argv) > 1 else 4
SIG = "加微信"           # 封面署名行，豁免
MIN_SENT = 12            # 精确通道的句子长度门槛
FUZZ = (7, 9)            # 模糊通道的片段长度区间
QM = r'[\u201c\u201d\u2018\u2019"\'\u300c\u300d]'

# 通用中文搭配白名单：跨书撞车只因汉语本身就这么说，不是作者套话。
# 这类只提示、不要求改写——强行替换反而会破坏自然度。
GENERIC = {
    "的是完全不同的", "最容易犯的错是", "的时候你会发现", "的一件事是什么",
    "判断标准很简单", "判断标准只有一", "还有一个更隐蔽", "还有一点要提醒",
}


def raw_sentences(path):
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


books = {}
for d in sorted(glob.glob(os.path.join(ROOT, "[0-9][0-9]_*"))):
    if not os.path.isdir(d):
        continue
    ss = []
    for f in sorted(glob.glob(os.path.join(d, "chapters", "*.md"))):
        ss += raw_sentences(f)
    books[os.path.basename(d)] = ss

print(f"书籍数: {len(books)}")
print("=" * 92)

# ---------- 通道一：精确句重复 ----------
sent_books = defaultdict(set)
for name, ss in books.items():
    for s in ss:
        if len(s) >= MIN_SENT:
            sent_books[s].add(name)
dup = {s: m for s, m in sent_books.items() if len(m) >= 2}
print(f"\n【通道一】精确句重复（>=2 本书，句长 >={MIN_SENT}）: {len(dup)} 句")
for s, m in sorted(dup.items(), key=lambda x: -len(x[1])):
    tag = " (署名行，豁免)" if SIG in s else ""
    print(f"  [{len(m):2d}本]{tag} {s[:76]}")

# ---------- 通道二：模糊片段重复 ----------
for N in range(FUZZ[0], FUZZ[1] + 1):
    gram_books = defaultdict(set)
    for name, ss in books.items():
        for s in ss:
            s2 = re.sub(r"[^\u4e00-\u9fff]", "", s)
            if len(s2) < N:
                continue
            for i in range(len(s2) - N + 1):
                g = s2[i:i + N]
                if SIG in g:
                    continue
                gram_books[g].add(name)
    hot = {g: m for g, m in gram_books.items() if len(m) >= K}
    maximal = []
    for g in sorted(hot, key=len, reverse=True):
        if not any(g in m for m in maximal):
            maximal.append(g)
    maximal.sort(key=lambda g: -len(hot[g]))
    print(f"\n【通道二】{N} 字共享片段（>={K} 本书）: {len(maximal)} 个")
    for g in maximal:
        ms = sorted(hot[g])
        print(f"  [{len(ms):2d}本] 「{g}」  ← {'、'.join(x.split('_', 1)[-1][:12] for x in ms)}")

print("\n" + "=" * 92)
print("判读：通道一应为 0（署名行除外）；通道二刻意保留的体裁通用词（如「直接抄走的话术」）可接受，"
      "但涉及具体道具、案例句式、章节预告的条目必须清零。")
