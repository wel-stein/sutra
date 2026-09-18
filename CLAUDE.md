# CLAUDE.md

**dabeixin.org** —— 纯静态佛教网站。没有框架、没有包管理、没有 CI；Vercel 从 `main` 直接部署整个仓库。
文档用简体中文，与站点主要语言、数据文件和历史提交信息保持一致。

---

## 最重要的一条

`wiki/` 与 `tc/` 底下的 HTML **全部是生成物，不要手改**。
唯一的事实来源是 `data/` 下的三个 JSON 加上两个构建脚本。手改生成物会在下一次构建时被无声覆盖。

---

## 站点由两部分组成

| 部分 | 路径 | 怎么来的 |
| --- | --- | --- |
| 大悲咒 · 八十四相 | `/`、`/tc/` | 手写 `index.html`；繁体版由 `build-tc.py` 转换生成 |
| 灵界志（通灵口述知识库） | `/wiki/`、`/tc/wiki/` | 全部由 `build-wiki.py` 从 `data/` 生成 |

八十四张化相图是 `01.webp` … `84.webp`（页面实际引用）；同名 `.png` / `.jpg` 是原始大图，
已在 `.vercelignore` 中排除，不参与部署。

---

## 目录

```
index.html          大悲咒主页（手写，简体）
tc/index.html       ↑ 的繁体版（生成物）
build-tc.py         由 index.html 生成 tc/index.html

data/               灵界志唯一事实来源
  sources.json        出处：一次访谈／影片／书
  mediums.json        通灵者档案与自述
  entries.json        词条（数组）
  README.md           数据格式与写作体例（改 data/ 前先读）
build-wiki.py       由 data/ 生成 wiki/ 与 tc/wiki/ 全部页面
wiki/ tc/wiki/      生成物

sitemap.xml         wiki 部分由 build-wiki.py 写回标记区间，其余手写
sw.js               PWA 离线缓存
vercel.json         仅设定静态资源缓存头
.vercelignore       原始大图、构建脚本、仓库文档不参与部署
```

---

## 构建

```bash
pip install opencc-python-reimplemented   # 只需一次，两个脚本都依赖
python3 build-wiki.py                     # 改了 data/ 之后必跑
python3 build-tc.py                       # 改了 index.html 之后必跑
```

两个脚本都可重复执行，输出稳定。生成结果要和源文件**一并提交**（Vercel 不做构建）。

- `build-wiki.py` 构建前会自检：slug 不可重复、词条与通灵者不可撞名、`see` 交叉引用与
  `source` / `medium` 必须指得到。有问题直接报错，不会生成半成品。
- `build-tc.py` 对 `index.html` 里的若干字符串做 `assert`。**改动 index.html 的 header、
  canonical、og 或语言切换链接时，必须同步更新脚本里的 `patches` 列表**，否则断言失败。

### 本地预览

```bash
python3 -m http.server 8899     # 然后开 http://localhost:8899/
```

容器里预装了 Chromium，可用 Playwright 截图核对排版：
`/opt/pw-browsers/chromium-1194/chrome-linux/chrome`（注意是带版本号的目录）。
`pip install playwright` 即可，**不要**跑 `playwright install`。

---

## 简繁双语

简体是源，繁体一律由 opencc `s2tw` 自动转换，**不要手写繁体页面**。

- 主页：`build-tc.py` 转换后再打补丁修正 canonical / og / hreflang / 语言切换链接。
- 灵界志：`build-wiki.py` 用 `prefix` 参数把同一页生成两次（`""` 与 `"/tc"`），
  再对繁体那份整体 `s2tw`。slug 是拼音，转换不会动到链接。

每页都带 canonical、hreflang（zh-Hans / zh-Hant / x-default）、og 与 schema.org 结构化数据。

---

## 灵界志的编辑体例

这部分是内容判断，不只是代码约定，改 `data/` 前请先读 `data/README.md`。核心三条：

1. **区分「谁说的」与「事实」。** 正文一律挂在具名的口述块下，写「她说」「他自述」，
   不写成断言句。页脚固定声明本站只作整理与索引。
2. **多家说法并列，不作调和。** 同一件事有第二位通灵者谈到，**不要另开词条**，
   往该条 `accounts` 数组追加一项。页面会自动并列、加标记，索引列表以 ◆ 标出。
   目前 79 条词条中有 11 条是两家并列——这是本站最有价值的部分。
3. **资料级别要标明。** 出处若不是逐字记录（例如影片没有字幕，只能依标题、
   官方简介与章节时间轴推得），必须在 source 填 `caveat`。页面会在口述内容**之前**
   显示虚线框声明依据。原则是**宁可少写，不要补齐**：细节从缺就写明从缺，
   不要凭常识或其他集数推测；连标题都撑不起具体说法的，只登记出处、不建词条。

分类共六个，顺序定义在 `build-wiki.py` 的 `CATEGORY_ORDER`：
彼岸地理 · 灵体与存有 · 法门与实践 · 因果与命理 · 通灵者之道 · 案例记录。

---

## 设计约定

配色与字体在两处各有一份（`index.html` 的 `<style>` 与 `build-wiki.py` 的 `CSS` 常量），
改动时注意同步：

```
--bg #1d1410   --card #2a201a   --card2 #241b15
--gold #c9a25e --gold-dim #8f7344
--text #efe6d8 --text-dim #b3a693 --line #3d2f24
--mist #8fa9a6（仅灵界志，用于分类标签与多家说法标记）
```

衬线字体栈，深色底金字，圆角卡片。**手机宽度必须无横向溢出**（390px 下验过再提交）。

---

## 陷阱

- **`[hidden]` 会被作者样式盖过。** `.tile{display:block}` 这类规则的优先级高于浏览器默认的
  `[hidden]{display:none}`，所以靠 `el.hidden = true` 做的过滤会失效。`build-wiki.py` 的 CSS
  已显式声明 `[hidden]{display:none!important}`，**不要删**（索引页搜索曾因此静默失效过一版）。
- **改分类要同步 `CATEGORY_ORDER`**，否则自检会以「未知分类」报错。
- **sitemap 有标记区间。** `<!-- wiki:start -->` / `<!-- wiki:end -->` 之间由脚本改写，
  不要手动编辑该区间，也不要删掉标记。
- **改了缓存核心页要升 `sw.js` 的 `CACHE` 版本号**（当前 `dbx-v2`），否则老用户拿到旧页面。
- **没有对外网络。** 这个环境的出口策略几乎拦下所有外部网域（已确认被挡：CBETA 三个站、
  deerpark.app、台大佛学、维基百科、Scribd、fodizi.net）。代理返回 403/407 时**不要重试或绕路**，
  直接向用户报告被挡的域名，请用户把资料贴进对话或提交进仓库。
- **图片附件不落盘。** 用户拖进对话的图片只进入模型的视觉输入，磁盘上没有文件，
  因此无法提交进仓库。要拿到图片文件，请用户压成 zip 后再传（非图片附件会落到
  `/root/.claude/uploads/`），或直接 commit 进仓库。文本贴进对话则完全可用。

---

## Git

- 在指定的功能分支上开发，提交信息用中文，说明**为什么**而不只是改了什么。
- 仓库惯例是 **squash 合并**，提交标题带 `(#N)`。
- **PR 合并之后不要在原分支上叠新提交**：从最新 `main` 重开同名分支
  （`git checkout -B <branch> origin/main`），新工作开新 PR。
- 生成物与源文件同一个提交，别分开。
