# -*- coding: utf-8 -*-
"""多风格电子书构建器：chapters/*.md -> HTML -> PDF（Edge headless 打印）

相比 ebook-factory 通用版，新增 4 种封面风格（对应四个闲鱼对标店铺的爆款主图视觉）：
  gold_dark  墨绿黑底 + 金色衬线大字 + 编号清单卡（台球界徐志摩）
  vintage    仿古做旧纸 + 红字楷书 + 描边副标题（人性智慧研修）
  minimal    极简黄绿底 + 半透明色块 + 黑体大字（银河知识）
  book3d     3D 立体书 + 金属金 + 底部卡片列表（开悟阅读01）

用法：python build_book.py            # 用 CONFIG
      python build_book.py --cover-style minimal --out 书名
"""
import re, html, subprocess, os, argparse, json

CONFIG = {
    "title": "书名",
    "kicker": "普通人的处世底层心法",
    "author": "屋里涛说 著",
    "series_label": "闲鱼对标复刻 · 第一册",
    "accent": "#c9a227",
    "toc_track": "从A到B · 从C到D",
    "desc_lines": ["", ""],
    "cover_style": "gold_dark",
    "cover": {
        "top_left": "",
        "pill": "",
        "title_lines": [],      # 书名分行（不填则自动单行）
        "sub_lines": [],
        "items": [],
        "quote": "",            # vintage 用的红字引题
        "btn": "",              # minimal 底部按钮文字
        "footer_left": "",
        "footer_right": "",
        "badge": "",
    },
    "chapters_dir": "./chapters",
    "output_name": "book",
    "edge": r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
}


# ============================ 文本处理 ============================
def inline(s: str) -> str:
    s = html.escape(s, quote=False)
    s = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', s)
    return s


def md_to_html(md_text: str) -> str:
    lines = md_text.split("\n")
    out, i = [], 0
    while i < len(lines):
        line = lines[i].rstrip()
        if not line.strip():
            i += 1
            continue
        if line.startswith("### "):
            out.append(f"<h3>{inline(line[4:])}</h3>"); i += 1; continue
        if line.startswith("## "):
            out.append(f'<h2 class="sec-title">{inline(line[3:])}</h2>'); i += 1; continue
        if line.startswith("# "):
            out.append(f'<h1 class="chapter-title"><span>{inline(line[2:])}</span></h1>'); i += 1; continue
        if re.match(r'^\d+\.\s+', line.strip()):
            items = []
            while i < len(lines) and re.match(r'^\d+\.\s+', lines[i].strip()):
                items.append(inline(re.sub(r'^\d+\.\s+', '', lines[i].strip())))
                i += 1
            out.append("<ol>" + "".join(f"<li>{it}</li>" for it in items) + "</ol>")
            continue
        if line.startswith("- "):
            items = []
            while i < len(lines) and lines[i].strip().startswith("- "):
                items.append(inline(lines[i].strip()[2:]))
                i += 1
            out.append("<ul>" + "".join(f"<li>{it}</li>" for it in items) + "</ul>")
            continue
        paras = []
        while i < len(lines) and lines[i].strip():
            paras.append(lines[i].strip())
            i += 1
        joined = "<br>".join(inline(x) for x in paras)
        cls = " template" if paras[0].startswith("\u300c") else ""
        out.append(f'<p class="para{cls}">{joined}</p>')
    return "\n".join(out)


