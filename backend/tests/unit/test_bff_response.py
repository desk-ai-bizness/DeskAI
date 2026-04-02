"""Unit tests for the BFF response envelope."""

import unittest

from deskai.bff.response import BffResponse


class BffResponseTest(unittest.TestCase):
    def test_data_field_stored(self) -> None:
        resp = BffResponse(
            data={"key": "value"}, contract_version="1.0"
        )
        self.assertEqual(resp.data, {"key": "value"})

    def test_contract_version_stored(self) -> None:
        resp = BffResponse(data={}, contract_version="2.1")
        self.assertEqual(resp.contract_version, "2.1")

    def test_is_frozen(self) -> None:
        resp = BffResponse(data={}, contract_version="1.0")
        with self.assertRaises(AttributeError):
            resp.data = {"new": "val"}  # type: ignore[misc]

    def test_empty_data(self) -> None:
        resp = BffResponse(data={}, contract_version="1.0")
        self.assertEqual(resp.data, {})

    def test_equality(self) -> None:
        a = BffResponse(data={"x": 1}, contract_version="1.0")
        b = BffResponse(data={"x": 1}, contract_version="1.0")
        self.assertEqual(a, b)

    def test_inequality_different_data(self) -> None:
        a = BffResponse(data={"x": 1}, contract_version="1.0")
        b = BffResponse(data={"x": 2}, contract_version="1.0")
        self.assertNotEqual(a, b)


if __name__ == "__main__":
    unittest.main()
