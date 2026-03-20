#!/usr/bin/env python3
"""
Save, list, and show Codex session history as readable Markdown.

Adapted from the Claude plugin session-history (transcript_parser.py,
save-session.sh, on-session-start.sh, backup-before-compact.sh,
on-compact-resume.sh).

Sessions are discovered from ~/.codex/sessions/ and saved as Markdown
under ~/.codex/session-history/sessions/<project-key>/.
"""

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path


DATA_DIR = Path.home() / ".codex" / "session-history"
SESSIONS_SRC_DIR = Path.home() / ".codex" / "sessions"
MAX_TRANSCRIPT_SIZE = 100 * 1024 * 1024  # 100 MB


def sanitize_filename(name: str) -> str:
    """Keep only safe characters for filenames."""
    return re.sub(r"[^a-zA-Z0-9_.\-]", "", name)


def escape_markdown(text: str) -> str:
    """Escape Markdown special characters."""
    return text.replace("`", "\\`").replace("<", "&lt;").replace(">", "&gt;")


def project_key(repo: Path) -> str:
    """Derive a safe directory name from a repo path."""
    raw = str(repo.resolve()).replace("/", "_").lstrip("_")
    return sanitize_filename(raw) or "unknown_project"


def strip_system_tags(text: str) -> str:
    """Remove system-reminder and other system tags."""
    patterns = [
        r"<system-reminder>.*?</system-reminder>",
        r"<available-deferred-tools>.*?</available-deferred-tools>",
        r"<env>.*?</env>",
    ]
    for pat in patterns:
        text = re.sub(pat, "", text, flags=re.DOTALL)
    return text.strip()


def format_timestamp(ts) -> str:
    """Convert various timestamp formats to a human-readable string."""
    if not ts:
        return ""
    try:
        if isinstance(ts, (int, float)):
            if ts > 1e12:
                ts = ts / 1000
            dt = datetime.fromtimestamp(ts, tz=timezone.utc).astimezone()
        elif isinstance(ts, str):
            dt = datetime.fromisoformat(ts.replace("Z", "+00:00")).astimezone()
        else:
            return ""
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except (ValueError, OSError):
        return ""


