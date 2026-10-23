from __future__ import annotations
import os
import unittest
from unittest.mock import patch
from scripts.build_environment import collect_build_environment, validate_build_environment, DISTRIBUTIONS
from scripts import standalone_entry

class BuildEnvironmentTests(unittest.TestCase):
    def test_actual_environment_and_patch_identity(self):
        environment = collect_build_environment()
        self.assertEqual(validate_build_environment(environment), ())
        self.assertEqual(len(environment["Python"].split(".")), 3)
        for python in ("3.12.10", "3.12.14"):
            self.assertEqual(validate_build_environment({**environment, "Python": python}), ())

    def test_missing_and_drift_fail_closed(self):
        environment = collect_build_environment()
        self.assertTrue(validate_build_environment(None))
        for key in (*DISTRIBUTIONS, "Qt", "Python", "implementation", "system", "bits"):
            with self.subTest(key=key):
                bad = dict(environment)
                bad.pop(key)
                self.assertTrue(validate_build_environment(bad))
                bad[key] = "unexpected"
                self.assertTrue(validate_build_environment(bad))

    def test_environment_variable_cannot_bypass_main(self):
        with patch.dict(os.environ, {"QZ_G08_IMAGE_PROBE_PATH": "unused.json"}), patch("sys.argv", ["app"]), patch.object(standalone_entry, "main", return_value=17) as main:
            self.assertEqual(standalone_entry.entry(), 17)
            main.assert_called_once_with()

    def test_probe_requires_explicit_output_and_rejects_extra_arguments(self):
        for arguments in (["--probe-images"], ["--probe-images", "out.json", "--unknown"]):
            with self.subTest(arguments=arguments), patch("sys.argv", ["app", *arguments]), self.assertRaises(SystemExit):
                standalone_entry.entry()
