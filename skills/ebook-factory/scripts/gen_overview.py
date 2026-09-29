# -*- coding: utf-8 -*-
"""Regenerate 20本合集总览.html from current on-disk data."""
import re, os, json, glob, html

ROOT = r"D:\项目\截图工具\闲鱼原创虚拟资料\复刻电子书20"
os.chdir(ROOT)
OLD = os.path.join(ROOT, "20本合集总览.html")

BAN = ["首先", "其次", "最后", "综上所述", "总而言之", "不难发现", "众所周知",
       "相信通过", "一方面", "另一方面", "值得注意的是", "在这个时代"]

# --- reuse pill labels from the previous overview (cover styles unchanged) ---
pill_map = {}
with open(OLD, encoding="utf-8") as f:
    old = f.read()
for m in re.finditer(r'<span class="no"[^>]*>NO\.(\d+)</span>\s*<span class="pill"[^>]*>([^<]+)</span>', old):
    pill_map[int(m.group(1))] = m.group(2)

DEFAULT_PILL = {"gold_dark": "暗金", "vintage": "复古", "minimal": "极简", "book3d": "立体"}

rows = []
for d in sorted(glob.glob("[0-9][0-9]_*")):
    if not os.path.isdir(d):
        continue
    no = int(d[:2])
    with open(os.path.join(d, "config.json"), encoding="utf-8") as f:
        cfg = json.load(f)
    # chapters
    text = ""
    chs = sorted(glob.glob(os.path.join(d, "chapters", "*.md")))
    for c in chs:
        with open(c, encoding="utf-8") as f:
            text += f.read()
    nchar = len(re.sub(r"\s", "", text))  # 与 qc.py 同口径：非空白字符数
    nquote = text.count("「")
    banned = sum(text.count(w) for w in BAN)
    pdfs = sorted(glob.glob(os.path.join(d, "*.pdf")))
    pdf = pdfs[0] if pdfs else ""
    npage = 0
    if pdf:
        with open(pdf, "rb") as f:
            npage = len(re.findall(rb"/Type\s*/Page(?![s])", f.read()))
    rows.append({
        "no": no,
        "dir": d.replace("\\", "/"),
        "pdf": os.path.basename(pdf),
        "title": cfg.get("title", ""),
        "kicker": cfg.get("kicker", ""),
        "track": cfg.get("toc_track", ""),
        "style": cfg.get("cover_style", ""),
        "label": cfg.get("series_label", ""),
        "pill": pill_map.get(no) or DEFAULT_PILL.get(cfg.get("cover_style", ""), cfg.get("cover_style", "")),
        "chars": nchar,
        "pages": npage,
        "quotes": nquote,
        "banned": banned,
        "size": os.path.getsize(pdf) if pdf else 0,
    })

rows.sort(key=lambda r: r["no"])
total_chars = sum(r["chars"] for r in rows)
total_pages = sum(r["pages"] for r in rows)
total_quotes = sum(r["quotes"] for r in rows)
total_banned = sum(r["banned"] for r in rows)

# group by store = series_label prefix before " · "
stores = {}
for r in rows:
    sn = r["label"].split(" · ")[0] if " · " in r["label"] else "其他"
    stores.setdefault(sn, []).append(r)


def esc(s):
    return html.escape(s, quote=False)


cards = []
for r in rows:
    cards.append(f'''    <a class="card" href="./{r["dir"]}/{r["pdf"]}" target="_blank">
      <div class="c-top">
        <span class="no">NO.{r["no"]:02d}</span>
        <span class="pill">{esc(r["pill"])}</span>
      </div>
      <h3>{esc(r["title"])}</h3>
      <p class="kick">{esc(r["kicker"])}</p>
      <p class="track">{esc(r["track"])}</p>
      <div class="c-bot">
        <span><b>{r["chars"]:,}</b> 字</span>
        <span><b>{r["pages"]}</b> 页</span>
        <span><b>{r["quotes"]}</b> 话术</span>
      </div>
      <div class="src">{esc(r["label"])}</div>
    </a>''')

store_chips = "".join(
    f'<div class="sb"><span class="sb-name">{esc(k)}</span>'
    f'<span class="sb-num">{len(v)} 本 · {sum(x["chars"] for x in v):,} 字</span></div>'
    for k, v in stores.items()
)

