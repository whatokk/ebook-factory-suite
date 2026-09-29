# -*- coding: utf-8 -*-
"""
跨书重复度检测：发现 20 本书之间复用的套话句 / 段落。
只读，不改任何文件。
"""
import os, re, json, collections, itertools, sys

ROOT = os.path.dirname(os.path.abspath(__file__))
SKIP = {'_素材', '_写作规范_共用.md'}

def book_dirs():
    out = []
    for n in sorted(os.listdir(ROOT)):
        p = os.path.join(ROOT, n)
        if os.path.isdir(p) and not n.startswith('_') and os.path.isdir(os.path.join(p, 'chapters')):
            out.append((n, p))
    return out

def sentences(text):
    """切句：按中文句末标点切，去掉标题行与空行"""
    lines = []
    for ln in text.split('\n'):
        s = ln.strip()
        if not s or s.startswith('#') or s.startswith('>'):
            continue
        s = re.sub(r'^\s*[\-\*\d\.\)]\s*', '', s)
        lines.append(s)
    joined = '\n'.join(lines)
    split = re.split(r'(?<=[。！？!?])', joined)
    res = []
    for p in split:
        p = p.strip().strip('|')
        p = re.sub(r'[\*`]', '', p)
        p = p.strip()
        if len(p) >= 12 and re.search(r'[\u4e00-\u9fff]', p):
            res.append(p)
    return res

def main():
    books = book_dirs()
    per_book = {}                     # 书名 -> set(句子)
    sent_owners = collections.defaultdict(set)   # 句子 -> {书名}
    sent_files = collections.defaultdict(set)
    total_sent = 0

    for name, p in books:
        chdir = os.path.join(p, 'chapters')
        s_all = []
        for fn in sorted(os.listdir(chdir)):
            if not fn.endswith('.md'):
                continue
            t = open(os.path.join(chdir, fn), encoding='utf-8').read()
            for s in sentences(t):
                s_all.append(s)
                sent_owners[s].add(name)
                sent_files[s].add((name, fn))
        per_book[name] = s_all
        total_sent += len(s_all)

    # 去重句总数
    uniq = len(sent_owners)
    print(f'书籍数: {len(books)}   有效句总数: {total_sent}   去重后: {uniq}')
    print(f'整体去重率: {(1 - uniq / total_sent) * 100:.2f}%  (纯篇内重复)')
    print('-' * 78)

    # 跨书重复（≥2 本都出现）
    cross = {s: o for s, o in sent_owners.items() if len(o) >= 2}
    print(f'跨书重复句（出现在 >=2 本书）: {len(cross)} 句')
    cross3 = {s: o for s, o in cross.items() if len(o) >= 3}
    print(f'  其中出现在 >=3 本书: {len(cross3)} 句')
    print()

    if cross:
        # 按覆盖书数排序，输出 Top 40
        ranked = sorted(cross.items(), key=lambda kv: -len(kv[1]))
        print('--- 跨书重复句 Top 40 ---')
        for s, owners in ranked[:40]:
            print(f'[{len(owners):2d}本] {s[:90]}')
        print()

    # 篇内高重复句（同一本书内出现 >=3 次）
    print('--- 篇内高频句（同书内出现 >=3 次）---')
    within_hits = 0
    for name, s_all in per_book.items():
        c = collections.Counter(s_all)
        hot = [(s, n) for s, n in c.items() if n >= 3]
        if hot:
            within_hits += len(hot)
            print(f'\n{name}:')
            for s, n in sorted(hot, key=lambda x: -x[1])[:6]:
                print(f'   x{n}  {s[:80]}')
    if within_hits == 0:
        print('（无）')

    # 段首/结尾套话检测
    print()
    print('--- 疑似通用套话开头（出现在 >=4 本书的相同前 10 字）---')
    heads = collections.Counter()
    head_books = collections.defaultdict(set)
    for name, s_all in per_book.items():
        for s in s_all:
            h = s[:10]
            if not re.search(r'[\u4e00-\u9fff]', h):   # 过滤纯符号/分隔线
                continue
            heads[h] += 1
            head_books[h].add(name)
    bad = [(h, len(head_books[h]), c) for h, c in heads.items() if len(head_books[h]) >= 4]
    bad.sort(key=lambda x: -x[1])
    for h, nb, c in bad[:25]:
        print(f'[{nb}本 x{c}次] {h}...')
    if not bad:
        print('（无）')

    # 落盘原始数据备用
    with open(os.path.join(ROOT, '_dup_report.json'), 'w', encoding='utf-8') as f:
        json.dump({
            'total_books': len(books),
            'total_sentences': total_sent,
            'unique_sentences': uniq,
            'cross_book_dups': {s: sorted(o) for s, o in ranked} if cross else {},
            'cross_book_dup_count': len(cross),
            'cross_book_dup3_count': len(cross3),
        }, f, ensure_ascii=False, indent=1)
    print()
    print('原始数据已写入 _dup_report.json')

if __name__ == '__main__':
    main()
