"""Unit tests for auth domain exceptions."""

import unittest

from deskai.domain.auth.exceptions import (
    AccountDisabledError,
    AccountNotVerifiedError,
    AuthenticationError,
    DoctorProfileNotFoundError,
    PlanLimitExceededError,
    TrialExpiredError,
    UnauthorizedAccessError,
)
from deskai.shared.errors import DeskAIError


class AuthExceptionsTest(unittest.TestCase):
    def test_all_exceptions_extend_deskai_error(self) -> None:
        exceptions = [
            AuthenticationError,
            AccountNotVerifiedError,
            AccountDisabledError,
            DoctorProfileNotFoundError,
            UnauthorizedAccessError,
            PlanLimitExceededError,
            TrialExpiredError,
        ]
        for exc_cls in exceptions:
            with self.subTest(exc=exc_cls.__name__):
                self.assertTrue(
                    issubclass(exc_cls, DeskAIError)
                )

    def test_exception_messages(self) -> None:
        exc = AuthenticationError("bad creds")
        self.assertEqual(str(exc), "bad creds")


if __name__ == "__main__":
    unittest.main()
