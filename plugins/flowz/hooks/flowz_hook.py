"""FlowZ session lifecycle, routing state, and toggle hook."""

from __future__ import annotations

import hashlib
import json
import re
import secrets
import sys
from pathlib import Path
from typing import Mapping


_SCHEMA_VERSION = 3
_CONTEXT_PACKAGE_KEYS = (
    "goal",
    "scope_and_non_goals",
    "constraints",
    "evidence",
    "confirmed_decisions",
    "options_and_tradeoffs",
    "acceptance_criteria",
    "validation",
    "approval_boundary",
    "pause_conditions",
)
_TASK_DEPTHS = {"unclassified", "Quick", "Standard", "Full"}
_PLAN_PHASES = {
    "idle",
    "routing",
    "planning",
    "awaiting_approval",
    "approved",
    "executing",
    "validating",
    "complete",
    "blocked",
}
_ONBOARDING_STATUSES = {"pending", "requested", "checked", "degraded"}
_STATE_MARKER = re.compile(
    r"(?m)^<!--[ \t]*flowz-state:[ \t]*(\{[^\r\n]*\})[ \t]*-->[ \t]*(?:\r?\n|$)"
)
_STATE_MARKER_LINE = re.compile(
    r"(?m)^<!--[ \t]*flowz-state:[^\r\n]*(?:\r?\n|$)"
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
    "open chatgpt web assistance": "enable_chatgpt_web_assist",
    "关闭 chatgpt 网页版辅助": "disable_chatgpt_web_assist",
    "disable chatgpt web assistance": "disable_chatgpt_web_assist",
    "close chatgpt web assistance": "disable_chatgpt_web_assist",
    "打开用户验证建议": "enable_user_validation",
    "enable user validation suggestions": "enable_user_validation",
    "open user validation suggestions": "enable_user_validation",
    "关闭用户验证建议": "disable_user_validation",
    "disable user validation suggestions": "disable_user_validation",
    "close user validation suggestions": "disable_user_validation",
    "重试安装第三方 skill": "retry_onboarding",
    "retry third-party skill installation": "retry_onboarding",
    "查看安装诊断": "show_onboarding_diagnostics",
    "show installation diagnostics": "show_onboarding_diagnostics",
}


def default_state() -> dict[str, object]:
    return {
        "schemaVersion": _SCHEMA_VERSION,
        "flowz_enabled": True,
        "chatgpt_web_assist_enabled": False,
        "user_validation_enabled": False,
        "onboarding_status": "pending",
        "onboarding_diagnostics": [],
        "onboarding_retry_pending": False,
        "marker_nonce": "",
        "task_depth": "unclassified",
        "plan_phase": "idle",
        "context_package": {},
        "reported_conflict_ids": [],
    }


def parse_control_command(prompt: str) -> str | None:
    if not isinstance(prompt, str):
        return None
    normalized = prompt.strip().casefold()
    direct = _CONTROL_COMMANDS.get(normalized)
    if direct:
        return direct

    # Allow ordinary polite wrappers while still requiring the command phrase
    # to be the whole actionable clause.  This avoids firing on explanatory
    # prose such as "document how to enable ...".
    prefixes = ("请帮我", "please ", "请", "please")
    suffixes = ("谢谢", "，谢谢", ", thanks", " please")
    changed = True
    while changed:
        changed = False
        for prefix in prefixes:
            if normalized.startswith(prefix):
                normalized = normalized[len(prefix) :].strip(" ,，。.!！")
                changed = True
                break
        for suffix in suffixes:
            if normalized.endswith(suffix):
                normalized = normalized[: -len(suffix)].strip(" ,，。.!！")
                changed = True
                break
    return _CONTROL_COMMANDS.get(normalized)


def apply_control(state: Mapping[str, object], action: str) -> dict[str, object]:
    updated = _persistable_state(state)
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
    elif action == "retry_onboarding":
        updated["onboarding_status"] = "requested"
        updated["onboarding_retry_pending"] = True
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


def _new_marker_nonce() -> str:
    return secrets.token_hex(16)


def _state_path(data_root: Path | None, session_id: str) -> Path | None:
    if data_root is None:
        return None
    return Path(data_root) / f"{_safe_session_name(session_id)}.json"


