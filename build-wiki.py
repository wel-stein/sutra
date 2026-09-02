#!/usr/bin/env python3
"""灵界志 — 通灵口述知识库 静态站生成器

由 data/*.json 生成：
    wiki/index.html            词条总览（简体）
    wiki/<slug>/index.html     词条页（简体）
    wiki/<medium>/index.html   通灵者页（简体）
    tc/wiki/...                以上各页的繁体版（需要 opencc-python-reimplemented）

同时把 wiki 的 URL 写回 sitemap.xml 中 <!-- wiki:start --> / <!-- wiki:end --> 之间。

用法：
    pip install opencc-python-reimplemented
    python3 build-wiki.py
"""
import html
import json
import os
import re
import shutil

SITE = "https://dabeixin.org"
ROOT = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(ROOT, "data")

WIKI_NAME = "灵界志"
WIKI_SUB = "通灵口述知识库"
CATEGORY_ORDER = ["彼岸地理", "灵体与存有", "法门与实践", "因果与命理", "通灵者之道", "案例记录"]

# ---------------------------------------------------------------- 读取数据

def load(name):
    with open(os.path.join(DATA, name), encoding="utf-8") as f:
        return json.load(f)

SOURCES = load("sources.json")
MEDIUMS = load("mediums.json")
ENTRIES = load("entries.json")

ENTRY_BY_SLUG = {e["slug"]: e for e in ENTRIES}

def validate():
    """数据自检：交叉引用必须都指得到，slug 不可重复。"""
    errs = []
    seen = set()
    for e in ENTRIES:
        if e["slug"] in seen:
            errs.append(f"词条 slug 重复：{e['slug']}")
        seen.add(e["slug"])
        if e["category"] not in CATEGORY_ORDER:
            errs.append(f"{e['slug']}：未知分类「{e['category']}」")
        for ref in e.get("see", []):
            if ref not in ENTRY_BY_SLUG and ref not in MEDIUMS:
                errs.append(f"{e['slug']}：相关词条指向不存在的 {ref}")
        for acc in e["accounts"]:
            if acc["medium"] not in MEDIUMS:
                errs.append(f"{e['slug']}：未知通灵者 {acc['medium']}")
            if acc["source"] not in SOURCES:
                errs.append(f"{e['slug']}：未知出处 {acc['source']}")
    for slug, m in MEDIUMS.items():
        for s in m.get("sources", []):
            if s not in SOURCES:
                errs.append(f"通灵者 {slug}：未知出处 {s}")
    if slug_conflicts := seen & set(MEDIUMS):
        errs.append(f"词条与通灵者 slug 撞车：{'、'.join(sorted(slug_conflicts))}")
    if errs:
        raise SystemExit("数据校验失败：\n  - " + "\n  - ".join(errs))

# ---------------------------------------------------------------- 小工具

def esc(s):
    return html.escape(s, quote=True)

def plain(s):
    """给 meta description 用：去掉标点噪音，截断。"""
    s = re.sub(r"\s+", "", s)
    return s[:150]

def entries_of(medium_slug):
    return [e for e in ENTRIES if any(a["medium"] == medium_slug for a in e["accounts"])]

def speakers(entry):
    return [MEDIUMS[a["medium"]]["name"] for a in entry["accounts"]]

def search_key(entry):
    """索引页搜索用的关键词：标题、别称、说话人（含其别名，如「芳姐」）、摘要。"""
    names = []
    for a in entry["accounts"]:
        m = MEDIUMS[a["medium"]]
        names += [m["name"], *m.get("aliases", [])]
    return " ".join([entry["title"], *entry.get("aliases", []),
                     *dict.fromkeys(names), entry["lead"]])

def multi_note(entry):
    """列表卡片上的「多家说法」标记；只有一家时不显示。"""
    names = speakers(entry)
    if len(names) < 2:
        return ""
    return f'<div class="m">◆ {len(names)} 家说法：{esc("、".join(names))}</div>'

def by_category(entries):
    out = []
    for cat in CATEGORY_ORDER:
        group = [e for e in entries if e["category"] == cat]
        if group:
            out.append((cat, group))
    return out

# ---------------------------------------------------------------- 样式

