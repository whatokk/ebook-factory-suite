# -*- coding: utf-8 -*-
"""批次质检：扫描 复刻电子书20 下每本书的 chapters/*.md，输出字数/章节数/「」话术数/禁用词/PDF 状态。
用法： python qc.py            # 全量
       python qc.py 05 06      # 只看指定前缀
"""
import glob, os, re, sys

# 硬禁：与 _写作规范_共用.md 第五节完全一致，出现即需改
BAD_WORDS = ['首先', '其次', '最后', '综上所述', '总而言之', '不难发现',
             '众所周知', '相信通过', '一方面', '另一方面', '值得注意的是',
             '在这个时代']
SOFT_WORDS = []
NEED_FILES = ['00_preface', '01_认知篇', '02_模式篇', '03_系统篇', '04_产品篇',
              '05_流量篇', '06_人性篇', '07_破局篇', '08_afterword']
MIN_WORDS = 30000


def need_files_for(book_dir):
    """优先从 config.json 的 toc_track 推导本书应有章节名；缺失时回退默认骨架。"""
    import json
    p = os.path.join(book_dir, 'config.json')
    if os.path.exists(p):
        try:
            cfg = json.load(open(p, encoding='utf-8'))
            track = cfg.get('toc_track', '')
            names = [x.strip() for x in track.split('·') if x.strip()]
            if len(names) == 7:
                out = ['00_preface']
                for i, n in enumerate(names, 1):
                    out.append('%02d_%s' % (i, n))
                out.append('08_afterword')
                return out
        except Exception:
            pass
    return NEED_FILES


def count(path):
    t = open(path, encoding='utf-8').read()
    return len(re.sub(r'\s', '', t)), t


def main():
    prefixes = sys.argv[1:]
    base = os.path.dirname(os.path.abspath(__file__))
    rows = []
    for d in sorted(glob.glob(os.path.join(base, '[0-9][0-9]_*'))):
        name = os.path.basename(d)
        if prefixes and not any(name.startswith(p) for p in prefixes):
            continue
        files = sorted(glob.glob(os.path.join(d, 'chapters', '*.md')))
        total = 0
        quotes = 0
        bad = {}
        soft = {}
        for f in files:
            w, t = count(f)
            total += w
            quotes += t.count('「')
            for b in BAD_WORDS:
                c = t.count(b)
                if c:
                    bad[b] = bad.get(b, 0) + c
            for b in SOFT_WORDS:
                c = t.count(b)
                if c:
                    soft[b] = soft.get(b, 0) + c
        have = [os.path.basename(f)[:-3] for f in files]
        missing = [n for n in need_files_for(d) if n not in have]
        pdfs = glob.glob(os.path.join(d, '*.pdf'))
        # PDF 是否比最新章节旧（stale）
        stale = ''
        if pdfs and files:
            newest_md = max(os.path.getmtime(f) for f in files)
            if os.path.getmtime(pdfs[0]) < newest_md:
                stale = '旧'
        rows.append({
            'name': name, 'files': len(files), 'words': total, 'quotes': quotes,
            'bad': bad, 'soft': soft, 'missing': missing,
            'pdf': (os.path.basename(pdfs[0]) + stale) if pdfs else '',
            'ok': not missing and total >= MIN_WORDS and not bad,
        })

    print('%-30s %4s %7s %5s %-8s %-14s %-16s %s' % (
        '书名', '章节', '字数', '「」', 'PDF', '缺失章节', '硬禁词', '软禁词'))
    print('-' * 128)
    for r in rows:
        print('%-30s %4d %7d %5d %-8s %-14s %-16s %s' % (
            r['name'], r['files'], r['words'], r['quotes'],
            r['pdf'] or '缺',
            ','.join(x[:2] for x in r['missing']) or '-',
            ','.join('%s×%d' % (k, v) for k, v in r['bad'].items()) or '-',
            ','.join('%s×%d' % (k, v) for k, v in r['soft'].items()) or '-'))
    print('-' * 128)
    done = sum(1 for r in rows if r['ok'])
    print('达标 %d / %d 本；总字数 %d' % (done, len(rows), sum(r['words'] for r in rows)))


if __name__ == '__main__':
    main()