def _bounded_text(value: object, limit: int) -> str | None:
    if not isinstance(value, str):
        return None
    compact = " ".join(value.split())
    if not compact:
        return None
    return compact[:limit]


def _normalize_context_value(value: object, *, depth: int = 0) -> str | None:
    """Turn a small Plan value into one bounded, reviewable string.

    FlowZ state is deliberately flat and compact.  Agents commonly represent
    acceptance criteria or trade-offs as short lists/maps, so retain those
    summaries instead of silently dropping them while keeping nesting and size
    bounded.
    """
    if depth > 2:
        return None
    if isinstance(value, str):
        text = " ".join(value.split())
        return text[:500] if text else ""
    if isinstance(value, bool):
        return str(value).lower()
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, (list, tuple)):
        parts: list[str] = []
        for item in value[:8]:
            item_text = _normalize_context_value(item, depth=depth + 1)
            if item_text:
                parts.append(item_text)
        if parts:
            return "; ".join(parts)[:500]
        return ""
    if isinstance(value, Mapping):
        parts: list[str] = []
        for key, item in list(value.items())[:8]:
            key_text = _bounded_text(key, 80)
            item_text = _normalize_context_value(item, depth=depth + 1)
            if key_text and item_text:
                parts.append(f"{key_text}: {item_text}")
        if parts:
            return "; ".join(parts)[:500]
        return ""
    return None


def _looks_sensitive(value: str) -> bool:
    """Reject obvious secrets and marker-shaped text from persisted summaries."""
    lowered = value.casefold()
    if "<!-- flowz-state:" in lowered or "-----begin " in lowered:
        return True
    patterns = (
        r"\b(?:api[_-]?key|access[_-]?token|refresh[_-]?token|password|passwd|secret)\s*[:=]",
        r"\b(?:sk|ghp|github_pat|xox[baprs])[-_][a-z0-9_-]{12,}\b",
        r"\b(?:bearer|basic)\s+[a-z0-9._~+/=-]{12,}\b",
    )
    return any(re.search(pattern, value, re.IGNORECASE) for pattern in patterns)


def _normalize_context_package(value: object) -> dict[str, str]:
    if not isinstance(value, Mapping):
        return {}
    normalized: dict[str, str] = {}
    for key in _CONTEXT_PACKAGE_KEYS:
        text = _normalize_context_value(value.get(key))
        if text and not _looks_sensitive(text):
            normalized[key] = text
    return normalized


def _normalize_string_list(
    value: object, *, item_limit: int, count_limit: int
) -> list[str]:
    if not isinstance(value, list):
        return []
    result: list[str] = []
    for item in value:
        text = _bounded_text(item, item_limit)
        if text and not _looks_sensitive(text) and text not in result:
            result.append(text)
        if len(result) >= count_limit:
            break
    return result


def _normalize_conflict_ids(value: object) -> list[str]:
    """Normalize stable conflict identifiers for case/spacing de-duplication."""
    if not isinstance(value, list):
        return []
    result: list[str] = []
    for item in value:
        text = _bounded_text(item, 128)
        if not text or _looks_sensitive(text):
            continue
        text = text.casefold().replace("\\", "/").strip()
        text = re.sub(r"^\./+", "", text)
        if ":" not in text:
            continue
        source, slug = text.rsplit(":", 1)
        source = re.sub(r"\s*/\s*", "/", source.strip())
        source = re.sub(r"\s*:\s*", ":", source)
        source = re.sub(r"[\s_]+", "-", source)
        source = re.sub(r"-+", "-", source).strip("-")
        slug = re.sub(r"[\s_]+", "-", slug.strip())
        slug = re.sub(r"-+", "-", slug).strip("-")

        source_segments = [
            path_segment
            for namespace_segment in source.split(":")
            for path_segment in namespace_segment.split("/")
        ]
        source_is_valid = bool(source_segments) and all(
            segment
            and segment not in {".", ".."}
            and any(character.isalnum() for character in segment)
            and all(
                character.isalnum() or character in ".-"
                for character in segment
            )
            for segment in source_segments
        )
        slug_is_valid = bool(slug) and all(
            character.isalnum() or character == "-" for character in slug
        )
        text = f"{source}:{slug}" if source_is_valid and slug_is_valid else ""
        if text and text not in result:
            result.append(text)
        if len(result) >= 32:
            break
    return result