def extract_text_content(content) -> str:
    """Extract readable text from a message content field."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        texts = []
        for block in content:
            if isinstance(block, dict):
                if block.get("type") == "text":
                    texts.append(block.get("text", ""))
                elif block.get("type") == "tool_use":
                    tool_name = block.get("name", "unknown")
                    tool_input = block.get("input", {})
                    if tool_name == "Bash":
                        cmd = tool_input.get("command", "")
                        texts.append(f"[Tool: {tool_name}] `{cmd}`")
                    elif tool_name in ("Read", "Write", "Edit"):
                        fp = tool_input.get("file_path", "")
                        texts.append(f"[Tool: {tool_name}] `{fp}`")
                    elif tool_name in ("Grep", "Glob"):
                        pattern = tool_input.get("pattern", "")
                        texts.append(f"[Tool: {tool_name}] `{pattern}`")
                    else:
                        texts.append(f"[Tool: {tool_name}]")
                elif block.get("type") == "tool_result":
                    pass
            elif isinstance(block, str):
                texts.append(block)
        return "\n".join(texts)
    return str(content) if content else ""


# ── parse / convert ─────────────────────────────────────────────────

def parse_transcript(transcript_path: Path) -> list[dict]:
    """Read a JSONL transcript file and return a list of events."""
    if not transcript_path.is_file():
        return []
    if transcript_path.stat().st_size > MAX_TRANSCRIPT_SIZE:
        print(f"Transcript too large ({transcript_path.stat().st_size} bytes). Skipping.",
              file=sys.stderr)
        return []
    events = []
    with transcript_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return events


def events_to_markdown(events: list[dict], session_id: str, cwd: str) -> str:
    """Convert a list of events into a Markdown session log."""
    lines: list[str] = []
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    safe_id = sanitize_filename(session_id)[:8] or "unknown"

    lines.append(f"# Session Log: {safe_id}")
    lines.append("")
    lines.append(f"- **Session ID**: `{safe_id}`")
    lines.append(f"- **Project**: `{escape_markdown(cwd)}`")
    lines.append(f"- **Saved at**: {now}")
    lines.append("")
    lines.append("---")
    lines.append("")

    msg_count = 0
    for event in events:
        role = event.get("role", "")
        event_type = event.get("type", "")
        content = event.get("content", "")
        timestamp = event.get("timestamp", "")

        if role == "user" or event_type == "user_message":
            text = extract_text_content(content)
            if not text or not text.strip():
                continue
            text = strip_system_tags(text)
            if not text:
                continue
            msg_count += 1
            ts = format_timestamp(timestamp)
            ts_str = f" ({ts})" if ts else ""
            lines.append(f"## User{ts_str}")
            lines.append("")
            lines.append(text)
            lines.append("")

        elif role == "assistant" or event_type == "assistant_message":
            text = extract_text_content(content)
            if not text or not text.strip():
                continue
            msg_count += 1
            ts = format_timestamp(timestamp)
            ts_str = f" ({ts})" if ts else ""
            lines.append(f"## Assistant{ts_str}")
            lines.append("")
            lines.append(text)
            lines.append("")

    if msg_count == 0:
        return ""

    lines.append("---")
    lines.append(f"*Total messages: {msg_count}*")
    return "\n".join(lines)


# ── actions ─────────────────────────────────────────────────────────

def action_save(repo: Path) -> int:
    """Find the most recent Codex session transcript and save it as Markdown."""
    key = project_key(repo)
    session_dir = DATA_DIR / "sessions" / key
    session_dir.mkdir(parents=True, exist_ok=True)

    # Look for transcript files in ~/.codex/sessions/
    transcripts: list[Path] = []
    if SESSIONS_SRC_DIR.is_dir():
        transcripts = sorted(SESSIONS_SRC_DIR.glob("*.jsonl"), key=lambda p: p.stat().st_mtime, reverse=True)

    if not transcripts:
        # Fall back: check if there are any JSON files
        if SESSIONS_SRC_DIR.is_dir():
            transcripts = sorted(SESSIONS_SRC_DIR.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)

    if not transcripts:
        print("No Codex session transcripts found in ~/.codex/sessions/.", file=sys.stderr)
        return 1

    # Use the most recent transcript
    transcript_path = transcripts[0]
    session_id = transcript_path.stem

    events = parse_transcript(transcript_path)
    if not events:
        print(f"No events found in {transcript_path}.", file=sys.stderr)
        return 1

    markdown = events_to_markdown(events, session_id, str(repo.resolve()))
    if not markdown:
        print("No user/assistant messages found in transcript.", file=sys.stderr)
        return 1

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_sid = sanitize_filename(session_id)[:8] or "unknown"
    filename = f"{timestamp}_{safe_sid}.md"
    output_path = session_dir / filename

    output_path.write_text(markdown, encoding="utf-8")
    print(f"Session log saved: {output_path}")
    return 0


def action_list(repo: Path) -> int:
    """List all saved session logs for a project."""
    key = project_key(repo)
    session_dir = DATA_DIR / "sessions" / key

    if not session_dir.is_dir():
        print(f"No sessions found for project {repo}.")
        return 0

    md_files = sorted(session_dir.glob("*.md"), reverse=True)
    if not md_files:
        print("No saved session logs found.")
        return 0

    print(f"=== Session History: {repo} ===")
    for md in md_files:
        size_kb = md.stat().st_size / 1024
        mtime = datetime.fromtimestamp(md.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")
        print(f"  {md.stem}  ({size_kb:.1f} KB, {mtime})")
    print(f"================================")
    print(f"\nDirectory: {session_dir}")
    return 0


def action_show(repo: Path, session_id: str) -> int:
    """Display a specific session log."""
    key = project_key(repo)
    session_dir = DATA_DIR / "sessions" / key

    if not session_dir.is_dir():
        print(f"No sessions found for project {repo}.", file=sys.stderr)
        return 1

    safe_id = sanitize_filename(session_id)

    # Try exact match first, then prefix match
    candidates = list(session_dir.glob(f"*{safe_id}*.md"))
    if not candidates:
        print(f"Session '{safe_id}' not found. Use --action list to see available sessions.", file=sys.stderr)
        return 1

    # Use the most recent match
    target = sorted(candidates, reverse=True)[0]
    content = target.read_text(encoding="utf-8")
    print(content)
    return 0


# ── main ────────────────────────────────────────────────────────────

def main() -> int:
    parser = argparse.ArgumentParser(description="Save, list, and show Codex session history.")
    parser.add_argument("--repo", default=".", help="Repository root path")
    parser.add_argument("--action", required=True, choices=["save", "list", "show"],
                        help="Action to perform")
    parser.add_argument("--session-id", default="", help="Session ID (for show action)")
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    if not repo.is_dir():
        print(f"Repo not found: {repo}", file=sys.stderr)
        return 1

    if args.action == "save":
        return action_save(repo)
    elif args.action == "list":
        return action_list(repo)
    elif args.action == "show":
        if not args.session_id:
            print("--session-id is required for show action.", file=sys.stderr)
            return 1
        return action_show(repo, args.session_id)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
