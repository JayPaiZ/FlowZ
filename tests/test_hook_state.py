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


def authenticated_marker(data_root: Path, session_id: str, update: dict) -> str:
    state = load_state(data_root, session_id)
    if not state["marker_nonce"]:
        start = read_fixture("session-start.json")
        start.update({"session_id": session_id})
        handle_event(start, {"PLUGIN_DATA": str(data_root)})
        state = load_state(data_root, session_id)
    payload = {**update, "marker_nonce": state["marker_nonce"]}
    return f"<!-- flowz-state: {json.dumps(payload)} -->"


class HookStateTests(unittest.TestCase):
    def test_default_state_is_enabled_with_optional_features_off(self):
        self.assertEqual(
            default_state(),
            {
                "schemaVersion": 3,
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
            "open chatgpt web assistance": "enable_chatgpt_web_assist",
            "close chatgpt web assistance": "disable_chatgpt_web_assist",
            "open user validation suggestions": "enable_user_validation",
            "close user validation suggestions": "disable_user_validation",
            "重试安装第三方 Skill": "retry_onboarding",
            "retry third-party skill installation": "retry_onboarding",
            "查看安装诊断": "show_onboarding_diagnostics",
            "show installation diagnostics": "show_onboarding_diagnostics",
        }
        for prompt, action in expected.items():
            self.assertEqual(parse_control_command(prompt), action)
        self.assertEqual(
            parse_control_command("请打开 ChatGPT 网页版辅助，谢谢"),
            "enable_chatgpt_web_assist",
        )
        self.assertEqual(
            parse_control_command("请帮我打开用户验证建议"),
            "enable_user_validation",
        )
        self.assertIsNone(parse_control_command("ordinary task request"))
        self.assertIsNone(
            parse_control_command("document how to enable ChatGPT web assistance")
        )

    def test_apply_control_preserves_unrelated_state(self):
        state = {**default_state(), "plan_phase": "approved"}
        updated = apply_control(state, "enable_chatgpt_web_assist")
        self.assertTrue(updated["chatgpt_web_assist_enabled"])
        self.assertTrue(updated["flowz_enabled"])
        self.assertFalse(updated["user_validation_enabled"])
        self.assertEqual(updated["plan_phase"], "approved")

    def test_first_real_task_requests_onboarding_once_and_starts_routing(self):
        with tempfile.TemporaryDirectory() as raw:
            env = {"PLUGIN_DATA": raw}
            event = read_fixture("session-start.json")
            event.update(
                {
                    "hook_event_name": "UserPromptSubmit",
                    "prompt": "实现一个小功能",
                    "session_id": "session-onboarding",
                }
            )
            first = handle_event(event, env)
            first_context = first["hookSpecificOutput"]["additionalContext"]
            state = load_state(Path(raw), "session-onboarding")
            self.assertEqual(state["onboarding_status"], "requested")
            self.assertEqual(state["plan_phase"], "routing")
            self.assertIn("$flowz-onboarding", first_context)

            second = handle_event(event, env)
            second_context = second["hookSpecificOutput"]["additionalContext"]
            self.assertNotIn("run $flowz-onboarding once now", second_context)

    def test_control_commands_do_not_consume_first_task_onboarding(self):
        with tempfile.TemporaryDirectory() as raw:
            event = read_fixture("session-start.json")
            event.update(
                {
                    "hook_event_name": "UserPromptSubmit",
                    "prompt": "打开用户验证建议",
                    "session_id": "session-control",
                }
            )
            result = handle_event(event, {"PLUGIN_DATA": raw})
            state = load_state(Path(raw), "session-control")

        self.assertEqual(state["onboarding_status"], "pending")
        self.assertEqual(state["plan_phase"], "idle")
        self.assertNotIn("$flowz-onboarding", result["hookSpecificOutput"]["additionalContext"])

    def test_stop_marker_persists_reviewable_task_and_onboarding_state(self):
        update = {
            "task_depth": "Standard",
            "plan_phase": "approved",
            "context_package": {
                "goal": "Add deterministic state recovery",
                "approval_boundary": "Implement and validate locally",
            },
            "reported_conflict_ids": ["agents.md:project-plan-policy"],
            "onboarding_status": "degraded",
            "onboarding_diagnostics": ["grilling: upstream path unavailable"],
        }
        with tempfile.TemporaryDirectory() as raw:
            env = {"PLUGIN_DATA": raw}
            marker = authenticated_marker(Path(raw), "session-state", update)
            stop = {
                "hook_event_name": "Stop",
                "session_id": "session-state",
                "turn_id": "turn-1",
                "stop_hook_active": False,
                "last_assistant_message": f"Visible result\n{marker}",
            }
            result = handle_event(stop, env)
            state = load_state(Path(raw), "session-state")
            stored = _state_path(Path(raw), "session-state").read_text(
                encoding="utf-8"
            )

        self.assertEqual(result, {"continue": True})
        self.assertEqual(state["task_depth"], "Standard")
        self.assertEqual(state["plan_phase"], "approved")
        self.assertEqual(
            state["context_package"]["goal"],
            "Add deterministic state recovery",
        )
        self.assertEqual(
            state["reported_conflict_ids"],
            ["agents.md:project-plan-policy"],
        )
        self.assertEqual(state["onboarding_status"], "degraded")
        self.assertNotIn("Visible result", stored)

    def test_stop_marker_is_strictly_normalized_and_cannot_change_switches(self):
        update = {
            "schemaVersion": 999,
            "flowz_enabled": False,
            "chatgpt_web_assist_enabled": True,
            "user_validation_enabled": True,
            "task_depth": "Impossible",
            "plan_phase": "secret-thinking",
            "reported_conflict_ids": ["AGENTS.md:Same", "agents.md:same", 42],
            "raw_prompt": "must never be saved",
            "unknown": "ignored",
        }
        with tempfile.TemporaryDirectory() as raw:
            data_root = Path(raw)
            save_state(data_root, "session-strict", default_state())
            marker = authenticated_marker(data_root, "session-strict", update)
            handle_event(
                {
                    "hook_event_name": "Stop",
                    "session_id": "session-strict",
                    "last_assistant_message": marker,
                },
                {"PLUGIN_DATA": raw},
            )
            state = load_state(data_root, "session-strict")
            stored = _state_path(data_root, "session-strict").read_text(
                encoding="utf-8"
            )

        self.assertEqual(state["schemaVersion"], 3)
        self.assertTrue(state["flowz_enabled"])
        self.assertFalse(state["chatgpt_web_assist_enabled"])
        self.assertFalse(state["user_validation_enabled"])
        self.assertEqual(state["task_depth"], "unclassified")
        self.assertEqual(state["plan_phase"], "idle")
        self.assertEqual(state["reported_conflict_ids"], ["agents.md:same"])
        self.assertNotIn("raw_prompt", stored)
        self.assertNotIn("unknown", stored)

    def test_stop_marker_does_not_persist_obvious_secret_material(self):
        update = {
            "context_package": {
                "goal": "safe summary",
                "evidence": "api_key=do-not-persist-this-value",
            },
            "onboarding_diagnostics": [
                "network unavailable",
                "access_token: do-not-persist-this-value",
            ],
        }
        with tempfile.TemporaryDirectory() as raw:
            data_root = Path(raw)
            marker = authenticated_marker(
                data_root, "session-secret-filter", update
            )
            handle_event(
                {
                    "hook_event_name": "Stop",
                    "session_id": "session-secret-filter",
                    "last_assistant_message": marker,
                },
                {"PLUGIN_DATA": raw},
            )
            state = load_state(data_root, "session-secret-filter")
            stored = _state_path(data_root, "session-secret-filter").read_text(
                encoding="utf-8"
            )

        self.assertEqual(state["context_package"], {"goal": "safe summary"})
        self.assertEqual(state["onboarding_diagnostics"], ["network unavailable"])
        self.assertNotIn("do-not-persist", stored)

    def test_partial_stop_marker_merges_compact_state_without_losing_prior_fields(self):
        with tempfile.TemporaryDirectory() as raw:
            data_root = Path(raw)
            state = {
                **default_state(),
                "task_depth": "Full",
                "plan_phase": "approved",
                "context_package": {
                    "goal": "Keep this goal",
                    "approval_boundary": "Original boundary",
                },
                "reported_conflict_ids": ["agents.md:first-conflict"],
            }
            save_state(data_root, "session-merge", state)
            update = {
                "plan_phase": "executing",
                "context_package": {"validation": "Run focused tests"},
                "reported_conflict_ids": ["skill:office-hours:second-conflict"],
            }
            marker = authenticated_marker(data_root, "session-merge", update)
            handle_event(
                {
                    "hook_event_name": "Stop",
                    "session_id": "session-merge",
                    "last_assistant_message": marker,
                },
                {"PLUGIN_DATA": raw},
            )
            merged = load_state(data_root, "session-merge")

        self.assertEqual(merged["task_depth"], "Full")
        self.assertEqual(merged["plan_phase"], "executing")
        self.assertEqual(merged["context_package"]["goal"], "Keep this goal")
        self.assertEqual(
            merged["context_package"]["validation"], "Run focused tests"
        )
        self.assertEqual(
            merged["reported_conflict_ids"],
            ["agents.md:first-conflict", "skill:office-hours:second-conflict"],
        )

    def test_stop_rejects_multiple_markers_instead_of_guessing_precedence(self):
        task_update = {
            "task_depth": "Quick",
            "plan_phase": "complete",
            "context_package": {"goal": "Finish first task"},
        }
        onboarding_update = {
            "onboarding_status": "checked",
            "onboarding_diagnostics": [],
        }
        with tempfile.TemporaryDirectory() as raw:
            data_root = Path(raw)
            first = authenticated_marker(
                data_root, "session-two-markers", task_update
            )
            nonce = load_state(data_root, "session-two-markers")["marker_nonce"]
            second = (
                "<!-- flowz-state: "
                + json.dumps({**onboarding_update, "marker_nonce": nonce})
                + " -->"
            )
            message = first + "\n" + second
            handle_event(
                {
                    "hook_event_name": "Stop",
                    "session_id": "session-two-markers",
                    "last_assistant_message": message,
                },
                {"PLUGIN_DATA": raw},
            )
            state = load_state(data_root, "session-two-markers")

        self.assertEqual(state["task_depth"], "unclassified")
        self.assertEqual(state["plan_phase"], "idle")
        self.assertEqual(state["onboarding_status"], "pending")

    def test_stop_rejects_malformed_marker_beside_valid_final_marker(self):
        with tempfile.TemporaryDirectory() as raw:
            data_root = Path(raw)
            valid = authenticated_marker(
                data_root,
                "session-malformed-marker",
                {"plan_phase": "approved"},
            )
            nonce = load_state(data_root, "session-malformed-marker")["marker_nonce"]
            malformed = '<!-- flowz-state: {"plan_phase": -->'
            handle_event(
                {
                    "hook_event_name": "Stop",
                    "session_id": "session-malformed-marker",
                    "last_assistant_message": malformed + "\n" + valid,
                },
                {"PLUGIN_DATA": raw},
            )
            state = load_state(data_root, "session-malformed-marker")

        self.assertEqual(state["plan_phase"], "idle")
        self.assertEqual(state["marker_nonce"], nonce)

    def test_stop_rejects_marker_split_across_lines(self):
        with tempfile.TemporaryDirectory() as raw:
            data_root = Path(raw)
            session_id = "session-multiline-marker"
            valid = authenticated_marker(
                data_root,
                session_id,
                {"plan_phase": "approved"},
            )
            nonce = load_state(data_root, session_id)["marker_nonce"]
            multiline = valid.replace("<!-- flowz-state:", "<!--\nflowz-state:")
            handle_event(
                {
                    "hook_event_name": "Stop",
                    "session_id": session_id,
                    "last_assistant_message": multiline,
                },
                {"PLUGIN_DATA": raw},
            )
            state = load_state(data_root, session_id)

        self.assertEqual(state["plan_phase"], "idle")
        self.assertEqual(state["marker_nonce"], nonce)

    def test_stop_rejects_nonstandard_json_constants(self):
        for constant in ("NaN", "Infinity", "-Infinity"):
            with self.subTest(constant=constant), tempfile.TemporaryDirectory() as raw:
                data_root = Path(raw)
                session_id = "session-json-" + constant.lower().replace("-", "negative-")
                authenticated_marker(data_root, session_id, {})
                nonce = load_state(data_root, session_id)["marker_nonce"]
                diagnostics = StringIO()
                marker = (
                    '<!-- flowz-state: {"marker_nonce":"'
                    + nonce
                    + '","context_package":{"goal":'
                    + constant
                    + "}} -->"
                )
                with redirect_stderr(diagnostics):
                    handle_event(
                        {
                            "hook_event_name": "Stop",
                            "session_id": session_id,
                            "last_assistant_message": marker,
                        },
                        {"PLUGIN_DATA": raw},
                    )
                state = load_state(data_root, session_id)

            self.assertEqual(state["context_package"], {})
            self.assertEqual(state["marker_nonce"], nonce)
            self.assertIn("state_marker", diagnostics.getvalue())

    def test_stop_marker_compacts_common_plan_collections(self):
        update = {
            "context_package": {
                "acceptance_criteria": ["criterion one", "criterion two"],
                "options_and_tradeoffs": {
                    "safe": "keep scope",
                    "fast": "less coverage",
                },
            }
        }
        with tempfile.TemporaryDirectory() as raw:
            data_root = Path(raw)
            marker = authenticated_marker(
                data_root, "session-collection-state", update
            )
            handle_event(
                {
                    "hook_event_name": "Stop",
                    "session_id": "session-collection-state",
                    "last_assistant_message": marker,
                },
                {"PLUGIN_DATA": raw},
            )
            state = load_state(data_root, "session-collection-state")

        self.assertEqual(
            state["context_package"]["acceptance_criteria"],
            "criterion one; criterion two",
        )
        self.assertIn(
            "safe: keep scope", state["context_package"]["options_and_tradeoffs"]
        )

    def test_conflict_ids_are_case_and_whitespace_stable(self):
        update = {
            "reported_conflict_ids": [
                "./AGENTS.md:Use_Host_Plan",
                "agents.md : use host plan",
                " Skill : Office_Hours : Use_Host_Plan ",
                "skill:office-hours:use host plan",
            ]
        }
        with tempfile.TemporaryDirectory() as raw:
            data_root = Path(raw)
            marker = authenticated_marker(
                data_root, "session-conflict-normalization", update
            )
            handle_event(
                {
                    "hook_event_name": "Stop",
                    "session_id": "session-conflict-normalization",
                    "last_assistant_message": marker,
                },
                {"PLUGIN_DATA": raw},
            )
            state = load_state(data_root, "session-conflict-normalization")

        self.assertEqual(
            state["reported_conflict_ids"],
            [
                "agents.md:use-host-plan",
                "skill:office-hours:use-host-plan",
            ],
        )

    def test_conflict_ids_require_a_source_locator_and_rule_slug(self):
        update = {
            "reported_conflict_ids": [
                "free form sentence without locator",
                "skill:office-hours:Use_Host_Plan",
                "agents.md: use host plan",
                "agents.md:bad!slug",
                ":missing-source",
                "agents.md:",
            ]
        }
        with tempfile.TemporaryDirectory() as raw:
            data_root = Path(raw)
            marker = authenticated_marker(
                data_root, "session-conflict-shape", update
            )
            handle_event(
                {
                    "hook_event_name": "Stop",
                    "session_id": "session-conflict-shape",
                    "last_assistant_message": marker,
                },
                {"PLUGIN_DATA": raw},
            )
            state = load_state(data_root, "session-conflict-shape")

        self.assertEqual(
            state["reported_conflict_ids"],
            [
                "skill:office-hours:use-host-plan",
                "agents.md:use-host-plan",
            ],
        )

    def test_stop_marker_does_not_persist_secret_shaped_conflict_ids(self):
        update = {
            "reported_conflict_ids": [
                "AGENTS.md:use-host-plan",
                "api_key=example-secret-value",
                "password:do-not-store",
            ]
        }
        with tempfile.TemporaryDirectory() as raw:
            data_root = Path(raw)
            marker = authenticated_marker(
                data_root, "session-secret-conflict", update
            )
            handle_event(
                {
                    "hook_event_name": "Stop",
                    "session_id": "session-secret-conflict",
                    "last_assistant_message": marker,
                },
                {"PLUGIN_DATA": raw},
            )
            state = load_state(data_root, "session-secret-conflict")

        self.assertEqual(
            state["reported_conflict_ids"],
            ["agents.md:use-host-plan"],
        )

    def test_stop_ignores_markers_that_are_not_in_the_final_marker_block(self):
        quoted = '<!-- flowz-state: {"context_package":{"goal":"quoted example"}} -->'
        with tempfile.TemporaryDirectory() as raw:
            data_root = Path(raw)
            actual = authenticated_marker(
                data_root, "session-marker-tail", {"task_depth": "Quick"}
            )
            message = "Example marker:\n" + quoted + "\n\nVisible result.\n" + actual
            handle_event(
                {
                    "hook_event_name": "Stop",
                    "session_id": "session-marker-tail",
                    "last_assistant_message": message,
                },
                {"PLUGIN_DATA": raw},
            )
            state = load_state(data_root, "session-marker-tail")

        self.assertEqual(state["task_depth"], "Quick")
        self.assertEqual(state["context_package"], {})

    def test_stop_ignores_marker_inside_a_fenced_code_block(self):
        with tempfile.TemporaryDirectory() as raw:
            data_root = Path(raw)
            marker = authenticated_marker(
                data_root, "session-marker-code", {"task_depth": "Full"}
            )
            message = "```text\n" + marker + "\n```"
            handle_event(
                {
                    "hook_event_name": "Stop",
                    "session_id": "session-marker-code",
                    "last_assistant_message": message,
                },
                {"PLUGIN_DATA": raw},
            )
            state = load_state(data_root, "session-marker-code")

        self.assertEqual(state["task_depth"], "unclassified")
        self.assertEqual(state["plan_phase"], "idle")

    def test_stop_ignores_marker_inside_an_indented_code_block(self):
        with tempfile.TemporaryDirectory() as raw:
            data_root = Path(raw)
            marker = authenticated_marker(
                data_root, "session-marker-indented-code", {"task_depth": "Full"}
            )
            handle_event(
                {
                    "hook_event_name": "Stop",
                    "session_id": "session-marker-indented-code",
                    "last_assistant_message": "    " + marker,
                },
                {"PLUGIN_DATA": raw},
            )
            state = load_state(data_root, "session-marker-indented-code")

        self.assertEqual(state["task_depth"], "unclassified")
        self.assertEqual(state["plan_phase"], "idle")

    def test_stop_does_not_treat_a_mismatched_fence_as_closing_code(self):
        with tempfile.TemporaryDirectory() as raw:
            data_root = Path(raw)
            marker = authenticated_marker(
                data_root, "session-marker-mixed-fence", {"plan_phase": "approved"}
            )
            handle_event(
                {
                    "hook_event_name": "Stop",
                    "session_id": "session-marker-mixed-fence",
                    "last_assistant_message": "```text\n~~~\n" + marker,
                },
                {"PLUGIN_DATA": raw},
            )
            state = load_state(data_root, "session-marker-mixed-fence")

        self.assertEqual(state["plan_phase"], "idle")

    def test_recursive_stop_does_not_replay_a_state_marker(self):
        with tempfile.TemporaryDirectory() as raw:
            data_root = Path(raw)
            marker = authenticated_marker(
                data_root, "session-recursive-stop", {"plan_phase": "approved"}
            )
            handle_event(
                {
                    "hook_event_name": "Stop",
                    "session_id": "session-recursive-stop",
                    "stop_hook_active": True,
                    "last_assistant_message": marker,
                },
                {"PLUGIN_DATA": raw},
            )
            state = load_state(data_root, "session-recursive-stop")

        self.assertEqual(state["plan_phase"], "idle")

    def test_stop_accepts_only_the_current_rotating_marker_nonce(self):
        with tempfile.TemporaryDirectory() as raw:
            data_root = Path(raw)
            env = {"PLUGIN_DATA": raw}
            start = read_fixture("session-start.json")
            start.update({"session_id": "session-marker-nonce"})
            handle_event(start, env)
            initial = load_state(data_root, "session-marker-nonce")
            nonce = initial["marker_nonce"]
            self.assertRegex(nonce, r"^[0-9a-f]{32}$")

            unauthenticated = '<!-- flowz-state: {"plan_phase":"approved"} -->'
            handle_event(
                {
                    "hook_event_name": "Stop",
                    "session_id": "session-marker-nonce",
                    "last_assistant_message": unauthenticated,
                },
                env,
            )
            self.assertEqual(
                load_state(data_root, "session-marker-nonce")["plan_phase"],
                "idle",
            )

            authenticated = (
                '<!-- flowz-state: '
                + json.dumps(
                    {"marker_nonce": nonce, "plan_phase": "approved"},
                    separators=(",", ":"),
                )
                + " -->"
            )
            handle_event(
                {
                    "hook_event_name": "Stop",
                    "session_id": "session-marker-nonce",
                    "last_assistant_message": authenticated,
                },
                env,
            )
            accepted = load_state(data_root, "session-marker-nonce")

        self.assertEqual(accepted["plan_phase"], "approved")
        self.assertNotEqual(accepted["marker_nonce"], nonce)

    def test_stop_marker_can_explicitly_clear_context_package(self):
        with tempfile.TemporaryDirectory() as raw:
            data_root = Path(raw)
            save_state(
                data_root,
                "session-clear",
                {
                    **default_state(),
                    "context_package": {
                        "goal": "obsolete goal",
                        "approval_boundary": "obsolete boundary",
                    },
                    "reported_conflict_ids": ["agents.md:obsolete-conflict"],
                },
            )
            marker = authenticated_marker(
                data_root,
                "session-clear",
                {"context_package": {}},
            )
            handle_event(
                {
                    "hook_event_name": "Stop",
                    "session_id": "session-clear",
                    "last_assistant_message": marker,
                },
                {"PLUGIN_DATA": raw},
            )
            state = load_state(data_root, "session-clear")

        self.assertEqual(state["context_package"], {})
        self.assertEqual(
            state["reported_conflict_ids"],
            ["agents.md:obsolete-conflict"],
        )

    def test_empty_conflict_update_does_not_erase_current_task_history(self):
        with tempfile.TemporaryDirectory() as raw:
            data_root = Path(raw)
            save_state(
                data_root,
                "session-keep-conflicts",
                {
                    **default_state(),
                    "reported_conflict_ids": ["agents.md:use-host-plan"],
                },
            )
            marker = authenticated_marker(
                data_root,
                "session-keep-conflicts",
                {
                    "plan_phase": "approved",
                    "reported_conflict_ids": [],
                },
            )
            handle_event(
                {
                    "hook_event_name": "Stop",
                    "session_id": "session-keep-conflicts",
                    "last_assistant_message": marker,
                },
                {"PLUGIN_DATA": raw},
            )
            state = load_state(data_root, "session-keep-conflicts")

        self.assertEqual(
            state["reported_conflict_ids"],
            ["agents.md:use-host-plan"],
        )

    def test_stop_marker_empty_value_removes_one_stale_context_field(self):
        with tempfile.TemporaryDirectory() as raw:
            data_root = Path(raw)
            save_state(
                data_root,
                "session-clear-field",
                {
                    **default_state(),
                    "context_package": {
                        "goal": "keep this goal",
                        "approval_boundary": "obsolete boundary",
                    },
                },
            )
            marker = authenticated_marker(
                data_root,
                "session-clear-field",
                {"context_package": {"approval_boundary": ""}},
            )
            handle_event(
                {
                    "hook_event_name": "Stop",
                    "session_id": "session-clear-field",
                    "last_assistant_message": marker,
                },
                {"PLUGIN_DATA": raw},
            )
            state = load_state(data_root, "session-clear-field")

        self.assertEqual(state["context_package"], {"goal": "keep this goal"})

    def test_completed_task_resets_on_the_next_real_prompt(self):
        with tempfile.TemporaryDirectory() as raw:
            data_root = Path(raw)
            state = {
                **default_state(),
                "task_depth": "Quick",
                "plan_phase": "complete",
                "context_package": {"goal": "Previous task"},
                "reported_conflict_ids": ["old-conflict"],
                "onboarding_status": "checked",
            }
            save_state(data_root, "session-next", state)
            event = read_fixture("session-start.json")
            event.update(
                {
                    "hook_event_name": "UserPromptSubmit",
                    "prompt": "开始另一个任务",
                    "session_id": "session-next",
                }
            )
            handle_event(event, {"PLUGIN_DATA": raw})
            updated = load_state(data_root, "session-next")

        self.assertEqual(updated["task_depth"], "unclassified")
        self.assertEqual(updated["plan_phase"], "routing")
        self.assertEqual(updated["context_package"], {})
        self.assertEqual(updated["reported_conflict_ids"], [])

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

    def test_manual_diagnostics_view_does_not_request_an_install_retry(self):
        with tempfile.TemporaryDirectory() as raw:
            data_root = Path(raw)
            state = {
                **default_state(),
                "onboarding_status": "degraded",
                "onboarding_diagnostics": ["humanizer: download failed"],
            }
            save_state(data_root, "session-diagnostics", state)
            event = read_fixture("session-start.json")
            event.update(
                {
                    "hook_event_name": "UserPromptSubmit",
                    "prompt": "查看安装诊断",
                    "session_id": "session-diagnostics",
                }
            )
            result = handle_event(event, {"PLUGIN_DATA": raw})
            updated = load_state(data_root, "session-diagnostics")

        context = result["hookSpecificOutput"]["additionalContext"]
        self.assertIn("humanizer: download failed", context)
        self.assertNotIn("$flowz-onboarding", context)
        self.assertIn("display only", context.lower())
        self.assertEqual(updated["onboarding_status"], "degraded")

    def test_explicit_retry_reopens_onboarding_without_starting_a_task(self):
        with tempfile.TemporaryDirectory() as raw:
            data_root = Path(raw)
            state = {
                **default_state(),
                "onboarding_status": "degraded",
                "onboarding_diagnostics": ["one saved failure"],
            }
            save_state(data_root, "session-retry", state)
            event = read_fixture("session-start.json")
            event.update(
                {
                    "hook_event_name": "UserPromptSubmit",
                    "prompt": "重试安装第三方 Skill",
                    "session_id": "session-retry",
                }
            )
            result = handle_event(event, {"PLUGIN_DATA": raw})
            updated = load_state(data_root, "session-retry")

        self.assertEqual(updated["onboarding_status"], "requested")
        self.assertEqual(updated["plan_phase"], "idle")
        self.assertIn("$flowz-onboarding", result["hookSpecificOutput"]["additionalContext"])

    def test_retry_requested_while_paused_is_delivered_after_resume(self):
        with tempfile.TemporaryDirectory() as raw:
            env = {"PLUGIN_DATA": raw}
            pause = read_fixture("pause.json")
            pause.update({"session_id": "session-paused-retry"})
            handle_event(pause, env)

            retry = read_fixture("pause.json")
            retry.update(
                {
                    "session_id": "session-paused-retry",
                    "prompt": "重试安装第三方 Skill",
                }
            )
            paused_result = handle_event(retry, env)
            paused_context = paused_result["hookSpecificOutput"]["additionalContext"]
            self.assertIn("queued", paused_context.lower())

            resume = read_fixture("resume.json")
            resume.update({"session_id": "session-paused-retry"})
            resumed_result = handle_event(resume, env)
            resumed_context = resumed_result["hookSpecificOutput"]["additionalContext"]

        self.assertIn("retry", resumed_context.lower())
        self.assertIn("once now", resumed_context.lower())

    def test_session_start_preserves_a_retry_queued_while_paused(self):
        with tempfile.TemporaryDirectory() as raw:
            data_root = Path(raw)
            save_state(
                data_root,
                "session-queued-retry",
                {
                    **default_state(),
                    "flowz_enabled": False,
                    "onboarding_status": "requested",
                    "onboarding_retry_pending": True,
                },
            )
            start = read_fixture("session-start.json")
            start.update(
                {
                    "session_id": "session-queued-retry",
                    "source": "compact",
                }
            )
            result = handle_event(start, {"PLUGIN_DATA": raw})
            context = result["hookSpecificOutput"]["additionalContext"]
            state = load_state(data_root, "session-queued-retry")

        self.assertIn("queued", context.lower())
        self.assertTrue(state["onboarding_retry_pending"])

    def test_session_start_recovers_compact_runtime_state(self):
        with tempfile.TemporaryDirectory() as raw:
            data_root = Path(raw)
            state = {
                **default_state(),
                "onboarding_status": "checked",
                "task_depth": "Full",
                "plan_phase": "executing",
                "context_package": {"goal": "Recover after compaction"},
                "reported_conflict_ids": ["skill:existing-workflow:host-plan"],
            }
            save_state(data_root, "session-compact", state)
            event = read_fixture("session-start.json")
            event.update({"session_id": "session-compact", "source": "compact"})
            result = handle_event(event, {"PLUGIN_DATA": raw})

        context = result["hookSpecificOutput"]["additionalContext"]
        for phrase in (
            "task depth: Full",
            "Plan phase: executing",
            "Recover after compaction",
            "skill:existing-workflow:host-plan",
            "onboarding: checked",
        ):
            self.assertIn(phrase, context)

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
        diagnostics = StringIO()
        with redirect_stderr(diagnostics):
            missing = handle_event(event, {})
            unwritable = handle_event(event, {"PLUGIN_DATA": "Z:\\does-not-exist"})
        self.assertIsInstance(missing, dict)
        self.assertIsInstance(unwritable, dict)

    def test_missing_data_root_uses_minimal_context_without_repeating_onboarding(self):
        event = read_fixture("session-start.json")
        event.update(
            {
                "hook_event_name": "UserPromptSubmit",
                "prompt": "Start the real task",
            }
        )
        diagnostics = StringIO()
        with redirect_stderr(diagnostics):
            first = handle_event(event, {})
            second = handle_event(event, {})

        for result in (first, second):
            context = result["hookSpecificOutput"]["additionalContext"]
            self.assertEqual(
                context,
                "FlowZ routing: enabled; hook state unavailable.",
            )
            self.assertNotIn("$flowz-onboarding", context)
        self.assertIn("state_root", diagnostics.getvalue())

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
        for event_name in ("SessionStart", "UserPromptSubmit", "Stop", "SessionEnd"):
            command = hooks["hooks"][event_name][0]["hooks"][0]
            self.assertEqual(command["type"], "command")
            self.assertIn("${PLUGIN_ROOT}", command["command"])
            self.assertIn("%PLUGIN_ROOT%", command["commandWindows"])
            self.assertTrue(command["command"].startswith("python3 "))
            self.assertTrue(command["commandWindows"].startswith("python "))
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

    def test_enabled_context_routes_through_workflow_but_paused_context_does_not(self):
        self.assertIn("$flowz-workflow", render_context(default_state()))
        paused = {**default_state(), "flowz_enabled": False}
        self.assertNotIn("$flowz-workflow", render_context(paused))

    def test_valid_hook_input_with_persistence_failure_exits_zero(self):
        event = read_fixture("session-start.json")
        with tempfile.TemporaryDirectory() as raw:
            blocked_root = Path(raw) / "not-a-directory"
            blocked_root.write_text("blocked", encoding="utf-8")
            env = os.environ.copy()
            env["PLUGIN_DATA"] = str(blocked_root)
            completed = subprocess.run(
                [sys.executable, str(HOOK)],
                input=json.dumps(event),
                text=True,
                capture_output=True,
                env=env,
                check=False,
            )
        self.assertEqual(completed.returncode, 0)
        self.assertIn("FlowZ hook diagnostic", completed.stderr)
        payload = json.loads(completed.stdout)
        self.assertEqual(
            payload["hookSpecificOutput"]["additionalContext"],
            "FlowZ routing: enabled; hook state unavailable.",
        )

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

    def test_script_uses_compatibility_data_root_across_the_hook_lifecycle(self):
        with tempfile.TemporaryDirectory() as raw:
            data_root = Path(raw)
            session_id = "session-compat-data"
            env = os.environ.copy()
            env.pop("PLUGIN_DATA", None)
            env["CLAUDE_PLUGIN_DATA"] = raw
            env["PLUGIN_ROOT"] = str(ROOT / "plugins/flowz")

            def run_event(event):
                completed = subprocess.run(
                    [sys.executable, str(HOOK)],
                    input=json.dumps(event),
                    text=True,
                    capture_output=True,
                    env=env,
                    check=False,
                )
                self.assertEqual(completed.returncode, 0, completed.stderr)
                return json.loads(completed.stdout)

            start = read_fixture("session-start.json")
            start["session_id"] = session_id
            run_event(start)
            self.assertTrue(_state_path(data_root, session_id).exists())

            prompt = read_fixture("pause.json")
            prompt.update(
                {
                    "session_id": session_id,
                    "prompt": "Continue the approved task",
                }
            )
            prompt_result = run_event(prompt)
            self.assertIn(
                "$flowz-onboarding",
                prompt_result["hookSpecificOutput"]["additionalContext"],
            )
            before_stop = load_state(data_root, session_id)
            nonce = before_stop["marker_nonce"]

            marker = (
                '<!-- flowz-state: '
                + json.dumps(
                    {"marker_nonce": nonce, "plan_phase": "approved"},
                    separators=(",", ":"),
                )
                + " -->"
            )
            run_event(
                {
                    "hook_event_name": "Stop",
                    "session_id": session_id,
                    "last_assistant_message": marker,
                    "stop_hook_active": False,
                }
            )
            after_stop = load_state(data_root, session_id)
            self.assertEqual(after_stop["plan_phase"], "approved")
            self.assertNotEqual(after_stop["marker_nonce"], nonce)

            compact = read_fixture("session-start.json")
            compact.update({"session_id": session_id, "source": "compact"})
            compact_result = run_event(compact)
            self.assertIn(
                "Plan phase: approved",
                compact_result["hookSpecificOutput"]["additionalContext"],
            )

            end = read_fixture("session-end.json")
            end["session_id"] = session_id
            run_event(end)
            self.assertFalse(_state_path(data_root, session_id).exists())

    def test_malformed_stdin_returns_nonzero_and_nonblocking_json(self):
        completed = subprocess.run(
            [sys.executable, str(HOOK)], input="not-json", text=True, capture_output=True
        )
        self.assertNotEqual(completed.returncode, 0)
        self.assertEqual(json.loads(completed.stdout), {"continue": True})
        self.assertIn("diagnostic", completed.stderr)


if __name__ == "__main__":
    unittest.main()
