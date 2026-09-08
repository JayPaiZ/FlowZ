import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
CATALOG = (
    ROOT
    / "plugins/flowz/skills/flowz-onboarding/references/third-party-skills.json"
)
COMMON_CATALOG = ROOT / "core/flowz/dependency-catalog.json"

EXPECTED = {
    "humanizer-zh": {
        "aliases": [],
        "repository": "op7418/Humanizer-zh",
        "installPath": ".",
        "sourceEntry": "SKILL.md",
    },
    "humanizer": {
        "aliases": ["humanizer-en"],
        "repository": "blader/humanizer",
        "installPath": ".",
        "sourceEntry": "SKILL.md",
    },
    "grilling": {
        "aliases": [],
        "repository": "mattpocock/skills",
        "installPath": "skills/productivity/grilling",
        "sourceEntry": "skills/productivity/grilling",
    },
    "gstack-openclaw-office-hours": {
        "aliases": ["office-hours"],
        "repository": "garrytan/gstack",
        "installPath": "openclaw/skills/gstack-openclaw-office-hours",
        "sourceEntry": "openclaw/skills/gstack-openclaw-office-hours",
    },
}


class DependencyCatalogTests(unittest.TestCase):
    def test_catalog_contains_only_optional_upstream_dependencies(self):
        payload = json.loads(CATALOG.read_text(encoding="utf-8"))
        self.assertEqual(payload["schemaVersion"], 2)
        dependencies = payload["dependencies"]
        self.assertEqual(set(dependencies), set(EXPECTED))

        names = set(dependencies)
        aliases = set()
        for canonical, expected in EXPECTED.items():
            entry = dependencies[canonical]
            self.assertEqual(entry["canonical"], canonical)
            self.assertEqual(entry["aliases"], expected["aliases"])
            self.assertEqual(entry["repository"], expected["repository"])
            self.assertEqual(entry["installPath"], expected["installPath"])
            self.assertEqual(entry["sourceEntry"], expected["sourceEntry"])
            self.assertFalse(entry["installPath"].endswith(".md"))
            if entry["installPath"] == ".":
                self.assertEqual(entry["sourceEntry"], "SKILL.md")
            else:
                self.assertTrue(
                    entry["sourceEntry"] == entry["installPath"]
                    or entry["sourceEntry"].startswith(entry["installPath"] + "/")
                )
            self.assertEqual(entry["installName"], canonical)
            self.assertTrue(entry["optional"])
            aliases.update(entry["aliases"])
        self.assertTrue(aliases.isdisjoint(names))
        self.assertNotIn("grill-me", names | aliases)
        self.assertFalse(any(name.startswith("flowz-") for name in names | aliases))

    def test_codex_catalog_is_a_projection_of_the_common_catalog(self):
        catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
        common = json.loads(COMMON_CATALOG.read_text(encoding="utf-8"))
        self.assertEqual(catalog["commonCatalog"], "core/flowz/dependency-catalog.json")
        self.assertEqual(common["schemaVersion"], 1)
        self.assertEqual(set(catalog["dependencies"]), set(common["dependencies"]))
        for dependency_id, common_entry in common["dependencies"].items():
            projection = catalog["dependencies"][dependency_id]
            self.assertEqual(projection["canonical"], common_entry["id"])
            self.assertEqual(projection["aliases"], common_entry["aliases"])
            self.assertEqual(projection["purpose"], common_entry["purpose"])
            self.assertEqual(projection["optional"], common_entry["optional"])
            self.assertEqual(projection["repository"], common_entry["source"]["repository"])
            self.assertEqual(projection["installPath"], common_entry["source"]["path"])


if __name__ == "__main__":
    unittest.main()
