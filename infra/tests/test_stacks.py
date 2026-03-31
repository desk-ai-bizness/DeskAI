"""Infrastructure synthesis tests for core MVP stack guarantees."""

from __future__ import annotations

import unittest
from typing import NamedTuple

import aws_cdk as cdk
from aws_cdk.assertions import Match, Template

from config.base import EnvironmentConfig
from config.dev import DEV_CONFIG
from stacks.api_stack import ApiStack
from stacks.auth_stack import AuthStack
from stacks.budget_stack import BudgetStack
from stacks.cdn_stack import CdnStack
from stacks.compute_stack import ComputeStack
from stacks.monitoring_stack import MonitoringStack
from stacks.orchestration_stack import OrchestrationStack
from stacks.security_stack import SecurityStack
from stacks.storage_stack import StorageStack


class Foundation(NamedTuple):
    security: SecurityStack
    storage: StorageStack
    auth: AuthStack
    compute: ComputeStack
    api: ApiStack
    orchestration: OrchestrationStack
    budget: BudgetStack
    monitoring: MonitoringStack
    cdn: CdnStack


class StackSynthesisTest(unittest.TestCase):
    """Validate baseline resource characteristics for Task 004."""

    def _create_foundation(
        self,
        *,
        config: EnvironmentConfig = DEV_CONFIG,
        shared_account_mode: bool = False,
    ) -> Foundation:
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
            user_pool_id=auth.user_pool.user_pool_id,
            user_pool_client_id=auth.user_pool_client.user_pool_client_id,
            user_pool_arn=auth.user_pool.user_pool_arn,
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
        monitoring = MonitoringStack(
            app,
            "deskai-dev-monitoring-test",
            config=config,
            alarm_topic=orchestration.alerts_topic,
            bff_handler=compute.bff_handler,
            websocket_handler=compute.websocket_handler,
            pipeline_handler=compute.pipeline_handler,
            http_api_id=api.http_api.api_id,
            websocket_api_id=api.websocket_api.api_id,
            consultation_workflow=orchestration.consultation_workflow,
            processing_dlq=orchestration.processing_dlq,
            env=aws_env,
        )
        cdn = CdnStack(
            app,
            "deskai-dev-cdn-test",
            config=config,
            env=aws_env,
        )

        return Foundation(
            security=security,
            storage=storage,
            auth=auth,
            compute=compute,
            api=api,
            orchestration=orchestration,
            budget=budget,
            monitoring=monitoring,
            cdn=cdn,
        )

    # --- Security ---

    def test_security_stack_provisions_kms_and_secrets(self) -> None:
        f = self._create_foundation()
        template = Template.from_stack(f.security)
        template.resource_count_is("AWS::KMS::Key", 2)
        template.resource_count_is("AWS::SecretsManager::Secret", 2)

    def test_security_stack_enables_kms_key_rotation(self) -> None:
        f = self._create_foundation()
        template = Template.from_stack(f.security)
        keys = template.find_resources("AWS::KMS::Key")
        for logical_id, resource in keys.items():
            self.assertTrue(
                resource["Properties"].get("EnableKeyRotation"),
                f"KMS key {logical_id} must have key rotation enabled",
            )

    # --- Storage ---

    def test_storage_stack_has_recovery_and_encryption_baselines(self) -> None:
        f = self._create_foundation()
        template = Template.from_stack(f.storage)
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

    def test_storage_stack_has_three_gsis(self) -> None:
        f = self._create_foundation()
        template = Template.from_stack(f.storage)
        template.has_resource_properties(
            "AWS::DynamoDB::Table",
            {
                "GlobalSecondaryIndexes": Match.array_with(
                    [
                        Match.object_like({"IndexName": "gsi_doctor_date"}),
                        Match.object_like({"IndexName": "gsi_status"}),
                        Match.object_like({"IndexName": "gsi_patient"}),
                    ]
                ),
            },
        )

    def test_storage_stack_blocks_public_s3_access(self) -> None:
        f = self._create_foundation()
        template = Template.from_stack(f.storage)
        template.has_resource_properties(
            "AWS::S3::Bucket",
            {
                "PublicAccessBlockConfiguration": {
                    "BlockPublicAcls": True,
                    "BlockPublicPolicy": True,
                    "IgnorePublicAcls": True,
                    "RestrictPublicBuckets": True,
                },
            },
        )

    # --- Auth ---

    def test_auth_stack_disables_self_signup(self) -> None:
        f = self._create_foundation()
        template = Template.from_stack(f.auth)
        template.has_resource_properties(
            "AWS::Cognito::UserPool",
            {
                "AdminCreateUserConfig": {"AllowAdminCreateUserOnly": True},
            },
        )

    def test_auth_stack_enforces_password_policy(self) -> None:
        f = self._create_foundation()
        template = Template.from_stack(f.auth)
        template.has_resource_properties(
            "AWS::Cognito::UserPool",
            {
                "Policies": {
                    "PasswordPolicy": Match.object_like(
                        {
                            "MinimumLength": 12,
                            "RequireLowercase": True,
                            "RequireUppercase": True,
                            "RequireNumbers": True,
                            "RequireSymbols": True,
                        }
                    ),
                },
            },
        )

    # --- Compute ---

    def test_compute_stack_provisions_four_lambda_functions(self) -> None:
        f = self._create_foundation()
        template = Template.from_stack(f.compute)
        template.resource_count_is("AWS::Lambda::Function", 4)
        template.has_resource_properties(
            "AWS::Lambda::Function",
            {"Runtime": "python3.12"},
        )

    # --- API ---

    def test_api_stack_provisions_http_and_websocket(self) -> None:
        f = self._create_foundation()
        template = Template.from_stack(f.api)
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

    # --- Orchestration ---

    def test_orchestration_stack_provisions_workflow_and_queues(self) -> None:
        f = self._create_foundation()
        template = Template.from_stack(f.orchestration)
        template.resource_count_is("AWS::StepFunctions::StateMachine", 1)
        template.resource_count_is("AWS::SQS::Queue", 2)
        template.resource_count_is("AWS::SNS::Topic", 1)
        template.resource_count_is("AWS::Events::EventBus", 1)

    # --- Budget ---

    def test_budget_stack_alerts_at_five_usd(self) -> None:
        f = self._create_foundation()
        template = Template.from_stack(f.budget)
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
        f = self._create_foundation(shared_account_mode=True)
        template = Template.from_stack(f.budget)
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

    # --- Monitoring ---

    def test_monitoring_stack_provisions_dashboard_and_alarms(self) -> None:
        f = self._create_foundation()
        template = Template.from_stack(f.monitoring)
        template.resource_count_is("AWS::CloudWatch::Dashboard", 1)
        template.resource_count_is("AWS::CloudWatch::Alarm", 6)

    # --- CDN ---

    def test_cdn_stack_provisions_two_distributions(self) -> None:
        f = self._create_foundation()
        template = Template.from_stack(f.cdn)
        template.resource_count_is("AWS::CloudFront::Distribution", 2)
        template.resource_count_is("AWS::S3::Bucket", 2)


if __name__ == "__main__":
    unittest.main()
