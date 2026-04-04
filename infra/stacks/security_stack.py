"""Security stack for encryption, secrets, and IAM guardrails."""

from aws_cdk import Stack
from aws_cdk import aws_iam as iam
from aws_cdk import aws_kms as kms
from aws_cdk import aws_secretsmanager as secretsmanager

from config.base import EnvironmentConfig
from constructs import Construct


class SecurityStack(Stack):
    """Provision baseline security controls shared by the infrastructure."""

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        config: EnvironmentConfig,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)
        self.config = config

        self.data_key = kms.Key(
            self,
            "DataKey",
            alias=f"alias/{config.resource_prefix}/data",
            enable_key_rotation=True,
            description="Encrypts consultation metadata and artifacts at rest.",
        )

        self.secrets_key = kms.Key(
            self,
            "SecretsKey",
            alias=f"alias/{config.resource_prefix}/secrets",
            enable_key_rotation=True,
            description="Encrypts provider credentials in Secrets Manager.",
        )

        self.permissions_boundary = iam.ManagedPolicy(
            self,
            "LambdaPermissionsBoundary",
            managed_policy_name=f"{config.resource_prefix}-lambda-permissions-boundary",
            statements=[
                iam.PolicyStatement(
                    sid="AllowLogDelivery",
                    actions=["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents"],
                    resources=[
                        f"arn:aws:logs:{self.region}:{self.account}:log-group:/aws/lambda/{config.resource_prefix}-*",
                        f"arn:aws:logs:{self.region}:{self.account}:log-group:/aws/lambda/{config.resource_prefix}-*:log-stream:*",
                    ],
                ),
                iam.PolicyStatement(
                    sid="AllowXRayTelemetry",
                    actions=["xray:PutTraceSegments", "xray:PutTelemetryRecords"],
                    resources=["*"],
                ),
                iam.PolicyStatement(
                    sid="AllowPrefixedDataAccess",
                    actions=[
                        "dynamodb:GetItem",
                        "dynamodb:PutItem",
                        "dynamodb:UpdateItem",
                        "dynamodb:DeleteItem",
                        "dynamodb:Query",
                        "dynamodb:BatchWriteItem",
                        "dynamodb:BatchGetItem",
                        "s3:GetObject",
                        "s3:PutObject",
                        "s3:DeleteObject",
                        "s3:ListBucket",
                        "sqs:SendMessage",
                        "sqs:ReceiveMessage",
                        "sqs:DeleteMessage",
                        "sqs:GetQueueAttributes",
                        "sqs:ChangeMessageVisibility",
                        "sns:Publish",
                        "events:PutEvents",
                        "states:StartExecution",
                        "states:SendTaskSuccess",
                        "states:SendTaskFailure",
                        "states:DescribeExecution",
                    ],
                    resources=[
                        f"arn:aws:dynamodb:{self.region}:{self.account}:table/{config.resource_prefix}-*",
                        f"arn:aws:s3:::{config.resource_prefix}-*",
                        f"arn:aws:s3:::{config.resource_prefix}-*/*",
                        f"arn:aws:sqs:{self.region}:{self.account}:{config.resource_prefix}-*",
                        f"arn:aws:sns:{self.region}:{self.account}:{config.resource_prefix}-*",
                        f"arn:aws:events:{self.region}:{self.account}:event-bus/{config.resource_prefix}-*",
                        f"arn:aws:states:{self.region}:{self.account}:stateMachine:{config.resource_prefix}-*",
                        f"arn:aws:states:{self.region}:{self.account}:execution:{config.resource_prefix}-*:*",
                    ],
                ),
                iam.PolicyStatement(
                    sid="AllowSecretReads",
                    actions=["secretsmanager:GetSecretValue", "secretsmanager:DescribeSecret"],
                    resources=[
                        f"arn:aws:secretsmanager:{self.region}:{self.account}:secret:deskai/{config.environment}/*"
                    ],
                ),
                iam.PolicyStatement(
                    sid="AllowKmsUsage",
                    actions=[
                        "kms:Encrypt",
                        "kms:Decrypt",
                        "kms:GenerateDataKey",
                        "kms:DescribeKey",
                    ],
                    resources=[self.data_key.key_arn, self.secrets_key.key_arn],
                ),
                iam.PolicyStatement(
                    sid="AllowCognitoAuth",
                    actions=[
                        "cognito-idp:InitiateAuth",
                        "cognito-idp:GlobalSignOut",
                        "cognito-idp:ForgotPassword",
                        "cognito-idp:ConfirmForgotPassword",
                    ],
                    resources=[
                        f"arn:aws:cognito-idp:{self.region}:{self.account}:userpool/{config.resource_prefix}-*"
                    ],
                ),
                iam.PolicyStatement(
                    sid="AllowWebSocketManageConnections",
                    actions=["execute-api:ManageConnections"],
                    resources=[
                        f"arn:aws:execute-api:{self.region}:{self.account}:*/*/@connections/*"
                    ],
                ),
                iam.PolicyStatement(
                    sid="AllowSSMParameterRead",
                    actions=["ssm:GetParameter"],
                    resources=[
                        f"arn:aws:ssm:{self.region}:{self.account}:parameter/{config.resource_prefix}/*"
                    ],
                ),
            ],
        )

        self.elevenlabs_secret = secretsmanager.Secret(
            self,
            "ElevenLabsSecret",
            secret_name=config.elevenlabs_secret_name,
            encryption_key=self.secrets_key,
            description="ElevenLabs Scribe v2 API credentials for transcription.",
            generate_secret_string=secretsmanager.SecretStringGenerator(
                secret_string_template='{"api_key": ""}',
                generate_string_key="placeholder",
                exclude_punctuation=True,
            ),
        )

        self.claude_secret = secretsmanager.Secret(
            self,
            "ClaudeSecret",
            secret_name=config.claude_secret_name,
            encryption_key=self.secrets_key,
            description="Claude API credentials placeholder for MVP bootstrap.",
            generate_secret_string=secretsmanager.SecretStringGenerator(
                secret_string_template='{"api_key": ""}',
                generate_string_key="placeholder",
                exclude_punctuation=True,
            ),
        )
