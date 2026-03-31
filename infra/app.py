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
    if env_name not in CONFIG_BY_ENV:
        supported_envs = ", ".join(sorted(CONFIG_BY_ENV))
        raise ValueError(
            f"Unsupported DESKAI_ENV '{env_name}'. Supported values: {supported_envs}."
        )

    config = CONFIG_BY_ENV[env_name]
    aws_env = cdk.Environment(account=config.aws_account_id, region=config.aws_region)
    shared_account_mode = DEV_CONFIG.aws_account_id == PROD_CONFIG.aws_account_id

    app = cdk.App()
    cdk.Tags.of(app).add("project", "deskai")
    cdk.Tags.of(app).add("environment", config.environment)
    cdk.Tags.of(app).add("managed-by", "cdk")
    cdk.Tags.of(app).add(
        "account-mode",
        "shared" if shared_account_mode else "dedicated",
    )
    cdk.Tags.of(app).add("data-classification", "sensitive-health")

    stack_hardening_kwargs = {
        "env": aws_env,
        "termination_protection": config.is_production and shared_account_mode,
    }

    security = SecurityStack(
        app,
        f"deskai-{config.environment}-security",
        config=config,
        **stack_hardening_kwargs,
    )
    storage = StorageStack(
        app,
        f"deskai-{config.environment}-storage",
        config=config,
        data_key=security.data_key,
        **stack_hardening_kwargs,
    )
    auth = AuthStack(
        app,
        f"deskai-{config.environment}-auth",
        config=config,
        **stack_hardening_kwargs,
    )
    compute = ComputeStack(
        app,
        f"deskai-{config.environment}-compute",
        config=config,
        permissions_boundary=security.permissions_boundary,
        consultation_table=storage.consultation_table,
        artifacts_bucket=storage.artifacts_bucket,
        data_key=security.data_key,
        deepgram_secret=security.deepgram_secret,
        claude_secret=security.claude_secret,
        user_pool_id=auth.user_pool.user_pool_id,
        user_pool_client_id=auth.user_pool_client.user_pool_client_id,
        user_pool_arn=auth.user_pool.user_pool_arn,
        **stack_hardening_kwargs,
    )
    api = ApiStack(
        app,
        f"deskai-{config.environment}-api",
        config=config,
        user_pool=auth.user_pool,
        user_pool_client=auth.user_pool_client,
        bff_handler=compute.bff_handler,
        websocket_handler=compute.websocket_handler,
        **stack_hardening_kwargs,
    )
    orchestration = OrchestrationStack(
        app,
        f"deskai-{config.environment}-orchestration",
        config=config,
        permissions_boundary=security.permissions_boundary,
        data_key=security.data_key,
        pipeline_handler=compute.pipeline_handler,
        **stack_hardening_kwargs,
    )
    monitoring = MonitoringStack(
        app,
        f"deskai-{config.environment}-monitoring",
        config=config,
        alarm_topic=orchestration.alerts_topic,
        bff_handler=compute.bff_handler,
        websocket_handler=compute.websocket_handler,
        pipeline_handler=compute.pipeline_handler,
        http_api_id=api.http_api.api_id,
        websocket_api_id=api.websocket_api.api_id,
        consultation_workflow=orchestration.consultation_workflow,
        processing_dlq=orchestration.processing_dlq,
        **stack_hardening_kwargs,
    )
    budget = BudgetStack(
        app,
        f"deskai-{config.environment}-budget",
        config=config,
        budget_alert_topic=orchestration.alerts_topic,
        shared_account_mode=shared_account_mode,
        **stack_hardening_kwargs,
    )
    cdn = CdnStack(
        app,
        f"deskai-{config.environment}-cdn",
        config=config,
        **stack_hardening_kwargs,
    )

    compute.add_dependency(storage)
    compute.add_dependency(security)
    compute.add_dependency(auth)
    api.add_dependency(auth)
    api.add_dependency(compute)
    orchestration.add_dependency(compute)
    monitoring.add_dependency(api)
    budget.add_dependency(monitoring)
    cdn.add_dependency(api)

    app.synth()


if __name__ == "__main__":
    main()
