"""Compute stack scaffold."""

from aws_cdk import Stack

from config.base import EnvironmentConfig
from constructs import Construct


class ComputeStack(Stack):
    """Stack scaffold to be implemented in infrastructure tasks."""

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
