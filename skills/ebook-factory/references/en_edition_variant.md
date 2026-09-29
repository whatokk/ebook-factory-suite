# 英文版（美国版）变体：从中文系列派生的全套做法

> 适用场景：已有中文「开窍系列」，要出对应的英文版（面向美国读者）。
> 实测来源：2026-09 开窍系列第 23-32 册 + Straight Talk Series（10 本英文版）批次。

## 一、定位铁律：英文版是「本土化原创」，不是翻译

翻译稿在美国市场基本卖不动，原因是中国专属语汇（闲鱼、小红书、网盘拉新、公众号、私域）在美国读者那里等于零信息。

做法：
- 系列名换一个美国读者能记住的英文品牌（本批用 **The Straight Talk Series**，书号 Book 1..10）。
- 每本书自己起英文书名 + 副题，**不要**直译中文书名。
  例：`谈判开窍 / 把话说成你要的回答` → `Straight Talk on Negotiation / Say It So You Actually Get It`
- 章节骨架沿用中文版（同章数、同小节数），内容重写：换案例、换平台、换法规、换货币。
- 必换清单：平台（LinkedIn / Indeed / Glassdoor / Upwork / Etsy / eBay / DoorDash / Substack / TikTok）、
  支付（Zelle / Venmo）、金融（401(k) / IRA / HSA / FICA / W-2 / 1099 / IRS / credit score）、
  机构（HOA / small claims court / Better Business Bureau / state attorney general）、
  商业惯例（net-30 / security deposit / at-will employment / PTO）。
- 金额一律 USD，且给真实区间而不是形容词："A 5 percent raise on a $62,000 salary is about $3,100 a year" 胜过 "a meaningful increase"。
- 拼写用美式（color / organize / realize / judgment / license）。
- 涉法的书必须写「rules vary by state, confirm with a professional」，全篇不给法律意见。

## 二、build_book.py 英文变体的 7 处补丁

复制中文书模板后，逐项替换（实测全部必要）：

| # | 原值 | 英文版 |
|---|---|---|
| 1 | `<html lang="zh-CN">` | `<html lang="en-US">` |
| 2 | `@page { size: A4; margin: 20mm 18mm; }` | `@page { size: Letter; margin: 22mm 20mm; }` |
| 3 | `font-family:"Microsoft YaHei","微软雅黑","PingFang SC",sans-serif;` | `font-family:"Georgia","Times New Roman",serif;` |
| 4 | `.cover-title` `font-size:40pt; letter-spacing:8px` | `font-size:30pt; letter-spacing:1.5px`（英文标题长，8px 字距会爆版） |
| 5 | `.cover-kicker` `letter-spacing:6px; font-size:12pt` | `letter-spacing:2px; font-size:9.5pt` |
| 6 | `.cover-author` `letter-spacing:4px` | `letter-spacing:1px` |
| 7 | 模板识别 `paras[0].startswith("\u300c")` | `paras[0].startswith("\u201c")`（英文模板段用弯引号 “ 开头） |

第 7 条最关键：漏改的话，英文书里所有话术模板都不会渲染成模板框。

## 三、英文写作规范（对应 WRITING_GUIDE.md）

写在每本英文书目录下的 `WRITING_GUIDE.md`，核心：
- 口语化、第二人称、短句。先给结论，再给原因，再给怎么做。零术语、零励志标语。
- 每节 480-620 words；每章 6 节 + 120-180 word 章引言。
- 每节 6 拍：verdict → scene → mechanism → the move → worked example → landing line。
- 每节至少一段可照念的台词，**段首必须是弯引号 “**（供 build_book.py 识别）。
- 禁用：in today's fast-paced world / it's important to note / at the end of the day / delve /
  game-changer / unlock your potential / journey / navigate the landscape / firstly / secondly /
  in conclusion / leverage synergies / take it to the next level / the bottom line is。

## 四、质检口径差异

- 中文书禁用词 12 个（含「最后」）；英文书用英文禁用词表。
- 中文字数口径按字符数（每节 850-950）；英文按单词数（每节 480-620 words）。
- 一体质检脚本：项目根 `_qc_series.py`（自动按目录名是否含中文判断中英口径，支持 `--clean`）。
