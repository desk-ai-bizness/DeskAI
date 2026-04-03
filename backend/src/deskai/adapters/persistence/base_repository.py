"""DynamoDB base repository with error handling, retries, and pagination."""

import time
from typing import Any

import boto3
from botocore.exceptions import ClientError, EndpointConnectionError, ReadTimeoutError

from deskai.shared.errors import (
    ConflictError,
    ConnectionError,
    RepositoryError,
    ThrottleError,
)
from deskai.shared.logging import get_logger

logger = get_logger()

_MAX_RETRIES = 3
_BASE_BACKOFF_SECONDS = 0.1

_THROTTLE_CODES = frozenset(
    {
        "ProvisionedThroughputExceededException",
        "ThrottlingException",
        "RequestLimitExceeded",
    }
)


class DynamoDBBaseRepository:
    """Centralised DynamoDB access with error mapping, retry, and pagination."""

    def __init__(self, table_name: str) -> None:
        self._table_name = table_name
        dynamodb = boto3.resource("dynamodb")
        self._table = dynamodb.Table(table_name)

    # --- safe wrappers ---

    def _safe_put_item(self, **kwargs: Any) -> dict:
        return self._execute("put_item", **kwargs)

    def _safe_get_item(self, **kwargs: Any) -> dict:
        return self._execute("get_item", **kwargs)

    def _safe_delete_item(self, **kwargs: Any) -> dict:
        return self._execute("delete_item", **kwargs)

    def _safe_update_item(self, **kwargs: Any) -> dict:
        return self._execute("update_item", **kwargs)

    def _safe_query(self, **kwargs: Any) -> dict:
        return self._execute("query", **kwargs)

    # --- pagination ---

    def _paginated_query(self, **kwargs: Any) -> list[dict]:
        """Auto-paginate a DynamoDB query, following LastEvaluatedKey."""
        all_items: list[dict] = []
        while True:
            response = self._safe_query(**kwargs)
            all_items.extend(response.get("Items", []))
            last_key = response.get("LastEvaluatedKey")
            if not last_key:
                break
            kwargs["ExclusiveStartKey"] = last_key
        return all_items

    # --- condition expression helper ---

    @staticmethod
    def _build_condition_expression(
        attribute: str, expected_value: Any
    ) -> dict[str, Any]:
        """Build a ConditionExpression dict for optimistic concurrency."""
        return {
            "ConditionExpression": "#cond_attr = :cond_val",
            "ExpressionAttributeNames": {"#cond_attr": attribute},
            "ExpressionAttributeValues": {":cond_val": expected_value},
        }

    # --- core execution with retry + error mapping ---

    def _execute(self, operation: str, **kwargs: Any) -> dict:
        method = getattr(self._table, operation)
        last_error: Exception | None = None

        for attempt in range(_MAX_RETRIES):
            try:
                return method(**kwargs)
            except ClientError as exc:
                last_error = exc
                code = exc.response["Error"]["Code"]

                if code == "ConditionalCheckFailedException":
                    raise ConflictError(
                        f"Conditional check failed on {operation}"
                    ) from exc

                if code == "ValidationException":
                    raise RepositoryError(
                        f"DynamoDB validation error on {operation}: "
                        f"{exc.response['Error']['Message']}"
                    ) from exc

                if code in _THROTTLE_CODES:
                    delay = _BASE_BACKOFF_SECONDS * (2**attempt)
                    logger.warning(
                        "DynamoDB throttle on %s (attempt %d/%d), "
                        "retrying in %.2fs",
                        operation,
                        attempt + 1,
                        _MAX_RETRIES,
                        delay,
                    )
                    time.sleep(delay)
                    continue

                raise RepositoryError(
                    f"DynamoDB error on {operation}: {code}"
                ) from exc

            except EndpointConnectionError as exc:
                raise ConnectionError(
                    f"Cannot reach DynamoDB for {operation}"
                ) from exc

            except ReadTimeoutError as exc:
                raise ConnectionError(
                    f"DynamoDB read timeout on {operation}"
                ) from exc

        raise ThrottleError(
            f"DynamoDB throttle on {operation} after {_MAX_RETRIES} retries"
        ) from last_error
