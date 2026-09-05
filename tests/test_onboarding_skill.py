from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "plugins/flowz/skills/flowz-onboarding/SKILL.md"


class OnboardingSkillTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contents = SKILL.read_text(encoding="utf-8")

    def test_skill_name_and_install_contract(self):
        self.assertIn("name: flowz-onboarding", self.contents)
        for phrase in (
            "humanizer-zh",
            "humanizer",
            "humanizer-en",
            "grilling",
            "gstack-openclaw-office-hours",
            "office-hours",
            "native Codex Skill Installer",
            "GitHub",
            "never overwrite",
            "do not proactively check",
            "must not block\n`flowz-workflow`",
        ):
            self.assertIn(phrase, self.contents)

    def test_first_task_and_fallback_order_are_explicit(self):
        self.assertIn("first real task", self.contents)
        native = self.contents.index("native Codex Skill Installer first")
        github = self.contents.index("fall back to GitHub")
        self.assertLess(native, github)

    def test_fallback_stays_with_original_source(self):
        self.assertIn("only the original repository and path", self.contents)
        self.assertIn("only inside that same author\nand repository", self.contents)
        self.assertIn("Never switch automatically to a fork", self.contents)

    def test_manual_retry_and_diagnostics_are_separate(self):
        self.assertIn("Retry installation only when the user explicitly asks", self.contents)
        self.assertIn("Show saved installation diagnostics without retrying", self.contents)
        self.assertIn("degraded capability", self.contents)

    def test_skill_does_not_claim_ownership_or_install_unrelated_skill(self):
        self.assertNotIn("flowz-humanizer", self.contents)
        self.assertNotIn("flowz-grilling", self.contents)
        self.assertNotIn("grill-me", self.contents)
        self.assertNotIn("overwrite existing files", self.contents)


if __name__ == "__main__":
    unittest.main()