CSS = """
:root{
  --bg:#1d1410; --card:#2a201a; --card2:#241b15;
  --gold:#c9a25e; --gold-dim:#8f7344;
  --text:#efe6d8; --text-dim:#b3a693; --line:#3d2f24;
  --mist:#8fa9a6;
}
*{margin:0;padding:0;box-sizing:border-box}
/* 必须显式声明：.tile 等作者样式的 display 会盖过浏览器默认的 [hidden]{display:none} */
[hidden]{display:none!important}
html{scroll-behavior:smooth}
body{
  background:var(--bg);color:var(--text);
  font-family:"Noto Serif TC","Noto Serif SC","Source Han Serif SC","STKaiti","KaiTi","DFKai-SB","STSong","SimSun",serif;
  line-height:1.85;
}
a{color:var(--gold-dim);text-decoration:none;transition:color .2s}
a:hover{color:var(--gold)}
.wrap{max-width:880px;margin:0 auto;padding:0 16px}

/* ---- 页眉 ---- */
.top{
  position:relative;text-align:center;padding:40px 16px 22px;
  background:radial-gradient(ellipse 70% 100% at 50% 0%,#34261c 0%,transparent 70%);
}
.top .mark{font-size:27px;color:var(--gold);letter-spacing:8px}
.top h1{
  font-size:clamp(27px,5.4vw,39px);letter-spacing:.2em;color:var(--gold);
  font-weight:600;margin:8px 0 6px;
}
.top .sub{color:var(--text-dim);font-size:15px;letter-spacing:.3em}
.top .home{
  position:absolute;top:16px;left:16px;
  border:1px solid var(--line);border-radius:999px;padding:4px 14px;
  font-size:14px;letter-spacing:.08em;color:var(--gold-dim);
}
.top .home:hover{border-color:var(--gold-dim)}
.lang-switch{
  position:absolute;top:16px;right:16px;
  color:var(--gold-dim);border:1px solid var(--line);border-radius:999px;
  padding:4px 14px;font-size:14px;letter-spacing:.1em;
}
.lang-switch:hover{color:var(--gold);border-color:var(--gold-dim)}
.divider{display:flex;align-items:center;justify-content:center;gap:14px;margin:18px auto 0;color:var(--gold-dim)}
.divider::before,.divider::after{content:"";height:1px;width:min(120px,22vw);background:linear-gradient(90deg,transparent,var(--gold-dim))}
.divider::after{background:linear-gradient(270deg,transparent,var(--gold-dim))}

/* ---- 面包屑 ---- */
.crumb{
  padding:18px 0 0;color:var(--text-dim);font-size:14px;letter-spacing:.08em;
}
.crumb a{color:var(--gold-dim)}
.crumb i{font-style:normal;opacity:.5;margin:0 8px}

section{padding:22px 0}
.card{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:24px 26px}
h2{color:var(--gold);font-size:21px;letter-spacing:.22em;margin-bottom:16px;font-weight:600}
h2.mid{text-align:center}
h3{color:var(--gold);font-size:17.5px;letter-spacing:.12em;font-weight:600;margin:22px 0 8px}
p{margin-bottom:12px;font-size:17.5px}
p:last-child{margin-bottom:0}
.indent p{text-indent:2em}
ul{margin:0 0 12px 1.1em}
li{margin-bottom:6px;font-size:17px}

/* ---- 提示条 ---- */
.notice{
  background:var(--card2);border:1px solid var(--line);border-left:3px solid var(--gold-dim);
  border-radius:8px;padding:14px 18px;color:var(--text-dim);font-size:15.5px;line-height:1.75;
}
.notice b{color:var(--gold-dim)}

/* ---- 条目标题区 ---- */
.entry-head h1{
  color:var(--gold);font-size:clamp(27px,5.2vw,35px);letter-spacing:.14em;font-weight:600;margin-bottom:8px;
}
.chips{display:flex;flex-wrap:wrap;gap:8px;margin-bottom:14px}
.chip{
  border:1px solid var(--line);border-radius:999px;padding:2px 12px;
  font-size:13.5px;letter-spacing:.08em;color:var(--mist);background:var(--card2);
}
.chip.cat{color:var(--gold-dim)}
.chip.multi{color:var(--bg);background:var(--mist);border-color:var(--mist)}

/* ---- 多家说法标记 ---- */
.multi-tag{
  display:inline-block;vertical-align:middle;margin-left:10px;
  border:1px solid var(--mist);border-radius:999px;padding:1px 10px;
  font-size:13px;letter-spacing:.06em;color:var(--mist);
}
.tile .m{color:var(--mist);font-size:13px;letter-spacing:.06em;margin-top:5px}
.alias{color:var(--text-dim);font-size:15px;letter-spacing:.05em;margin-bottom:14px}
.lead{
  font-size:18px;color:var(--text);border-left:3px solid var(--gold-dim);
  padding-left:16px;margin-bottom:4px;
}

/* ---- 口述块 ---- */
.account{margin-top:20px}
.account .who{
  display:flex;flex-wrap:wrap;align-items:baseline;gap:10px;
  border-bottom:1px solid var(--line);padding-bottom:8px;margin-bottom:14px;
}
.account .who .name{color:var(--gold);font-size:18px;letter-spacing:.12em;font-weight:600}
.account .who .tag{color:var(--text-dim);font-size:14px;letter-spacing:.08em}
blockquote{
  border-left:2px solid var(--gold-dim);background:var(--card2);
  border-radius:0 8px 8px 0;padding:10px 16px;margin:14px 0;
  color:var(--gold);font-size:17.5px;letter-spacing:.04em;
}
.cite{
  margin-top:14px;padding-top:12px;border-top:1px dashed var(--line);
  color:var(--text-dim);font-size:14px;letter-spacing:.04em;line-height:1.7;
}
.cite a{word-break:break-all}

/* ---- 档案表 ---- */
.profile{width:100%;border-collapse:collapse;margin-bottom:4px}
.profile th,.profile td{
  border-bottom:1px solid var(--line);padding:9px 4px;text-align:left;
  font-size:16.5px;vertical-align:top;font-weight:400;
}
.profile th{color:var(--gold-dim);white-space:nowrap;width:6.5em;letter-spacing:.08em}
.profile tr:last-child th,.profile tr:last-child td{border-bottom:none}

/* ---- 列表与卡片 ---- */
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:10px}
.tile{
  display:block;background:var(--card2);border:1px solid var(--line);border-radius:9px;
  padding:12px 16px;color:var(--text);
}
.tile:hover{border-color:var(--gold-dim);color:var(--text)}
.tile .t{color:var(--gold);font-size:17.5px;letter-spacing:.08em}
.tile .d{color:var(--text-dim);font-size:14px;line-height:1.65;margin-top:4px}

.person{
  display:flex;gap:16px;align-items:flex-start;background:var(--card2);
  border:1px solid var(--line);border-radius:10px;padding:18px 20px;color:var(--text);
}
.person:hover{border-color:var(--gold-dim);color:var(--text)}
.person .sigil{
  flex:none;width:52px;height:52px;border-radius:50%;border:1px solid var(--gold-dim);
  display:flex;align-items:center;justify-content:center;color:var(--gold);font-size:23px;
}
.person .n{color:var(--gold);font-size:20px;letter-spacing:.12em}
.person .r{color:var(--mist);font-size:14px;letter-spacing:.08em;margin-left:8px}
.person .d{color:var(--text-dim);font-size:15px;line-height:1.7;margin-top:5px}

.catblock{margin-bottom:22px}
.catblock:last-child{margin-bottom:0}
.cathead{
  display:flex;align-items:baseline;gap:10px;margin-bottom:10px;
  color:var(--gold);font-size:17px;letter-spacing:.2em;
}
.cathead span{color:var(--text-dim);font-size:13.5px;letter-spacing:.05em}

/* ---- 搜索 ---- */
.search{
  width:100%;background:var(--card2);border:1px solid var(--line);border-radius:9px;
  padding:11px 16px;color:var(--text);font-family:inherit;font-size:17px;letter-spacing:.06em;
}
.search:focus{outline:none;border-color:var(--gold-dim)}
.search::placeholder{color:var(--text-dim)}
.empty{color:var(--text-dim);font-size:15.5px;text-align:center;padding:14px 0}

footer{text-align:center;color:var(--text-dim);font-size:14px;padding:34px 16px 48px;letter-spacing:.12em}
footer .credit{margin-top:10px;font-size:13px;letter-spacing:.04em;opacity:.85;line-height:1.8}
"""

