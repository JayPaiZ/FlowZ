"""End-to-end repository contract for the FlowZ Codex plugin."""

from __future__ import annotations

import json
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "plugins" / "flowz"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def frontmatter_name(skill_file: Path) -> str:
    content = skill_file.read_text(encoding="utf-8")
    match = re.search(r"(?m)^name:\s*([^\r\n]+)$", content)
    if match is None:
        raise AssertionError(f"missing frontmatter name: {skill_file}")
    return match.group(1).strip()


class EndToEndContractTests(unittest.TestCase):
    def test_marketplace_resolves_the_valid_plugin_manifest(self):
        marketplace = load_json(ROOT / ".agents/plugins/marketplace.json")
        entry = next(item for item in marketplace["plugins"] if item["name"] == "flowz")
        self.assertEqual(marketplace["name"], "flowz-local")
        self.assertEqual(entry["source"], {"source": "local", "path": "./plugins/flowz"})

        resolved_plugin = ROOT / entry["source"]["path"]
        manifest_path = resolved_plugin / ".codex-plugin/plugin.json"
        self.assertTrue(manifest_path.is_file())
        manifest = load_json(manifest_path)
        self.assertEqual(manifest["name"], entry["name"])
        for asset_field in ("composerIcon", "logo"):
            relative_asset = manifest["interface"][asset_field].removeprefix("./")
            self.assertTrue((resolved_plugin / relative_asset).is_file(), asset_field)

    def test_plugin_exposes_both_flowz_skills_and_session_hooks(self):
        expected_skills = {
            "flowz-workflow": PLUGIN / "skills/flowz-workflow/SKILL.md",
            "flowz-onboarding": PLUGIN / "skills/flowz-onboarding/SKILL.md",
        }
        self.assertEqual(
            {frontmatter_name(path) for path in expected_skills.values()},
            set(expected_skills),
        )

        hooks_path = PLUGIN / "hooks/hooks.json"
        self.assertTrue(hooks_path.is_file())
        hooks = load_json(hooks_path)["hooks"]
        self.assertEqual(
            set(hooks), {"SessionStart", "UserPromptSubmit", "Stop", "SessionEnd"}
        )

    def test_all_optional_upstream_dependencies_are_resolvable(self):
        catalog = load_json(
            PLUGIN / "skills/flowz-onboarding/references/third-party-skills.json"
        )
        common_path = ROOT / catalog["commonCatalog"]
        self.assertTrue(common_path.is_file())
        common = load_json(common_path)
        self.assertEqual(common["schemaVersion"], 1)
        expected = {
            "humanizer-zh",
            "humanizer",
            "grilling",
            "gstack-openclaw-office-hours",
        }
        self.assertEqual(set(catalog["dependencies"]), expected)
        self.assertEqual(set(common["dependencies"]), expected)
        for name, dependency in catalog["dependencies"].items():
            self.assertEqual(dependency["canonical"], name)
            self.assertTrue(dependency["optional"])
            self.assertTrue(dependency["repository"])
            self.assertTrue(dependency["installPath"])
            self.assertFalse(dependency["installPath"].endswith(".md"))

    def test_readme_keeps_both_optional_switches_off_by_default(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        controls_start = readme.index("## 暂停、恢复与可选功能")
        controls_end = readme.index("\n## ", controls_start + 1)
        controls = readme[controls_start:controls_end]
        self.assertIn("ChatGPT 网页版辅助默认关闭", controls)
        self.assertIn("用户验证建议也默认关闭", controls)
        self.assertIn("下一轮用户消息", controls)

    def test_main_contains_no_retired_cline_runtime_or_pdf(self):
        self.assertFalse((ROOT / ".clinerules").exists())
        self.assertFalse((ROOT / "使用说明.pdf").exists())

        legacy_resources = ROOT / ".workflow/resources"
        remaining_files = (
            [path for path in legacy_resources.rglob("*") if path.is_file()]
            if legacy_resources.exists()
            else []
        )
        self.assertEqual(remaining_files, [])

    def test_runtime_contract_does_not_depend_on_design_records(self):
        workflow = PLUGIN / "skills/flowz-workflow"
        workflow_text = (workflow / "SKILL.md").read_text(encoding="utf-8")
        onboarding_text = (
            PLUGIN / "skills/flowz-onboarding/SKILL.md"
        ).read_text(encoding="utf-8")
        runtime = (workflow / "references/runtime-state.md").read_text(
            encoding="utf-8"
        )
        self.assertTrue((workflow / "references/superpowers-integration.md").is_file())
        self.assertIn("Superpowers is not a FlowZ dependency", workflow_text)
        self.assertIn("four catalog dependencies", onboarding_text)
        self.assertIn("recommended_optional_workflows", runtime)
        self.assertIn("available_dependencies", runtime)
        self.assertFalse((ROOT / "docs" / "design").exists())
        ignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
        self.assertIn("/docs/design/", ignore)
        self.assertIn("/AGENTS.md", ignore)

    def test_hook_contract_keeps_task_scoped_recommendations_and_onboarding_separate(self):
        hook = (PLUGIN / "hooks/flowz_hook.py").read_text(encoding="utf-8")
        self.assertIn("recommended_optional_workflows", hook)
        self.assertIn("available_dependencies", hook)
        self.assertIn("_start_task", hook)
        self.assertIn("activate_flowz", hook)
        self.assertIn("defer_onboarding", hook)
        self.assertIn("response_detail", hook)
        self.assertIn("plan_summary", hook)
        self.assertNotIn("codex plugin add", hook)


if __name__ == "__main__":
    unittest.main()
