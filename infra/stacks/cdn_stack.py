"""CDN stack for public website and authenticated app delivery."""

from aws_cdk import RemovalPolicy, Stack
from aws_cdk import aws_cloudfront as cloudfront
from aws_cdk import aws_s3 as s3
from aws_cdk.aws_cloudfront_origins import S3BucketOrigin

from config.base import EnvironmentConfig
from constructs import Construct


class CdnStack(Stack):
    """Provision static asset buckets and CloudFront distributions."""

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

        retain_assets = config.is_production
        self.website_bucket = s3.Bucket(
            self,
            "WebsiteBucket",
            bucket_name=config.website_bucket_name,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            encryption=s3.BucketEncryption.S3_MANAGED,
            enforce_ssl=True,
            versioned=True,
            removal_policy=RemovalPolicy.RETAIN if retain_assets else RemovalPolicy.DESTROY,
            auto_delete_objects=not retain_assets,
            object_ownership=s3.ObjectOwnership.BUCKET_OWNER_ENFORCED,
        )
        self.app_bucket = s3.Bucket(
            self,
            "AppBucket",
            bucket_name=config.app_bucket_name,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            encryption=s3.BucketEncryption.S3_MANAGED,
            enforce_ssl=True,
            versioned=True,
            removal_policy=RemovalPolicy.RETAIN if retain_assets else RemovalPolicy.DESTROY,
            auto_delete_objects=not retain_assets,
            object_ownership=s3.ObjectOwnership.BUCKET_OWNER_ENFORCED,
        )

        website_oai = cloudfront.OriginAccessIdentity(
            self,
            "WebsiteOai",
            comment=f"{config.resource_prefix} website distribution origin access identity",
        )
        app_oai = cloudfront.OriginAccessIdentity(
            self,
            "AppOai",
            comment=f"{config.resource_prefix} app distribution origin access identity",
        )

        self.website_bucket.grant_read(website_oai)
        self.app_bucket.grant_read(app_oai)

        self.website_distribution = cloudfront.Distribution(
            self,
            "WebsiteDistribution",
            comment=f"{config.resource_prefix} public website distribution",
            default_root_object="index.html",
            default_behavior=cloudfront.BehaviorOptions(
                origin=S3BucketOrigin.with_origin_access_identity(
                    self.website_bucket,
                    origin_access_identity=website_oai,
                ),
                viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
                cache_policy=cloudfront.CachePolicy.CACHING_OPTIMIZED,
                response_headers_policy=cloudfront.ResponseHeadersPolicy.SECURITY_HEADERS,
            ),
            minimum_protocol_version=cloudfront.SecurityPolicyProtocol.TLS_V1_2_2021,
            price_class=cloudfront.PriceClass.PRICE_CLASS_100,
        )
        self.app_distribution = cloudfront.Distribution(
            self,
            "AppDistribution",
            comment=f"{config.resource_prefix} authenticated app distribution",
            default_root_object="index.html",
            default_behavior=cloudfront.BehaviorOptions(
                origin=S3BucketOrigin.with_origin_access_identity(
                    self.app_bucket,
                    origin_access_identity=app_oai,
                ),
                viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
                cache_policy=cloudfront.CachePolicy.CACHING_OPTIMIZED,
                response_headers_policy=cloudfront.ResponseHeadersPolicy.SECURITY_HEADERS,
            ),
            minimum_protocol_version=cloudfront.SecurityPolicyProtocol.TLS_V1_2_2021,
            price_class=cloudfront.PriceClass.PRICE_CLASS_100,
        )
