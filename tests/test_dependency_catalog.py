import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "plugins/flowz/references/third-party-skills.json"

EXPECTED = {
    "humanizer-zh": {
        "aliases": [],
        "repository": "op7418/Humanizer-zh",
        "path": "SKILL.md",
    },
    "humanizer": {
        "aliases": ["humanizer-en"],
        "repository": "blader/humanizer",
        "path": "SKILL.md",
    },
    "grilling": {
        "aliases": [],
        "repository": "mattpocock/skills",
        "path": "skills/productivity/grilling",
    },
    "gstack-openclaw-office-hours": {
        "aliases": ["office-hours"],
        "repository": "garrytan/gstack",
        "path": "openclaw/skills/gstack-openclaw-office-hours",
    },
}


class DependencyCatalogTests(unittest.TestCase):
    def test_catalog_contains_only_optional_upstream_dependencies(self):
        payload = json.loads(CATALOG.read_text(encoding="utf-8"))
        self.assertEqual(payload["schemaVersion"], 1)
        dependencies = payload["dependencies"]
        self.assertEqual(set(dependencies), set(EXPECTED))

        names = set(dependencies)
        aliases = set()
        for canonical, expected in EXPECTED.items():
            entry = dependencies[canonical]
            self.assertEqual(entry["canonical"], canonical)
            self.assertEqual(entry["aliases"], expected["aliases"])
            self.assertEqual(entry["repository"], expected["repository"])
            self.assertEqual(entry["path"], expected["path"])
            self.assertEqual(entry["installName"], canonical)
            self.assertTrue(entry["optional"])
            aliases.update(entry["aliases"])
        self.assertTrue(aliases.isdisjoint(names))
        self.assertNotIn("grill-me", names | aliases)
        self.assertFalse(any(name.startswith("flowz-") for name in names | aliases))


if __name__ == "__main__":
    unittest.main()