# ============================ 封面 HTML ============================
def cover_html(cfg):
    st = cfg.get("cover_style", "gold_dark")
    c = cfg.get("cover", {})
    E = html.escape
    title = E(cfg["title"])
    author = E(cfg["author"])
    series = E(cfg.get("series_label", "") or "")
    series_block = f'<div class="cv-series">{series}</div>' if series else ""

    if st == "gold_dark":
        tl = c.get("title_lines") or [cfg["title"]]
        title_html = "<br>".join(E(x) for x in tl)
        subs = "<br>".join(E(x) for x in c.get("sub_lines", []))
        items = "".join(
            f'<div class="cv-item"><span class="cv-num">{i+1:02d}</span>'
            f'<span class="cv-itxt">{E(x)}</span></div>'
            for i, x in enumerate(c.get("items", [])))
        return f'''<section class="cover cv-gold">
  <div class="cv-grid"></div>
  <div class="cv-arc"></div>
  <div class="cv-gold-top">
    <span class="cv-cat">{E(c.get("top_left",""))}</span>
    <span class="cv-pill">{E(c.get("pill",""))}</span>
  </div>
  <div class="cv-gold-mid">
    <h1 class="cv-gold-title">{title_html}</h1>
    <div class="cv-rule"><i></i><b></b><i></i></div>
    <p class="cv-gold-sub">{subs}</p>
  </div>
  <div class="cv-gold-cta">{author}</div>
  <div class="cv-gold-card">{items}</div>
  <div class="cv-foot"><span>{E(c.get("footer_left",""))}</span><span>{E(c.get("footer_right",""))}</span></div>
</section>'''

    if st == "vintage":
        return f'''<section class="cover cv-vin">
  <div class="cv-paper">
    <div class="cv-paper-in">
      <h1 class="cv-vin-title">{title}</h1>
      <div class="cv-vin-orn"><span></span><b></b><span></span></div>
      <p class="cv-vin-quote">{E(c.get("quote",""))}</p>
      <div class="cv-vin-lines">
        {"".join(f'<p>{E(x)}</p>' for x in c.get("sub_lines", []))}
      </div>
      <div class="cv-vin-badge">{E(c.get("badge",""))}</div>
    </div>
  </div>
  <div class="cv-foot cv-foot-vin"><span>{E(c.get("footer_left",""))}</span><span>{E(c.get("footer_right",""))}</span></div>
</section>'''

    if st == "minimal":
        tl = c.get("title_lines") or [cfg["title"]]
        title_html = "".join(f'<span>{E(x)}</span>' for x in tl)
        wm = E(c.get("watermark", "屋里涛说"))
        foot = E(c.get("footer_left", ""))
        return f'''<section class="cover cv-min">
  <div class="cv-min-mark">{"".join(f'<i>{wm}</i>' for _ in range(6))}</div>
  <div class="cv-min-card">
    <h1 class="cv-min-title">{title_html}</h1>
  </div>
  <div class="cv-min-btn">{E(c.get("btn",""))}</div>
  <div class="cv-min-foot">{foot}</div>
</section>'''

    if st == "book3d":
        tl = c.get("title_lines") or [cfg["title"]]
        title_html = "<br>".join(E(x) for x in tl)
        items = "".join(
            f'<div class="cv3-item"><b>◆</b><span>{E(x)}</span></div>'
            for x in c.get("items", []))
        return f'''<section class="cover cv-3d">
  <div class="cv3-glow"></div>
  <div class="cv3-stage">
    <div class="cv3-book">
      <div class="cv3-spine"><span>{title}</span></div>
      <div class="cv3-face">
        <div class="cv3-head">
          <h1 class="cv3-title">{title_html}</h1>
          <p class="cv3-sub">— {E(c.get("quote",""))} —</p>
        </div>
        <div class="cv3-plate">{items}</div>
      </div>
      <div class="cv3-pages"></div>
    </div>
  </div>
  <div class="cv3-badge">{E(c.get("badge",""))}</div>
  <div class="cv3-author">{series_block}</div>
</section>'''

    raise SystemExit("未知封面风格: " + st)


