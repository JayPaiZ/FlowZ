from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = ROOT / "plugins/flowz/skills/flowz-workflow"
SKILL = SKILL_DIR / "SKILL.md"


class WorkflowSkillTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contents = SKILL.read_text(encoding="utf-8")
        cls.normalized = re.sub(r"\s+", " ", cls.contents).lower()

    def test_skill_frontmatter_and_task_depth_contract(self):
        self.assertRegex(self.contents, r"(?m)^name:\s*flowz-workflow\s*$")
        for label in ("Quick", "Standard", "Full"):
            self.assertIn(label, self.contents)
        self.assertNotRegex(
            self.contents,
            r"(?i)\b(?:Micro|Extended|Deep|Emergency)\s+(?:task|mode|depth)",
        )

    def test_plan_reasoning_and_approval_contract(self):
        for phrase in (
            "host Plan first",
            "structured contract fallback",
            "reasoning",
            "must not modify `config.toml`",
            "approved boundary",
            "continue implementation and validation",
            "pause for out-of-scope",
            "destructive operation",
        ):
            self.assertIn(phrase.lower(), self.normalized)

    def test_quick_explicitly_bypasses_plan_paths(self):
        quick_start = self.normalized.index("- **quick**")
        standard_start = self.normalized.index("- **standard**", quick_start)
        quick = self.normalized[quick_start:standard_start]
        self.assertIn("does not use the host plan", quick)
        self.assertIn("or the structured contract fallback", quick)
        self.assertNotIn("use the host plan first", quick)
        self.assertNotIn("use the structured contract fallback", quick)

    def test_standard_and_full_order_plan_before_fallback(self):
        plan = re.sub(
            r"\s+",
            " ",
            (SKILL_DIR / "references" / "plan-policy.md").read_text(
                encoding="utf-8"
            ),
        ).lower()
        standard_start = plan.index("- **standard**")
        full_start = plan.index("- **full**", standard_start)
        standard = plan[standard_start:full_start]
        full = plan[full_start:]
        self.assertLess(
            standard.index("host plan first"),
            standard.index("structured contract fallback"),
        )
        self.assertLess(
            full.index("prefer the host plan"),
            full.index("structured design as fallback"),
        )

    def test_approval_continuity_precedes_pause_conditions(self):
        approval = self.normalized.index("once the user approves a plan")
        continuation = self.normalized.index("continue implementation and validation", approval)
        pause = self.normalized.index("pause for out-of-scope work", continuation)
        self.assertLess(approval, continuation)
        self.assertLess(continuation, pause)

    def test_conflict_and_superpowers_contract(self):
        for phrase in (
            "skip",
            "report once",
            "do not modify the source",
            "Superpowers",
            "only when it is visibly loaded",
        ):
            self.assertIn(phrase.lower(), self.normalized)
        self.assertNotIn("superpowers:brainstorming", self.contents)
        self.assertNotIn("/deep-planning", self.contents)

    def test_switches_and_references_are_explicit(self):
        for phrase in (
            "ChatGPT web assistance is off by default",
            "user validation suggestions are off by default",
            "pause FlowZ",
            "resume FlowZ",
            "next user turn",
        ):
            self.assertIn(phrase.lower(), self.normalized)
        for name in (
            "plan-policy.md",
            "conflict-policy.md",
            "host-adaptation.md",
            "runtime-state.md",
        ):
            self.assertTrue((SKILL_DIR / "references" / name).is_file(), name)

    def test_optional_switches_have_enabled_behavior_not_only_boolean_state(self):
        host = (SKILL_DIR / "references" / "host-adaptation.md").read_text(
            encoding="utf-8"
        )
        normalized = re.sub(r"\s+", " ", host).lower()
        for phrase in (
            "when chatgpt web assistance is on",
            "visible browser capability",
            "when user validation suggestions are on",
            "non-critical",
            "environment-specific",
            "critical regression",
        ):
            self.assertIn(phrase.lower(), normalized)

    def test_humanizer_language_routing_keeps_the_two_skills_distinct(self):
        for phrase in (
            "Chinese output",
            "humanizer-zh",
            "English output",
            "humanizer",
            "humanizer-en",
            "never substitute",
            "same passage",
        ):
            self.assertIn(phrase.lower(), self.normalized)

    def test_humanizer_mixed_language_and_explicit_dual_request_have_one_route(self):
        for phrase in (
            "mixed-language passage",
            "ask once",
            "same paragraph",
            "explicitly requests both",
            "separate sections",
        ):
            self.assertIn(phrase.lower(), self.normalized)

    def test_runtime_state_reference_defines_reviewable_stop_marker(self):
        state = (SKILL_DIR / "references" / "runtime-state.md").read_text(
            encoding="utf-8"
        )
        normalized = re.sub(r"\s+", " ", state).casefold()
        for phrase in (
            "<!-- flowz-state:",
            "task_depth",
            "plan_phase",
            "context_package",
            "reported_conflict_ids",
            "onboarding_status",
            "marker_nonce",
            "never include the original user prompt",
            "Stop hook",
        ):
            self.assertIn(phrase.casefold(), normalized)

    def test_supporting_references_cover_required_policies(self):
        for name, phrases in {
            "plan-policy.md": (
                "Quick",
                "Standard",
                "Full",
                "Goal",
                "Scope and non-goals",
                "Acceptance criteria",
                "Approval boundary",
            ),
            "conflict-policy.md": (
                "AGENTS.md",
                "existing Skills",
                "skip",
                "report once",
                "do not modify",
                "source locator",
                "rule-slug",
                "same id",
            ),
            "host-adaptation.md": (
                "CLI",
                "desktop",
                "host Plan",
                "next user turn",
                "not promise hot loading",
            ),
            "runtime-state.md": (
                "task_depth",
                "plan_phase",
                "context_package",
                "reported_conflict_ids",
                "onboarding_status",
            ),
        }.items():
            text = (SKILL_DIR / "references" / name).read_text(encoding="utf-8")
            normalized = re.sub(r"\s+", " ", text).lower()
            for phrase in phrases:
                self.assertIn(phrase.lower(), normalized, f"{name}: {phrase}")

    def test_skill_metadata_is_ascii_and_openai_metadata_exists(self):
        self.contents.encode("ascii")
        metadata = SKILL_DIR / "agents/openai.yaml"
        self.assertTrue(metadata.is_file())
        self.assertIn("display_name:", metadata.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
