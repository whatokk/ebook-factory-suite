# -*- coding: utf-8 -*-
"""ebook-factory 通用构建器：chapters/*.md -> 精美 HTML -> PDF (Edge headless 打印)

用法 1：改下方 CONFIG 后直接 run
    python build_book.py
用法 2：命令行覆盖关键字段
    python build_book.py --title "书名" --author "作者 著" --chapters ./chapters --out book
依赖：本机 Windows 已安装 Microsoft Edge（默认安装路径）。
"""
import re, html, subprocess, os, argparse

# ============ 配置区（按需修改，或命令行覆盖）============
CONFIG = {
    "title": "社会化开窍指南",
    "subtitle": "普通人的处世底层心法",
    "kicker": "普通人的处世底层心法",          # 封面顶部小字
    "author": "屋里涛说 著",
    "series_label": "",                        # 封面底部系列角标，如"开窍系列 · 第一册"；留空则不显示
    "accent": "#c9a227",                       # 强调色（金线/标题/话术框/分隔线），默认开窍金
    "card_gradient": "linear-gradient(160deg,#1c1f26 0%,#2b2d3a 55%,#3a2f22 100%)",  # 封面卡片渐变，默认深蓝灰→金褐
    "card_text": "#f0e9d8",                    # 封面卡片文字主色
    "card_accent_text": "#e8dcc0",             # 卡片作者/副题文字色
    "toc_track": "从心态到表达 · 从破冰到识人 · 从职场到处世 · 从边界到人脉 · 从认知到布局",  # 封面副线
    "desc_lines": [                            # 封面描述，每元素一行
        "一套帮你从根上打通社交任督二脉、彻底吃透社会化生存逻辑的开窍宝典",
        "不讲虚浮道理 · 不逼你改性格 · 零基础社恐也能用",
    ],
    "chapters_dir": "./chapters",              # 含 *.md 的目录（文件名排序即章节顺序）
    "output_name": "book",                     # 输出文件前缀
    "edge": r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
}


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


