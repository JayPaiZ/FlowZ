import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
CATALOG = (
    ROOT
    / "plugins/flowz/skills/flowz-onboarding/references/third-party-skills.json"
)

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


if __name__ == "__main__":
    unittest.main()
