"""Compute stack for per-Lambda functions with least-privilege IAM roles."""

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
    """Provision per-Lambda compute primitives with least-privilege IAM roles."""

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
            "DESKAI_EVENT_BUS_NAME": f"{config.resource_prefix}-event-bus",
        }

        secrets_arns = [
            f"arn:aws:secretsmanager:{self.region}:{self.account}:secret:{config.elevenlabs_secret_name}-??????",
            f"arn:aws:secretsmanager:{self.region}:{self.account}:secret:{config.claude_secret_name}-??????",
        ]
        ssm_websocket_arn = (
            f"arn:aws:ssm:{self.region}:{self.account}"
            f":parameter/{config.resource_prefix}/websocket-url"
        )

        # --- BFF role: full DynamoDB + S3, secrets, Cognito, SSM, KMS ---
        # NOTE: We use manual IAM policies (not secret.grant_read) to avoid
        # cross-stack dependency cycles.  grant_read adds a resource policy
        # on the secret (SecurityStack) referencing the role ARN (ComputeStack),
        # creating SecurityStack -> ComputeStack -> SecurityStack cycle.
        self.bff_role = self._create_role(
            "BffRole", f"{config.resource_prefix}-bff-role", permissions_boundary
        )
        consultation_table.grant_read_write_data(self.bff_role)
        artifacts_bucket.grant_read_write(self.bff_role)
        secrets_key.grant_decrypt(self.bff_role)
        self.bff_role.add_to_policy(
            iam.PolicyStatement(
                actions=["kms:Encrypt", "kms:Decrypt", "kms:GenerateDataKey", "kms:DescribeKey"],
                resources=[data_key.key_arn],
            )
        )
        self.bff_role.add_to_policy(
            iam.PolicyStatement(
                actions=["secretsmanager:GetSecretValue", "secretsmanager:DescribeSecret"],
                resources=secrets_arns,
            )
        )
        self.bff_role.add_to_policy(
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
        self.bff_role.add_to_policy(
            iam.PolicyStatement(actions=["ssm:GetParameter"], resources=[ssm_websocket_arn])
        )
        self.bff_role.add_to_policy(
            iam.PolicyStatement(
                actions=["events:PutEvents"],
                resources=[
                    f"arn:aws:events:{self.region}:{self.account}:event-bus/{config.resource_prefix}-*"
                ],
            )
        )

        # --- WebSocket role: DynamoDB r/w, ManageConnections, KMS, SSM ---
        self.websocket_role = self._create_role(
            "WebsocketRole", f"{config.resource_prefix}-ws-role", permissions_boundary
        )
        consultation_table.grant_read_write_data(self.websocket_role)
        self.websocket_role.add_to_policy(
            iam.PolicyStatement(
                actions=["kms:Encrypt", "kms:Decrypt", "kms:GenerateDataKey", "kms:DescribeKey"],
                resources=[data_key.key_arn],
            )
        )
        self.websocket_role.add_to_policy(
            iam.PolicyStatement(
                actions=["execute-api:ManageConnections"],
                resources=[f"arn:aws:execute-api:{self.region}:{self.account}:*/*/@connections/*"],
            )
        )
        self.websocket_role.add_to_policy(
            iam.PolicyStatement(actions=["ssm:GetParameter"], resources=[ssm_websocket_arn])
        )
        artifacts_bucket.grant_read_write(self.websocket_role)
        secrets_key.grant_decrypt(self.websocket_role)
        self.websocket_role.add_to_policy(
            iam.PolicyStatement(
                actions=["secretsmanager:GetSecretValue", "secretsmanager:DescribeSecret"],
                resources=secrets_arns,
            )
        )
        self.websocket_role.add_to_policy(
            iam.PolicyStatement(
                actions=["events:PutEvents"],
                resources=[
                    f"arn:aws:events:{self.region}:{self.account}:event-bus/{config.resource_prefix}-*"
                ],
            )
        )

        # --- Pipeline role: DynamoDB r/w, S3 r/w, secrets, events, KMS ---
        self.pipeline_role = self._create_role(
            "PipelineRole", f"{config.resource_prefix}-pipeline-role", permissions_boundary
        )
        consultation_table.grant_read_write_data(self.pipeline_role)
        artifacts_bucket.grant_read_write(self.pipeline_role)
        secrets_key.grant_decrypt(self.pipeline_role)
        self.pipeline_role.add_to_policy(
            iam.PolicyStatement(
                actions=["kms:Encrypt", "kms:Decrypt", "kms:GenerateDataKey", "kms:DescribeKey"],
                resources=[data_key.key_arn],
            )
        )
        self.pipeline_role.add_to_policy(
            iam.PolicyStatement(
                actions=["secretsmanager:GetSecretValue", "secretsmanager:DescribeSecret"],
                resources=secrets_arns,
            )
        )
        self.pipeline_role.add_to_policy(
            iam.PolicyStatement(
                actions=["events:PutEvents"],
                resources=[
                    f"arn:aws:events:{self.region}:{self.account}:event-bus/{config.resource_prefix}-*"
                ],
            )
        )

        # --- Export role: DynamoDB read-only, S3 read-only, KMS decrypt ---
        self.export_role = self._create_role(
            "ExportRole", f"{config.resource_prefix}-export-role", permissions_boundary
        )
        consultation_table.grant_read_data(self.export_role)
        artifacts_bucket.grant_read(self.export_role)
        self.export_role.add_to_policy(
            iam.PolicyStatement(
                actions=["kms:Decrypt", "kms:DescribeKey"],
                resources=[data_key.key_arn],
            )
        )

        asset_path = Path(__file__).resolve().parent.parent / ".build" / "lambda"

        # Reserved concurrency is only set in production where the account
        # has enough quota.  Dev accounts often have just 10 total concurrent
        # executions, so reserving any would breach the minimum-unreserved limit.
        bff_concurrency = 50 if config.is_production else None
        ws_concurrency = 50 if config.is_production else None
        pipeline_concurrency = 10 if config.is_production else None
        export_concurrency = 5 if config.is_production else None

        self.bff_handler = self._create_function(
            function_id="BffHandler",
            function_name=f"{config.resource_prefix}-bff-handler",
            handler="bff.handler",
            asset_path=asset_path,
            role=self.bff_role,
            reserved_concurrent_executions=bff_concurrency,
        )
        self.websocket_handler = self._create_function(
            function_id="WebsocketHandler",
            function_name=f"{config.resource_prefix}-ws-handler",
            handler="websocket.handler",
            asset_path=asset_path,
            role=self.websocket_role,
            reserved_concurrent_executions=ws_concurrency,
        )
        self.pipeline_handler = self._create_function(
            function_id="PipelineHandler",
            function_name=f"{config.resource_prefix}-pipeline-handler",
            handler="pipeline.handler",
            asset_path=asset_path,
            role=self.pipeline_role,
            reserved_concurrent_executions=pipeline_concurrency,
        )
        self.export_handler = self._create_function(
            function_id="ExportHandler",
            function_name=f"{config.resource_prefix}-export-handler",
            handler="exporter.handler",
            asset_path=asset_path,
            role=self.export_role,
            reserved_concurrent_executions=export_concurrency,
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

    def _create_role(
        self,
        role_id: str,
        role_name: str,
        permissions_boundary: iam.IManagedPolicy,
    ) -> iam.Role:
        return iam.Role(
            self,
            role_id,
            role_name=role_name,
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            permissions_boundary=permissions_boundary,
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AWSLambdaBasicExecutionRole"
                )
            ],
        )

    def _create_function(
        self,
        *,
        function_id: str,
        function_name: str,
        handler: str,
        asset_path: Path,
        role: iam.IRole,
        reserved_concurrent_executions: int | None,
    ) -> lambda_.Function:
        return lambda_.Function(
            self,
            function_id,
            function_name=function_name,
            runtime=lambda_.Runtime.PYTHON_3_12,
            handler=handler,
            code=lambda_.Code.from_asset(str(asset_path)),
            role=role,
            timeout=Duration.seconds(30),
            memory_size=256,
            environment=self._shared_environment,
            reserved_concurrent_executions=reserved_concurrent_executions,
        )