def _persistable_state(state: Mapping[str, object]) -> dict[str, object]:
    defaults = default_state()
    if not isinstance(state, Mapping):
        return defaults

    for key in (
        "flowz_enabled",
        "chatgpt_web_assist_enabled",
        "user_validation_enabled",
        "onboarding_retry_pending",
    ):
        if isinstance(state.get(key), bool):
            defaults[key] = state[key]

    onboarding_status = state.get("onboarding_status")
    if onboarding_status in _ONBOARDING_STATUSES:
        defaults["onboarding_status"] = onboarding_status
    defaults["onboarding_diagnostics"] = _normalize_string_list(
        state.get("onboarding_diagnostics"), item_limit=300, count_limit=8
    )
    marker_nonce = state.get("marker_nonce")
    if isinstance(marker_nonce, str) and re.fullmatch(r"[0-9a-f]{32}", marker_nonce):
        defaults["marker_nonce"] = marker_nonce

    task_depth = state.get("task_depth")
    if task_depth in _TASK_DEPTHS:
        defaults["task_depth"] = task_depth
    plan_phase = state.get("plan_phase")
    if plan_phase in _PLAN_PHASES:
        defaults["plan_phase"] = plan_phase
    defaults["context_package"] = _normalize_context_package(
        state.get("context_package")
    )
    defaults["reported_conflict_ids"] = _normalize_conflict_ids(
        state.get("reported_conflict_ids")
    )
    defaults["schemaVersion"] = _SCHEMA_VERSION
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


def _start_task(state: Mapping[str, object]) -> dict[str, object]:
    updated = _persistable_state(state)
    updated["task_depth"] = "unclassified"
    updated["plan_phase"] = "routing"
    updated["context_package"] = {}
    updated["reported_conflict_ids"] = []
    return updated


def _has_unclosed_markdown_fence(text: str) -> bool:
    fence_char: str | None = None
    fence_length = 0
    for line in text.splitlines():
        if fence_char is None:
            opening = re.match(r"^[ ]{0,3}(`{3,}|~{3,})", line)
            if opening:
                delimiter = opening.group(1)
                fence_char = delimiter[0]
                fence_length = len(delimiter)
            continue

        closing = re.match(r"^[ ]{0,3}(`{3,}|~{3,})[ \t]*$", line)
        if (
            closing
            and closing.group(1)[0] == fence_char
            and len(closing.group(1)) >= fence_length
        ):
            fence_char = None
            fence_length = 0
    return fence_char is not None


def _reject_json_constant(value: str) -> None:
    raise ValueError(f"non-standard JSON constant: {value}")


def _state_updates_from_message(message: object) -> list[Mapping[str, object]]:
    if not isinstance(message, str):
        return []
    marker_lines = list(_STATE_MARKER_LINE.finditer(message))
    if not marker_lines:
        return []

    # Only a contiguous block of standalone marker lines at the very end of
    # the assistant message is state.  This prevents examples, quoted text,
    # and markers inside an ordinary response from mutating the session.
    last_match = marker_lines[-1]
    if message[last_match.end() :].strip():
        return []
    block_start = last_match.start()
    selected = [last_match]
    for match in reversed(marker_lines[:-1]):
        if message[match.end() : block_start].strip():
            break
        selected.append(match)
        block_start = match.start()
    selected.reverse()

    # Do not accept an unterminated fenced code block as a state suffix.  A
    # properly closed code example has the closing fence after the marker and
    # therefore already fails the end-of-message check above.
    if _has_unclosed_markdown_fence(message[:block_start]):
        return []

    if len(selected) != 1:
        return []

    valid_match = _STATE_MARKER.fullmatch(selected[0].group(0))
    if valid_match is None:
        _record_state_error("state_marker", ValueError("invalid marker syntax"))
        return []

    updates: list[Mapping[str, object]] = []
    try:
        payload = json.loads(
            valid_match.group(1), parse_constant=_reject_json_constant
        )
    except (TypeError, ValueError) as exc:
        _record_state_error("state_marker", exc)
        return []
    if isinstance(payload, dict):
        updates.append(payload)
    else:
        _record_state_error(
            "state_marker", ValueError("marker payload must be an object")
        )
    return updates


