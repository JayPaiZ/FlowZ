"""Release-scope checks for the public Codex README.

The gate protects user actions and durable capability relationships, not a
specific Chinese copy style.  A phrase is insufficient when its ordering or
scope changes the action a user must take.
"""

from pathlib import Path
import re
import unittest


README = Path(__file__).resolve().parents[1] / "README.md"


class ReadmeScopeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.content = README.read_text(encoding="utf-8")

    def section(self, heading: str, content: str | None = None) -> str:
        document = self.content if content is None else content
        start = document.index(heading)
        end = document.find("\n## ", start + len(heading))
        return document[start:] if end == -1 else document[start:end]

    def assert_installation_contract(self, content: str) -> None:
        installation = self.section("## 安装与首次启用", content)
        self.assertRegex(
            installation,
            r"仓库根目录[\s\S]*?`\.agents/plugins/marketplace\.json`",
        )
        self.assertRegex(
            installation,
            r"(?m)^codex plugin marketplace add <REPOSITORY_ROOT>$",
        )
        self.assertRegex(installation, r"(?m)^codex plugin add flowz@flowz-local$")
        self.assertNotIn("flowz@personal", installation)
        self.assertLess(
            installation.index("codex plugin marketplace add <REPOSITORY_ROOT>"),
            installation.index("codex plugin add flowz@flowz-local"),
        )
        self.assertIn("不需要手动编辑", installation)
        self.assertIn("config.toml", installation)
        self.assertIn("AGENTS.md", installation)
        self.assertIn("并指向同一个仓库根目录", installation)
        self.assertNotIn("并指向同一个文件", installation)
        self.assertRegex(
            installation,
            r"查看安装诊断[\s\S]*?不会重试",
        )

    def assert_plan_contract(self, content: str) -> None:
        self.assertRegex(
            content,
            r"FlowZ[\s\S]*?不替代 Codex 的 Plan",
        )
        routing = self.section("## FlowZ 如何选择工作深度", content)
        self.assertRegex(routing, r"\*\*Quick\*\*[\s\S]*?直接实施[\s\S]*?自动验证")
        for depth in ("Standard", "Full"):
            self.assertRegex(
                routing,
                rf"\*\*{depth}\*\*[\s\S]*?优先使用宿主 Plan[\s\S]*?"
                r"宿主没有可用 Plan[\s\S]*?结构化契约",
            )

    def assert_dependency_contract(self, content: str) -> None:
        dependencies = self.section("## 可选第三方 Skill", content)
        for canonical, alias in (
            ("humanizer-zh", "—"),
            ("humanizer", "humanizer-en"),
            ("grilling", "—"),
            ("gstack-openclaw-office-hours", "office-hours"),
        ):
            self.assertIn(canonical, dependencies)
            self.assertIn(alias, dependencies)
        self.assertLess(
            dependencies.index("Codex 原生 Skill Installer"),
            dependencies.index("GitHub"),
        )
        self.assertRegex(dependencies, r"若该路径失败[\s\S]*?GitHub 仓库和路径回退")
        self.assertIn("不会自动替换为 Fork", dependencies)
        catalog_link = re.search(r"\]\(([^)]+third-party-skills\.json)\)", dependencies)
        self.assertIsNotNone(catalog_link)
        self.assertTrue((README.parent / catalog_link.group(1)).is_file())

    def assert_control_and_conflict_contract(self, content: str) -> None:
        collaboration = self.section("## 与已有工作流协作", content)
        self.assertRegex(
            collaboration,
            r"冲突[\s\S]*?跳过[\s\S]*?只报告一次[\s\S]*?不会修改",
        )
        controls = self.section("## 暂停、恢复与可选功能", content)
        self.assertIn("下一轮用户消息", controls)
        self.assertIn("暂停 FlowZ", controls)
        self.assertIn("恢复 FlowZ", controls)
        self.assertIn("ChatGPT 网页版辅助默认关闭", controls)
        self.assertIn("用户验证建议也默认关闭", controls)
        self.assertIn("非关键", controls)
        self.assertIn("环境相关", controls)
        self.assertIn("浏览器", controls)

    def assert_privacy_and_metadata_contract(self, content: str) -> None:
        metadata = self.section("## 图标、作者与本地开发状态", content)
        self.assertIn("JayPaiZ", metadata)
        self.assertIn("MIT", metadata)
        self.assertIn("logo.png", metadata)
        self.assertIn("icon.png", metadata)
        privacy = self.section("## 隐私与项目边界", content)
        self.assertIn("不会把规则或隐藏状态写入你的项目", privacy)
        self.assertIn("不会修改项目 `AGENTS.md`", privacy)
        self.assertIn("`config.toml`", privacy)
        self.assertIn("不读取或输出凭据", privacy)
        self.assertIn("不保存原始提示", privacy)

    def test_readme_exposes_actionable_codex_installation(self):
        """Fails if registration and installation actions become ambiguous or reversed."""
        self.assert_installation_contract(self.content)

    def test_readme_describes_host_plan_priority_without_replacing_plan(self):
        """Fails if FlowZ stops being a host-Plan-first orchestration layer."""
        self.assert_plan_contract(self.content)

    def test_readme_preserves_dependency_fallback_and_optional_skills(self):
        """Fails if the supported Installer-to-GitHub fallback contract is lost."""
        self.assert_dependency_contract(self.content)

    def test_readme_preserves_conflict_controls_and_default_off_switches(self):
        """Fails if conflict handling or independent session controls become unclear."""
        self.assert_control_and_conflict_contract(self.content)

    def test_readme_preserves_project_write_and_privacy_boundary(self):
        """Fails if FlowZ could appear to modify a project or retain sensitive prompts."""
        self.assert_privacy_and_metadata_contract(self.content)

    def test_does_not_require_retired_cline_or_legacy_planning_dependencies(self):
        """Fails if retired Cline/PDF requirements return to the Codex entry point."""
        lowered = self.content.lower()
        for phrase in (
            "使用说明.pdf",
            "install-flowz-cline",
            "install-cline-skills",
            "/deep-planning",
            "superpowers:brainstorming",
        ):
            self.assertNotIn(phrase, lowered)

    def test_contract_checks_reject_missing_or_reversed_actions(self):
        """Proves each relationship check rejects the regression it is meant to catch."""
        self.assert_installation_contract(self.content)
        self.assert_plan_contract(self.content)
        self.assert_dependency_contract(self.content)
        self.assert_control_and_conflict_contract(self.content)
        self.assert_privacy_and_metadata_contract(self.content)

        mutations = (
            (
                "missing marketplace registration",
                self.assert_installation_contract,
                self.content.replace(
                    "codex plugin marketplace add <REPOSITORY_ROOT>",
                    "# registration omitted",
                    1,
                ),
            ),
            (
                "reversed installation order",
                self.assert_installation_contract,
                self.content.replace(
                    "codex plugin marketplace add <REPOSITORY_ROOT>\ncodex plugin add flowz@flowz-local",
                    "codex plugin add flowz@flowz-local\ncodex plugin marketplace add <REPOSITORY_ROOT>",
                    1,
                ),
            ),
            (
                "manual configuration requirement",
                self.assert_installation_contract,
                self.content.replace("不需要手动编辑", "需要手动编辑", 1),
            ),
            (
                "host Plan is no longer preferred",
                self.assert_plan_contract,
                self.content.replace("优先使用宿主 Plan", "仅在需要时使用宿主 Plan"),
            ),
            (
                "Plan replacement claim",
                self.assert_plan_contract,
                self.content.replace("不替代 Codex 的 Plan", "替代 Codex 的 Plan", 1),
            ),
            (
                "reversed fallback order",
                self.assert_dependency_contract,
                self.content.replace(
                    "Codex 原生 Skill Installer；若该路径失败，才按",
                    "GitHub；若该路径失败，才按 Codex 原生 Skill Installer 和",
                    1,
                ),
            ),
            (
                "default-off controls removed",
                self.assert_control_and_conflict_contract,
                self.content.replace("用户验证建议也默认关闭", "用户验证建议默认开启", 1),
            ),
            (
                "project-write privacy regression",
                self.assert_privacy_and_metadata_contract,
                self.content.replace(
                    "不会把规则或隐藏状态写入你的项目",
                    "会把规则或隐藏状态写入你的项目",
                    1,
                ),
            ),
        )
        for name, check, mutated in mutations:
            with self.subTest(name=name):
                with self.assertRaises(AssertionError):
                    check(mutated)


if __name__ == "__main__":
    unittest.main()