# ---------------------------------------------------------------- 页面骨架

def page(lang, path, title, desc, body, jsonld=None, script=""):
    """lang: 'sc' | 'tc'；path: 站内路径，如 '/wiki/difu/'（简体版路径）"""
    tc = lang == "tc"
    sc_url = SITE + path
    tc_url = SITE + "/tc" + path
    canonical = tc_url if tc else sc_url
    ld = ""
    if jsonld:
        ld = '<script type="application/ld+json">\n%s\n</script>\n' % json.dumps(
            jsonld, ensure_ascii=False, indent=2
        )
    return f"""<!DOCTYPE html>
<html lang="{'zh-Hant' if tc else 'zh-CN'}">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<link rel="canonical" href="{canonical}">
<link rel="alternate" hreflang="zh-Hans" href="{sc_url}">
<link rel="alternate" hreflang="zh-Hant" href="{tc_url}">
<link rel="alternate" hreflang="x-default" href="{sc_url}">
<meta name="theme-color" content="#1d1410">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="icon" href="/favicon.ico" sizes="48x48">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
<meta property="og:type" content="article">
<meta property="og:site_name" content="{WIKI_NAME} · dabeixin.org">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:url" content="{canonical}">
<meta property="og:image" content="{SITE}/og-image.jpg">
<meta property="og:locale" content="{'zh_TW' if tc else 'zh_CN'}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{esc(title)}">
<meta name="twitter:description" content="{esc(desc)}">
<meta name="twitter:image" content="{SITE}/og-image.jpg">
{ld}<style>{CSS}</style>
</head>
<body>
{body}
<footer>
  记录者不等于见证者 ❖ 存疑而不轻慢
  <div class="credit">{WIKI_NAME}收录的是通灵者本人的口述，本站只作整理与索引，不作事实断言。<br>
  内容不构成医疗、法律、投资或任何决策建议。</div>
</footer>
{script}</body>
</html>
"""

