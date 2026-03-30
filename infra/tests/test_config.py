"""Basic tests for infrastructure environment configuration."""

import unittest

from config.dev import DEV_CONFIG
from config.prod import PROD_CONFIG


class EnvironmentConfigTest(unittest.TestCase):
    """Ensure environment configs expose expected naming prefix."""

    def test_resource_prefixes(self) -> None:
        self.assertEqual(DEV_CONFIG.resource_prefix, "deskai-dev")
        self.assertEqual(PROD_CONFIG.resource_prefix, "deskai-prod")


if __name__ == "__main__":
    unittest.main()