# ============================ 封面 CSS ============================
def cover_css(cfg):
    st = cfg.get("cover_style", "gold_dark")
    A = cfg.get("accent", "#c9a227")
    c = cfg.get("cover", {})
    ts = c.get("title_size")          # 书名自定义字号（pt），不填用各风格默认
    base = f'''
  /* ---- 通用封面基座（满版 A4） ---- */
  .cover {{ page: cover; width:210mm; height:297mm; position:relative; overflow:hidden;
            page-break-after:always; -webkit-print-color-adjust:exact; print-color-adjust:exact;
            font-family:"Microsoft YaHei","微软雅黑","PingFang SC",sans-serif; }}
  .cv-foot {{ position:absolute; left:16mm; right:16mm; bottom:12mm; display:flex;
              justify-content:space-between; font-size:9pt; letter-spacing:2px; }}
  .cv-series {{ font-size:9pt; letter-spacing:3px; margin-top:10px; opacity:.85; }}
'''

    if st == "gold_dark":
        return base + f'''
  .cv-gold {{ background:radial-gradient(120% 90% at 78% 8%, #123a2e 0%, #081a15 45%, #040c0a 100%); color:#fff; }}
  .cv-grid {{ position:absolute; inset:0;
    background-image:linear-gradient(rgba(201,162,39,.07) 1px, transparent 1px),
                     linear-gradient(90deg, rgba(201,162,39,.07) 1px, transparent 1px);
    background-size:14mm 14mm; }}
  .cv-arc {{ position:absolute; right:-28mm; top:-30mm; width:150mm; height:150mm; border-radius:50%;
    border:1.2px solid rgba(201,162,39,.45); box-shadow:0 0 60px rgba(201,162,39,.12) inset; }}
  .cv-arc:after {{ content:""; position:absolute; right:14mm; top:24mm; width:120mm; height:120mm;
    border-radius:50%; border:1px solid rgba(201,162,39,.22); }}
  .cv-gold-top {{ position:absolute; left:18mm; right:18mm; top:18mm; display:flex; justify-content:space-between; align-items:center; }}
  .cv-cat {{ font-size:12pt; font-weight:700; color:{A}; letter-spacing:2px; }}
  .cv-pill {{ font-size:9.5pt; color:{A}; border:1px solid rgba(201,162,39,.7); border-radius:20px;
    padding:4px 14px; letter-spacing:1px; }}
  .cv-gold-mid {{ position:absolute; left:18mm; right:18mm; top:74mm; text-align:center; }}
  .cv-gold-title {{ font-family:"Source Han Serif SC","Noto Serif SC","STSong","SimSun",serif;
    font-size:46pt; font-weight:700; line-height:1.32; letter-spacing:5px;
    background:linear-gradient(180deg,#f6e59a 0%,{A} 42%,#8f6d13 100%);
    -webkit-background-clip:text; background-clip:text; color:transparent; }}
  .cv-rule {{ display:flex; align-items:center; justify-content:center; gap:6px; margin:14mm 0 9mm; }}
  .cv-rule i {{ width:34mm; height:1.4px; background:linear-gradient(90deg, transparent, {A}); }}
  .cv-rule i:last-child {{ background:linear-gradient(90deg, {A}, transparent); }}
  .cv-rule b {{ width:5px; height:5px; border-radius:50%; background:{A}; }}
  .cv-gold-sub {{ font-size:13pt; line-height:1.95; color:#e8e6df; letter-spacing:1px; }}
  .cv-gold-cta {{ position:absolute; left:18mm; right:18mm; top:174mm; text-align:center;
    font-size:13pt; font-weight:700; letter-spacing:2px;
    background:linear-gradient(180deg,#f6e59a 0%,{A} 60%,#8f6d13 100%);
    -webkit-background-clip:text; background-clip:text; color:transparent; }}
  .cv-gold-card {{ position:absolute; left:18mm; right:18mm; bottom:32mm;
    border:1px solid rgba(201,162,39,.42); border-radius:6px; padding:9mm 10mm 9mm 12mm;
    background:linear-gradient(100deg, rgba(12,40,32,.72), rgba(6,18,15,.5)); }}
  .cv-gold-card:before {{ content:""; position:absolute; left:5mm; top:9mm; bottom:9mm; width:2.5px;
    background:linear-gradient(180deg,{A},rgba(201,162,39,.15)); }}
  .cv-item {{ display:flex; align-items:center; gap:5mm; margin:5.2mm 0; }}
  .cv-num {{ flex:0 0 auto; width:9.5mm; height:9.5mm; border:1px solid rgba(201,162,39,.75); border-radius:50%;
    color:{A}; font-size:10pt; display:flex; align-items:center; justify-content:center; }}
  .cv-itxt {{ font-size:13pt; font-weight:600; color:#f2f0ea; letter-spacing:.5px; }}
  .cv-foot {{ color:rgba(201,162,39,.85); }}'''

    if st == "vintage":
        tsz = ts or 52
        lsp = c.get("title_spacing", 6)
        return base + f'''
  .cv-vin {{ background:#d9cfae; padding:11mm; }}
  .cv-paper {{ width:100%; height:100%; border-radius:2mm; position:relative;
    background:
      radial-gradient(60% 45% at 22% 18%, rgba(255,255,255,.55), transparent 60%),
      radial-gradient(50% 40% at 82% 78%, rgba(150,120,60,.28), transparent 62%),
      radial-gradient(38% 30% at 68% 22%, rgba(160,130,70,.22), transparent 66%),
      radial-gradient(45% 35% at 15% 82%, rgba(150,120,60,.22), transparent 64%),
      linear-gradient(150deg,#f0e5c6 0%,#e6d9b4 40%,#dccfa6 70%,#e8dcbb 100%);
    box-shadow:0 0 0 1px rgba(120,95,45,.25) inset, 0 6px 18px rgba(80,60,20,.22); overflow:hidden; }}
  .cv-paper:before {{ content:""; position:absolute; inset:0;
    background-image:repeating-linear-gradient(0deg, rgba(140,110,55,.055) 0 1px, transparent 1px 3px),
                     repeating-linear-gradient(90deg, rgba(140,110,55,.045) 0 1px, transparent 1px 4px); }}
  .cv-paper:after {{ content:""; position:absolute; inset:0; border:1px solid rgba(120,95,45,.2); margin:6mm; }}
  .cv-paper-in {{ position:relative; z-index:2; padding:36mm 20mm 0; text-align:center; }}
  .cv-vin-title {{ font-family:"STKaiti","KaiTi","楷体","STSong","SimSun",serif;
    font-size:{tsz}pt; font-weight:700; color:#b1201c; letter-spacing:{lsp}px; line-height:1.2;
    white-space:nowrap;
    text-shadow:0 1px 0 rgba(255,250,235,.6), 0 3px 8px rgba(110,30,20,.22); }}
  .cv-vin-orn {{ display:flex; align-items:center; justify-content:center; gap:5mm; margin:11mm 0 6mm; }}
  .cv-vin-orn span {{ width:38mm; height:1px; background:linear-gradient(90deg,transparent,#8d7a4e); }}
  .cv-vin-orn span:last-child {{ background:linear-gradient(90deg,#8d7a4e,transparent); }}
  .cv-vin-orn b {{ width:7px; height:7px; transform:rotate(45deg); background:#8d7a4e; }}
  .cv-vin-quote {{ font-size:19pt; font-weight:800; color:#241d10; letter-spacing:2px;
    font-family:"STKaiti","KaiTi","楷体","Microsoft YaHei",serif; line-height:1.6; }}
  .cv-vin-lines {{ margin-top:12mm; }}
  .cv-vin-lines p {{ font-size:13.5pt; font-weight:700; color:#231c0f; line-height:2.05; letter-spacing:1px;
    text-shadow:0 1px 0 rgba(255,252,240,.85), 0 0 1px rgba(255,255,255,.9); }}
  .cv-vin-badge {{ margin-top:20mm; font-size:10pt; color:#5d4a22; letter-spacing:4px; }}
  .cv-foot-vin {{ color:#4d3e1c; }}'''

    if st == "minimal":
        return base + f'''
  .cv-min {{ background:#e9edd3; color:#17240f; }}
  .cv-min-mark {{ position:absolute; inset:0; overflow:hidden; }}
  .cv-min-mark i {{ position:absolute; font-style:normal; font-size:9pt; color:rgba(60,80,40,.16);
    white-space:nowrap; transform:rotate(-28deg); }}
  .cv-min-mark i:nth-child(1) {{ left:4mm;  top:22mm; }}
  .cv-min-mark i:nth-child(2) {{ left:58mm; top:74mm; }}
  .cv-min-mark i:nth-child(3) {{ left:12mm; top:150mm; }}
  .cv-min-mark i:nth-child(4) {{ left:70mm; top:206mm; }}
  .cv-min-mark i:nth-child(5) {{ left:6mm;  top:258mm; }}
  .cv-min-mark i:nth-child(6) {{ left:52mm; top:112mm; }}
  .cv-min-card {{ position:absolute; left:9mm; right:9mm; top:22mm; bottom:62mm; border-radius:4mm;
    background:rgba(104,124,74,.30); display:flex; align-items:center; justify-content:center; padding:0 12mm; }}
  .cv-min-title {{ font-family:"Microsoft YaHei","微软雅黑",sans-serif; font-weight:400;
    font-size:44pt; line-height:1.42; letter-spacing:2px; color:#16210e; }}
  .cv-min-title span {{ display:block; }}
  .cv-min-btn {{ position:absolute; left:50%; transform:translateX(-50%); bottom:40mm;
    background:rgba(104,124,74,.42); color:#2a351d; font-size:13pt; letter-spacing:2px;
    padding:5mm 13mm; border-radius:1.6mm; white-space:nowrap; }}
  .cv-min-foot {{ position:absolute; left:0; right:0; bottom:20mm; text-align:center;
    font-size:9.5pt; color:rgba(50,66,32,.75); letter-spacing:2px; }}'''

    if st == "book3d":
        return base + f'''
  .cv-3d {{ background:radial-gradient(90% 70% at 50% 42%, #16243f 0%, #0a1120 48%, #05070e 100%); color:#fff; }}
  .cv3-glow {{ position:absolute; left:50%; top:44%; width:190mm; height:150mm; transform:translate(-50%,-50%);
    background:radial-gradient(closest-side, rgba(212,172,74,.22), transparent 72%); }}
  .cv3-stage {{ position:absolute; left:0; right:0; top:38mm; height:190mm;
    display:flex; align-items:center; justify-content:center; perspective:1600px; }}
  .cv3-book {{ position:relative; width:126mm; height:178mm; transform-style:preserve-3d;
    transform:rotateY(-19deg) rotateX(3deg); }}
  .cv3-face {{ position:absolute; inset:0; border-radius:1.5mm 3mm 3mm 1.5mm; overflow:hidden;
    background:linear-gradient(160deg,#101d33 0%,#0a1424 55%,#060b14 100%);
    box-shadow:0 26px 60px rgba(0,0,0,.62), 0 0 0 1px rgba(212,172,74,.28) inset;
    padding:0; text-align:center; }}
  .cv3-head {{ position:absolute; left:9mm; right:9mm; top:14mm; bottom:52mm;
    display:flex; flex-direction:column; align-items:center; justify-content:center; }}
  .cv3-face:before {{ content:""; position:absolute; inset:-30% -10%;
    background:linear-gradient(115deg, transparent 38%, rgba(255,240,190,.10) 46%, transparent 54%); }}
  .cv3-title {{ font-family:"Microsoft YaHei","微软雅黑",sans-serif; font-weight:800;
    font-size:31pt; line-height:1.34; letter-spacing:2px;
    background:linear-gradient(180deg,#fff6d0 0%,#e8c760 40%,#a9812a 100%);
    -webkit-background-clip:text; background-clip:text; color:transparent;
    filter:drop-shadow(0 2px 3px rgba(0,0,0,.6)); }}
  .cv3-sub {{ margin-top:5mm; font-size:10.5pt; color:#cbb98a; letter-spacing:1px; line-height:1.7; }}
  .cv3-plate {{ position:absolute; left:8mm; right:8mm; bottom:11mm; border-radius:1.5mm;
    border:1px solid rgba(212,172,74,.42); background:linear-gradient(180deg, rgba(12,22,38,.88), rgba(6,11,20,.9));
    padding:5mm 5mm; text-align:left; }}
  .cv3-item {{ display:flex; gap:3mm; align-items:flex-start; margin:3.4mm 0; }}
  .cv3-item b {{ color:{A}; font-size:8pt; line-height:1.9; }}
  .cv3-item span {{ font-size:10pt; color:#f0ead8; line-height:1.72; }}
  .cv3-spine {{ position:absolute; left:0; top:0; width:7mm; height:100%; transform-origin:left center;
    transform:rotateY(-90deg); border-radius:1.5mm 0 0 1.5mm;
    background:linear-gradient(90deg,#0a1322,#152840 55%,#0a1322); box-shadow:0 0 14px rgba(0,0,0,.5); }}
  .cv3-spine span {{ position:absolute; left:50%; top:50%; transform:translate(-50%,-50%);
    font-size:9pt; color:#dfc98a; letter-spacing:3px; white-space:nowrap;
    writing-mode:vertical-rl; }}
  .cv3-pages {{ position:absolute; right:-1.6mm; top:1.5mm; bottom:1.5mm; width:3.4mm;
    background:repeating-linear-gradient(90deg,#f3efe6 0 .5mm,#cdc7b8 .5mm .9mm);
    border-radius:0 2mm 2mm 0; transform:translateZ(-1px); box-shadow:0 6px 16px rgba(0,0,0,.45); }}
  .cv3-badge {{ position:absolute; left:0; right:0; bottom:20mm; text-align:center;
    font-size:14pt; color:#f2ece0; letter-spacing:3px; text-shadow:0 2px 8px rgba(0,0,0,.7); }}
  .cv3-author {{ position:absolute; left:0; right:0; bottom:12mm; text-align:center;
    color:rgba(212,172,74,.9); }}'''

    raise SystemExit("未知封面风格: " + st)


