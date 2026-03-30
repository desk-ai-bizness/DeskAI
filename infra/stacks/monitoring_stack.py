"""Monitoring stack for dashboards and operational alarms."""

from aws_cdk import Duration, Stack
from aws_cdk import aws_cloudwatch as cloudwatch
from aws_cdk import aws_cloudwatch_actions as cloudwatch_actions
from aws_cdk import aws_lambda as lambda_
from aws_cdk import aws_sns as sns
from aws_cdk import aws_sqs as sqs
from aws_cdk import aws_stepfunctions as sfn

from config.base import EnvironmentConfig
from constructs import Construct


class MonitoringStack(Stack):
    """Provision baseline metrics, alarms, and dashboards for MVP operations."""

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        config: EnvironmentConfig,
        alarm_topic: sns.ITopic,
        bff_handler: lambda_.IFunction,
        websocket_handler: lambda_.IFunction,
        pipeline_handler: lambda_.IFunction,
        http_api_id: str,
        websocket_api_id: str,
        consultation_workflow: sfn.IStateMachine,
        processing_dlq: sqs.IQueue,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)
        self.config = config

        sns_action = cloudwatch_actions.SnsAction(alarm_topic)

        lambda_error_alarm = cloudwatch.Alarm(
            self,
            "BffLambdaErrorsAlarm",
            alarm_name=f"{config.resource_prefix}-bff-errors",
            metric=bff_handler.metric_errors(period=Duration.minutes(5), statistic="sum"),
            threshold=1,
            evaluation_periods=1,
            datapoints_to_alarm=1,
            treat_missing_data=cloudwatch.TreatMissingData.NOT_BREACHING,
        )
        lambda_error_alarm.add_alarm_action(sns_action)

        websocket_error_alarm = cloudwatch.Alarm(
            self,
            "WebsocketLambdaErrorsAlarm",
            alarm_name=f"{config.resource_prefix}-ws-errors",
            metric=websocket_handler.metric_errors(period=Duration.minutes(5), statistic="sum"),
            threshold=1,
            evaluation_periods=1,
            datapoints_to_alarm=1,
            treat_missing_data=cloudwatch.TreatMissingData.NOT_BREACHING,
        )
        websocket_error_alarm.add_alarm_action(sns_action)

        pipeline_error_alarm = cloudwatch.Alarm(
            self,
            "PipelineLambdaErrorsAlarm",
            alarm_name=f"{config.resource_prefix}-pipeline-errors",
            metric=pipeline_handler.metric_errors(period=Duration.minutes(5), statistic="sum"),
            threshold=1,
            evaluation_periods=1,
            datapoints_to_alarm=1,
            treat_missing_data=cloudwatch.TreatMissingData.NOT_BREACHING,
        )
        pipeline_error_alarm.add_alarm_action(sns_action)

        api_5xx_metric = cloudwatch.Metric(
            namespace="AWS/ApiGateway",
            metric_name="5xx",
            dimensions_map={"ApiId": http_api_id, "Stage": config.environment},
            statistic="sum",
            period=Duration.minutes(5),
        )
        api_5xx_alarm = cloudwatch.Alarm(
            self,
            "HttpApi5xxAlarm",
            alarm_name=f"{config.resource_prefix}-http-5xx",
            metric=api_5xx_metric,
            threshold=1,
            evaluation_periods=1,
            datapoints_to_alarm=1,
            treat_missing_data=cloudwatch.TreatMissingData.NOT_BREACHING,
        )
        api_5xx_alarm.add_alarm_action(sns_action)

        state_machine_failed_alarm = cloudwatch.Alarm(
            self,
            "StateMachineFailedAlarm",
            alarm_name=f"{config.resource_prefix}-workflow-failures",
            metric=consultation_workflow.metric_failed(period=Duration.minutes(5), statistic="sum"),
            threshold=1,
            evaluation_periods=1,
            datapoints_to_alarm=1,
            treat_missing_data=cloudwatch.TreatMissingData.NOT_BREACHING,
        )
        state_machine_failed_alarm.add_alarm_action(sns_action)

        dlq_visible_alarm = cloudwatch.Alarm(
            self,
            "DlqVisibleAlarm",
            alarm_name=f"{config.resource_prefix}-processing-dlq-visible",
            metric=processing_dlq.metric_approximate_number_of_messages_visible(
                period=Duration.minutes(5),
                statistic="max",
            ),
            threshold=1,
            evaluation_periods=1,
            datapoints_to_alarm=1,
            treat_missing_data=cloudwatch.TreatMissingData.NOT_BREACHING,
        )
        dlq_visible_alarm.add_alarm_action(sns_action)

        websocket_disconnect_metric = cloudwatch.Metric(
            namespace="AWS/ApiGateway",
            metric_name="DisconnectCount",
            dimensions_map={"ApiId": websocket_api_id, "Stage": config.environment},
            statistic="sum",
            period=Duration.minutes(5),
        )

        dashboard = cloudwatch.Dashboard(
            self,
            "MvpDashboard",
            dashboard_name=f"{config.resource_prefix}-mvp-dashboard",
        )
        dashboard.add_widgets(
            cloudwatch.GraphWidget(
                title="Lambda Errors",
                left=[
                    bff_handler.metric_errors(period=Duration.minutes(5), statistic="sum"),
                    websocket_handler.metric_errors(period=Duration.minutes(5), statistic="sum"),
                    pipeline_handler.metric_errors(period=Duration.minutes(5), statistic="sum"),
                ],
            ),
            cloudwatch.GraphWidget(
                title="API and WebSocket Health",
                left=[api_5xx_metric, websocket_disconnect_metric],
            ),
            cloudwatch.GraphWidget(
                title="Workflow and Queue Health",
                left=[
                    consultation_workflow.metric_failed(
                        period=Duration.minutes(5),
                        statistic="sum",
                    ),
                    processing_dlq.metric_approximate_number_of_messages_visible(
                        period=Duration.minutes(5),
                        statistic="max",
                    ),
                ],
            ),
        )
