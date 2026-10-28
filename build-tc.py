#!/usr/bin/env python3
"""从 dabei/index.html 生成繁体版 tc/dabei/index.html（需要: pip install opencc-python-reimplemented）
   修改简体主页后重新运行本脚本即可同步繁体版。"""
from opencc import OpenCC
import os

cc = OpenCC("s2tw")
out = cc.convert(open("dabei/index.html", encoding="utf-8").read())

patches = [
    ('<html lang="zh-CN">', '<html lang="zh-Hant">'),
    ('<link rel="canonical" href="https://dabeixin.org/dabei/">',
     '<link rel="canonical" href="https://dabeixin.org/tc/dabei/">'),
    ('<meta property="og:url" content="https://dabeixin.org/dabei/">',
     '<meta property="og:url" content="https://dabeixin.org/tc/dabei/">'),
    ('<meta property="og:locale" content="zh_CN">', '<meta property="og:locale" content="zh_TW">'),
    ('"@id": "https://dabeixin.org/dabei/#webpage",\n      "url": "https://dabeixin.org/dabei/",',
     '"@id": "https://dabeixin.org/tc/dabei/#webpage",\n      "url": "https://dabeixin.org/tc/dabei/",'),
    ('"inLanguage": "zh-CN"', '"inLanguage": "zh-Hant"'),
    ('<a class="lang-switch" href="/tc/dabei/">繁體</a>', '<a class="lang-switch" href="/dabei/">简体</a>'),
    ('<a class="wiki-link" href="/">← 首页</a>', '<a class="wiki-link" href="/tc/">← 首頁</a>'),
]
for old, new in patches:
    assert old in out, f"patch source missing: {old[:60]}"
    out = out.replace(old, new)

os.makedirs("tc/dabei", exist_ok=True)
open("tc/dabei/index.html", "w", encoding="utf-8").write(out)
print("tc/dabei/index.html generated,", len(out), "bytes")
