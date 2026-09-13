from __future__ import annotations

from dataclasses import replace
from datetime import date, datetime, timezone
from decimal import Decimal
import unittest

from packages.core import (
    AccountingPeriod,
    DomainValidationError,
    ElectricityAcquisitionMode,
    ElectricityAttribute,
    ElectricityConsumptionDetail,
    ElectricityProofStatus,
    ElectricityProofType,
    ElectricityResolutionRoute,
    Factor,
    Parameter,
    ParameterResolver,
    ParameterType,
    PeriodType,
    ReviewStatus,
    ValueType,
)


STANDARD_ID = "gbt_32151_34_2024"
ENTERPRISE_ID = "enterprise.multi.electricity"
PERIOD = AccountingPeriod(
    PeriodType.ANNUAL,
    date(2025, 1, 1),
    date(2025, 12, 31),
)
SNAPSHOT_AT = datetime(2026, 9, 12, 12, 0, tzinfo=timezone.utc)


class MemoryParameterRepository:
    def __init__(self, parameters: tuple[Parameter, ...], factors: tuple[Factor, ...]) -> None:
        self.parameters = parameters
        self.factors = factors

    def get_parameter(self, parameter_id: str) -> Parameter | None:
        return next((item for item in self.parameters if item.parameter_id == parameter_id), None)

    def get_factor(self, factor_id: str) -> Factor | None:
        return next((item for item in self.factors if item.factor_id == factor_id), None)

    def list_factors(self, parameter_id: str) -> tuple[Factor, ...]:
        return tuple(item for item in self.factors if item.parameter_id == parameter_id)


def _parameters() -> tuple[Parameter, Parameter]:
    return (
        Parameter(
            "electricity_emission_factor_national",
            "purchased_electricity",
            ParameterType.ELECTRICITY_EMISSION_FACTOR,
            "全国电力因子",
            "tCO₂/MWh",
            "2025",
        ),
        Parameter(
            "electricity_emission_factor_nonfossil",
            "purchased_electricity",
            ParameterType.ELECTRICITY_EMISSION_FACTOR,
            "非化石能源电力排放因子",
            "tCO₂/MWh",
            "2024",
        ),
    )


def _factors(include_zero: bool = True) -> tuple[Factor, ...]:
    national = Factor(
        factor_id="electricity_national_average_2024",
        parameter_id="electricity_emission_factor_national",
        subject_id="purchased_electricity",
        parameter_type=ParameterType.ELECTRICITY_EMISSION_FACTOR,
        value="0.5306",
        unit="tCO₂/MWh",
        version="2024",
        value_type=ValueType.GOVERNMENT_PUBLISHED,
        review_status=ReviewStatus.VERIFIED,
        source_id="SRC-ELEC-2024-OFFICIAL",
        source_location="最新全国平均因子",
        applicable_standard_ids=(STANDARD_ID,),
        factor_year=2024,
        valid_from=date(2025, 3, 1),
    )
    if not include_zero:
        return (national,)
    zero = Factor(
        factor_id="electricity_nonfossil_zero_gbt32151_34_2024",
        parameter_id="electricity_emission_factor_nonfossil",
        subject_id="purchased_electricity",
        parameter_type=ParameterType.ELECTRICITY_EMISSION_FACTOR,
        value="0",
        unit="tCO₂/MWh",
        version="2024",
        value_type=ValueType.STANDARD_SPECIFIED,
        review_status=ReviewStatus.VERIFIED,
        source_id="SRC-32151-34-2024",
        source_location="GB/T 32151.34—2024 第5.2.6.1条、附录D.1.1；PDF第30页；印刷页22",
        applicable_standard_ids=(STANDARD_ID,),
        factor_year=2024,
        valid_from=date(2025, 3, 1),
    )
    return national, zero


def _resolver(*, include_zero: bool = True) -> ParameterResolver:
    return ParameterResolver.with_default_g05_rules(
        MemoryParameterRepository(_parameters(), _factors(include_zero=include_zero))
    )