def header(lang, current):
    """current: 'index' | 'entry'（决定语言切换按钮指向哪里）"""
    tc = lang == "tc"
    p = "/tc" if tc else ""
    other = current if tc else "/tc" + current   # 语言切换指向同一页的另一版本
    return f"""<div class="top">
  <a class="home" href="{p}/">← 大悲咒</a>
  <a class="lang-switch" href="{other}">{'简体' if tc else '繁體'}</a>
  <div class="mark">☰</div>
  <h1>{WIKI_NAME}</h1>
  <div class="sub">{WIKI_SUB}</div>
  <div class="divider">❖</div>
</div>
"""

def crumb(lang, trail):
    p = "/tc" if lang == "tc" else ""
    bits = [f'<a href="{p}/">大悲咒</a>', f'<a href="{p}/wiki/">{WIKI_NAME}</a>']
    bits += [esc(t) for t in trail]
    return '<div class="wrap"><div class="crumb">' + '<i>›</i>'.join(bits) + "</div></div>\n"

# ---------------------------------------------------------------- 内容块渲染

def render_blocks(blocks):
    out = []
    for b in blocks:
        t = b["t"]
        if t == "p":
            out.append(f"<p>{esc(b['v'])}</p>")
        elif t == "h":
            out.append(f"<h3>{esc(b['v'])}</h3>")
        elif t == "ul":
            items = "".join(f"<li>{esc(x)}</li>" for x in b["v"])
            out.append(f"<ul>{items}</ul>")
        elif t == "quote":
            out.append(f"<blockquote>「{esc(b['v'])}」</blockquote>")
        else:
            raise SystemExit(f"未知内容块类型：{t}")
    return "\n".join(out)

def render_cite(src_id):
    s = SOURCES[src_id]
    parts = [f'出处：<a href="{esc(s["url"])}" target="_blank" rel="noopener">{esc(s["title"])}</a>']
    meta = " · ".join(x for x in [s.get("program"), s.get("type"), s.get("length")] if x)
    if meta:
        parts.append(meta)
    if s.get("host"):
        parts.append("主持：" + esc(s["host"]))
    if s.get("note"):
        parts.append(esc(s["note"]))
    return '<div class="cite">' + "<br>".join(parts) + "</div>"

def render_account(acc, lang, show_link=True):
    p = "/tc" if lang == "tc" else ""
    m = MEDIUMS[acc["medium"]]
    name = esc(m["name"])
    if show_link:
        name = f'<a href="{p}/wiki/{acc["medium"]}/" style="color:inherit">{name}</a>'
    return f"""<div class="account">
  <div class="who">
    <span class="name">{name}</span>
    <span class="tag">{esc(m["title"])} · {esc(m["region"])}</span>
    <span class="tag">口述</span>
  </div>
  {render_blocks(acc["blocks"])}
  {render_cite(acc["source"])}
</div>"""

