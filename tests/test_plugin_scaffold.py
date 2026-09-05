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

        plugin = json.loads(manifest.read_text(encoding="utf-8"))
        catalog = json.loads(marketplace.read_text(encoding="utf-8"))
        self.assertEqual(plugin["name"], "flowz")
        self.assertEqual(catalog["plugins"][0]["name"], "flowz")
        self.assertEqual(catalog["plugins"][0]["source"]["path"], "./plugins/flowz")


if __name__ == "__main__":
    unittest.main()
