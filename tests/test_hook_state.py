import json
import os
import subprocess
import sys
import tempfile
from contextlib import redirect_stderr
from io import StringIO
from pathlib import Path
import unittest

from plugins.flowz.hooks.flowz_hook import (
    apply_control,
    clear_state,
    default_state,
    handle_event,
    load_state,
    parse_control_command,
    render_context,
    save_state,
    _safe_session_name,
    _state_path,
)


ROOT = Path(__file__).resolve().parents[1]
HOOK = ROOT / "plugins/flowz/hooks/flowz_hook.py"
FIXTURES = ROOT / "tests/fixtures/hooks"


def read_fixture(name):
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


class HookStateTests(unittest.TestCase):
    def test_default_state_is_enabled_with_optional_features_off(self):
        self.assertEqual(
            default_state(),
            {
                "schemaVersion": 1,
                "flowz_enabled": True,
                "chatgpt_web_assist_enabled": False,
                "user_validation_enabled": False,
                "plan_state": "idle",
            },
        )

    def test_control_commands_support_chinese_and_english(self):
        expected = {
            "暂停 FlowZ": "pause_flowz",
            "pause FlowZ": "pause_flowz",
            "恢复 FlowZ": "resume_flowz",
            "resume FlowZ": "resume_flowz",
            "打开 ChatGPT 网页版辅助": "enable_chatgpt_web_assist",
            "enable ChatGPT web assistance": "enable_chatgpt_web_assist",
            "关闭 ChatGPT 网页版辅助": "disable_chatgpt_web_assist",
            "disable ChatGPT web assistance": "disable_chatgpt_web_assist",
            "打开用户验证建议": "enable_user_validation",
            "enable user validation suggestions": "enable_user_validation",
            "关闭用户验证建议": "disable_user_validation",
            "disable user validation suggestions": "disable_user_validation",
        }
        for prompt, action in expected.items():
            self.assertEqual(parse_control_command(prompt), action)
        self.assertIsNone(parse_control_command("ordinary task request"))

    def test_apply_control_preserves_unrelated_state(self):
        state = {**default_state(), "plan_state": "approved"}
        updated = apply_control(state, "enable_chatgpt_web_assist")
        self.assertTrue(updated["chatgpt_web_assist_enabled"])
        self.assertTrue(updated["flowz_enabled"])
        self.assertFalse(updated["user_validation_enabled"])
        self.assertEqual(updated["plan_state"], "approved")

    def test_paused_state_removes_route_context_on_next_prompt(self):
        with tempfile.TemporaryDirectory() as raw:
            data_root = Path(raw)
            env = {"PLUGIN_DATA": str(data_root)}
            pause_event = read_fixture("pause.json")
            pause_event["session_id"] = "session-a"
            result = handle_event(pause_event, env)
            self.assertNotIn("FlowZ routing", result["hookSpecificOutput"]["additionalContext"])
            ordinary = read_fixture("session-start.json")
            ordinary.update({"session_id": "session-a", "hook_event_name": "UserPromptSubmit", "prompt": "继续任务"})
            next_result = handle_event(ordinary, env)
            self.assertNotIn("FlowZ routing", next_result["hookSpecificOutput"]["additionalContext"])

    def test_resume_fixture_restores_flowz_without_enabling_other_toggles(self):
        with tempfile.TemporaryDirectory() as raw:
            env = {"PLUGIN_DATA": raw}
            pause = read_fixture("pause.json")
            resume = read_fixture("resume.json")
            pause_result = handle_event(pause, env)
            self.assertIn("paused", pause_result["hookSpecificOutput"]["additionalContext"])
            resume_result = handle_event(resume, env)
            context = resume_result["hookSpecificOutput"]["additionalContext"]
            self.assertIn("FlowZ routing: enabled", context)
            self.assertIn("ChatGPT web assistance: off", context)
            self.assertIn("user validation suggestions: off", context)

    def test_optional_toggles_are_independent(self):
        with tempfile.TemporaryDirectory() as raw:
            env = {"PLUGIN_DATA": raw}
            event = read_fixture("session-start.json")
            event.update({"hook_event_name": "UserPromptSubmit", "prompt": "打开 ChatGPT 网页版辅助"})
            result = handle_event(event, env)
            context = result["hookSpecificOutput"]["additionalContext"]
            self.assertIn("ChatGPT web assistance: on", context)
            self.assertIn("user validation suggestions: off", context)
            event["prompt"] = "打开用户验证建议"
            result = handle_event(event, env)
            context = result["hookSpecificOutput"]["additionalContext"]
            self.assertIn("ChatGPT web assistance: on", context)
            self.assertIn("user validation suggestions: on", context)

    def test_state_file_never_contains_prompt(self):
        with tempfile.TemporaryDirectory() as raw:
            data_root = Path(raw)
            prompt = "secret original prompt"
            event = read_fixture("session-start.json")
            event.update({"session_id": "session-a", "hook_event_name": "UserPromptSubmit", "prompt": prompt})
            handle_event(event, {"PLUGIN_DATA": str(data_root)})
            contents = _state_path(data_root, "session-a").read_text(encoding="utf-8")
            self.assertNotIn(prompt, contents)

    def test_session_names_cannot_collide_after_sanitization_or_truncation(self):
        self.assertNotEqual(_safe_session_name("a/b"), _safe_session_name("a?b"))
        long_a = "x" * 200 + "A"
        long_b = "x" * 200 + "B"
        self.assertNotEqual(_safe_session_name(long_a), _safe_session_name(long_b))
        self.assertLessEqual(len(_safe_session_name(long_a)), 128)
        with tempfile.TemporaryDirectory() as raw:
            data_root = Path(raw)
            save_state(data_root, "a/b", default_state())
            save_state(data_root, "a?b", default_state())
            self.assertEqual(len(list(data_root.glob("*.json"))), 2)
            clear_state(data_root, "a/b")
            self.assertTrue(_state_path(data_root, "a?b").exists())

    def test_missing_or_unwritable_data_root_does_not_raise(self):
        event = read_fixture("session-start.json")
        self.assertIsInstance(handle_event(event, {}), dict)
        self.assertIsInstance(handle_event(event, {"PLUGIN_DATA": "Z:\\does-not-exist"}), dict)

    def test_session_end_only_clears_current_session(self):
        with tempfile.TemporaryDirectory() as raw:
            data_root = Path(raw)
            save_state(data_root, "session-a", default_state())
            save_state(data_root, "session-b", default_state())
            event = read_fixture("session-end.json")
            event["session_id"] = "session-a"
            handle_event(event, {"PLUGIN_DATA": str(data_root)})
            self.assertFalse(_state_path(data_root, "session-a").exists())
            self.assertTrue(_state_path(data_root, "session-b").exists())

    def test_persistence_errors_emit_diagnostics_and_minimal_context(self):
        event = read_fixture("session-start.json")
        with tempfile.TemporaryDirectory() as raw:
            data_root = Path(raw) / "state-root"
            data_root.write_text("not a directory", encoding="utf-8")
            diagnostics = StringIO()
            with redirect_stderr(diagnostics):
                result = handle_event(event, {"PLUGIN_DATA": str(data_root)})
        self.assertEqual(result["hookSpecificOutput"]["additionalContext"], "FlowZ routing: enabled; hook state unavailable.")
        self.assertIn("FlowZ hook diagnostic", diagnostics.getvalue())

    def test_hooks_json_schema_contains_all_events_and_command_fields(self):
        hooks = json.loads((ROOT / "plugins/flowz/hooks/hooks.json").read_text(encoding="utf-8"))
        self.assertIsInstance(hooks.get("hooks"), dict)
        for event_name in ("SessionStart", "UserPromptSubmit", "SessionEnd"):
            command = hooks["hooks"][event_name][0]["hooks"][0]
            self.assertEqual(command["type"], "command")
            self.assertIn("${PLUGIN_ROOT}", command["command"])
            self.assertIn("%PLUGIN_ROOT%", command["commandWindows"])
            self.assertIsInstance(command["timeout"], int)

    def test_unknown_event_has_no_context_delta(self):
        event = {"hook_event_name": "Unknown", "session_id": "session-a"}
        result = handle_event(event, {})
        self.assertEqual(result, {"continue": True})

    def test_round_trip_state_and_context(self):
        with tempfile.TemporaryDirectory() as raw:
            data_root = Path(raw)
            state = {**default_state(), "user_validation_enabled": True}
            save_state(data_root, "session-a", state)
            self.assertEqual(load_state(data_root, "session-a"), state)
            self.assertIn("user validation suggestions: on", render_context(state))
            clear_state(data_root, "session-a")
            self.assertEqual(load_state(data_root, "session-a"), default_state())

    def test_script_accepts_stdin_and_returns_hook_json(self):
        event = read_fixture("session-start.json")
        with tempfile.TemporaryDirectory() as raw:
            env = os.environ.copy()
            env["PLUGIN_DATA"] = raw
            env["PLUGIN_ROOT"] = str(ROOT / "plugins/flowz")
            completed = subprocess.run(
                [sys.executable, str(HOOK)],
                input=json.dumps(event),
                text=True,
                capture_output=True,
                env=env,
                check=False,
            )
            self.assertEqual(completed.returncode, 0)
            payload = json.loads(completed.stdout)
            self.assertTrue(payload["continue"])
            self.assertEqual(payload["hookSpecificOutput"]["hookEventName"], "SessionStart")

    def test_malformed_stdin_returns_nonzero_and_nonblocking_json(self):
        completed = subprocess.run(
            [sys.executable, str(HOOK)], input="not-json", text=True, capture_output=True
        )
        self.assertNotEqual(completed.returncode, 0)
        self.assertEqual(json.loads(completed.stdout), {"continue": True})
        self.assertIn("diagnostic", completed.stderr)


if __name__ == "__main__":
    unittest.main()