# ---------------------------------------------------------------- 页面：词条

def build_entry(entry, lang):
    p = "/tc" if lang == "tc" else ""
    path = f"/wiki/{entry['slug']}/"
    speakers = "、".join(sorted({MEDIUMS[a["medium"]]["name"] for a in entry["accounts"]}))
    title = f"{entry['title']}｜{WIKI_NAME} · {WIKI_SUB}"

    n_acc = len(entry["accounts"])
    chips = [f'<span class="chip cat">{esc(entry["category"])}</span>']
    chips += [f'<span class="chip">口述 · {esc(MEDIUMS[a["medium"]]["name"])}</span>'
              for a in entry["accounts"]]
    if n_acc > 1:
        chips.append(f'<span class="chip multi">{n_acc} 家说法</span>')
    heading = "口述内容"
    if n_acc > 1:
        heading += f'<span class="multi-tag">{n_acc} 家说法并列 · 不作调和</span>'
    alias = ""
    if entry.get("aliases"):
        alias = f'<div class="alias">又称：{esc("、".join(entry["aliases"]))}</div>'

    accounts = "\n".join(render_account(a, lang) for a in entry["accounts"])

    see = ""
    refs = [r for r in entry.get("see", []) if r in ENTRY_BY_SLUG]
    if refs:
        tiles = "\n".join(
            f'<a class="tile" href="{p}/wiki/{r}/"><div class="t">{esc(ENTRY_BY_SLUG[r]["title"])}</div>'
            f'<div class="d">{esc(ENTRY_BY_SLUG[r]["category"])}</div></a>'
            for r in refs
        )
        see = f"""
  <section>
    <h2>相关词条</h2>
    <div class="grid">
{tiles}
    </div>
  </section>"""

    body = header(lang, path) + crumb(lang, [entry["category"], entry["title"]]) + f"""
<div class="wrap">
  <section>
    <div class="card entry-head">
      <h1>{esc(entry["title"])}</h1>
      <div class="chips">{"".join(chips)}</div>
      {alias}
      <div class="lead">{esc(entry["lead"])}</div>
    </div>
  </section>

  <section>
    <div class="card">
      <h2>{heading}</h2>
{accounts}
    </div>
  </section>
{see}
</div>
"""
    jsonld = {
        "@context": "https://schema.org",
        "@type": "DefinedTerm",
        "name": entry["title"],
        "alternateName": entry.get("aliases", []),
        "description": entry["lead"],
        "inDefinedTermSet": {
            "@type": "DefinedTermSet",
            "name": f"{WIKI_NAME} · {WIKI_SUB}",
            "url": SITE + "/wiki/",
        },
        "url": SITE + path,
        "termCode": entry["slug"],
        "subjectOf": [
            {
                "@type": "CreativeWork",
                "name": SOURCES[a["source"]]["title"],
                "url": SOURCES[a["source"]]["url"],
                "creator": {"@type": "Person", "name": MEDIUMS[a["medium"]]["name"]},
            }
            for a in entry["accounts"]
        ],
    }
    desc = f"{entry['title']}：{plain(entry['lead'])}（口述：{speakers}）"
    return path, page(lang, path, title, desc, body, jsonld)

# ---------------------------------------------------------------- 页面：通灵者

