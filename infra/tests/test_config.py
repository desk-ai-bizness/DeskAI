"""Basic tests for infrastructure environment configuration."""

import unittest

from config.dev import DEV_CONFIG
from config.prod import PROD_CONFIG


class EnvironmentConfigTest(unittest.TestCase):
    """Ensure environment configs expose expected naming prefix."""

    def test_resource_prefixes(self) -> None:
        self.assertEqual(DEV_CONFIG.resource_prefix, "deskai-dev")
        self.assertEqual(PROD_CONFIG.resource_prefix, "deskai-prod")

    def test_environment_specific_cors_origins(self) -> None:
        self.assertIn("https://app.dev.deskai.com.br", DEV_CONFIG.allowed_cors_origins)
        self.assertNotIn("http://localhost:5173", DEV_CONFIG.allowed_cors_origins)
        self.assertIn("https://app.deskai.com.br", PROD_CONFIG.allowed_cors_origins)

    def test_budget_limit_defaults(self) -> None:
        self.assertEqual(DEV_CONFIG.monthly_budget_limit_usd, 5)
        self.assertEqual(PROD_CONFIG.monthly_budget_limit_usd, 5)


if __name__ == "__main__":
    unittest.main()
