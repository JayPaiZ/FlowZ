import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class PluginScaffoldTests(unittest.TestCase):
    def test_plugin_manifest_and_marketplace_exist(self):
        manifest = ROOT / "plugins/flowz/.codex-plugin/plugin.json"
        marketplace = ROOT / ".agents/plugins/marketplace.json"
        self.assertTrue(manifest.is_file())
        self.assertTrue(marketplace.is_file())
        for directory in ("skills", "hooks", "assets"):
            self.assertTrue((ROOT / "plugins/flowz" / directory).is_dir())

        plugin = json.loads(manifest.read_text(encoding="utf-8"))
        catalog = json.loads(marketplace.read_text(encoding="utf-8"))
        self.assertEqual(plugin["name"], "flowz")
        self.assertIn("version", plugin)
        self.assertIn("description", plugin)
        self.assertEqual(len(catalog["plugins"]), 1)
        entry = catalog["plugins"][0]
        self.assertEqual(entry["name"], "flowz")
        self.assertEqual(entry["source"]["source"], "local")
        self.assertEqual(entry["source"]["path"], "./plugins/flowz")
        self.assertEqual(entry["policy"]["installation"], "AVAILABLE")
        self.assertEqual(entry["policy"]["authentication"], "ON_INSTALL")
        self.assertEqual(entry["category"], "Productivity")


if __name__ == "__main__":
    unittest.main()