def _apply_state_update(
    state: Mapping[str, object], update: Mapping[str, object]
) -> dict[str, object]:
    merged = _persistable_state(state)

    task_depth = update.get("task_depth")
    if task_depth in _TASK_DEPTHS - {"unclassified"}:
        merged["task_depth"] = task_depth
    plan_phase = update.get("plan_phase")
    if plan_phase in _PLAN_PHASES - {"idle"}:
        merged["plan_phase"] = plan_phase
    if "context_package" in update and isinstance(update["context_package"], Mapping):
        raw_package = update["context_package"]
        if not raw_package:
            merged["context_package"] = {}
        else:
            package = dict(merged["context_package"])
            for key in _CONTEXT_PACKAGE_KEYS:
                if key not in raw_package:
                    continue
                normalized_value = _normalize_context_value(raw_package[key])
                if normalized_value and not _looks_sensitive(normalized_value):
                    package[key] = normalized_value
                elif normalized_value == "":
                    package.pop(key, None)
            merged["context_package"] = package
    if "reported_conflict_ids" in update and isinstance(
        update["reported_conflict_ids"], list
    ):
        raw_conflicts = update["reported_conflict_ids"]
        if raw_conflicts:
            new_conflicts = _normalize_conflict_ids(raw_conflicts)
            if new_conflicts:
                merged["reported_conflict_ids"] = _normalize_conflict_ids(
                    [*merged["reported_conflict_ids"], *new_conflicts]
                )

    onboarding_status = update.get("onboarding_status")
    if onboarding_status in {"checked", "degraded"}:
        merged["onboarding_status"] = onboarding_status
        merged["onboarding_retry_pending"] = False
    if isinstance(update.get("onboarding_diagnostics"), list):
        merged["onboarding_diagnostics"] = _normalize_string_list(
            update["onboarding_diagnostics"], item_limit=300, count_limit=8
        )
    return _persistable_state(merged)


