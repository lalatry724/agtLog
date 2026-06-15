---
name: recall
description: Restore Claude Code conversation transcripts into human-readable HTML/text — current session or all historical sessions — with three views (full verbatim / simple one-line tools / talk pure conversation), local timestamps, and path highlighting. Equivalent to saving the on-screen conversation 1:1 for review and context.
userInvocable: true
triggers: recall, save conversation, save transcript, export all sessions, export conversation, dump transcript, /recall
pattern: tool-wrapper
---

# Skill: recall (Tool Wrapper)

> Wraps "locate transcript JSONL → restore → write file" so the agent never hand-parses JSONL.
> All rendering goes through `scripts/render_core.py` (single source of truth); the CLI entry is `scripts/recall.py`.

## Capability boundary

- ✅ Can: restore **all the text** of a conversation to HTML/txt. Source is the transcript JSONL Claude Code stores itself — more complete than the screen (which collapses long output).
- ❌ Cannot: capture pixel-level terminal screenshots (borders/colors/UI chrome). HTML colors are by element type, not reconstructed from the screen.

## Core rules

1. **Never let the agent read JSONL and hand-parse it** — always go through `scripts/recall.py`. Encoding / path / block / meta traps are sealed inside.
2. On wrapper failure, read the JSON `error` field; **do not switch to an ad-hoc workaround**.
3. Done = stdout JSON `status == "ok"`; report `output`/`turns` to the user.

## Main entry: `scripts/recall.py`

```
python3 scripts/recall.py [options]
```

| Option | Values (default) | Meaning |
|--------|------------------|---------|
| `--scope` | **current** / all / init-all | Current session / all → `./session-export/` / all → `~/.claude/session-archive/<project>/<view>/` (+ index) |
| `--view` | full / **simple** / talk | Verbatim+tools / tools one-liner / pure conversation |
| `--format` | **html** / txt | Colored HTML by default |
| `--timestamps` / `--no-timestamps` | **on** | Prefix each turn with local time |
| `--include-thinking` | off | Include thinking in `full` |
| `--include-subagents` | off | Include sub-agent transcripts (scope all / init-all) |
| `--force` | off | init-all: rebuild existing archives (default idempotent skip) |
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

### Choosing a view
- **simple** (default): conversation + one-line tool summaries (`• Update(file)`). For review / finding loose ends. Filters injected meta, merges consecutive same-role turns.
- **talk**: only user/assistant text, tools hidden. For reading the narrative.
- **full**: verbatim + tool body + tool_result, meta preserved, 1:1. For audit / reproduction.

### scope=all vs scope=init-all
- `all` writes one view to `./session-export/` in the current dir (throwaway export).
- `init-all` backfills all history into `~/.claude/session-archive/<project>/<view>/`, always simple+talk, merged with the auto-archive tree, plus a top-level `index.html` (each row links `[simple] [talk]`). Idempotent; `--force` rebuilds; re-run to refresh.

## Architecture: thin wrapper, token-free core

- **Execution layer** (`render_core.py` + `recall.py`): pure Python, deterministic, **zero AI token**.
- **Invocation layer** (this SKILL.md): only tells the agent which script + args to run.
- Fully skippable by the agent — run the CLI directly:
  ```bash
  python3 ~/.claude/skills/recall/scripts/recall.py --scope all
  ```

## Auto-archive (SessionEnd / SessionStart hooks)

Register via `install.sh` into `~/.claude/settings.json` (takes effect next session):
- **SessionEnd** → `scripts/session_end_archive.py`: save the conversation as **simple + talk HTML** to `~/.claude/session-archive/<project>/<view>/`. fail-open, never blocks session end.
- **SessionStart** → `scripts/session_start_reminder.py`: a one-line reminder of where archives go.
- Controlled by `archive.conf.json` (`enabled` / `archive_dir` / `views` / `format` / `timestamps`). Set `enabled` false to disable.

Note: the assistant label shows the actual model name (e.g. `claude-opus-4-8`); synthetic messages fall back to `ASSISTANT`.

## Failure handling
- `status == "fail"`: usually transcript not found → report `error` verbatim, do not reroute.
- exit 2 / `status == "error"`: internal exception → report `error`, do not retry.

## Notes
- Cross-platform (standard library only, no third-party deps).
- The last few turns of the **current** session may not be flushed yet — normal.
- Path encoding (`~/.claude/projects/<non-alnum→->`) is in `render_core.encode_project_dirname`; missing encoded dir falls back to the globally newest JSONL.
