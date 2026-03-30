"""Budget stack for monthly cost guardrails."""

from aws_cdk import Stack
from aws_cdk import aws_budgets as budgets
from aws_cdk import aws_sns as sns

from config.base import EnvironmentConfig
from constructs import Construct


class BudgetStack(Stack):
    """Provision a monthly budget alert routed through SNS."""

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        config: EnvironmentConfig,
        budget_alert_topic: sns.ITopic,
        shared_account_mode: bool,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)
        self.config = config
        self.shared_account_mode = shared_account_mode

        should_create_account_budget = not shared_account_mode or config.is_production
        if should_create_account_budget:
            self._create_budget(
                budget_id="MonthlyCostBudget",
                budget_name=f"{config.resource_prefix}-monthly-cost-account",
                budget_alert_topic=budget_alert_topic,
            )

        self._create_budget(
            budget_id="EnvironmentScopedMonthlyCostBudget",
            budget_name=f"{config.resource_prefix}-monthly-cost-env",
            budget_alert_topic=budget_alert_topic,
            filter_expression=budgets.CfnBudget.ExpressionProperty(
                tags=budgets.CfnBudget.TagValuesProperty(
                    key="environment",
                    match_options=["EQUALS"],
                    values=[config.environment],
                )
            ),
        )

    def _create_budget(
        self,
        *,
        budget_id: str,
        budget_name: str,
        budget_alert_topic: sns.ITopic,
        filter_expression: budgets.CfnBudget.ExpressionProperty | None = None,
    ) -> None:
        budget_payload = budgets.CfnBudget.BudgetDataProperty(
            budget_type="COST",
            budget_name=budget_name,
            time_unit="MONTHLY",
            budget_limit=budgets.CfnBudget.SpendProperty(
                amount=self.config.monthly_budget_limit_usd,
                unit="USD",
            ),
            cost_types=budgets.CfnBudget.CostTypesProperty(
                include_credit=True,
                include_discount=True,
                include_other_subscription=True,
                include_recurring=True,
                include_refund=False,
                include_subscription=True,
                include_support=True,
                include_tax=True,
                include_upfront=True,
                use_amortized=False,
                use_blended=False,
            ),
            filter_expression=filter_expression,
        )
        budgets.CfnBudget(
            self,
            budget_id,
            budget=budget_payload,
            notifications_with_subscribers=[
                budgets.CfnBudget.NotificationWithSubscribersProperty(
                    notification=budgets.CfnBudget.NotificationProperty(
                        comparison_operator="GREATER_THAN",
                        notification_type="ACTUAL",
                        threshold=float(self.config.monthly_budget_limit_usd),
                        threshold_type="ABSOLUTE_VALUE",
                    ),
                    subscribers=[
                        budgets.CfnBudget.SubscriberProperty(
                            address=budget_alert_topic.topic_arn,
                            subscription_type="SNS",
                        )
                    ],
                ),
                budgets.CfnBudget.NotificationWithSubscribersProperty(
                    notification=budgets.CfnBudget.NotificationProperty(
                        comparison_operator="GREATER_THAN",
                        notification_type="FORECASTED",
                        threshold=float(self.config.monthly_budget_limit_usd),
                        threshold_type="ABSOLUTE_VALUE",
                    ),
                    subscribers=[
                        budgets.CfnBudget.SubscriberProperty(
                            address=budget_alert_topic.topic_arn,
                            subscription_type="SNS",
                        )
                    ],
                ),
            ],
        )