def build_medium(slug, lang):
    p = "/tc" if lang == "tc" else ""
    m = MEDIUMS[slug]
    path = f"/wiki/{slug}/"
    title = f"{m['name']}（{m['title']}）｜{WIKI_NAME}"

    rows = "\n".join(
        f"<tr><th>{esc(x['k'])}</th><td>{esc(x['v'])}</td></tr>" for x in m.get("profile", [])
    )
    profile = f'<table class="profile">{rows}</table>' if rows else ""

    groups = by_category(entries_of(slug))
    total = sum(len(g) for _, g in groups)
    blocks = []
    for cat, group in groups:
        tiles = "\n".join(
            f'<a class="tile" href="{p}/wiki/{e["slug"]}/"><div class="t">{esc(e["title"])}</div>'
            f'<div class="d">{esc(plain(e["lead"])[:44])}…</div></a>'
            for e in group
        )
        blocks.append(
            f'<div class="catblock"><div class="cathead">{esc(cat)}<span>{len(group)} 条</span></div>'
            f'<div class="grid">\n{tiles}\n</div></div>'
        )

    srcs = "\n".join(render_cite(s) for s in m.get("sources", []))

    body = header(lang, path) + crumb(lang, ["通灵者", m["name"]]) + f"""
<div class="wrap">
  <section>
    <div class="card entry-head">
      <h1>{esc(m["name"])}</h1>
      <div class="chips">
        <span class="chip cat">通灵者</span>
        <span class="chip">{esc(m["title"])}</span>
        <span class="chip">{esc(m["region"])}</span>
        <span class="chip">{total} 条词条</span>
      </div>
      <div class="lead">{esc(m["lead"])}</div>
    </div>
  </section>

  <section>
    <div class="card">
      <h2>档案</h2>
      {profile}
    </div>
  </section>

  <section>
    <div class="card">
      <h2>自述</h2>
      {render_blocks(m["blocks"])}
    </div>
  </section>

  <section>
    <div class="card">
      <h2>其口述的词条</h2>
      {"".join(blocks)}
    </div>
  </section>

  <section>
    <div class="card">
      <h2>出处</h2>
      {srcs}
    </div>
  </section>
</div>
"""
    jsonld = {
        "@context": "https://schema.org",
        "@type": "Person",
        "name": m["name"],
        "jobTitle": m["title"],
        "description": m["lead"],
        "url": SITE + path,
        "subjectOf": [
            {"@type": "CreativeWork", "name": SOURCES[s]["title"], "url": SOURCES[s]["url"]}
            for s in m.get("sources", [])
        ],
    }
    return path, page(lang, path, title, f"{m['name']}，{m['title']}。{plain(m['lead'])}", body, jsonld)

# ---------------------------------------------------------------- 页面：总览

def build_index(lang):
    p = "/tc" if lang == "tc" else ""
    path = "/wiki/"

    people = "\n".join(
        f"""<a class="person" href="{p}/wiki/{slug}/">
      <div class="sigil">☯</div>
      <div>
        <div><span class="n">{esc(m["name"])}</span><span class="r">{esc(m["title"])} · {esc(m["region"])}</span></div>
        <div class="d">{esc(plain(m["lead"])[:88])}…</div>
        <div class="d" style="color:var(--gold-dim)">收录 {len(entries_of(slug))} 条词条 →</div>
      </div>
    </a>"""
        for slug, m in MEDIUMS.items()
    )

    blocks = []
    for cat, group in by_category(ENTRIES):
        tiles = "\n".join(
            f'<a class="tile" data-k="{esc(search_key(e))}" '
            f'href="{p}/wiki/{e["slug"]}/"><div class="t">{esc(e["title"])}</div>'
            f'<div class="d">{esc(plain(e["lead"])[:46])}…</div>{multi_note(e)}</a>'
            for e in group
        )
        blocks.append(
            f'<div class="catblock" data-cat><div class="cathead">{esc(cat)}<span>{len(group)} 条</span></div>'
            f'<div class="grid">\n{tiles}\n</div></div>'
        )

    body = header(lang, path) + f"""
<div class="wrap">

  <section>
    <div class="notice">
      <b>体例说明</b>　本站收录通灵者本人对另一维度的口述，逐条注明<b>是谁说的</b>、<b>在哪里说的</b>。
      各家说法未必一致，本站不作调和、不作裁断，也不代表本站认同其内容为事实。
      多位通灵者谈过同一件事的，一律并列收录于同一页供对读，列表上以
      <b>◆</b> 标出——地府、生死册、牛头马面这几条，正是各家说法出入最大的地方。
    </div>
  </section>

  <section>
    <h2>通灵者</h2>
    <div class="grid" style="grid-template-columns:1fr">
{people}
    </div>
  </section>

  <section>
    <h2>词条索引 <span style="color:var(--text-dim);font-size:14px;letter-spacing:.05em">共 {len(ENTRIES)} 条</span></h2>
    <input class="search" id="q" type="search" placeholder="搜索词条：地府、孟婆汤、改命、斋戒…" autocomplete="off">
    <div style="height:14px"></div>
    <div id="list">
{"".join(blocks)}
    </div>
    <div class="empty" id="none" hidden>没有匹配的词条</div>
  </section>

</div>
"""
    script = """<script>
const q = document.getElementById("q");
const cats = [...document.querySelectorAll("[data-cat]")];
const none = document.getElementById("none");
q.addEventListener("input", () => {
  const k = q.value.trim().toLowerCase();
  let hits = 0;
  for (const c of cats) {
    let shown = 0;
    for (const t of c.querySelectorAll(".tile")) {
      const ok = !k || t.dataset.k.toLowerCase().includes(k);
      t.hidden = !ok;
      if (ok) shown++;
    }
    c.hidden = shown === 0;
    hits += shown;
  }
  none.hidden = hits > 0;
});
</script>
"""
    jsonld = {
        "@context": "https://schema.org",
        "@type": "DefinedTermSet",
        "name": f"{WIKI_NAME} · {WIKI_SUB}",
        "description": "收录通灵者对彼岸世界的口述，逐条注明出处与说话人。",
        "url": SITE + path,
        "hasDefinedTerm": [
            {"@type": "DefinedTerm", "name": e["title"], "url": SITE + f"/wiki/{e['slug']}/"}
            for e in ENTRIES
        ],
    }
    desc = f"{WIKI_NAME}：收录通灵者口述的彼岸见闻，含地府、天庭、送灵、因果等 {len(ENTRIES)} 条词条，逐条注明说话人与出处。"
    return path, page(lang, path, f"{WIKI_NAME}｜{WIKI_SUB}", desc, body, jsonld, script)

