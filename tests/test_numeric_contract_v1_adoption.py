from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal, ROUND_HALF_EVEN, ROUND_HALF_UP, localcontext
import json
from pathlib import Path
import unittest

from packages.core import AccountingPeriod, PeriodType
from packages.core.decimal_policy import DecimalPolicy
from packages.core.errors import DomainValidationError
from packages.core.units import UnitService
from packages.application.carbon_accounting import CarbonAccountingUseCase
from packages.persistence.in_memory_records import InMemoryRecordRepository
from packages.standards.carbon_material import (
    ALGORITHM_VERSION,
    CarbonMaterialCalculator,
    CarbonMaterialInput,
    FuelInput,
)


ROOT = Path(__file__).resolve().parents[1]
LOCK_PATH = ROOT / "platform-lock.json"
VECTOR_PATH = ROOT / "conformance" / "numeric" / "qz.carbon_accounting" / "gbt32151_34_n01c.json"
CARBON_SOURCE = ROOT / "packages" / "standards" / "carbon_material.py"
CENTRAL_NUMERIC_V1_SHA = "ee5feb0cc34dbd99790500fadd0c4c932e202a20"
CARBON_PROFILE_ID = "GHGTOOL_CARBON_DECIMAL40_CURRENT"
SNAPSHOT_AT = datetime(2026, 10, 1, 0, 0, tzinfo=timezone.utc)
PERIOD = AccountingPeriod(PeriodType.ANNUAL, date(2025, 1, 1), date(2025, 12, 31))


def _fuel_only_input() -> CarbonMaterialInput:
    return CarbonMaterialInput(
        input_id="numeric-v1-adoption",
        enterprise_id="enterprise.numeric-v1-adoption",
        enterprise_name="Numeric v1 adoption",
        period=PERIOD,
        boundary_confirmed=True,
        fuel_inputs=(FuelInput.mass("fuel.numeric-v1", "1", "1", "1"),),
    )