def build(cfg: dict):
    ch_dir = cfg["chapters_dir"]
    files = sorted([f for f in os.listdir(ch_dir) if f.endswith(".md")])
    if not files:
        raise SystemExit(f"未找到任何 .md 文件：{ch_dir}")
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
    toc_html = []
    for t, k in toc:
        cls = "toc-h1" if k == "h1" else "toc-h2"
        toc_html.append(f'<div class="{cls}">{html.escape(t)}</div>')
    desc = "<br>".join(html.escape(d) for d in cfg["desc_lines"])
    cover = f'''<section class="cover">
  <div class="cover-inner">
    <div class="cover-kicker">{html.escape(cfg["kicker"])}</div>
    <h1 class="cover-title">{html.escape(cfg["title"])}</h1>
    <div class="cover-line"></div>
    <p class="cover-sub">{html.escape(cfg["toc_track"])}</p>
    <p class="cover-desc">{desc}</p>
    <div class="cover-author">{html.escape(cfg["author"])}</div>
    {('<div class="cover-series">'+html.escape(cfg["series_label"])+'</div>') if cfg.get("series_label") else ''}
  </div>
</section>'''
    html_doc = f'''<!DOCTYPE html><html lang="zh-CN"><head><meta charset="UTF-8">
<title>{html.escape(cfg["title"])}</title>
<style>
  @page {{ size: A4; margin: 20mm 18mm; }}
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  body {{ font-family:"Microsoft YaHei","微软雅黑","PingFang SC",sans-serif; color:#2b2b2b; font-size:10.5pt; line-height:1.85; }}
  .cover {{ page-break-after:always; background:#f4efe6; padding:28mm 0; min-height:240mm; display:flex; align-items:center; justify-content:center; }}
  .cover-inner {{ background:{cfg["card_gradient"]}; color:{cfg["card_text"]}; padding:36mm 26mm; border-radius:8px; box-shadow:0 12px 40px rgba(0,0,0,.18); min-height:200mm; display:flex; flex-direction:column; align-items:center; justify-content:center; text-align:center; }}
  .cover-kicker {{ letter-spacing:6px; font-size:12pt; color:{cfg["accent"]}; margin-bottom:22px; }}
  .cover-title {{ font-size:40pt; font-weight:800; letter-spacing:8px; color:#f5efdc; text-shadow:0 2px 18px rgba(0,0,0,.45); }}
  .cover-line {{ width:90px; height:3px; background:{cfg["accent"]}; margin:26px auto; }}
  .cover-sub {{ font-size:11pt; color:#d8cdb4; letter-spacing:1px; margin-bottom:26px; }}
  .cover-desc {{ font-size:10pt; color:#a89d88; line-height:2; }}
  .cover-author {{ margin-top:40px; font-size:13pt; letter-spacing:4px; color:{cfg["card_accent_text"]}; }}
  .cover-series {{ margin-top:12px; font-size:9.5pt; letter-spacing:3px; color:{cfg["accent"]}; opacity:.85; }}
  .toc-page {{ page-break-after:always; }}
  .toc-page h2 {{ font-size:20pt; color:#1c1f26; border-bottom:3px solid {cfg["accent"]}; padding-bottom:10px; margin-bottom:20px; letter-spacing:4px; }}
  .toc-h1 {{ font-size:12pt; font-weight:700; color:#1c1f26; margin:16px 0 4px; }}
  .toc-h2 {{ font-size:9.5pt; color:#666; margin:3px 0 3px 22px; }}
  h1.chapter-title {{ page-break-before:always; text-align:center; padding:42px 0 26px; margin-bottom:30px; border-bottom:2px solid {cfg["accent"]}; }}
  h1.chapter-title span {{ font-size:21pt; letter-spacing:3px; color:#1c1f26; }}
  h2.sec-title {{ font-size:13.5pt; color:#5a4a15; margin:30px 0 12px; padding-left:12px; border-left:5px solid {cfg["accent"]}; line-height:1.5; }}
  h3 {{ font-size:11.5pt; color:#444; margin:18px 0 8px; }}
  p.para {{ margin:0 0 12px; text-align:justify; }}
  p.template {{ background:#f8f3e8; border-left:4px solid {cfg["accent"]}; padding:12px 16px; margin:14px 0; color:#4a3f2a; font-size:10pt; }}
  ol,ul {{ margin:8px 0 14px 6px; padding-left:24px; }}
  li {{ margin:5px 0; }}
  strong {{ color:#1c1f26; }}
</style></head><body>
{cover}
<section class="toc-page"><h2>目录</h2>{''.join(toc_html)}</section>
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
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
    if os.path.exists(pdf_path):
        print("PDF 已生成:", pdf_path, os.path.getsize(pdf_path), "bytes")
    else:
        print("首次失败，stderr:", (r.stderr or "")[-600:])
        cmd2 = [cfg["edge"], "--headless", "--disable-gpu", "--print-to-pdf-no-header",
                f"--user-data-dir={user_dir}", f"--print-to-pdf={pdf_path}",
                "--virtual-time-budget=20000", url]
        r2 = subprocess.run(cmd2, capture_output=True, text=True, timeout=180)
        print("兜底退出码:", r2.returncode, "PDF存在:", os.path.exists(pdf_path))


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="ebook-factory 构建器")
    p.add_argument("--title", help="书名")
    p.add_argument("--author", help="作者署名，如 '屋里涛说 著'")
    p.add_argument("--chapters", default=CONFIG["chapters_dir"], help="章节 md 目录")
    p.add_argument("--out", default=CONFIG["output_name"], help="输出文件前缀")
    p.add_argument("--series", default="", help="系列角标，如 '开窍系列 · 第一册'")
    p.add_argument("--accent", default="", help="强调色 hex，如 '#c9a227'")
    a = p.parse_args()
    cfg = dict(CONFIG)
    if a.title:
        cfg["title"] = a.title
    if a.author:
        cfg["author"] = a.author
    if a.series:
        cfg["series_label"] = a.series
    if a.accent:
        cfg["accent"] = a.accent
    cfg["chapters_dir"] = a.chapters
    cfg["output_name"] = a.out
    build(cfg)
