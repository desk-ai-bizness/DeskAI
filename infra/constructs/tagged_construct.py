"""Shared construct helpers for standard stack tagging."""

from aws_cdk import Tags

from constructs import Construct


class TaggedConstruct(Construct):
    """Base construct that applies baseline tags to child resources."""

    def __init__(self, scope: Construct, construct_id: str, environment: str) -> None:
        super().__init__(scope, construct_id)
        Tags.of(self).add("project", "deskai")
        Tags.of(self).add("environment", environment)
