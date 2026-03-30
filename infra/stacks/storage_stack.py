"""Storage stack for DynamoDB and S3 artifacts."""

from aws_cdk import (
    Duration,
    RemovalPolicy,
    Stack,
)
from aws_cdk import (
    aws_dynamodb as dynamodb,
)
from aws_cdk import (
    aws_kms as kms,
)
from aws_cdk import (
    aws_s3 as s3,
)

from config.base import EnvironmentConfig
from constructs import Construct


class StorageStack(Stack):
    """Provision baseline storage resources for consultation data and artifacts."""

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        config: EnvironmentConfig,
        data_key: kms.IKey,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)
        self.config = config
        retain_data = config.is_production

        self.consultation_table = dynamodb.Table(
            self,
            "ConsultationRecordsTable",
            table_name=config.consultation_table_name,
            partition_key=dynamodb.Attribute(name="PK", type=dynamodb.AttributeType.STRING),
            sort_key=dynamodb.Attribute(name="SK", type=dynamodb.AttributeType.STRING),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            point_in_time_recovery_specification=dynamodb.PointInTimeRecoverySpecification(
                point_in_time_recovery_enabled=True
            ),
            removal_policy=RemovalPolicy.RETAIN if retain_data else RemovalPolicy.DESTROY,
            encryption=dynamodb.TableEncryption.CUSTOMER_MANAGED,
            encryption_key=data_key,
        )

        self.consultation_table.add_global_secondary_index(
            index_name="gsi_doctor_date",
            partition_key=dynamodb.Attribute(name="GSI1PK", type=dynamodb.AttributeType.STRING),
            sort_key=dynamodb.Attribute(name="GSI1SK", type=dynamodb.AttributeType.STRING),
            projection_type=dynamodb.ProjectionType.ALL,
        )
        self.consultation_table.add_global_secondary_index(
            index_name="gsi_status",
            partition_key=dynamodb.Attribute(name="GSI2PK", type=dynamodb.AttributeType.STRING),
            sort_key=dynamodb.Attribute(name="GSI2SK", type=dynamodb.AttributeType.STRING),
            projection_type=dynamodb.ProjectionType.ALL,
        )
        self.consultation_table.add_global_secondary_index(
            index_name="gsi_patient",
            partition_key=dynamodb.Attribute(name="GSI3PK", type=dynamodb.AttributeType.STRING),
            sort_key=dynamodb.Attribute(name="GSI3SK", type=dynamodb.AttributeType.STRING),
            projection_type=dynamodb.ProjectionType.ALL,
        )

        self.artifacts_bucket = s3.Bucket(
            self,
            "ArtifactsBucket",
            bucket_name=config.artifacts_bucket_name,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            encryption=s3.BucketEncryption.KMS,
            encryption_key=data_key,
            enforce_ssl=True,
            versioned=True,
            removal_policy=RemovalPolicy.RETAIN if retain_data else RemovalPolicy.DESTROY,
            auto_delete_objects=not retain_data,
            object_ownership=s3.ObjectOwnership.BUCKET_OWNER_ENFORCED,
            lifecycle_rules=[
                s3.LifecycleRule(
                    id="AudioRetentionFreeTrial",
                    enabled=True,
                    prefix="clinics/",
                    tag_filters={"audio_retention": "7"},
                    expiration=Duration.days(7),
                ),
                s3.LifecycleRule(
                    id="AudioRetentionPlus",
                    enabled=True,
                    prefix="clinics/",
                    tag_filters={"audio_retention": "30"},
                    expiration=Duration.days(30),
                ),
                s3.LifecycleRule(
                    id="AudioRetentionPro",
                    enabled=True,
                    prefix="clinics/",
                    tag_filters={"audio_retention": "90"},
                    expiration=Duration.days(90),
                ),
            ],
        )
