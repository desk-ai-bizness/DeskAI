"""CDK app entrypoint for DeskAI infrastructure."""

from os import getenv

import aws_cdk as cdk

from config.base import EnvironmentConfig
from config.dev import DEV_CONFIG
from config.prod import PROD_CONFIG
from stacks.api_stack import ApiStack
from stacks.auth_stack import AuthStack
from stacks.budget_stack import BudgetStack
from stacks.cdn_stack import CdnStack
from stacks.compute_stack import ComputeStack
from stacks.monitoring_stack import MonitoringStack
from stacks.orchestration_stack import OrchestrationStack
from stacks.security_stack import SecurityStack
from stacks.storage_stack import StorageStack

CONFIG_BY_ENV: dict[str, EnvironmentConfig] = {
    "dev": DEV_CONFIG,
    "prod": PROD_CONFIG,
}


def main() -> None:
    env_name = getenv("DESKAI_ENV", "dev")
    config = CONFIG_BY_ENV[env_name]

    app = cdk.App()

    security = SecurityStack(app, f"deskai-{config.environment}-security", config=config)
    storage = StorageStack(app, f"deskai-{config.environment}-storage", config=config)
    auth = AuthStack(app, f"deskai-{config.environment}-auth", config=config)
    compute = ComputeStack(app, f"deskai-{config.environment}-compute", config=config)
    api = ApiStack(app, f"deskai-{config.environment}-api", config=config)
    orchestration = OrchestrationStack(
        app,
        f"deskai-{config.environment}-orchestration",
        config=config,
    )
    monitoring = MonitoringStack(app, f"deskai-{config.environment}-monitoring", config=config)
    budget = BudgetStack(app, f"deskai-{config.environment}-budget", config=config)
    cdn = CdnStack(app, f"deskai-{config.environment}-cdn", config=config)

    compute.add_dependency(storage)
    compute.add_dependency(security)
    api.add_dependency(auth)
    api.add_dependency(compute)
    orchestration.add_dependency(compute)
    monitoring.add_dependency(api)
    budget.add_dependency(monitoring)
    cdn.add_dependency(api)

    app.synth()


if __name__ == "__main__":
    main()