HTML = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>复刻电子书20 · 合集总览</title>
<style>
  * {{ box-sizing: border-box; }}
  body {{ margin:0; background:#f7f3e8; color:#2a2118;
         font-family:"Microsoft YaHei","微软雅黑","PingFang SC",sans-serif; }}
  .wrap {{ max-width:1180px; margin:0 auto; padding:48px 28px 80px; }}
  header {{ border-bottom:2px solid #c9a227; padding-bottom:26px; margin-bottom:34px; }}
  h1 {{ font-size:34px; margin:0 0 12px; letter-spacing:1px; }}
  h1 em {{ font-style:normal; color:#c9a227; }}
  .lead {{ color:#6b5c46; font-size:15px; line-height:1.9; margin:0; }}
  .stats {{ display:flex; gap:34px; flex-wrap:wrap; margin:24px 0 0; }}
  .stat b {{ display:block; font-size:26px; color:#8a6d12; letter-spacing:1px; }}
  .stat span {{ font-size:12.5px; color:#7a6a52; letter-spacing:2px; }}
  .stores {{ display:flex; gap:12px; flex-wrap:wrap; margin:26px 0 40px; }}
  .sb {{ background:#fff; border:1px solid #e6dcc2; border-radius:999px; padding:8px 16px;
        display:flex; gap:10px; align-items:center; font-size:13px; }}
  .sb-name {{ font-weight:600; }}
  .sb-num {{ color:#8a7a5e; }}
  .grid {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(268px,1fr)); gap:18px; }}
  .card {{ display:block; background:#fff; border:1px solid #e8dfc8; border-radius:10px;
          padding:20px 20px 16px; text-decoration:none; color:inherit;
          transition:transform .15s, box-shadow .15s, border-color .15s; }}
  .card:hover {{ transform:translateY(-3px); box-shadow:0 10px 26px rgba(120,95,20,.13); border-color:#c9a227; }}
  .c-top {{ display:flex; justify-content:space-between; align-items:center; margin-bottom:12px; }}
  .no {{ font-size:11.5px; letter-spacing:2px; color:#b09246; }}
  .pill {{ font-size:11px; letter-spacing:1px; background:#f3ecd8; color:#7d6524;
          border-radius:999px; padding:3px 10px; }}
  .card h3 {{ font-size:19px; margin:0 0 8px; letter-spacing:.5px; }}
  .kick {{ font-size:12.5px; color:#8b7a60; margin:0 0 10px; line-height:1.7; }}
  .track {{ font-size:12px; color:#a08c68; margin:0 0 16px; line-height:1.8;
           border-left:2px solid #eadfc2; padding-left:9px; }}
  .c-bot {{ display:flex; gap:14px; font-size:12.5px; color:#6b5c46; border-top:1px solid #f0e8d6;
           padding-top:11px; }}
  .c-bot b {{ color:#8a6d12; }}
  .src {{ margin-top:9px; font-size:11px; color:#b3a58c; letter-spacing:.5px; }}
  footer {{ margin-top:52px; padding-top:20px; border-top:1px solid #e6dcc2;
           font-size:12.5px; color:#8b7a60; line-height:2; }}
  footer b {{ color:#6b5c46; }}
</style>
</head>
<body>
<div class="wrap">
  <header>
    <h1>复刻电子书20 · <em>合集总览</em></h1>
    <p class="lead">第二批 20 本，按四个对标店铺的「想要榜」第 2–6 名选题复刻成书。每本 9 个章节文件（序言 + 七章 + 结语），
    每章 6–9 小节，每节六段式（结论句 → 痛点场景 → 底层逻辑 → 含话术模板的方法 → 场景演练 → 收束），
    话术模板用「」标注、可直接抄走。四套封面视觉对应四个店铺的高浏览商品风格。
    全部稿件已过跨书重复度检测：正文无跨书复用模板句。</p>
    <div class="stats">
      <div class="stat"><b>{len(rows)}</b><span>本数</span></div>
      <div class="stat"><b>{total_chars:,}</b><span>总字数</span></div>
      <div class="stat"><b>{total_pages}</b><span>总页数</span></div>
      <div class="stat"><b>{total_quotes:,}</b><span>话术模板</span></div>
      <div class="stat"><b>{len(stores)}</b><span>封面风格</span></div>
      <div class="stat"><b>{total_banned}</b><span>禁用词命中</span></div>
    </div>
    <div class="stores">
      {store_chips}
    </div>
  </header>

  <div class="grid">
{chr(10).join(cards)}
  </div>

  <footer>
    <b>质量口径</b>：12 个硬禁用词（首先／其次／最后／综上所述／总而言之／不难发现／众所周知／相信通过／一方面／另一方面／值得注意的是／在这个时代）全库命中 <b>{total_banned}</b>；
    跨书重复模板句 <b>0</b>（仅封面署名行共用）。<br>
    <b>署名</b>：加微信abcd15574进读者群　|　<b>出品</b>：屋里涛说 原创整理
  </footer>
</div>
</body>
</html>
'''

out = os.path.join(ROOT, "20本合集总览.html")
with open(out, "w", encoding="utf-8") as f:
    f.write(HTML)
print(f"已生成 {out}")
print(f"本数 {len(rows)}  总字数 {total_chars:,}  总页数 {total_pages}  话术 {total_quotes:,}  禁词 {total_banned}")
for k, v in stores.items():
    print(f"  {k}: {len(v)} 本 · {sum(x['chars'] for x in v):,} 字 · {sum(x['pages'] for x in v)} 页")