# ---------------------------------------------------------------- 写盘

def write(path, lang, content):
    rel = ("tc" + path if lang == "tc" else path.lstrip("/")) + "index.html"
    dest = os.path.join(ROOT, rel)
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    with open(dest, "w", encoding="utf-8") as f:
        f.write(content)
    return rel

def update_sitemap(paths):
    sm = os.path.join(ROOT, "sitemap.xml")
    with open(sm, encoding="utf-8") as f:
        xml = f.read()
    urls = []
    for path in paths:
        urls.append(
            f"""  <url>
    <loc>{SITE}{path}</loc>
    <changefreq>monthly</changefreq>
    <xhtml:link rel="alternate" hreflang="zh-Hans" href="{SITE}{path}"/>
    <xhtml:link rel="alternate" hreflang="zh-Hant" href="{SITE}/tc{path}"/>
  </url>
  <url>
    <loc>{SITE}/tc{path}</loc>
    <changefreq>monthly</changefreq>
    <xhtml:link rel="alternate" hreflang="zh-Hans" href="{SITE}{path}"/>
    <xhtml:link rel="alternate" hreflang="zh-Hant" href="{SITE}/tc{path}"/>
  </url>"""
        )
    block = "<!-- wiki:start -->\n" + "\n".join(urls) + "\n  <!-- wiki:end -->"
    new, n = re.subn(r"<!-- wiki:start -->.*?<!-- wiki:end -->", block, xml, flags=re.S)
    if n != 1:
        raise SystemExit("sitemap.xml 缺少 <!-- wiki:start --> / <!-- wiki:end --> 标记")
    with open(sm, "w", encoding="utf-8") as f:
        f.write(new)

def main():
    validate()

    try:
        from opencc import OpenCC
    except ImportError:
        raise SystemExit("缺少依赖，请先执行：pip install opencc-python-reimplemented")
    cc = OpenCC("s2tw")

    # 清空旧产物，避免删掉词条后留下孤儿页
    for d in (os.path.join(ROOT, "wiki"), os.path.join(ROOT, "tc", "wiki")):
        shutil.rmtree(d, ignore_errors=True)

    builders = [build_index] + \
               [lambda lang, s=s: build_medium(s, lang) for s in MEDIUMS] + \
               [lambda lang, e=e: build_entry(e, lang) for e in ENTRIES]

    paths, count = [], 0
    for build in builders:
        path, sc_html = build("sc")
        paths.append(path)
        write(path, "sc", sc_html)
        write(path, "tc", cc.convert(build("tc")[1]))
        count += 2

    update_sitemap(paths)
    print(f"生成 {count} 个页面（{len(paths)} 页 × 简繁）")
    print(f"  通灵者 {len(MEDIUMS)} 位 · 词条 {len(ENTRIES)} 条 · 出处 {len(SOURCES)} 项")
    print("  sitemap.xml 已更新")

if __name__ == "__main__":
    main()
