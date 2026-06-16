# recall

> Turn your Claude Code conversation transcripts into human-readable HTML / text — current session or your entire history — with three views (full / simple / talk), local timestamps, and optional auto-archiving on every session end.

*(繁體中文說明見下方 [中文](#中文說明))*

`recall` is a [Claude Code](https://claude.com/claude-code) skill. It reads the JSONL transcripts Claude Code already stores under `~/.claude/projects/` and renders them as clean, browsable HTML (or plain text). The transcript is **more complete than the on-screen view** — the terminal collapses long tool output; the JSONL keeps it all.

It is a **thin wrapper over deterministic Python**: the rendering core (`render_core.py`) and CLI (`recall.py`) are pure standard-library Python with **zero AI token cost**. The skill layer only tells the agent which command to run.

## What it does / does not do

- ✅ Restores **all the text** of a conversation (user, assistant, tool calls, tool results) to HTML/txt.
- ✅ Exports a single session, or **all** historical sessions across every project, with an index.
- ✅ Auto-archives each session to HTML when it ends (optional hooks).
- ❌ Does **not** capture pixel-level terminal screenshots (borders/colors/UI chrome). HTML colors are applied by element type, not reconstructed from the screen.

## Install

Requires Python 3 (standard library only — no third-party packages). Works on macOS / Linux / Windows.

> **Python command differs by OS.** macOS / Linux use `python3`. On **Windows** the bundled Python installs as **`python`**, and a bare `python3` is usually a Microsoft Store stub that silently does nothing — so use `python` everywhere on Windows. `install.sh` auto-detects this (it probes each launcher and bakes the working one into the hook command).

### macOS / Linux

1. Copy this folder into your skills directory:
   ```bash
   cp -r recall ~/.claude/skills/recall
   ```
2. (Optional) Enable auto-archiving hooks — see [Auto-archive](#auto-archive):
   ```bash
   bash ~/.claude/skills/recall/install.sh
   ```
   This backs up `~/.claude/settings.json`, then **appends** the SessionStart/SessionEnd hooks idempotently (existing hooks untouched).

Run the CLI directly without installing it as a skill:
```bash
python3 path/to/scripts/recall.py --scope all
```

### Windows

1. Copy this folder into your skills directory (PowerShell):
   ```powershell
   Copy-Item -Recurse -Force recall "$env:USERPROFILE\.claude\skills\recall"
   ```
2. (Optional) Enable auto-archiving hooks. `install.sh` is a bash script, so run it from **Git Bash** (ships with Git for Windows):
   ```bash
   bash ~/.claude/skills/recall/install.sh
   ```
   It detects that `python` (not `python3`) is the working launcher and writes the hook commands accordingly. If you have no bash, register the two hooks in `%USERPROFILE%\.claude\settings.json` manually, using `python "<skill>/scripts/<hook>.py"`.

Run the CLI directly without installing it as a skill:
```powershell
python path\to\scripts\recall.py --scope all
```

| | macOS / Linux | Windows |
|---|---|---|
| Python command | `python3` | `python` (bare `python3` is a no-op Store stub) |
| Copy folder | `cp -r recall ~/.claude/skills/recall` | `Copy-Item -Recurse -Force recall "$env:USERPROFILE\.claude\skills\recall"` |
| Run `install.sh` | native shell | **Git Bash** required |
| Hook command written | `python3 "…"` | `python "…"` (auto-detected) |

## Usage

```bash
python3 scripts/recall.py [options]
```

| Option | Values (default) | Meaning |
|--------|------------------|---------|
| `--scope` | **current** / all / init-all | Current session / all → `./session-export/` / all → `~/.claude/session-archive/<project>/<view>/` (+ index) |
| `--view` | full / **simple** / talk | Verbatim+tools / tools as one-liners / pure conversation |
| `--format` | **html** / txt | Colored HTML by default |
| `--timestamps` / `--no-timestamps` | **on** | Prefix each turn with local time `[YYYY-MM-DD HH:MM:SS]` |
| `--include-thinking` | off | Include thinking blocks in the `full` view |
| `--include-subagents` | off | Include sub-agent transcripts (scope all / init-all) |
| `--force` | off | init-all: rebuild existing archives (default is idempotent skip) |
| `--arg-width N` | 80 | Truncate tool args in `simple` |
| `--max-result-chars N` | 0 | Truncate tool_result in `full` |
| `--output` / `--output-dir` / `--transcript` / `--cwd` | — | Path overrides |

Common:
```bash
python3 scripts/recall.py                  # current session → recall-simple.html
python3 scripts/recall.py --view talk      # pure conversation (cleanest)
python3 scripts/recall.py --scope all      # all history → ./session-export/ + index.html
python3 scripts/recall.py --scope init-all # backfill all history into the archive + index.html
```

Output is a JSON status line on stdout (`status == "ok"` on success, with `output`/`turns`).

### The three views

- **simple** (default): conversation + one-line tool summaries (`• Update(file)`). Best for **review / finding loose ends**. Filters injected meta messages, merges consecutive same-role turns.
- **talk**: only user/assistant text, no tools. Best for **reading the narrative**.
- **full**: verbatim, tool commands + results, meta preserved, 1:1. Best for **audit / reproduction**.

### scope=all vs scope=init-all

- `--scope all` writes one chosen view into `./session-export/` in the current directory — a throwaway export.
- `--scope init-all` backfills **all history** into `~/.claude/session-archive/<project>/<view>/`, always simple+talk, **merged with the auto-archive tree** so past and future conversations live together. Idempotent (skips existing files; `--force` rebuilds). Re-run anytime to refresh the index and pick up new sessions.

## Auto-archive

Two optional Claude Code hooks (registered by `install.sh` into `~/.claude/settings.json`):

- **SessionEnd** → `scripts/session_end_archive.py`: on session end, save the conversation as **simple + talk HTML** to `~/.claude/session-archive/<project>/<view>/`. *fail-open* — any error exits silently, never blocking session end.
- **SessionStart** → `scripts/session_start_reminder.py`: a one-line reminder that archiving is on and where files go.

Behavior is controlled by `archive.conf.json`:
```json
{
  "enabled": true,
  "archive_dir": "~/.claude/session-archive",
  "views": ["simple", "talk"],
  "format": "html",
  "timestamps": true
}
```
Set `"enabled": false` to turn archiving off without removing the hooks.

## Repository layout

```
recall/
├── README.md             this file
├── LICENSE               MIT
├── SKILL.md              skill manifest (how the agent invokes it)
├── archive.conf.json     auto-archive config
├── install.sh            register hooks into settings.json (backup → idempotent append → verify)
├── scripts/
│   ├── recall.py            single CLI entry point
│   ├── render_core.py            the one rendering core (single source of truth)
│   ├── session_end_archive.py    SessionEnd hook
│   └── session_start_reminder.py SessionStart hook
└── evals/
    └── triggers.json     skill trigger evals
```

## Notes

- Standard library only; no third-party dependencies.
- The last few turns of the **current** session may not be flushed to disk yet — that's normal.
- Project path encoding (`~/.claude/projects/<non-alnum→->`) is handled by `render_core.encode_project_dirname`; if the encoded dir is missing it falls back to the globally newest JSONL.
- macOS system Python can be 3.8 — all scripts use `from __future__ import annotations`; keep that line if you add scripts.

## Changelog

This project follows [Semantic Versioning](https://semver.org/). Newest first.

### 1.1.0 — 2026-06-16 · Readability & cross-platform
- **Slash commands restored** — a user `/command args` stored as `<command-name>…</command-args>` is rendered back as the typed `/command args` (simple/talk) with its own color (`⌘`-prefixed); `full` keeps the raw tags verbatim. The command also becomes the filename's first-prompt slug.
- **Markdown tables → HTML tables** — contiguous `| … |` blocks render as real `<table>` (borders, header tint, column alignment) in simple/talk; `full` keeps them verbatim; code-fence content untouched.
- **Per-role backgrounds** — user / assistant turns get distinct solid block backgrounds (deep blue / deep green), not just a left border.
- **Filenames include the first message's time** — `<date>_<HH-MM-SS>_<slug>_<id8>` (was date-only); colons swapped for `-` for Windows.
- **Cross-platform install** — README splits macOS/Linux vs Windows (`python3` vs `python`, `cp -r` vs `Copy-Item`, Git Bash for `install.sh`); `install.sh` now probes for a working Python launcher and bakes it into the hook command (fixes the Windows `python3` Store-stub trap).

### 1.0.0 — 2026-06-15 · First public release
Consolidates the internal development milestones into one public release:
- **Three views** — `full` (verbatim + tools + results) / `simple` (one-line tools) / `talk` (pure conversation), with local timestamps and path highlighting.
- **Scopes** — `current` (one session), `all` (export every session to `./session-export/` + index).
- **`init_all`** (`--scope init-all`) — backfill **all** history into `~/.claude/session-archive/<project>/<view>/`, idempotent (`--force` to rebuild), with a top-level `index.html` linking simple/talk per session.
- **Per-view archive layout** — `<project>/<view>/` so simple and talk live in separate folders.
- **Auto-archive hooks** — SessionEnd saves simple+talk HTML on session end (fail-open); SessionStart prints a reminder. Registered via `install.sh` (backup → idempotent append → verify).
- **Single rendering core** — `render_core.py` is the one source of truth; pure standard-library Python, zero AI token cost.

<!-- Template for future entries:
### X.Y.Z — YYYY-MM-DD
- Added: ...
- Changed: ...
- Fixed: ...
-->

## License

MIT — see [LICENSE](LICENSE).

---

## 中文說明

`recall` 是一個 [Claude Code](https://claude.com/claude-code) 技能（skill）。它讀取 Claude Code 自存在 `~/.claude/projects/` 下的 JSONL transcript，還原成乾淨可瀏覽的 HTML（或純文字）。transcript **比畫面更完整**——終端機會摺疊長輸出，JSONL 全留著。

它是**薄包裝、核心是免 token 程式**：渲染核心 `render_core.py` 與 CLI `recall.py` 是純標準庫 Python，**零 AI token**；技能層只告訴 agent 跑哪支指令。

### 能做 / 不能做
- ✅ 把對話**所有文字**（user / assistant / 工具呼叫 / 工具結果）還原成 HTML/txt。
- ✅ 匯出單一 session，或跨全部專案的**所有**歷史 session，並產索引。
- ✅ session 結束時自動把對話歸檔成 HTML（選用 hook）。
- ❌ **不**抓終端機像素級截圖。HTML 顏色依元素類型上色，非還原螢幕色票。

### 安裝
需要 Python 3（純標準庫）。

> **Python 指令依系統不同**：mac / Linux 用 `python3`；**Windows 用 `python`**（裸 `python3` 多半是 Microsoft Store 跳板，會靜默失效）。`install.sh` 會自動偵測（逐一試跑 launcher，把能用的那個寫進 hook 指令）。

**mac / Linux：**
```bash
cp -r recall ~/.claude/skills/recall
bash ~/.claude/skills/recall/install.sh   # 選用：啟用自動歸檔 hook
```

**Windows（PowerShell 複製 + Git Bash 跑 install）：**
```powershell
Copy-Item -Recurse -Force recall "$env:USERPROFILE\.claude\skills\recall"
```
```bash
bash ~/.claude/skills/recall/install.sh   # 在 Git Bash 內跑；自動用 python 而非 python3
```
沒有 bash → 手動把兩個 hook 寫進 `%USERPROFILE%\.claude\settings.json`，指令用 `python "<skill>/scripts/<hook>.py"`。

`install.sh` 會先備份 `~/.claude/settings.json`，再**冪等 append** 兩個 hook（既有 hook 不動）。

| | mac / Linux | Windows |
|---|---|---|
| Python 指令 | `python3` | `python`（`python3` 是空跳板）|
| 複製資料夾 | `cp -r …` | `Copy-Item -Recurse -Force …` |
| 跑 `install.sh` | 原生 shell | 需 **Git Bash** |
| hook 寫入的指令 | `python3 "…"` | `python "…"`（自動偵測）|

### 三視圖
- **simple**（預設）：對話＋工具單行摘要，適合回顧、找未處理項目。
- **talk**：只有對話文字，適合純脈絡整理。
- **full**：逐字＋工具本文＋結果，1:1 還原，適合稽核重現。

### init_all（補建全部歷史）
```bash
python3 scripts/recall.py --scope init-all
```
把全部歷史補建到 `~/.claude/session-archive/<專案>/<view>/`，固定 simple+talk，**與自動歸檔合一**（過去+未來同一棵），並產頂層 `index.html`（每列附 simple/talk 雙連結）。**冪等**：已存在跳過（`--force` 強制重建），隨時重跑刷新索引。

### 自動歸檔設定
由 `archive.conf.json` 控（`enabled` / `archive_dir` / `views` / `format` / `timestamps`）。要關閉把 `enabled` 設 `false` 即可。

### 變更紀錄
採[語意化版號](https://semver.org/)，完整內容見上方 [Changelog](#changelog)。
- **1.1.0（2026-06-16）可讀性與跨平台**：slash command 還原成 `/cmd args` 並上色（full 保留原始標籤）、markdown 表格轉真 `<table>`（full 逐字）、user/assistant 整塊深藍/深綠底色區分、檔名加首則訊息時間 `HH-MM-SS`、README 拆 mac/Windows 安裝差異 + `install.sh` 自動偵測 `python`/`python3`。
- **1.0.0（2026-06-15）首次公開**：三視圖（full/simple/talk）、scope current/all/init-all、init_all 補建全部歷史（冪等 + index）、simple/talk 分資料夾版面、SessionEnd/SessionStart 自動歸檔 hook（install.sh 安裝）、單一渲染核心 render_core.py。

### 授權
MIT。
