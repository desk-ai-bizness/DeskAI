"""API stack for HTTP and WebSocket ingress layers."""

from aws_cdk import Duration, Stack
from aws_cdk import aws_apigatewayv2 as apigwv2
from aws_cdk import aws_cognito as cognito
from aws_cdk import aws_iam as iam
from aws_cdk import aws_logs as logs
from aws_cdk.aws_apigatewayv2_authorizers import HttpUserPoolAuthorizer
from aws_cdk.aws_apigatewayv2_integrations import HttpLambdaIntegration, WebSocketLambdaIntegration
from aws_cdk.aws_lambda import IFunction

from config.base import EnvironmentConfig
from constructs import Construct


class ApiStack(Stack):
    """Provision HTTP and WebSocket APIs with explicit CORS and auth defaults."""

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        config: EnvironmentConfig,
        user_pool: cognito.IUserPool,
        user_pool_client: cognito.IUserPoolClient,
        bff_handler: IFunction,
        websocket_handler: IFunction,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)
        self.config = config

        self.http_api = apigwv2.HttpApi(
            self,
            "HttpApi",
            api_name=config.http_api_name,
            create_default_stage=False,
            cors_preflight=apigwv2.CorsPreflightOptions(
                allow_origins=list(config.allowed_cors_origins),
                allow_methods=[
                    apigwv2.CorsHttpMethod.GET,
                    apigwv2.CorsHttpMethod.POST,
                    apigwv2.CorsHttpMethod.PUT,
                    apigwv2.CorsHttpMethod.PATCH,
                    apigwv2.CorsHttpMethod.DELETE,
                    apigwv2.CorsHttpMethod.OPTIONS,
                ],
                allow_headers=["Authorization", "Content-Type", "X-Request-Id"],
                expose_headers=["X-Request-Id"],
                allow_credentials=True,
                max_age=Duration.hours(1),
            ),
        )

        bff_integration = HttpLambdaIntegration("BffProxyIntegration", handler=bff_handler)
        authorizer = HttpUserPoolAuthorizer(
            "UserPoolAuthorizer",
            user_pool,
            user_pool_clients=[user_pool_client],
        )

        self.http_api.add_routes(
            path="/health",
            methods=[apigwv2.HttpMethod.GET],
            integration=bff_integration,
        )

        # Auth endpoints are unauthenticated — explicit routes take precedence
        # over the /v1/{proxy+} catch-all in API Gateway v2.
        for auth_path in [
            "/v1/auth/session",
            "/v1/auth/forgot-password",
            "/v1/auth/confirm-forgot-password",
        ]:
            self.http_api.add_routes(
                path=auth_path,
                methods=[apigwv2.HttpMethod.POST],
                integration=bff_integration,
            )
        self.http_api.add_routes(
            path="/v1/auth/session",
            methods=[apigwv2.HttpMethod.DELETE],
            integration=bff_integration,
        )

        self.http_api.add_routes(
            path="/v1/{proxy+}",
            methods=[apigwv2.HttpMethod.ANY],
            integration=bff_integration,
            authorizer=authorizer,
        )

        self.http_access_logs = logs.LogGroup(
            self,
            "HttpApiAccessLogs",
            log_group_name=f"/aws/apigateway/{config.http_api_name}",
            retention=logs.RetentionDays.ONE_MONTH,
        )
        self.http_access_logs.add_to_resource_policy(
            iam.PolicyStatement(
                actions=["logs:CreateLogStream", "logs:PutLogEvents"],
                principals=[iam.ServicePrincipal("apigateway.amazonaws.com")],
                resources=[f"{self.http_access_logs.log_group_arn}:*"],
            )
        )

        self.http_stage = apigwv2.CfnStage(
            self,
            "HttpStage",
            api_id=self.http_api.api_id,
            stage_name=config.environment,
            auto_deploy=True,
            access_log_settings=apigwv2.CfnStage.AccessLogSettingsProperty(
                destination_arn=self.http_access_logs.log_group_arn,
                format='{"requestId":"$context.requestId","status":"$context.status","path":"$context.path"}',
            ),
            default_route_settings=apigwv2.CfnStage.RouteSettingsProperty(
                throttling_burst_limit=100,
                throttling_rate_limit=200.0,
                detailed_metrics_enabled=True,
            ),
        )

        websocket_integration = WebSocketLambdaIntegration(
            "WebSocketLambdaIntegration",
            handler=websocket_handler,
        )
        self.websocket_api = apigwv2.WebSocketApi(
            self,
            "WebSocketApi",
            api_name=config.websocket_api_name,
            connect_route_options=apigwv2.WebSocketRouteOptions(integration=websocket_integration),
            disconnect_route_options=apigwv2.WebSocketRouteOptions(
                integration=websocket_integration
            ),
            default_route_options=apigwv2.WebSocketRouteOptions(integration=websocket_integration),
        )
        self.websocket_api.add_route(
            route_key="session.init",
            integration=websocket_integration,
        )
        self.websocket_api.add_route(
            route_key="audio.chunk",
            integration=websocket_integration,
        )
        self.websocket_api.add_route(
            route_key="session.stop",
            integration=websocket_integration,
        )
        self.websocket_api.add_route(
            route_key="client.ping",
            integration=websocket_integration,
        )

        self.websocket_stage = apigwv2.WebSocketStage(
            self,
            "WebSocketStage",
            web_socket_api=self.websocket_api,
            stage_name=config.environment,
            auto_deploy=True,
        )
