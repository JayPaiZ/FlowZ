from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "plugins/flowz/skills/flowz-onboarding/SKILL.md"
CATALOG = SKILL.parent / "references/third-party-skills.json"


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
            "must not block\n`flowz-workflow`",
        ):
            self.assertIn(phrase, self.contents)

    def test_referenced_catalog_exists_beside_the_skill(self):
        self.assertTrue(CATALOG.is_file())
        self.assertIn("references/third-party-skills.json", self.contents)
        self.assertIn("installPath", self.contents)
        self.assertIn("sourceEntry", self.contents)

    def test_first_task_and_fallback_order_are_explicit(self):
        self.assertIn("first real task", self.contents)
        native = self.contents.index("native Codex Skill Installer first")
        github = self.contents.index("fall back to GitHub")
        self.assertLess(native, github)

    def test_fallback_stays_with_original_source(self):
        normalized = " ".join(self.contents.split())
        self.assertIn("only the original repository and the catalog's `installPath` directory", normalized)
        self.assertIn("`sourceEntry` only to locate or verify", normalized)
        self.assertIn("only inside that same author and repository", normalized)
        self.assertIn("Never switch automatically to a\nfork", self.contents)

    def test_manual_retry_and_diagnostics_are_separate(self):
        normalized = " ".join(self.contents.split())
        self.assertIn("Retry installation only when the user explicitly asks", normalized)
        self.assertIn("display only the diagnostics", normalized)
        self.assertIn("do not run checks or retry an installation", normalized)
        self.assertIn("degraded capability", self.contents)
        self.assertIn("FlowZ state marker", self.contents)
        self.assertIn("marker_nonce", self.contents)

    def test_skill_does_not_claim_ownership_or_install_unrelated_skill(self):
        self.assertNotIn("flowz-humanizer", self.contents)
        self.assertNotIn("flowz-grilling", self.contents)
        self.assertNotIn("grill-me", self.contents)
        self.assertNotIn("overwrite existing files", self.contents)


if __name__ == "__main__":
    unittest.main()
