# -*- coding: utf-8 -*-
"""
提取 20 本复刻电子书的封面图。
封面是嵌在每本 HTML 里的 <section class="cover ..."> 区块（纯 CSS 渲染，无独立图片），
本脚本：抽 cover 区块 + 原 <style> -> 生成仅含封面的独立 HTML -> Edge headless 按 A4 比例截图。
输出：复刻电子书20/封面/NN_书名.png

注意：暂存目录放在项目外（D:/_wb_cover_scratch），避免在交付目录产生中间产物；
Edge profile 全局复用一份，保证文件数少、无需批量删除。
"""
import os, re, sys, subprocess, shutil, pathlib

BATCH = pathlib.Path(r"D:\项目\截图工具\闲鱼原创虚拟资料\复刻电子书20")
EDGE  = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
OUTDIR  = BATCH / "封面"                       # 交付目录：封面图
SCRATCH = pathlib.Path(r"D:\_wb_cover_scratch")  # 项目外暂存
PROFILE = SCRATCH / "edge_profile"               # 全局复用

W_LOGICAL, H_LOGICAL = 794, 1123   # A4 @96dpi 逻辑尺寸

def sanitize(name):
    return re.sub(r'[\\/:*?"<>|]', '_', name).strip()

def extract(html_path):
    html = html_path.read_text(encoding="utf-8", errors="ignore")
    style_m = re.search(r"<style.*?>(.*?)</style>", html, re.S)
    style = style_m.group(1) if style_m else ""
    cover_m = re.search(r'<section class="cover.*?</section>', html, re.S)
    if not cover_m:
        raise RuntimeError(f"未找到 cover 区块: {html_path}")
    cover = cover_m.group(0)
    title_m = re.search(r"<title>(.*?)</title>", html, re.S)
    title = (title_m.group(1).strip() if title_m else html_path.stem)
    return style, cover, title

def build_standalone(style, cover):
    return f"""<!DOCTYPE html><html lang="zh-CN"><head><meta charset="UTF-8">
<title>cover</title>
<style>
{style}
/* ===== 提取覆盖：仅渲染封面，白底，固定 A4 逻辑尺寸 ===== */
* {{ margin:0 !important; padding:0 !important; box-sizing:border-box !important; }}
html, body {{ width:{W_LOGICAL}px; height:{H_LOGICAL}px; background:#ffffff; }}
.cover {{ page:auto !important; page-break-after:auto !important; page-break-before:auto !important;
          width:{W_LOGICAL}px !important; height:{H_LOGICAL}px !important;
          -webkit-print-color-adjust:exact !important; print-color-adjust:exact !important; }}
</style></head><body>
{cover}
</body></html>"""

def screenshot(html_uri, png_path):
    cmd = [
        EDGE, "--headless=new", "--no-sandbox", "--disable-gpu",
        "--hide-scrollbars", "--no-first-run", "--no-default-browser-check",
        "--disable-extensions", "--force-device-scale-factor=2",
        f"--user-data-dir={PROFILE}", f"--window-size={W_LOGICAL},{H_LOGICAL}",
        f"--screenshot={png_path}", "--virtual-time-budget=12000", html_uri,
    ]
    return subprocess.run(cmd, capture_output=True, text=True, timeout=120)

def main():
    OUTDIR.mkdir(exist_ok=True)
    SCRATCH.mkdir(exist_ok=True)
    PROFILE.mkdir(exist_ok=True)
    books = sorted([p for p in BATCH.iterdir() if p.is_dir() and re.match(r"\d{2}_", p.name)])
    ok, fail = [], []
    for b in books:
        nn = b.name[:2]
        htmls = list(b.glob("*.html"))
        if not htmls:
            fail.append((nn, "无HTML")); continue
        html_path = htmls[0]
        try:
            style, cover, title = extract(html_path)
            tmp_html = SCRATCH / f"cover_{nn}.html"
            tmp_html.write_text(build_standalone(style, cover), encoding="utf-8")
            out_png = OUTDIR / f"{nn}_{sanitize(title)}.png"
            if out_png.exists():
                out_png.unlink()   # 单文件覆盖，非批量删除
            r = screenshot(tmp_html.as_uri(), str(out_png))
            if out_png.exists() and out_png.stat().st_size > 2000:
                ok.append((out_png.name, out_png.stat().st_size // 1024))
            else:
                fail.append((nn, f"截图缺失/过小 rc={r.returncode} err={r.stderr[-200:]}"))
        except Exception as e:
            fail.append((nn, str(e)[:200]))
    print("=== 成功 %d / 失败 %d ===" % (len(ok), len(fail)))
    for name, kb in ok:
        print(f"  OK  {name}  ({kb} KB)")
    for x in fail:
        print("  FAIL", x)

if __name__ == "__main__":
    main()