# ============================ 组装 ============================
def build(cfg: dict):
    ch_dir = cfg["chapters_dir"]
    files = sorted([f for f in os.listdir(ch_dir) if f.endswith(".md")])
    if not files:
        raise SystemExit("未找到任何 .md 文件：" + ch_dir)
    toc, body = [], []
    for f in files:
        with open(os.path.join(ch_dir, f), encoding="utf-8") as fh:
            text = fh.read()
        body.append(md_to_html(text))
        for line in text.split("\n"):
            if line.startswith("# ") and not line.startswith("## "):
                toc.append((line[2:].strip(), "h1"))
            elif line.startswith("## "):
                toc.append((line[3:].strip(), "h2"))
    body_html = "\n".join(body)
    toc_html = "".join(
        f'<div class="toc-{"h1" if k=="h1" else "h2"}">{html.escape(t)}</div>' for t, k in toc)
    A = cfg.get("accent", "#c9a227")

    html_doc = f'''<!DOCTYPE html><html lang="zh-CN"><head><meta charset="UTF-8">
<title>{html.escape(cfg["title"])}</title>
<style>
  @page {{ size:A4; margin:20mm 18mm; }}
  @page cover {{ size:A4; margin:0; }}
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  body {{ font-family:"Microsoft YaHei","微软雅黑","PingFang SC",sans-serif; color:#2b2b2b; font-size:10.5pt; line-height:1.85; }}
  {cover_css(cfg)}
  .toc-page {{ page-break-after:always; }}
  .toc-page h2 {{ font-size:20pt; color:#1c1f26; border-bottom:3px solid {A}; padding-bottom:10px; margin-bottom:20px; letter-spacing:4px; }}
  .toc-h1 {{ font-size:12pt; font-weight:700; color:#1c1f26; margin:15px 0 4px; }}
  .toc-h2 {{ font-size:9.5pt; color:#666; margin:3px 0 3px 22px; }}
  h1.chapter-title {{ page-break-before:always; text-align:center; padding:40px 0 24px; margin-bottom:28px; border-bottom:2px solid {A}; }}
  h1.chapter-title span {{ font-size:21pt; letter-spacing:3px; color:#1c1f26; }}
  h2.sec-title {{ font-size:13.5pt; color:#5a4a15; margin:28px 0 12px; padding-left:12px; border-left:5px solid {A}; line-height:1.5; }}
  h3 {{ font-size:11.5pt; color:#444; margin:18px 0 8px; }}
  p.para {{ margin:0 0 12px; text-align:justify; }}
  p.template {{ background:#f8f3e8; border-left:4px solid {A}; padding:12px 16px; margin:14px 0; color:#4a3f2a; font-size:10pt; }}
  ol,ul {{ margin:8px 0 14px 6px; padding-left:24px; }}
  li {{ margin:5px 0; }}
  strong {{ color:#1c1f26; }}
</style></head><body>
{cover_html(cfg)}
<section class="toc-page"><h2>目录</h2>{toc_html}</section>
{body_html}
</body></html>'''

    base = os.getcwd()
    html_path = os.path.join(base, cfg["output_name"] + ".html")
    with open(html_path, "w", encoding="utf-8") as fh:
        fh.write(html_doc)
    print("HTML 已生成:", html_path)

    pdf_path = os.path.join(base, cfg["output_name"] + ".pdf")
    user_dir = os.path.join(base, "assets", "edge_tmp")
    os.makedirs(user_dir, exist_ok=True)
    url = "file:///" + html_path.replace("\\", "/")
    cmd = [cfg["edge"], "--headless", "--disable-gpu", "--no-pdf-header-footer",
           f"--user-data-dir={user_dir}", f"--print-to-pdf={pdf_path}",
           "--virtual-time-budget=20000", url]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    if os.path.exists(pdf_path):
        print("PDF 已生成:", pdf_path, os.path.getsize(pdf_path), "bytes")
    else:
        print("首次失败，stderr:", (r.stderr or "")[-800:])
        cmd2 = [cfg["edge"], "--headless", "--disable-gpu", "--no-pdf-header-footer",
                f"--user-data-dir={user_dir}", f"--print-to-pdf={pdf_path}",
                "--virtual-time-budget=20000", "--run-all-compositor-stages-before-draw",
                "--disable-gpu-compositing", url]
        r2 = subprocess.run(cmd2, capture_output=True, text=True, timeout=300)
        print("兜底退出码:", r2.returncode, "PDF存在:", os.path.exists(pdf_path))
        if not os.path.exists(pdf_path):
            print("stderr:", (r2.stderr or "")[-800:])


def merge_local_config(cfg: dict) -> dict:
    """若当前目录存在 config.json，则用它覆盖内置 CONFIG（cover 字段做浅合并）。"""
    if os.path.exists("config.json"):
        with open("config.json", encoding="utf-8") as fh:
            user = json.load(fh)
        for k, v in user.items():
            if k == "cover" and isinstance(v, dict):
                cfg["cover"] = {**cfg.get("cover", {}), **v}
            else:
                cfg[k] = v
    return cfg


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="多风格电子书构建器")
    p.add_argument("--title")
    p.add_argument("--author")
    p.add_argument("--chapters", default=None)
    p.add_argument("--out", default=None)
    p.add_argument("--cover-style", default=None)
    p.add_argument("--accent", default="")
    a = p.parse_args()
    cfg = merge_local_config(dict(CONFIG))
    if a.chapters: cfg["chapters_dir"] = a.chapters
    if a.out: cfg["output_name"] = a.out
    if a.title: cfg["title"] = a.title
    if a.author: cfg["author"] = a.author
    if a.cover_style: cfg["cover_style"] = a.cover_style
    if a.accent: cfg["accent"] = a.accent
    build(cfg)
