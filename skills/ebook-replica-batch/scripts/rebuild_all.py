# -*- coding: utf-8 -*-
"""全量重建批次内所有书的 PDF。

用法：把本脚本复制到批次根目录（与 NN_书名 同级），运行：
        python rebuild_all.py
默认重建所有书；可指定前缀只看部分：
        python rebuild_all.py 05 06

依据：每本目录内必须有 build_book.py（或把 ebook-factory 的 build_book.py 复制进去）。
只重建、不改稿件；PDF 成功与否以 returncode + 目录内存在 .pdf 判定。
"""
import subprocess, sys, os, time, glob

ROOT = os.path.dirname(os.path.abspath(__file__))
PREFIX = sys.argv[1:]
PY = sys.executable

books = []
for d in sorted(glob.glob(os.path.join(ROOT, "[0-9][0-9]_*"))):
    if not os.path.isdir(d):
        continue
    name = os.path.basename(d)
    if PREFIX and not any(name.startswith(p) for p in PREFIX):
        continue
    books.append(d)

if not books:
    print("未找到 NN_书名 目录。请在本脚本同级放书目录，或指定正确前缀。")
    sys.exit(1)

ok = []
t_all = time.time()
for d in books:
    name = os.path.basename(d).split("_", 1)[-1]
    if not os.path.exists(os.path.join(d, "build_book.py")):
        print(f"[SKIP] {name:26s} 缺 build_book.py"); continue
    t0 = time.time()
    r = subprocess.run([PY, "build_book.py"], cwd=d,
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    pdfs = [f for f in os.listdir(d) if f.lower().endswith(".pdf")]
    if r.returncode == 0 and pdfs:
        p = os.path.join(d, pdfs[0])
        print(f"[OK]   {name:26s} {time.time()-t0:5.1f}s  {os.path.getsize(p):>10,} bytes")
        ok.append(name)
    else:
        print(f"[FAIL] {name:26s} rc={r.returncode}")
        print(r.stdout[-400:])
        print(r.stderr[-700:])

print("-" * 72)
print(f"重建完成：成功 {len(ok)} / {len(books)}，总耗时 {time.time()-t_all:.1f}s")
