"""
Unit tests for the authoritative aria2 OptionRegistry and Serializers.
"""

import unittest

from shusha.infrastructure.aria2.errors import Aria2OptionValidationError
from shusha.infrastructure.aria2.option_registry import OptionRegistry


class TestOptionRegistry(unittest.TestCase):
    def setUp(self):
        self.registry = OptionRegistry.load_from_spec()

    def test_registry_loading(self):
        self.assertGreater(len(self.registry._options), 180)
        self.assertTrue(self.registry.contains("dir"))
        self.assertTrue(self.registry.contains("max-connection-per-server"))
        self.assertTrue(self.registry.contains("rpc-secret"))

    def test_lookup_by_short_name(self):
        # -d is short for --dir
        opt = self.registry.get("d")
        self.assertIsNotNone(opt)
        assert opt is not None
        self.assertEqual(opt.name, "dir")

    def test_validation_boolean(self):
        valid, _ = self.registry.validate_option("check-integrity", "true")
        self.assertTrue(valid)

        valid, _ = self.registry.validate_option("check-integrity", "false")
        self.assertTrue(valid)

        invalid, err = self.registry.validate_option("check-integrity", "maybe")
        self.assertFalse(invalid)
        self.assertIn("must be one of [true, false]", str(err))

    def test_validation_numeric_bounds(self):
        # connect-timeout possible values: 1-600
        valid, _ = self.registry.validate_option("connect-timeout", "30")
        self.assertTrue(valid)

        invalid, err = self.registry.validate_option("connect-timeout", "0")
        self.assertFalse(invalid)
        self.assertIn("below minimum", str(err))

        invalid_high, err_high = self.registry.validate_option("connect-timeout", "900")
        self.assertFalse(invalid_high)
        self.assertIn("exceeds maximum", str(err_high))

    def test_serialization_for_rpc(self):
        opts = {"dir": "/downloads", "max-connection-per-server": "16"}
        serialized = self.registry.serialize_for_rpc(opts)
        self.assertEqual(serialized["dir"], "/downloads")
        self.assertEqual(serialized["max-connection-per-server"], "16")

        with self.assertRaises(Aria2OptionValidationError):
            self.registry.serialize_for_rpc({"unknown-nonexistent-opt": "123"})

    def test_serialization_for_cli(self):
        opts = {"dir": "/downloads", "check-integrity": "true"}
        cli_args = self.registry.serialize_for_cli(opts)
        self.assertIn("--dir=/downloads", cli_args)
        self.assertIn("--check-integrity=true", cli_args)

    def test_serialization_for_config(self):
        opts = {"dir": "/downloads", "rpc-listen-port": "6800"}
        conf = self.registry.serialize_for_config_file(opts)
        self.assertIn("dir=/downloads", conf)
        self.assertIn("rpc-listen-port=6800", conf)

    def test_sensitive_flag(self):
        self.assertTrue(self.registry.is_sensitive("rpc-secret"))
        self.assertTrue(self.registry.is_sensitive("http-passwd"))
        self.assertFalse(self.registry.is_sensitive("dir"))

    def test_search(self):
        results = self.registry.search("bittorrent")
        self.assertGreater(len(results), 5)


if __name__ == "__main__":
    unittest.main()