def render_context(
    state: Mapping[str, object],
    *,
    onboarding_action: str | None = None,
    show_diagnostics: bool = False,
) -> str:
    current = _persistable_state(state)
    diagnostics = current["onboarding_diagnostics"]
    if not current["flowz_enabled"]:
        context = "FlowZ is paused; routing is disabled for this session."
        if onboarding_action == "queued" or current["onboarding_retry_pending"]:
            context += (
                " An onboarding retry is queued; resume FlowZ before running it."
            )
        if show_diagnostics:
            shown = "; ".join(diagnostics) if diagnostics else "none saved"
            context += f" Saved installation diagnostics: {shown}."
        return context

    web = "on" if current["chatgpt_web_assist_enabled"] else "off"
    validation = "on" if current["user_validation_enabled"] else "off"
    parts = [
        "FlowZ routing: enabled",
        f"ChatGPT web assistance: {web}",
        f"user validation suggestions: {validation}",
        f"task depth: {current['task_depth']}",
        f"Plan phase: {current['plan_phase']}",
    ]

    package = current["context_package"]
    if package:
        parts.append(
            "compact task package: "
            + json.dumps(package, ensure_ascii=False, separators=(",", ":"))
        )
    conflicts = current["reported_conflict_ids"]
    if conflicts:
        parts.append("already reported conflicts: " + ", ".join(conflicts))

    status = current["onboarding_status"]
    if onboarding_action == "initial":
        parts.append(
            "onboarding: run $flowz-onboarding once now for this first real task"
        )
    elif onboarding_action == "retry":
        parts.append(
            "onboarding: the user explicitly requested one retry; run "
            "$flowz-onboarding once now"
        )
    elif status == "pending":
        parts.append("onboarding: pending until the first real task")
    elif status == "requested":
        parts.append(
            "onboarding: initial check already requested; do not run it again automatically"
        )
    elif status == "checked":
        parts.append("onboarding: checked")
    else:
        parts.append(f"onboarding: degraded ({len(diagnostics)} saved diagnostic(s))")

    if show_diagnostics:
        shown = "; ".join(diagnostics) if diagnostics else "none saved"
        parts.append(
            f"display only the saved installation diagnostics: {shown}; "
            "do not run checks or start an installation"
        )

    parts.append(
        "Use $flowz-workflow for routing. When durable FlowZ state changes, "
        "append exactly one compact marker defined in references/runtime-state.md "
        f"with marker_nonce {current['marker_nonce']}; "
        "never include hidden reasoning or the original prompt"
    )
    return "; ".join(parts) + "."


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
        if event_name not in {"SessionStart", "UserPromptSubmit", "Stop", "SessionEnd"}:
            return {"continue": True}
        session_id = str(event.get("session_id") or "session")
        data_root_value = env.get("PLUGIN_DATA") or env.get("CLAUDE_PLUGIN_DATA")
        if not data_root_value:
            _record_state_error(
                "state_root", RuntimeError("plugin data directory is unavailable")
            )
            if event_name == "Stop":
                return {"continue": True}
            return _result(str(event_name), _MINIMAL_CONTEXT)
        data_root = Path(data_root_value) if data_root_value else None
        if event_name == "SessionEnd":
            clear_state(data_root, session_id)
            context = _MINIMAL_CONTEXT if _STATE_ERROR else ""
            return _result("SessionEnd", context)

        state = load_state(data_root, session_id)
        if event_name == "Stop":
            updates = _state_updates_from_message(event.get("last_assistant_message"))
            if updates and event.get("stop_hook_active") is True:
                # A recursive Stop pass is not a new assistant decision.  Do
                # not let it replay or mutate the state captured on the first
                # Stop event.
                return {"continue": True}
            if len(updates) != 1:
                return {"continue": True}
            update = updates[0]
            nonce = state.get("marker_nonce")
            if not nonce or update.get("marker_nonce") != nonce:
                return {"continue": True}
            state = _apply_state_update(state, update)
            state["marker_nonce"] = _new_marker_nonce()
            if updates:
                save_state(data_root, session_id, state)
            return {"continue": True}

        if not state["marker_nonce"]:
            state["marker_nonce"] = _new_marker_nonce()

        onboarding_action = None
        show_diagnostics = False
        if event_name == "UserPromptSubmit":
            action = parse_control_command(event.get("prompt", ""))
            if action:
                state = apply_control(state, action)
                if action == "retry_onboarding":
                    if state["flowz_enabled"]:
                        state["onboarding_retry_pending"] = False
                        onboarding_action = "retry"
                    else:
                        onboarding_action = "queued"
                elif action == "resume_flowz" and state["onboarding_retry_pending"]:
                    state["onboarding_retry_pending"] = False
                    onboarding_action = "retry"
                elif action == "show_onboarding_diagnostics":
                    show_diagnostics = True
            elif state["flowz_enabled"]:
                if state["plan_phase"] in {"idle", "complete"}:
                    state = _start_task(state)
                if state["onboarding_status"] == "pending":
                    state["onboarding_status"] = "requested"
                    onboarding_action = "initial"

        save_state(data_root, session_id, state)
        if _STATE_ERROR:
            return _result(str(event_name), _MINIMAL_CONTEXT)
        return _result(
            str(event_name),
            render_context(
                state,
                onboarding_action=onboarding_action,
                show_diagnostics=show_diagnostics,
            ),
        )
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
        result = handle_event(
            payload,
            {
                "PLUGIN_DATA": __import__("os").environ.get("PLUGIN_DATA", ""),
                "CLAUDE_PLUGIN_DATA": __import__("os").environ.get(
                    "CLAUDE_PLUGIN_DATA", ""
                ),
            },
        )
        json.dump(result, sys.stdout, ensure_ascii=False)
        sys.stdout.write("\n")
        # A valid hook request with a recoverable state problem must still
        # deliver its safe stdout context to Codex.
        return 0
    except Exception as exc:
        _record_state_error("main", exc)
        json.dump({"continue": True}, sys.stdout)
        sys.stdout.write("\n")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
