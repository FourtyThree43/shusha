import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SPEC_DIR = ROOT / "spec" / "aria2"


class TestAria2Specification(unittest.TestCase):
    def test_options_spec_integrity(self):
        options_file = SPEC_DIR / "options.json"
        self.assertTrue(options_file.exists(), "options.json must exist")

        with open(options_file, encoding="utf-8") as f:
            options = json.load(f)

        self.assertGreaterEqual(
            len(options), 180, "Must catalogue at least 180 aria2 options"
        )

        required_fields = {
            "name",
            "short_name",
            "category",
            "type",
            "default",
            "minimum",
            "maximum",
            "enum_values",
            "scope",
            "rpc_supported",
            "cli_supported",
            "sensitive",
            "deprecated",
            "experimental",
            "description",
            "documentation_reference",
        }

        for opt in options:
            self.assertTrue(
                required_fields.issubset(opt.keys()),
                f"Option {opt.get('name')} missing fields",
            )
            self.assertIsInstance(opt["name"], str)
            self.assertIsInstance(opt["scope"], list)
            self.assertIsInstance(opt["sensitive"], bool)

        # Verify sensitive options classification
        rpc_secret_opt = next((o for o in options if o["name"] == "rpc-secret"), None)
        self.assertIsNotNone(rpc_secret_opt)
        assert rpc_secret_opt is not None
        self.assertTrue(
            rpc_secret_opt["sensitive"], "rpc-secret must be classified as sensitive"
        )

    def test_rpc_methods_integrity(self):
        rpc_file = SPEC_DIR / "rpc.json"
        self.assertTrue(rpc_file.exists(), "rpc.json must exist")

        with open(rpc_file, encoding="utf-8") as f:
            methods = json.load(f)

        self.assertGreaterEqual(
            len(methods), 30, "Must catalogue at least 30 RPC methods"
        )

        method_names = {m["name"] for m in methods}
        expected_core_methods = {
            "aria2.addUri",
            "aria2.addTorrent",
            "aria2.addMetalink",
            "aria2.remove",
            "aria2.pause",
            "aria2.unpause",
            "aria2.tellStatus",
            "aria2.getFiles",
            "aria2.getPeers",
            "aria2.getServers",
            "aria2.tellActive",
            "aria2.tellWaiting",
            "aria2.tellStopped",
            "aria2.changePosition",
            "aria2.changeUri",
            "aria2.getOption",
            "aria2.changeOption",
            "aria2.getGlobalOption",
            "aria2.changeGlobalOption",
            "aria2.getGlobalStat",
            "aria2.getVersion",
            "aria2.shutdown",
            "system.multicall",
        }
        self.assertTrue(expected_core_methods.issubset(method_names))

    def test_notifications_spec_integrity(self):
        notif_file = SPEC_DIR / "notifications.json"
        self.assertTrue(notif_file.exists())

        with open(notif_file, encoding="utf-8") as f:
            notifs = json.load(f)

        names = {n["name"] for n in notifs}
        self.assertIn("aria2.onDownloadStart", names)
        self.assertIn("aria2.onDownloadComplete", names)
        self.assertIn("aria2.onDownloadError", names)

    def test_errors_spec_integrity(self):
        errors_file = SPEC_DIR / "errors.json"
        self.assertTrue(errors_file.exists())

        with open(errors_file, encoding="utf-8") as f:
            errors = json.load(f)

        codes = {e["code"] for e in errors}
        # Check standard aria2 error codes (0 to 32)
        for i in range(33):
            self.assertIn(i, codes, f"Error code {i} must be catalogued")

    def test_versions_spec_integrity(self):
        ver_file = SPEC_DIR / "versions.json"
        self.assertTrue(ver_file.exists())

        with open(ver_file, encoding="utf-8") as f:
            ver = json.load(f)

        self.assertIn("minimum_supported_version", ver)
        self.assertIn("required_features", ver)


if __name__ == "__main__":
    unittest.main()
