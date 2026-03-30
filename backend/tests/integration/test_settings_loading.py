"""Integration-style tests for settings defaults."""

import os
import unittest

from deskai.shared.config import load_settings


class SettingsLoadingTest(unittest.TestCase):
    """Validate environment fallback behavior for bootstrap settings."""

    def test_loads_default_environment(self) -> None:
        previous = os.environ.pop("DESKAI_ENV", None)
        settings = load_settings()
        self.assertEqual(settings.environment, "dev")
        if previous is not None:
            os.environ["DESKAI_ENV"] = previous


if __name__ == "__main__":
    unittest.main()
