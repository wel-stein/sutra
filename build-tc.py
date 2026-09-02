#!/usr/bin/env python3
"""从 index.html 生成繁体版 tc/index.html（需要: pip install opencc-python-reimplemented）
   修改简体主页后重新运行本脚本即可同步繁体版。"""
from opencc import OpenCC
import os

cc = OpenCC("s2tw")
out = cc.convert(open("index.html", encoding="utf-8").read())

patches = [
    ('<html lang="zh-CN">', '<html lang="zh-Hant">'),
    ('<link rel="canonical" href="https://dabeixin.org/">',
     '<link rel="canonical" href="https://dabeixin.org/tc/">'),
    ('<meta property="og:url" content="https://dabeixin.org/">',
     '<meta property="og:url" content="https://dabeixin.org/tc/">'),
    ('<meta property="og:locale" content="zh_CN">', '<meta property="og:locale" content="zh_TW">'),
    ('"@id": "https://dabeixin.org/#webpage",\n      "url": "https://dabeixin.org/",',
     '"@id": "https://dabeixin.org/tc/#webpage",\n      "url": "https://dabeixin.org/tc/",'),
    ('"inLanguage": "zh-CN"', '"inLanguage": "zh-Hant"'),
    ('<a class="lang-switch" href="/tc/">繁體</a>', '<a class="lang-switch" href="/">简体</a>'),
    ('<a class="wiki-link" href="/wiki/">', '<a class="wiki-link" href="/tc/wiki/">'),
]
for old, new in patches:
    assert old in out, f"patch source missing: {old[:60]}"
    out = out.replace(old, new)

os.makedirs("tc", exist_ok=True)
open("tc/index.html", "w", encoding="utf-8").write(out)
print("tc/index.html generated,", len(out), "bytes")
