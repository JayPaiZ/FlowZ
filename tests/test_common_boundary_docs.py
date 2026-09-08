from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
BOUNDARY = ROOT / "docs/common-boundary.md"
README = ROOT / "README.md"


class CommonBoundaryDocumentationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.boundary = BOUNDARY.read_text(encoding="utf-8")
        cls.readme = README.read_text(encoding="utf-8")

    def test_boundary_defines_one_way_sync_and_classification(self):
        for phrase in (
            "main -> FlowZ-Codex",
            "main -> FlowZ-Cline",
            "common contract",
            "Codex-only",
            "Cline-only",
            "experimental",
            "common and platform commits separate",
        ):
            self.assertIn(phrase, self.boundary)

    def test_boundary_defines_extraction_triggers_and_non_scope(self):
        for phrase in (
            "same logic",
            "two consecutive",
            "same defect",
            "three or more locations",
            "host event",
            "installer",
            "vendored",
            "platform-specific commits remain on their branch",
        ):
            self.assertIn(phrase.casefold(), self.boundary.casefold())

    def test_readme_points_to_common_boundary(self):
        self.assertIn("main", self.readme)
        self.assertIn("共通工作流语义", self.readme)
        self.assertIn("docs/common-boundary.md", self.readme)
        self.assertTrue(BOUNDARY.is_file())


if __name__ == "__main__":
    unittest.main()
