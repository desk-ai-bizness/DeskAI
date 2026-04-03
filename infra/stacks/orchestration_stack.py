"""Orchestration stack for workflow and asynchronous primitives."""

from aws_cdk import Duration, Stack
from aws_cdk import aws_events as events
from aws_cdk import aws_events_targets as events_targets
from aws_cdk import aws_iam as iam
from aws_cdk import aws_kms as kms
from aws_cdk import aws_lambda as lambda_
from aws_cdk import aws_sns as sns
from aws_cdk import aws_sns_subscriptions as sns_subs
from aws_cdk import aws_sqs as sqs
from aws_cdk import aws_stepfunctions as sfn
from aws_cdk import aws_stepfunctions_tasks as sfn_tasks

from config.base import EnvironmentConfig
from constructs import Construct


class OrchestrationStack(Stack):
    """Provision Step Functions, EventBridge, SQS, and SNS baseline resources."""

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        config: EnvironmentConfig,
        permissions_boundary: iam.IManagedPolicy,
        data_key: kms.IKey,
        pipeline_handler: lambda_.IFunction,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)
        self.config = config

        self.processing_dlq = sqs.Queue(
            self,
            "ProcessingDlq",
            queue_name=f"{config.resource_prefix}-processing-dlq",
            retention_period=Duration.days(14),
            encryption=sqs.QueueEncryption.KMS,
            encryption_master_key=data_key,
        )

        self.processing_queue = sqs.Queue(
            self,
            "ProcessingQueue",
            queue_name=f"{config.resource_prefix}-processing-queue",
            visibility_timeout=Duration.minutes(5),
            encryption=sqs.QueueEncryption.KMS,
            encryption_master_key=data_key,
            dead_letter_queue=sqs.DeadLetterQueue(
                max_receive_count=3,
                queue=self.processing_dlq,
            ),
        )

        self.alerts_topic = sns.Topic(
            self,
            "OperationalAlertsTopic",
            topic_name=f"{config.resource_prefix}-alerts",
            master_key=data_key,
        )

        if config.alert_email:
            self.alerts_topic.add_subscription(
                sns_subs.EmailSubscription(config.alert_email)
            )

        self.event_bus = events.EventBus(
            self,
            "DomainEventBus",
            event_bus_name=f"{config.resource_prefix}-event-bus",
        )

        self.state_machine_role = iam.Role(
            self,
            "StateMachineRole",
            role_name=f"{config.resource_prefix}-workflow-role",
            assumed_by=iam.ServicePrincipal("states.amazonaws.com"),
            permissions_boundary=permissions_boundary,
        )

        pipeline_handler.grant_invoke(self.state_machine_role)
        self.processing_dlq.grant_send_messages(self.state_machine_role)

        process_consultation = sfn_tasks.LambdaInvoke(
            self,
            "ProcessConsultation",
            lambda_function=pipeline_handler,
            output_path="$.Payload",
        )
        process_consultation.add_retry(
            max_attempts=3,
            interval=Duration.seconds(2),
            backoff_rate=2.0,
        )

        send_to_dlq = sfn_tasks.SqsSendMessage(
            self,
            "SendFailedExecutionToDlq",
            queue=self.processing_dlq,
            message_body=sfn.TaskInput.from_json_path_at("$"),
        )

        fail_state = sfn.Fail(self, "ProcessingFailed")
        process_consultation.add_catch(send_to_dlq.next(fail_state), result_path="$.error")

        definition = process_consultation.next(sfn.Succeed(self, "ProcessingSucceeded"))

        self.consultation_workflow = sfn.StateMachine(
            self,
            "ConsultationWorkflow",
            state_machine_name=f"{config.resource_prefix}-consultation-workflow",
            definition_body=sfn.DefinitionBody.from_chainable(definition),
            role=self.state_machine_role,
            timeout=Duration.minutes(15),
            tracing_enabled=True,
        )

        self.consultation_completed_rule = events.Rule(
            self,
            "ConsultationCompletedRule",
            event_bus=self.event_bus,
            event_pattern=events.EventPattern(
                source=["deskai.consultation"],
                detail_type=["consultation.session.ended"],
            ),
            targets=[
                events_targets.SfnStateMachine(
                    machine=self.consultation_workflow,
                    dead_letter_queue=self.processing_dlq,
                )
            ],
        )
