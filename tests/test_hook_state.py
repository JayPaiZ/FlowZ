import json
import os
import subprocess
import sys
import tempfile
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

    def test_state_file_never_contains_prompt(self):
        with tempfile.TemporaryDirectory() as raw:
            data_root = Path(raw)
            prompt = "secret original prompt"
            event = read_fixture("session-start.json")
            event.update({"session_id": "session-a", "hook_event_name": "UserPromptSubmit", "prompt": prompt})
            handle_event(event, {"PLUGIN_DATA": str(data_root)})
            contents = (data_root / "session-a.json").read_text(encoding="utf-8")
            self.assertNotIn(prompt, contents)

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
            self.assertFalse((data_root / "session-a.json").exists())
            self.assertTrue((data_root / "session-b.json").exists())

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
                check=True,
            )
            payload = json.loads(completed.stdout)
            self.assertTrue(payload["continue"])
            self.assertEqual(payload["hookSpecificOutput"]["hookEventName"], "SessionStart")


if __name__ == "__main__":
    unittest.main()
