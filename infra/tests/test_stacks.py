"""Infrastructure synthesis tests for core MVP stack guarantees."""

from __future__ import annotations

import unittest

import aws_cdk as cdk
from aws_cdk.assertions import Match, Template

from config.base import EnvironmentConfig
from config.dev import DEV_CONFIG
from stacks.api_stack import ApiStack
from stacks.auth_stack import AuthStack
from stacks.budget_stack import BudgetStack
from stacks.compute_stack import ComputeStack
from stacks.orchestration_stack import OrchestrationStack
from stacks.security_stack import SecurityStack
from stacks.storage_stack import StorageStack


class StackSynthesisTest(unittest.TestCase):
    """Validate baseline resource characteristics for Task 004."""

    def _create_foundation(
        self,
        *,
        config: EnvironmentConfig = DEV_CONFIG,
        shared_account_mode: bool = False,
    ) -> tuple[
        SecurityStack,
        StorageStack,
        AuthStack,
        ComputeStack,
        ApiStack,
        OrchestrationStack,
        BudgetStack,
    ]:
        app = cdk.App()
        aws_env = cdk.Environment(
            account=config.aws_account_id,
            region=config.aws_region,
        )

        security = SecurityStack(
            app,
            "deskai-dev-security-test",
            config=config,
            env=aws_env,
        )
        storage = StorageStack(
            app,
            "deskai-dev-storage-test",
            config=config,
            data_key=security.data_key,
            env=aws_env,
        )
        auth = AuthStack(
            app,
            "deskai-dev-auth-test",
            config=config,
            env=aws_env,
        )
        compute = ComputeStack(
            app,
            "deskai-dev-compute-test",
            config=config,
            permissions_boundary=security.permissions_boundary,
            consultation_table=storage.consultation_table,
            artifacts_bucket=storage.artifacts_bucket,
            data_key=security.data_key,
            deepgram_secret=security.deepgram_secret,
            claude_secret=security.claude_secret,
            env=aws_env,
        )
        api = ApiStack(
            app,
            "deskai-dev-api-test",
            config=config,
            user_pool=auth.user_pool,
            user_pool_client=auth.user_pool_client,
            bff_handler=compute.bff_handler,
            websocket_handler=compute.websocket_handler,
            env=aws_env,
        )
        orchestration = OrchestrationStack(
            app,
            "deskai-dev-orchestration-test",
            config=config,
            permissions_boundary=security.permissions_boundary,
            data_key=security.data_key,
            pipeline_handler=compute.pipeline_handler,
            env=aws_env,
        )
        budget = BudgetStack(
            app,
            "deskai-dev-budget-test",
            config=config,
            budget_alert_topic=orchestration.alerts_topic,
            shared_account_mode=shared_account_mode,
            env=aws_env,
        )

        return security, storage, auth, compute, api, orchestration, budget

    def test_security_stack_provisions_kms_and_secrets(self) -> None:
        security, *_ = self._create_foundation()
        template = Template.from_stack(security)
        template.resource_count_is("AWS::KMS::Key", 2)
        template.resource_count_is("AWS::SecretsManager::Secret", 2)

    def test_storage_stack_has_recovery_and_encryption_baselines(self) -> None:
        _, storage, *_ = self._create_foundation()
        template = Template.from_stack(storage)
        template.has_resource_properties(
            "AWS::DynamoDB::Table",
            {
                "BillingMode": "PAY_PER_REQUEST",
                "PointInTimeRecoverySpecification": {"PointInTimeRecoveryEnabled": True},
                "SSESpecification": {"KMSMasterKeyId": Match.any_value(), "SSEEnabled": True},
            },
        )
        template.has_resource_properties(
            "AWS::S3::Bucket",
            {
                "VersioningConfiguration": {"Status": "Enabled"},
                "BucketEncryption": Match.any_value(),
            },
        )

    def test_api_stack_provisions_http_and_websocket(self) -> None:
        *_, api, _, _ = self._create_foundation()
        template = Template.from_stack(api)
        template.resource_count_is("AWS::ApiGatewayV2::Api", 2)
        template.has_resource_properties(
            "AWS::ApiGatewayV2::Api",
            {
                "Name": DEV_CONFIG.http_api_name,
                "CorsConfiguration": Match.object_like(
                    {"AllowOrigins": Match.array_with(["https://app.dev.deskai.com.br"])}
                ),
                "ProtocolType": "HTTP",
            },
        )
        template.has_resource_properties(
            "AWS::ApiGatewayV2::Api",
            {
                "Name": DEV_CONFIG.websocket_api_name,
                "ProtocolType": "WEBSOCKET",
            },
        )

    def test_budget_stack_alerts_at_five_usd(self) -> None:
        *_, budget = self._create_foundation()
        template = Template.from_stack(budget)
        template.has_resource_properties(
            "AWS::Budgets::Budget",
            {
                "Budget": {
                    "BudgetLimit": {"Amount": 5, "Unit": "USD"},
                    "TimeUnit": "MONTHLY",
                },
                "NotificationsWithSubscribers": Match.array_with(
                    [
                        Match.object_like(
                            {"Notification": {"Threshold": 5.0, "ThresholdType": "ABSOLUTE_VALUE"}}
                        )
                    ]
                ),
            },
        )

    def test_budget_stack_adds_environment_filter_for_scoped_budget(self) -> None:
        *_, budget = self._create_foundation(shared_account_mode=True)
        template = Template.from_stack(budget)
        template.resource_count_is("AWS::Budgets::Budget", 1)
        template.has_resource_properties(
            "AWS::Budgets::Budget",
            {
                "Budget": Match.object_like(
                    {
                        "BudgetName": "deskai-dev-monthly-cost-env",
                        "FilterExpression": Match.object_like(
                            {
                                "Tags": Match.object_like(
                                    {
                                        "Key": "environment",
                                        "Values": Match.array_with(["dev"]),
                                    }
                                )
                            }
                        ),
                    }
                )
            },
        )


if __name__ == "__main__":
    unittest.main()
