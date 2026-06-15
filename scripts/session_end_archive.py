#!/usr/bin/env python3
"""session_end_archive: SessionEnd hook 用——session 結束時自動把本次對話歸檔成 HTML。

由 settings.json 的 SessionEnd hook 以 stdin 餵 JSON payload 觸發。
設計原則：**fail-open**，任何錯誤都安靜 exit 0，絕不阻擋 session 結束。

payload 取用：transcript_path（缺則用 cwd+session_id 推導）、cwd、session_id。
設定檔（選用）：~/.claude/skills/recall/archive.conf.json
  { "enabled": true, "archive_dir": "~/.claude/session-archive",
    "views": ["simple", "talk"], "format": "html", "timestamps": true }
每個 view 各自一資料夾：<archive>/<專案>/<view>/<date>_<slug>_<id8>.<ext>。
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

SK = Path(__file__).resolve().parent
sys.path.insert(0, str(SK))

DEFAULTS = {"enabled": True, "archive_dir": "~/.claude/session-archive",
            "views": ["simple", "talk"], "format": "html", "timestamps": True}


def _load_conf() -> dict:
    conf = dict(DEFAULTS)
    cfg_path = SK.parent / "archive.conf.json"
    try:
        if cfg_path.is_file():
            conf.update(json.loads(cfg_path.read_text(encoding="utf-8")))
    except Exception:
        pass
    return conf


def main() -> int:
    try:
        payload = json.loads(sys.stdin.read() or "{}")
    except Exception:
        return 0  # 無法解析 → 放行

    conf = _load_conf()
    if not conf.get("enabled", True):
        return 0

    import render_core as rc
    from recall import run_current, _session_meta, _slugify

    cwd = payload.get("cwd") or ""
    session_id = payload.get("session_id") or ""
    tp = payload.get("transcript_path") or ""

    transcript = None
    if tp and Path(tp).expanduser().is_file():
        transcript = Path(tp).expanduser()
    elif cwd and session_id:  # 推導：projects/<encode(cwd)>/<session_id>.jsonl
        guess = Path.home() / ".claude" / "projects" / rc.encode_project_dirname(cwd) / f"{session_id}.jsonl"
        if guess.is_file():
            transcript = guess
    if transcript is None:
        return 0  # 找不到 → 放行

    try:
        meta = _session_meta(transcript)
        if not meta["start"]:  # 空 session 不歸檔
            return 0
        proj = rc.encode_project_dirname(cwd).lstrip("-") if cwd else "unknown"
        date = meta["start"][:10]
        fmt = conf.get("format", "html")
        ext = "html" if fmt == "html" else "txt"
        archive_root = Path(conf["archive_dir"]).expanduser()
        base = f"{date}_{_slugify(meta['first_prompt'])}_{transcript.stem[:8]}"
        for view in conf.get("views", ["simple", "talk"]):  # 各 view 各自一資料夾
            archive = archive_root / proj / view             # <archive>/<專案>/<view>/
            archive.mkdir(parents=True, exist_ok=True)
            out = archive / f"{base}.{ext}"
            run_current(cwd or str(SK), str(transcript), view, fmt,
                        conf.get("timestamps", True), False, 0, 80, str(out))
    except Exception:
        return 0  # 渲染/寫檔出錯 → 放行，不擾 session 結束
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(0)  # 最外層保險：永遠放行
