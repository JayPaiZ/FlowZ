import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
CORE = ROOT / "core/flowz"


class CommonContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contract = json.loads(
            (CORE / "workflow-contract.json").read_text(encoding="utf-8")
        )
        cls.vectors = json.loads(
            (CORE / "conformance-vectors.json").read_text(encoding="utf-8")
        )

    def test_contract_has_stable_host_neutral_shape(self):
        self.assertEqual(self.contract["schemaVersion"], 1)
        self.assertEqual(
            set(self.contract["taskTiers"]), {"Quick", "Standard", "Full"}
        )
        self.assertEqual(
            self.contract["lifecycle"]["stages"],
            [
                "intake",
                "problem_exploration",
                "solution_design",
                "design_challenge",
                "human_approval",
                "writing_plan",
                "implementation",
                "verification",
            ],
        )
        self.assertTrue(self.contract["lifecycle"]["singleStageLead"])
        self.assertEqual(
            self.contract["contextPacket"]["requiredFields"],
            [
                "goal",
                "scopeAndNonGoals",
                "constraints",
                "evidence",
                "confirmedDecisions",
                "openQuestions",
                "acceptanceCriteria",
                "verification",
                "nextStep",
            ],
        )

    def test_contract_captures_risk_privacy_and_completion_semantics(self):
        risk = self.contract["riskAndApproval"]
        self.assertTrue(risk["lowImpact"]["continueWithoutApproval"])
        self.assertEqual(
            set(risk["approvalTriggers"]),
            {
                "behavior",
                "data",
                "permissions",
                "architecture",
                "externalState",
                "irreversible",
            },
        )
        self.assertTrue(self.contract["conflictPolicy"]["preserveHigherPriority"])
        self.assertFalse(self.contract["conflictPolicy"]["modifyConflictingSource"])
        self.assertEqual(
            self.contract["completionSummary"]["requiredFields"],
            ["changed", "verified", "remainingRisksOrUnfinished", "nextUserStep"],
        )
        forbidden = set(self.contract["privacy"]["mustNotPersist"])
        self.assertTrue(
            {"fullPrompt", "fullResponse", "hiddenReasoning", "credentials"}
            <= forbidden
        )

    def test_vectors_are_platform_neutral_and_match_contract(self):
        self.assertEqual(self.vectors["schemaVersion"], 1)
        self.assertEqual(self.vectors["tiers"], ["Quick", "Standard", "Full"])
        self.assertEqual(
            self.vectors["completionSummaryFields"],
            self.contract["completionSummary"]["requiredFields"],
        )
        self.assertEqual(
            {case["name"] for case in self.vectors["approvalCases"]},
            {"low_impact_local", "material_boundary"},
        )
        serialized = json.dumps(
            {"contract": self.contract, "vectors": self.vectors},
            ensure_ascii=False,
        ).casefold()
        for forbidden in (
            "codex",
            "cline",
            "hook_event_name",
            "plugin_data",
            "/deep-planning",
            ".clinerules",
            "plugins/flowz",
        ):
            self.assertNotIn(forbidden, serialized)

    def test_common_files_remain_host_neutral(self):
        for path in sorted(CORE.rglob("*")):
            if not path.is_file():
                continue
            content = path.read_text(encoding="utf-8").casefold()
            for forbidden in (
                "codex",
                "cline",
                "hook_event_name",
                "plugin_data",
                "/deep-planning",
                ".clinerules",
                "plugins/flowz",
            ):
                self.assertNotIn(forbidden, content, path.name)

    def test_host_specific_marker_mutations_are_rejected(self):
        forbidden_markers = (
            "codex",
            "cline",
            "hook_event_name",
            "plugin_data",
            "/deep-planning",
            ".clinerules",
            "plugins/flowz",
        )

        def assert_host_neutral(serialized):
            for marker in forbidden_markers:
                if marker in serialized:
                    raise AssertionError(f"host marker leaked: {marker}")

        clean = json.dumps(self.contract, ensure_ascii=False).casefold()
        assert_host_neutral(clean)
        for forbidden in forbidden_markers:
            with self.subTest(forbidden=forbidden):
                with self.assertRaises(AssertionError):
                    assert_host_neutral(clean + forbidden)


if __name__ == "__main__":
    unittest.main()
