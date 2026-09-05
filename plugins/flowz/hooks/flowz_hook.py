"""FlowZ session lifecycle and toggle hook."""

from __future__ import annotations

import json
import hashlib
import re
import sys
from pathlib import Path
from typing import Mapping


_STATE_KEYS = (
    "schemaVersion",
    "flowz_enabled",
    "chatgpt_web_assist_enabled",
    "user_validation_enabled",
    "plan_state",
)

_MINIMAL_CONTEXT = "FlowZ routing: enabled; hook state unavailable."
_STATE_ERROR: str | None = None

_CONTROL_COMMANDS = {
    "暂停 flowz": "pause_flowz",
    "pause flowz": "pause_flowz",
    "恢复 flowz": "resume_flowz",
    "resume flowz": "resume_flowz",
    "打开 chatgpt 网页版辅助": "enable_chatgpt_web_assist",
    "enable chatgpt web assistance": "enable_chatgpt_web_assist",
    "关闭 chatgpt 网页版辅助": "disable_chatgpt_web_assist",
    "disable chatgpt web assistance": "disable_chatgpt_web_assist",
    "打开用户验证建议": "enable_user_validation",
    "enable user validation suggestions": "enable_user_validation",
    "关闭用户验证建议": "disable_user_validation",
    "disable user validation suggestions": "disable_user_validation",
}


def default_state() -> dict[str, object]:
    return {
        "schemaVersion": 1,
        "flowz_enabled": True,
        "chatgpt_web_assist_enabled": False,
        "user_validation_enabled": False,
        "plan_state": "idle",
    }


def parse_control_command(prompt: str) -> str | None:
    if not isinstance(prompt, str):
        return None
    return _CONTROL_COMMANDS.get(prompt.strip().casefold())


def apply_control(state: Mapping[str, object], action: str) -> dict[str, object]:
    updated = dict(state)
    if action == "pause_flowz":
        updated["flowz_enabled"] = False
    elif action == "resume_flowz":
        updated["flowz_enabled"] = True
    elif action == "enable_chatgpt_web_assist":
        updated["chatgpt_web_assist_enabled"] = True
    elif action == "disable_chatgpt_web_assist":
        updated["chatgpt_web_assist_enabled"] = False
    elif action == "enable_user_validation":
        updated["user_validation_enabled"] = True
    elif action == "disable_user_validation":
        updated["user_validation_enabled"] = False
    return updated


def _safe_session_name(session_id: str) -> str:
    raw_value = str(session_id or "session")
    value = raw_value.strip() or "session"
    safe_value = re.sub(r"[^A-Za-z0-9._-]", "_", value) or "session"
    # Keep a readable prefix while hashing the original ID so sanitization and
    # truncation cannot cause two sessions to share a state file.
    digest = hashlib.sha256(raw_value.encode("utf-8")).hexdigest()[:20]
    prefix = safe_value[:105]
    return f"{prefix}--{digest}"


def _state_path(data_root: Path | None, session_id: str) -> Path | None:
    if data_root is None:
        return None
    return Path(data_root) / f"{_safe_session_name(session_id)}.json"


def _persistable_state(state: Mapping[str, object]) -> dict[str, object]:
    defaults = default_state()
    for key in _STATE_KEYS:
        if key in state:
            defaults[key] = state[key]
    defaults["schemaVersion"] = 1
    return defaults


def _record_state_error(operation: str, exc: BaseException) -> None:
    global _STATE_ERROR
    _STATE_ERROR = f"{operation} failed ({type(exc).__name__})"
    print(f"FlowZ hook diagnostic: {_STATE_ERROR}", file=sys.stderr)


def load_state(data_root: Path | None, session_id: str) -> dict[str, object]:
    path = _state_path(data_root, session_id)
    if path is None:
        return default_state()
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            _record_state_error("load_state", ValueError("state payload must be an object"))
            return default_state()
        return _persistable_state(payload)
    except FileNotFoundError:
        return default_state()
    except (OSError, ValueError, TypeError) as exc:
        _record_state_error("load_state", exc)
        return default_state()


def save_state(data_root: Path | None, session_id: str, state: Mapping[str, object]) -> None:
    path = _state_path(data_root, session_id)
    if path is None:
        return
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(_persistable_state(state), ensure_ascii=False, sort_keys=True),
            encoding="utf-8",
        )
    except (OSError, TypeError, ValueError) as exc:
        _record_state_error("save_state", exc)


def clear_state(data_root: Path | None, session_id: str) -> None:
    path = _state_path(data_root, session_id)
    if path is None:
        return
    try:
        path.unlink(missing_ok=True)
    except OSError as exc:
        _record_state_error("clear_state", exc)


def render_context(state: Mapping[str, object]) -> str:
    current = _persistable_state(state)
    if not current["flowz_enabled"]:
        return "FlowZ is paused; routing is disabled for this session."
    web = "on" if current["chatgpt_web_assist_enabled"] else "off"
    validation = "on" if current["user_validation_enabled"] else "off"
    return (
        "FlowZ routing: enabled; "
        f"ChatGPT web assistance: {web}; "
        f"user validation suggestions: {validation}; "
        f"plan state: {current['plan_state']}."
    )


def _result(event_name: str, context: str = "") -> dict[str, object]:
    return {
        "continue": True,
        "hookSpecificOutput": {
            "hookEventName": event_name,
            "additionalContext": context,
        },
    }


def handle_event(event: Mapping[str, object], env: Mapping[str, str]) -> Mapping[str, object]:
    global _STATE_ERROR
    _STATE_ERROR = None
    try:
        if not isinstance(event, Mapping):
            raise TypeError("hook input must be a mapping")
        event_name = event.get("hook_event_name")
        if event_name not in {"SessionStart", "UserPromptSubmit", "SessionEnd"}:
            return {"continue": True}
        session_id = str(event.get("session_id") or "session")
        data_root_value = env.get("PLUGIN_DATA")
        data_root = Path(data_root_value) if data_root_value else None
        if event_name == "SessionEnd":
            clear_state(data_root, session_id)
            context = _MINIMAL_CONTEXT if _STATE_ERROR else ""
            return _result("SessionEnd", context)

        state = load_state(data_root, session_id)
        if event_name == "UserPromptSubmit":
            action = parse_control_command(event.get("prompt", ""))
            if action:
                state = apply_control(state, action)
        save_state(data_root, session_id, state)
        if _STATE_ERROR:
            return _result(str(event_name), _MINIMAL_CONTEXT)
        return _result(str(event_name), render_context(state))
    except Exception as exc:
        _record_state_error("handle_event", exc)
        event_name = locals().get("event_name")
        if event_name in {"SessionStart", "UserPromptSubmit", "SessionEnd"}:
            return _result(str(event_name), _MINIMAL_CONTEXT)
        return {"continue": True}


def main() -> int:
    try:
        payload = json.load(sys.stdin)
        if not isinstance(payload, dict):
            raise ValueError("hook input must be a JSON object")
        result = handle_event(payload, {
            "PLUGIN_DATA": __import__("os").environ.get("PLUGIN_DATA", ""),
            "CLAUDE_PLUGIN_DATA": __import__("os").environ.get("CLAUDE_PLUGIN_DATA", ""),
        })
        json.dump(result, sys.stdout, ensure_ascii=False)
        sys.stdout.write("\n")
        return 1 if _STATE_ERROR else 0
    except Exception as exc:
        _record_state_error("main", exc)
        json.dump({"continue": True}, sys.stdout)
        sys.stdout.write("\n")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
