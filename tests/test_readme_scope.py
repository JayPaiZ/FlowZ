"""Release-scope checks for the public Codex README.

These checks deliberately protect user-facing capabilities and retired runtime
dependencies, rather than prescribing prose or a particular Chinese wording.
"""

from pathlib import Path
import unittest


README = Path(__file__).resolve().parents[1] / "README.md"


class ReadmeScopeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.content = README.read_text(encoding="utf-8").lower()

    def test_explains_codex_installation_and_workflow_routing(self):
        """Fails if users lose the marketplace entry point or route choices."""
        for phrase in (
            "本地 marketplace",
            "quick",
            "standard",
            "full",
            "宿主 plan",
        ):
            self.assertIn(phrase, self.content)

    def test_explains_safety_controls_and_optional_assistance(self):
        """Fails if users lose control boundaries or the disabled-by-default aids."""
        for phrase in (
            "冲突",
            "暂停",
            "恢复",
            "chatgpt 网页版辅助",
            "默认关闭",
            "用户验证建议",
            "github",
            "隐私",
            "图标",
        ):
            self.assertIn(phrase, self.content)

    def test_does_not_require_retired_cline_or_legacy_planning_dependencies(self):
        """Fails if retired Cline/PDF requirements return to the Codex entry point."""
        for phrase in (
            "使用说明.pdf",
            "install-flowz-cline",
            "install-cline-skills",
            "/deep-planning",
            "superpowers:brainstorming",
        ):
            self.assertNotIn(phrase, self.content)


if __name__ == "__main__":
    unittest.main()
