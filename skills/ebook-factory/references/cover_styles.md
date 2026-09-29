# 多风格封面模板（build_book_multistyle.py）

`scripts/build_book_multistyle.py` 在原 `build_book.py`（开窍系列单一封面）之外，提供 **4 种可切换的封面风格**，并支持用同目录 `config.json` 覆盖内置配置（`cover` 字段做浅合并）。

典型场景：给一批「对标账号」做复刻书，每本书的封面复刻对标账号**浏览量最高商品**的视觉风格。

## 用法

```bash
# 在书目目录下放 config.json + chapters/*.md，然后：
python build_book_multistyle.py                     # 用 config.json 的 cover_style
python build_book_multistyle.py --cover-style vintage --out 书名
```

改完构建器后，若各书目目录各存了一份 `build_book.py`，需 **先 cp 覆盖再跑**（否则改的是 `_build/` 里的副本）。

## 四种风格

| style | 视觉 | 元素位置 | 微信/CTA 落点 |
|---|---|---|---|
| `gold_dark` | 墨绿黑底 + 金色衬线渐变大字 + 编号圆形清单卡 | 顶栏「分类 + 药丸」、中部大标题、右侧同心圆弧、底部清单卡 | 新增 `.cv-gold-cta`（副标题下方 `top:174mm` 居中金色字） |
| `vintage` | 仿古泛黄纸 + 红色楷书大字 + 菱形分隔线 | 纸面内居中：书名 / 装饰线 / 引言 / 三行短句 / 角标 | `cover.badge` |
| `minimal` | 黄绿底 + 半透明大色块 + 黑体大字 + 斜排淡色水印 | 满版卡片居中标题，底部一枚半透明按钮 | `cover.btn`（按钮） |
| `book3d` | 深蓝黑底 + 3D 立体书（书脊/书页/高光）+ 金属金大字 | 书面上部标题、下部信息板（`◆` 列表） | `cover.badge` |

## config.json schema（`cover` 字段）

```jsonc
{
  "title": "书名", "author": "加微信xxxx进读者群",
  "series_label": "分类 · 第N册", "accent": "#c9a227",
  "cover_style": "book3d",
  "cover": {
    // gold_dark
    "top_left": "商业 · 认知", "pill": "思维升级",
    "title_lines": ["一天赚十万", "逻辑"],   // 手动控制断行
    "sub_lines": ["…", "…"],
    "items": ["…", "…", "…"],
    "footer_left": "屋里涛说 原创整理", "footer_right": "NO.001",

    // vintage
    "quote": "这本没空话",
    "title_size": 56, "title_spacing": 8,    // 6 字书名防折行
    "sub_lines": ["…", "…", "…"], "badge": "加微信xxxx进读者群",

    // minimal
    "title_lines": ["人性算法", "拆穿所有", "伪装"],
    "btn": "加微信xxxx进读者群",
    "watermark": "屋里涛说 · 原创",           // 斜排淡色水印，勿与页脚重复

    // book3d
    "title_lines": ["利益捆绑", "才是最牢关系"],
    "quote": "…", "items": ["…", "…", "…"], "badge": "加微信xxxx进读者群"
  }
}
```

## 坑位（实测）

1. **书名折行**：`vintage` 默认 62pt 会把 6 字书名挤出纸面。改用 `title_size`≤56 + `title_spacing`8，并加 `white-space:nowrap`。
2. **按钮折行**：`minimal` 的 `.cv-min-btn` 只设了 `left:50%`，宽度受容器限制，长文案会折行。必须加 `white-space:nowrap` 并把字号降到 13pt。
3. **页脚重复**：`minimal` 原模板页脚写成 `footer_right · author`，当 `author` 就是按钮上的微信时会重复。改为页脚只放品牌行，`author` 只出现在按钮上。
4. **书名贴顶**：`book3d` 的 `.cv3-face` 若用 padding 定位，标题会顶在最上。改为 `padding:0` + `.cv3-head { position:absolute; top:14mm; bottom:52mm; display:flex; justify-content:center; }` 垂直居中，给底部信息板留位。
5. **署名要统一三处**：封面 CTA、序言落款、结语落款。用户要求「作者改成微信」时三处都要改（`——加微信xxxx进读者群`）。
6. **A4 一致性核验**：用 PyMuPDF 检查每页 `rect` 是否统一为 595×842，防止某页被 `@page` 规则带偏。
