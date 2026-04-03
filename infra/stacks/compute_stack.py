"""Compute stack for baseline Lambda functions and execution roles."""

from pathlib import Path

from aws_cdk import Duration, RemovalPolicy, Stack
from aws_cdk import aws_dynamodb as dynamodb
from aws_cdk import aws_iam as iam
from aws_cdk import aws_kms as kms
from aws_cdk import aws_lambda as lambda_
from aws_cdk import aws_logs as logs
from aws_cdk import aws_s3 as s3
from aws_cdk import aws_secretsmanager as secretsmanager

from config.base import EnvironmentConfig
from constructs import Construct


class ComputeStack(Stack):
    """Provision reusable compute primitives for BFF and background processing."""

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        config: EnvironmentConfig,
        permissions_boundary: iam.IManagedPolicy,
        consultation_table: dynamodb.ITable,
        artifacts_bucket: s3.IBucket,
        data_key: kms.IKey,
        secrets_key: kms.IKey,
        elevenlabs_secret: secretsmanager.ISecret,
        claude_secret: secretsmanager.ISecret,
        user_pool_id: str,
        user_pool_client_id: str,
        user_pool_arn: str,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)
        self.config = config
        retain_logs = config.is_production
        self._shared_environment = {
            "DESKAI_ENV": self.config.environment,
            "DESKAI_RESOURCE_PREFIX": self.config.resource_prefix,
            "DESKAI_DYNAMODB_TABLE": consultation_table.table_name,
            "DESKAI_ARTIFACTS_BUCKET": artifacts_bucket.bucket_name,
            "DESKAI_ELEVENLABS_SECRET_NAME": config.elevenlabs_secret_name,
            "DESKAI_CLAUDE_SECRET_NAME": claude_secret.secret_name,
            "DESKAI_COGNITO_USER_POOL_ID": user_pool_id,
            "DESKAI_COGNITO_CLIENT_ID": user_pool_client_id,
            "DESKAI_WEBSOCKET_URL_PARAM": f"/{config.resource_prefix}/websocket-url",
            "DESKAI_COGNITO_CLIENT_SECRET_NAME": config.cognito_secret_name,
        }

        self.lambda_execution_role = iam.Role(
            self,
            "LambdaExecutionRole",
            role_name=f"{config.resource_prefix}-lambda-exec-role",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            permissions_boundary=permissions_boundary,
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AWSLambdaBasicExecutionRole"
                )
            ],
        )

        consultation_table.grant_read_write_data(self.lambda_execution_role)
        artifacts_bucket.grant_read_write(self.lambda_execution_role)

        self.lambda_execution_role.add_to_policy(
            iam.PolicyStatement(
                actions=["events:PutEvents"],
                resources=[
                    f"arn:aws:events:{self.region}:{self.account}:event-bus/{config.resource_prefix}-*"
                ],
            )
        )
        self.lambda_execution_role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    "kms:Encrypt",
                    "kms:Decrypt",
                    "kms:GenerateDataKey",
                    "kms:DescribeKey",
                ],
                resources=[data_key.key_arn],
            )
        )
        secrets_key.grant_decrypt(self.lambda_execution_role)
        self.lambda_execution_role.add_to_policy(
            iam.PolicyStatement(
                actions=["secretsmanager:GetSecretValue", "secretsmanager:DescribeSecret"],
                # Derive ARNs from config (single source of truth for secret names).
                # The -?????? suffix matches the 6-char random ID Secrets Manager
                # appends. No cross-stack exports — avoids CDK rename issues.
                resources=[
                    f"arn:aws:secretsmanager:{self.region}:{self.account}:secret:{config.elevenlabs_secret_name}-??????",
                    f"arn:aws:secretsmanager:{self.region}:{self.account}:secret:{config.claude_secret_name}-??????",
                ],
            )
        )
        self.lambda_execution_role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    "cognito-idp:InitiateAuth",
                    "cognito-idp:GlobalSignOut",
                    "cognito-idp:ForgotPassword",
                    "cognito-idp:ConfirmForgotPassword",
                ],
                resources=[user_pool_arn],
            )
        )
        self.lambda_execution_role.add_to_policy(
            iam.PolicyStatement(
                actions=["ssm:GetParameter"],
                resources=[
                    f"arn:aws:ssm:{self.region}:{self.account}:parameter/{config.resource_prefix}/websocket-url"
                ],
            )
        )
        self.lambda_execution_role.add_to_policy(
            iam.PolicyStatement(
                actions=["execute-api:ManageConnections"],
                resources=[
                    f"arn:aws:execute-api:{self.region}:{self.account}:*/*/@connections/*"
                ],
            )
        )

        asset_path = Path(__file__).resolve().parent.parent / ".build" / "lambda"

        self.bff_handler = self._create_function(
            function_id="BffHandler",
            function_name=f"{config.resource_prefix}-bff-handler",
            handler="bff.handler",
            asset_path=asset_path,
        )
        self.websocket_handler = self._create_function(
            function_id="WebsocketHandler",
            function_name=f"{config.resource_prefix}-ws-handler",
            handler="websocket.handler",
            asset_path=asset_path,
        )
        self.pipeline_handler = self._create_function(
            function_id="PipelineHandler",
            function_name=f"{config.resource_prefix}-pipeline-handler",
            handler="pipeline.handler",
            asset_path=asset_path,
        )
        self.export_handler = self._create_function(
            function_id="ExportHandler",
            function_name=f"{config.resource_prefix}-export-handler",
            handler="exporter.handler",
            asset_path=asset_path,
        )

        for function in [
            self.bff_handler,
            self.websocket_handler,
            self.pipeline_handler,
            self.export_handler,
        ]:
            logs.LogGroup(
                self,
                f"{function.node.id}LogGroup",
                log_group_name=f"/aws/lambda/{function.function_name}",
                retention=logs.RetentionDays.ONE_MONTH,
                removal_policy=RemovalPolicy.RETAIN if retain_logs else RemovalPolicy.DESTROY,
            )

    def _create_function(
        self,
        *,
        function_id: str,
        function_name: str,
        handler: str,
        asset_path: Path,
    ) -> lambda_.Function:
        return lambda_.Function(
            self,
            function_id,
            function_name=function_name,
            runtime=lambda_.Runtime.PYTHON_3_12,
            handler=handler,
            code=lambda_.Code.from_asset(str(asset_path)),
            role=self.lambda_execution_role,
            timeout=Duration.seconds(30),
            memory_size=256,
            environment=self._shared_environment,
        )
