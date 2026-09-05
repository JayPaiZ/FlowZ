import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "plugins/flowz"


class PluginMetadataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads(
            (PLUGIN / ".codex-plugin/plugin.json").read_text(encoding="utf-8")
        )

    def test_identity_and_license(self):
        self.assertEqual(self.manifest["name"], "flowz")
        self.assertEqual(self.manifest["author"]["name"], "JayPaiZ")
        self.assertEqual(self.manifest["license"], "MIT")
        self.assertEqual(self.manifest["repository"], "https://github.com/JayPaiZ/FlowZ")
        self.assertEqual(self.manifest["homepage"], "https://github.com/JayPaiZ/FlowZ")

    def test_interface_points_to_real_assets(self):
        interface = self.manifest["interface"]
        self.assertTrue(interface["displayName"])
        self.assertTrue(interface["shortDescription"])
        self.assertTrue(interface["longDescription"])
        self.assertEqual(interface["developerName"], "JayPaiZ")
        for field in ("composerIcon", "logo"):
            path = interface[field]
            self.assertTrue(path.startswith("./assets/"))
            self.assertTrue((PLUGIN / path[2:]).is_file(), path)

    def test_manifest_does_not_use_unsupported_top_level_hooks_field(self):
        self.assertNotIn("hooks", self.manifest)


if __name__ == "__main__":
    unittest.main()
