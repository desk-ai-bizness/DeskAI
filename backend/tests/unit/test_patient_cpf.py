"""Unit tests for CPF normalization, validation, and display masking."""

import unittest

from deskai.domain.patient.exceptions import PatientValidationError


class PatientCpfTest(unittest.TestCase):
    def test_normalizes_punctuated_cpf_to_digits(self) -> None:
        from deskai.domain.patient.cpf import normalize_cpf

        self.assertEqual(normalize_cpf(" 529.982.247-25 "), "52998224725")

    def test_rejects_invalid_checksum(self) -> None:
        from deskai.domain.patient.cpf import normalize_cpf

        with self.assertRaises(PatientValidationError):
            normalize_cpf("529.982.247-26")

    def test_rejects_repeated_digits(self) -> None:
        from deskai.domain.patient.cpf import normalize_cpf

        with self.assertRaises(PatientValidationError):
            normalize_cpf("111.111.111-11")

    def test_masks_normalized_cpf_for_display(self) -> None:
        from deskai.domain.patient.cpf import mask_cpf

        self.assertEqual(mask_cpf("52998224725"), "529.***.***-25")


if __name__ == "__main__":
    unittest.main()