def _detail(
    detail_id: str,
    amount: str,
    acquisition_mode: ElectricityAcquisitionMode,
    attribute: ElectricityAttribute,
    *,
    proof_type: ElectricityProofType = ElectricityProofType.NONE,
    proof_status: ElectricityProofStatus = ElectricityProofStatus.NOT_PROVIDED,
) -> ElectricityConsumptionDetail:
    return ElectricityConsumptionDetail(
        detail_id=detail_id,
        enterprise_id=ENTERPRISE_ID,
        standard_id=STANDARD_ID,
        accounting_period=PERIOD,
        electricity_amount=Decimal(amount),
        electricity_unit="MWh",
        acquisition_mode=acquisition_mode,
        attribute=attribute,
        proof_type=proof_type,
        proof_status=proof_status,
    )


class G05MultiElectricityTests(unittest.TestCase):
    def test_same_enterprise_resolves_three_details_independently(self) -> None:
        details = (
            _detail(
                "detail.purchased.ordinary",
                "100",
                ElectricityAcquisitionMode.PURCHASED,
                ElectricityAttribute.ORDINARY,
            ),
            _detail(
                "detail.purchased.nonfossil",
                "20",
                ElectricityAcquisitionMode.PURCHASED,
                ElectricityAttribute.NONFOSSIL,
                proof_type=ElectricityProofType.CONTRACT_AND_SETTLEMENT,
                proof_status=ElectricityProofStatus.VALID,
            ),
            _detail(
                "detail.self.nonfossil",
                "30",
                ElectricityAcquisitionMode.SELF_CONSUMED,
                ElectricityAttribute.NONFOSSIL,
                proof_type=ElectricityProofType.MONTHLY_ORIGINAL_RECORD,
                proof_status=ElectricityProofStatus.VALID,
            ),
        )

        results = _resolver().resolve_electricity_details(details, snapshot_at=SNAPSHOT_AT)

        self.assertEqual(len(results), 3)
        self.assertTrue(all(not result.blocked for result in results))
        self.assertEqual(
            [result.route for result in results],
            [
                ElectricityResolutionRoute.PURCHASED_ELECTRICITY,
                ElectricityResolutionRoute.PURCHASED_ELECTRICITY,
                ElectricityResolutionRoute.SELF_CONSUMED_NONFOSSIL,
            ],
        )
        self.assertEqual(
            [result.snapshot.factor_id for result in results if result.snapshot is not None],
            [
                "electricity_national_average_2024",
                "electricity_nonfossil_zero_gbt32151_34_2024",
                "electricity_nonfossil_zero_gbt32151_34_2024",
            ],
        )
        snapshots = [result.snapshot for result in results]
        self.assertEqual(
            {snapshot.detail_id for snapshot in snapshots if snapshot is not None},
            {detail.detail_id for detail in details},
        )
        self.assertEqual(
            {snapshot.snapshot_id for snapshot in snapshots if snapshot is not None},
            {f"{detail.detail_id}.parameter-snapshot" for detail in details},
        )
        self.assertEqual(results[0].snapshot.value_used, Decimal("0.5306"))
        self.assertEqual(
            [result.result.context.parameter_id for result in results if result.result is not None],
            [
                "electricity_emission_factor_national",
                "electricity_emission_factor_nonfossil",
                "electricity_emission_factor_nonfossil",
            ],
        )
        self.assertEqual(
            results[0].result.context.electricity_attribute,
            ElectricityAttribute.ORDINARY,
        )
        self.assertEqual(
            results[1].result.context.electricity_acquisition_mode,
            ElectricityAcquisitionMode.PURCHASED,
        )
        self.assertEqual(
            results[2].result.context.electricity_acquisition_mode,
            ElectricityAcquisitionMode.SELF_CONSUMED,
        )

    def test_missing_proof_is_error_without_zero_or_national_fallback(self) -> None:
        result = _resolver().resolve_electricity_details(
            (
                _detail(
                    "detail.missing.proof",
                    "20",
                    ElectricityAcquisitionMode.PURCHASED,
                    ElectricityAttribute.NONFOSSIL,
                    proof_type=ElectricityProofType.GEC,
                    proof_status=ElectricityProofStatus.NOT_PROVIDED,
                ),
            ),
            snapshot_at=SNAPSHOT_AT,
        )[0]

        self.assertTrue(result.blocked)
        self.assertIsNone(result.snapshot)
        self.assertIsNotNone(result.result)
        assert result.result is not None
        self.assertIsNone(result.result.recommended)
        self.assertTrue(
            any(problem.code == "GEN-VAL-NONFOSSIL-EVIDENCE" for problem in result.problems)
        )
        self.assertNotIn(
            "electricity_national_average_2024",
            {value.factor_id for value in result.result.alternatives},
        )

    def test_missing_canonical_zero_is_error_without_average_fallback(self) -> None:
        result = _resolver(include_zero=False).resolve_electricity_details(
            (
                _detail(
                    "detail.no.canonical.zero",
                    "20",
                    ElectricityAcquisitionMode.PURCHASED,
                    ElectricityAttribute.NONFOSSIL,
                    proof_type=ElectricityProofType.GEC,
                    proof_status=ElectricityProofStatus.VALID,
                ),
            ),
            snapshot_at=SNAPSHOT_AT,
        )[0]

        self.assertTrue(result.blocked)
        self.assertIsNone(result.snapshot)
        self.assertTrue(
            any(
                problem.code == "GEN-VAL-NONFOSSIL-ZERO-FACTOR-MISSING"
                for problem in result.problems
            )
        )
        assert result.result is not None
        self.assertIsNone(result.result.recommended)
        self.assertNotIn(
            "electricity_national_average_2024",
            {value.factor_id for value in result.result.alternatives},
        )

    def test_zero_factor_selection_uses_stable_id_not_source_location_text(self) -> None:
        counterfeit = replace(
            _factors()[1],
            factor_id="counterfeit_zero_factor",
            source_location="GB/T 32151.34—2024 第5.2.6.1条、附录D.1.1；PDF第30页；印刷页22",
        )
        result = ParameterResolver.with_default_g05_rules(
            MemoryParameterRepository(_parameters(), (_factors()[0], counterfeit))
        ).resolve_electricity_details(
            (
                _detail(
                    "detail.counterfeit.zero",
                    "20",
                    ElectricityAcquisitionMode.PURCHASED,
                    ElectricityAttribute.NONFOSSIL,
                    proof_type=ElectricityProofType.GEC,
                    proof_status=ElectricityProofStatus.VALID,
                ),
            ),
            snapshot_at=SNAPSHOT_AT,
        )[0]

        self.assertTrue(result.blocked)
        self.assertIsNone(result.snapshot)
        self.assertTrue(
            any(
                problem.code == "GEN-VAL-NONFOSSIL-ZERO-FACTOR-MISSING"
                for problem in result.problems
            )
        )
    def test_self_consumed_fossil_is_delegated_without_purchased_path(self) -> None:
        result = _resolver().resolve_electricity_details(
            (
                _detail(
                    "detail.self.fossil",
                    "15",
                    ElectricityAcquisitionMode.SELF_CONSUMED,
                    ElectricityAttribute.FOSSIL,
                ),
            ),
            snapshot_at=SNAPSHOT_AT,
        )[0]

        self.assertEqual(result.route, ElectricityResolutionRoute.DELEGATE_DIRECT_FUEL_PATH)
        self.assertTrue(result.blocked)
        self.assertIsNone(result.result)
        self.assertIsNone(result.snapshot)
        self.assertEqual(
            {problem.code for problem in result.problems},
            {"GEN-VAL-SELF-CONSUMED-FOSSIL-ROUTE"},
        )

    def test_electricity_dimensions_require_domain_enums(self) -> None:
        with self.assertRaises(DomainValidationError):
            _detail(
                "detail.raw.enum",
                "1",
                "PURCHASED",  # type: ignore[arg-type]
                ElectricityAttribute.ORDINARY,
            )
        with self.assertRaises(DomainValidationError):
            _detail(
                "detail.raw.attribute",
                "1",
                ElectricityAcquisitionMode.PURCHASED,
                "NONFOSSIL",  # type: ignore[arg-type]
            )


if __name__ == "__main__":
    unittest.main()