class NumericContractV1AdoptionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.lock = json.loads(LOCK_PATH.read_text(encoding="utf-8"))
        self.vectors = json.loads(VECTOR_PATH.read_text(encoding="utf-8"))

    def test_platform_lock_adopts_only_frozen_numeric_v1_baseline(self) -> None:
        self.assertEqual(self.lock["commit_sha"], CENTRAL_NUMERIC_V1_SHA)
        self.assertEqual(self.lock["numeric_contract"]["version"], "v1")
        self.assertEqual(self.lock["numeric_contract"]["status"], "FROZEN")
        self.assertEqual(
            self.lock["numeric_contract"]["document"],
            "contracts/numeric/NUMERIC_CONTRACT_V1_FROZEN.md",
        )
        self.assertEqual(self.lock["architecture_version"]["status"], "FROZEN")
        for key in (
            "unit_contract",
            "module_capability_contract",
            "record_contract",
            "package_contract",
        ):
            self.assertEqual(self.lock[key]["status"], "DRAFT", key)
        self.assertNotIn("quantity_contract", self.lock)
        self.assertFalse(self.lock["auto_upgrade"])

    def test_carbon_profile_metadata_matches_frozen_profile_evidence(self) -> None:
        contract = self.vectors["numeric_contract"]
        profile = self.vectors["numeric_profile"]
        self.assertEqual(contract["version"], "v1")
        self.assertEqual(contract["status"], "FROZEN")
        self.assertEqual(contract["central_baseline_sha"], CENTRAL_NUMERIC_V1_SHA)
        self.assertEqual(profile["numeric_profile_id"], CARBON_PROFILE_ID)
        self.assertEqual(profile["numeric_contract_version"], "v1")
        self.assertEqual(profile["calculator_version"], ALGORITHM_VERSION)
        self.assertEqual(profile["representation"], "decimal")
        self.assertEqual(profile["working_precision"], 40)
        self.assertEqual(profile["rounding_mode"], "ROUND_HALF_UP")
        self.assertEqual(profile["comparison_policy"], "full_value_exact")
        self.assertEqual(
            profile["tolerance_policy"],
            "purpose_specific_no_global_business_epsilon",
        )
        self.assertEqual(
            profile["display_policy"],
            "presentation_only_no_feedback_to_authoritative_decision",
        )

    def test_formal_result_and_record_algorithm_version_map_to_numeric_v1_profile(self) -> None:
        profile = self.vectors["numeric_profile"]
        outcome = CarbonAccountingUseCase(
            CarbonMaterialCalculator(policy=DecimalPolicy()), InMemoryRecordRepository()
        ).calculate(_fuel_only_input(), calculated_at=SNAPSHOT_AT)
        self.assertTrue(outcome.successful)
        self.assertIsNotNone(outcome.result)
        self.assertIsNotNone(outcome.record)
        self.assertEqual(outcome.algorithm_version, profile["calculator_version"])
        self.assertEqual(outcome.result.algorithm_version, profile["calculator_version"])
        self.assertEqual(outcome.record.algorithm_version, profile["calculator_version"])
        self.assertEqual(profile["numeric_contract_version"], "v1")
        self.assertEqual(profile["numeric_profile_id"], CARBON_PROFILE_ID)

    def test_current_carbon_decimal_policy_is_project_p40_half_up(self) -> None:
        policy = DecimalPolicy()
        self.assertEqual(policy.precision, 40)
        self.assertEqual(policy.rounding, ROUND_HALF_UP)
        self.assertEqual(policy.display_places, 2)

    def test_declared_p40_result_is_ambient_independent(self) -> None:
        expected = Decimal("3.666666666666666666666666666666666666667")
        observed: list[Decimal] = []
        for ambient_precision, ambient_rounding in (
            (28, ROUND_HALF_EVEN),
            (34, ROUND_HALF_EVEN),
            (40, ROUND_HALF_UP),
            (50, ROUND_HALF_EVEN),
        ):
            with localcontext() as context:
                context.prec = ambient_precision
                context.rounding = ambient_rounding
                outcome = CarbonMaterialCalculator(policy=DecimalPolicy()).calculate(
                    _fuel_only_input(), calculated_at=SNAPSHOT_AT
                )
                self.assertTrue(outcome.successful)
                self.assertIsNotNone(outcome.result)
                observed.append(outcome.result.total_amount)
        self.assertTrue(all(value == expected for value in observed))

    def test_profile_mismatch_still_fails_instead_of_silent_fallback(self) -> None:
        calculator = CarbonMaterialCalculator(
            policy=DecimalPolicy(precision=50, rounding=ROUND_HALF_UP),
            unit_service=UnitService(DecimalPolicy(precision=40, rounding=ROUND_HALF_UP)),
        )
        with self.assertRaisesRegex(DomainValidationError, "numeric profile mismatch"):
            calculator.calculate(_fuel_only_input(), calculated_at=SNAPSHOT_AT)

    def test_exact_business_comparison_and_display_separation_remain_intact(self) -> None:
        vector = next(
            item for item in self.vectors["vectors"] if item["kind"] == "display_separation"
        )
        calculation_value = Decimal(vector["calculation_value"])
        comparison_limit = Decimal(vector["comparison_limit"])
        display_value = DecimalPolicy().format_for_display(
            calculation_value, vector["display_places"]
        )
        self.assertEqual(display_value, vector["display_value"])
        self.assertEqual(calculation_value <= comparison_limit, vector["expected_lte"])
        self.assertNotIn("is_close(", CARBON_SOURCE.read_text(encoding="utf-8"))

    def test_requested_and_effective_profiles_remain_identical(self) -> None:
        propagation = [
            item for item in self.vectors["vectors"] if item["kind"] == "profile_propagation"
        ]
        self.assertEqual(
            {item["case_id"] for item in propagation},
            {"N01C-P28", "N01C-P34", "N01C-P40", "N01C-P50", "N01C-P60"},
        )
        for item in propagation:
            self.assertEqual(
                item["requested_numeric_profile"],
                item["effective_numeric_profile"],
                item["case_id"],
            )


if __name__ == "__main__":
    unittest.main()
