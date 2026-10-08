from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal
import json
from pathlib import Path
import tempfile
import unittest

from packages.application.carbon_accounting import create_g06_parameter_resolver
from packages.application.canonical_input_codec import decode_canonical_input, encode_canonical_input
from packages.application.catalog_queries import CatalogQueryService
from packages.application.uat03_parameter_queries import UAT03ParameterQueries
from packages.application.reporting.model import build_report_model
from packages.core.errors import IssueLevel
from packages.core.models import (
    AccountingPeriod,
    AccountingRecord,
    ElectricityAcquisitionMode,
    ElectricityAttribute,
    ElectricityProofStatus,
    ElectricityProofType,
    ParameterSelectionMethod,
    PeriodType,
    ParameterType,
    RecordStatus,
)
from packages.core.parameter_resolution import (
    ElectricityConsumptionDetail,
    NATIONAL_ELECTRICITY_PARAMETER_ID,
    NONFOSSIL_ELECTRICITY_PARAMETER_ID,
    PROVINCIAL_ELECTRICITY_PARAMETER_ID,
    ParameterResolutionContext,
    UserProvidedParameterValue,
)
from packages.core.rules import RuleOrigin
from packages.persistence import SQLiteCatalogRepository, build_catalog_database
from packages.standards.carbon_material import (
    CarbonMaterialCalculator,
    CarbonMaterialInput,
    CarbonateComponent,
    ElectricityOutputLine,
    FGDInput,
    FuelInput,
    FuelPath,
    FuelType,
    InputValue,
    ParameterSourceKind,
    ParameterValue,
    fuel_mass_emission,
    fuel_volume_emission,
)


STANDARD_ID = "gbt_32151_34_2024"
PERIOD = AccountingPeriod(PeriodType.ANNUAL, date(2025, 1, 1), date(2025, 12, 31))
SNAPSHOT_AT = datetime(2026, 10, 9, 12, 0, tzinfo=timezone.utc)


class UAT03RuleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._temporary_directory = tempfile.TemporaryDirectory()
        cls.catalog_path = Path(cls._temporary_directory.name) / "catalog.sqlite"
        build_catalog_database(output_path=cls.catalog_path)
        cls.repository = SQLiteCatalogRepository(cls.catalog_path)
        cls.catalog = CatalogQueryService(cls.repository)
        cls.resolver = create_g06_parameter_resolver(cls.repository)
        cls.queries = UAT03ParameterQueries(cls.catalog, cls.resolver)

    @classmethod
    def tearDownClass(cls) -> None:
        cls._temporary_directory.cleanup()

    def test_fuel_and_carbonate_candidates_follow_verified_canonical_bindings(self) -> None:
        fuel_options = {item.subject_id: item for item in self.queries.fuel_options()}
        self.assertIn("anthracite", fuel_options)
        self.assertIn("natural_gas", fuel_options)
        self.assertEqual(fuel_options["natural_gas"].label, "天然气")
        self.assertEqual(fuel_options["natural_gas"].fuel_type, FuelType.NATURAL_GAS)

        defaults = self.queries.fuel_defaults("natural_gas", PERIOD)
        self.assertIsNotNone(defaults.lower_heating_value)
        self.assertIsNotNone(defaults.carbon_content_per_heat)
        self.assertIsNotNone(defaults.oxidation_rate)
        assert defaults.lower_heating_value is not None
        assert defaults.carbon_content_per_heat is not None
        assert defaults.oxidation_rate is not None
        self.assertEqual(defaults.lower_heating_value.factor.factor_id, "natural_gas_lhv_gbt32151_34_c1")
        self.assertEqual(defaults.carbon_content_per_heat.factor.factor_id, "natural_gas_carbon_content_gbt32151_34_c1")
        self.assertEqual(defaults.oxidation_rate.factor.factor_id, "natural_gas_oxidation_rate_gbt32151_34_c1")
        self.assertTrue(all(
            item.factor.source_id == "SRC-32151-34-2024"
            for item in (defaults.lower_heating_value, defaults.carbon_content_per_heat, defaults.oxidation_rate)
        ))

        carbonate_options = {item.subject_id: item for item in self.queries.carbonate_options(PERIOD)}
        self.assertEqual(len(carbonate_options), 11)
        self.assertEqual(carbonate_options["carbonate_caco3"].factor.factor_id, "carbonate_caco3_gbt32151_34_c2")
        self.assertEqual(carbonate_options["carbonate_caco3"].factor.source_id, "SRC-32151-34-2024")
        canonical_caco3 = next(item for item in self.catalog.list_subjects() if item.subject_id == "carbonate_caco3")
        self.assertEqual(carbonate_options["carbonate_caco3"].label, canonical_caco3.name)
        self.assertEqual(carbonate_options["carbonate_caco3"].aliases, canonical_caco3.aliases)

    def test_fgd_c2_factor_snapshot_preserves_official_catalog_source(self) -> None:
        option = next(
            item for item in self.queries.carbonate_options(PERIOD)
            if item.subject_id == "carbonate_caco3"
        )
        factor = option.factor
        parameter_value = ParameterValue(
            parameter_id=factor.parameter_id,
            value=factor.normalized_value,
            unit=factor.normalized_unit,
            source_kind=ParameterSourceKind.STANDARD_SPECIFIED,
            source_id=factor.source_id,
            source_version=str(factor.factor_year),
            source_location=factor.source_location,
            selection_reason=option.selection_reason,
            factor_id=factor.factor_id,
            factor_year=factor.factor_year,
        )
        input_value = CarbonMaterialInput(
            "input.fgd-c2",
            "enterprise.uat03",
            None,
            PERIOD,
            boundary_confirmed=True,
            fgd=FGDInput(components=(CarbonateComponent("10", "0.9", parameter_value, "1", "CaCO3"),)),
        )

        outcome = CarbonMaterialCalculator().calculate(input_value, calculated_at=SNAPSHOT_AT)

        self.assertTrue(outcome.successful, outcome.problems)
        snapshot = next(item for item in outcome.parameter_snapshots if item.factor_id == factor.factor_id)
        self.assertEqual(snapshot.parameter_id, factor.parameter_id)
        self.assertEqual(snapshot.source_id, "SRC-32151-34-2024")
        self.assertEqual(snapshot.source_location, factor.source_location)
        self.assertEqual(snapshot.value_used, Decimal("0.440"))
        self.assertEqual(snapshot.selection_method, ParameterSelectionMethod.STANDARD_REQUIRED)

    def test_direct_mass_and_volume_carbon_paths_keep_44_over_12_without_lhv(self) -> None:
        def measured(parameter_id: str, value: str, unit: str) -> ParameterValue:
            return ParameterValue(
                parameter_id,
                value,
                unit,
                source_kind=ParameterSourceKind.MEASURED,
                source_id="SRC-ENTERPRISE-LAB",
                source_version="lab-2025-v1",
                source_location="燃料检测报告第2页",
                selection_reason="采用企业直接实测含碳量。",
            )

        mass = FuelInput(
            "fuel.mass.measured",
            FuelPath.MASS,
            InputValue("10", "t"),
            measured("mass.carbon", "0.02", "tC/t"),
            measured("mass.oxidation", "1", "ratio"),
            lower_heating_value=None,
            fuel_type=FuelType.DIESEL,
        )
        volume = FuelInput(
            "fuel.volume.measured",
            FuelPath.VOLUME,
            InputValue("2", "10^4Nm3"),
            measured("volume.carbon", "0.015", "tC/10^4Nm3"),
            measured("volume.oxidation", "0.98", "ratio"),
            lower_heating_value=None,
            fuel_type=FuelType.NATURAL_GAS,
        )
        input_value = CarbonMaterialInput(
            "input.direct-carbon",
            "enterprise.uat03",
            None,
            PERIOD,
            boundary_confirmed=True,
            fuel_inputs=(mass, volume),
        )

        outcome = CarbonMaterialCalculator().calculate(input_value, calculated_at=SNAPSHOT_AT)

        self.assertTrue(outcome.successful, outcome.problems)
        amounts = {line.line_id: line.amount for line in outcome.result.lines}
        from packages.core.decimal_policy import DecimalPolicy
        from packages.standards._numeric_authority import declared_numeric_profile

        policy = DecimalPolicy()
        with declared_numeric_profile(policy):
            expected_mass = fuel_mass_emission("10", "0.02", "1")
            expected_volume = fuel_volume_emission("2", "0.015", "0.98")
        self.assertEqual(amounts["CAR-SRC-FUEL-001.fuel.mass.measured"], expected_mass)
        self.assertEqual(amounts["CAR-SRC-FUEL-001.fuel.volume.measured"], expected_volume)
        self.assertIsNone(mass.lower_heating_value)
        self.assertIsNone(volume.lower_heating_value)
        self.assertFalse(any(snapshot.parameter_id.endswith(".LHV") for snapshot in outcome.parameter_snapshots))

    def test_region_selection_is_exact_and_unselected_region_keeps_national_route(self) -> None:
        regions = self.queries.electricity_regions(PERIOD)
        self.assertIn("宁夏", regions)
        self.assertEqual(self.queries.preferred_electricity_region(PERIOD), "宁夏")
        ningxia = self.queries.electricity_options("宁夏", PERIOD)
        self.assertEqual(len(ningxia), 1)
        self.assertEqual(ningxia[0].factor.factor_id, "electricity_provincial_average_2023_29")
        self.assertEqual(ningxia[0].factor.normalized_value, Decimal("0.6187"))
        self.assertEqual(ningxia[0].factor.source_id, "SRC-ELEC-2023-47")
        self.assertEqual(ningxia[0].region, "宁夏")

        selected_detail = ElectricityConsumptionDetail(
            "power.selected.catalog.factor",
            "enterprise.uat03",
            STANDARD_ID,
            PERIOD,
            "1",
            "MWh",
            ElectricityAcquisitionMode.PURCHASED,
            ElectricityAttribute.ORDINARY,
            region="宁夏",
            selected_factor_id=ningxia[0].factor.factor_id,
        )
        selected_resolution = self.resolver.resolve_electricity_details(
            (selected_detail,), snapshot_at=SNAPSHOT_AT
        )[0]
        self.assertFalse(selected_resolution.blocked)
        self.assertEqual(selected_resolution.snapshot.factor_id, ningxia[0].factor.factor_id)
        self.assertEqual(
            selected_resolution.snapshot.selection_method,
            ParameterSelectionMethod.USER_SELECTED_LIBRARY_VALUE,
        )

        detail = ElectricityConsumptionDetail(
            "power.national",
            "enterprise.uat03",
            STANDARD_ID,
            PERIOD,
            "1",
            "MWh",
            ElectricityAcquisitionMode.PURCHASED,
            ElectricityAttribute.ORDINARY,
        )
        national = self.resolver.resolve_electricity_details((detail,), snapshot_at=SNAPSHOT_AT)[0]
        self.assertFalse(national.blocked)
        self.assertEqual(detail.parameter_id, NATIONAL_ELECTRICITY_PARAMETER_ID)
        self.assertEqual(national.snapshot.parameter_id, NATIONAL_ELECTRICITY_PARAMETER_ID)

        unsupported = ElectricityConsumptionDetail(
            "power.unsupported.region",
            "enterprise.uat03",
            STANDARD_ID,
            PERIOD,
            "1",
            "MWh",
            ElectricityAcquisitionMode.PURCHASED,
            ElectricityAttribute.ORDINARY,
            region="目录无此地区",
        )
        no_fallback = self.resolver.resolve_electricity_details((unsupported,), snapshot_at=SNAPSHOT_AT)[0]
        self.assertTrue(no_fallback.blocked)
        self.assertEqual(unsupported.parameter_id, PROVINCIAL_ELECTRICITY_PARAMETER_ID)
        self.assertIsNone(no_fallback.snapshot)
        self.assertTrue(all(
            item.factor.parameter_id == NATIONAL_ELECTRICITY_PARAMETER_ID
            for item in self.queries.electricity_options(None, PERIOD)
        ))

    def test_nonfossil_without_verified_proof_uses_only_independent_zero_factor(self) -> None:
        detail = ElectricityConsumptionDetail(
            "power.nonfossil.no-proof",
            "enterprise.uat03",
            STANDARD_ID,
            PERIOD,
            "1",
            "MWh",
            ElectricityAcquisitionMode.PURCHASED,
            ElectricityAttribute.NONFOSSIL,
            proof_type=ElectricityProofType.GEC,
            proof_status=ElectricityProofStatus.NOT_PROVIDED,
        )
        result = self.resolver.resolve_electricity_details((detail,), snapshot_at=SNAPSHOT_AT)[0]

        self.assertFalse(result.blocked)
        self.assertEqual(detail.parameter_id, NONFOSSIL_ELECTRICITY_PARAMETER_ID)
        self.assertEqual(result.snapshot.factor_id, "electricity_nonfossil_zero_gbt32151_34_2024")
        self.assertEqual(result.snapshot.source_id, "SRC-32151-34-2024")
        rule = next(item for item in self.resolver.rule_definitions if item.rule_id == "CAR-RULE-NONFOSSIL-POWER-001")
        self.assertEqual(rule.origin, RuleOrigin.SOFTWARE_DERIVED)
        self.assertIn(("decision", "GHG-STD-32151-34-007"), rule.payload)
        self.assertEqual(rule.evidence_source_id, "EVID-32151-34-PDF-2024-LOCAL")
        self.assertEqual(rule.confirmation_id, "GHG-STD-32151-34-007")

    def test_unbound_provincial_factors_are_not_candidates_for_any_region(self) -> None:
        provincial_assets = {
            item.asset_id
            for item in self.repository.list_reference_data_assets()
            if item.parameter_id == PROVINCIAL_ELECTRICITY_PARAMETER_ID
        }

        class RepositoryWithoutProvincialBindings:
            def __init__(self, repository):
                self._repository = repository

            def __getattr__(self, name):
                return getattr(self._repository, name)

            def list_reference_data_bindings(self):
                return tuple(
                    binding
                    for binding in self._repository.list_reference_data_bindings()
                    if binding.asset_id not in provincial_assets
                )

        resolver = create_g06_parameter_resolver(RepositoryWithoutProvincialBindings(self.repository))
        resolution = resolver.resolve(
            ParameterResolutionContext(
                parameter_id=PROVINCIAL_ELECTRICITY_PARAMETER_ID,
                standard_id=STANDARD_ID,
                accounting_period=PERIOD,
                region="宁夏",
                subject_id="purchased_electricity",
                parameter_type=ParameterType.ELECTRICITY_EMISSION_FACTOR,
            )
        )

        self.assertIsNone(resolution.recommended)
        self.assertEqual(resolution.alternatives, ())

    def test_user_provided_purchase_factor_is_a_manual_override_snapshot(self) -> None:
        detail = ElectricityConsumptionDetail(
            "power.manual.override",
            "enterprise.uat03",
            STANDARD_ID,
            PERIOD,
            "1",
            "MWh",
            ElectricityAcquisitionMode.PURCHASED,
            ElectricityAttribute.ORDINARY,
            region="宁夏",
            factor_override=UserProvidedParameterValue(
                "0.7",
                "tCO₂/MWh",
                source_reference="2025年宁夏购电合同因子说明",
                selection_reason="企业依据当期合同资料手动修订因子。",
            ),
        )
        input_value = CarbonMaterialInput(
            "input.manual-electricity-factor",
            "enterprise.uat03",
            None,
            PERIOD,
            boundary_confirmed=True,
            electricity_details=(detail,),
        )

        outcome = CarbonMaterialCalculator(parameter_resolver=self.resolver).calculate(
            input_value,
            calculated_at=SNAPSHOT_AT,
        )

        self.assertTrue(outcome.successful, outcome.problems)
        resolution = self.resolver.resolve(detail.to_parameter_context())
        self.assertEqual(resolution.selection_method, ParameterSelectionMethod.MANUAL_OVERRIDE)
        self.assertIsNone(resolution.recommended.factor.factor_id)
        decoded = decode_canonical_input(encode_canonical_input(input_value))
        self.assertEqual(decoded.electricity_details[0].factor_override, detail.factor_override)
        snapshot = next(item for item in outcome.parameter_snapshots if item.detail_id == detail.detail_id)
        self.assertEqual(snapshot.parameter_id, PROVINCIAL_ELECTRICITY_PARAMETER_ID)
        self.assertIsNone(snapshot.factor_id)
        self.assertIsNone(snapshot.source_id)
        self.assertIsNone(snapshot.source_version)
        self.assertEqual(snapshot.value_used, Decimal("0.7"))
        self.assertEqual(snapshot.source_location, "2025年宁夏购电合同因子说明")
        self.assertEqual(snapshot.selection_method, ParameterSelectionMethod.MANUAL_OVERRIDE)
        line = next(item for item in outcome.result.lines if item.line_id == f"CAR-FLD-PWR-PURCHASED-RESULT.{detail.detail_id}")
        self.assertEqual(line.amount, Decimal("0.7"))

        self.assertIsNotNone(outcome.evidence)
        evidence = outcome.evidence
        has_warnings = any(
            problem.level is IssueLevel.WARNING
            for problem in (*outcome.problems, *outcome.result.problems)
        )
        record = AccountingRecord(
            "record.manual-electricity-report",
            STANDARD_ID,
            outcome.algorithm_version,
            SNAPSHOT_AT,
            evidence.input_snapshot,
            outcome.result,
            RecordStatus.COMPLETED_WITH_WARNINGS if has_warnings else RecordStatus.COMPLETED,
            outcome.parameter_snapshots,
            outcome.problems,
        )
        report = build_report_model(
            record,
            json.loads(evidence.raw_input_snapshot_json),
            json.loads(evidence.trace_snapshot_json),
            json.loads(evidence.provenance_snapshot_json),
            json.loads(evidence.reporting_snapshot_json),
            json.loads(evidence.report_qualification_json),
            today=date(2026, 10, 9),
        )
        report_electricity = next(section for section in report.sections if section.section_id == "b8")
        factor_cell = report_electricity.tables[0].rows[0].cells[3]
        self.assertEqual(factor_cell.value, "0.7")
        self.assertEqual(factor_cell.source, "用户手动填写；2025年宁夏购电合同因子说明")

    def test_exported_electricity_selected_factor_keeps_catalog_snapshot_provenance(self) -> None:
        option = self.queries.electricity_options("宁夏", PERIOD)[0]
        factor = option.factor
        parameter_value = ParameterValue(
            parameter_id=factor.parameter_id,
            value=factor.normalized_value,
            unit=factor.normalized_unit,
            source_kind=ParameterSourceKind.OFFICIAL_PUBLISHED,
            source_id=factor.source_id,
            source_version=str(factor.factor_year),
            source_location=factor.source_location,
            selection_reason="用户选择了目录中适用于宁夏的电力因子。",
            factor_id=factor.factor_id,
            factor_year=factor.factor_year,
        )
        input_value = CarbonMaterialInput(
            "input.exported-region",
            "enterprise.uat03",
            None,
            PERIOD,
            boundary_confirmed=True,
            exported_electricity=(ElectricityOutputLine("power.out.nz", "1", parameter_value, region="宁夏"),),
        )

        outcome = CarbonMaterialCalculator(parameter_resolver=self.resolver).calculate(
            input_value,
            calculated_at=SNAPSHOT_AT,
        )

        self.assertTrue(outcome.successful, outcome.problems)
        snapshot = next(item for item in outcome.parameter_snapshots if item.detail_id == "power.out.nz")
        self.assertEqual(snapshot.factor_id, factor.factor_id)
        self.assertEqual(snapshot.parameter_id, PROVINCIAL_ELECTRICITY_PARAMETER_ID)
        self.assertEqual(snapshot.source_id, "SRC-ELEC-2023-47")
        self.assertEqual(snapshot.factor_year, 2023)
        self.assertEqual(snapshot.selection_method, ParameterSelectionMethod.USER_SELECTED_LIBRARY_VALUE)
        self.assertEqual(snapshot.selection_reason, parameter_value.selection_reason)
        output_line = next(line for line in outcome.result.lines if line.line_id == "CAR-FLD-POWER-EXPORTED-RESULT.power.out.nz")
        self.assertEqual(output_line.amount, Decimal("0.6187"))

    def test_exported_electricity_user_value_is_not_marked_measured_or_catalogued(self) -> None:
        factor = ParameterValue(
            parameter_id=PROVINCIAL_ELECTRICITY_PARAMETER_ID,
            value="0.7",
            unit="tCO2/MWh",
            source_kind=ParameterSourceKind.USER_DEFINED,
            source_id=None,
            source_version=None,
            source_location="2025年宁夏购电合同因子说明",
            selection_reason="企业按合同资料手动填写外供因子。",
        )
        input_value = CarbonMaterialInput(
            "input.exported-manual-factor",
            "enterprise.uat03",
            None,
            PERIOD,
            boundary_confirmed=True,
            exported_electricity=(
                ElectricityOutputLine("power.out.manual", "1", factor, region="宁夏"),
            ),
        )

        outcome = CarbonMaterialCalculator(parameter_resolver=self.resolver).calculate(
            input_value,
            calculated_at=SNAPSHOT_AT,
        )

        self.assertTrue(outcome.successful, outcome.problems)
        snapshot = next(item for item in outcome.parameter_snapshots if item.detail_id == "CAR-FLD-POWER-EXPORTED-EF.power.out.manual")
        self.assertEqual(snapshot.parameter_id, PROVINCIAL_ELECTRICITY_PARAMETER_ID)
        self.assertIsNone(snapshot.factor_id)
        self.assertIsNone(snapshot.source_id)
        self.assertIsNone(snapshot.source_version)
        self.assertEqual(snapshot.selection_method, ParameterSelectionMethod.MANUAL_OVERRIDE)
        self.assertEqual(snapshot.source_location, "2025年宁夏购电合同因子说明")
        line = next(item for item in outcome.result.lines if item.line_id == "CAR-FLD-POWER-EXPORTED-RESULT.power.out.manual")
        self.assertEqual(line.amount, Decimal("0.7"))

    def test_pre_region_saved_inputs_decode_with_region_unset(self) -> None:
        detail = ElectricityConsumptionDetail(
            "power.codec",
            "enterprise.uat03",
            STANDARD_ID,
            PERIOD,
            "1",
            "MWh",
            ElectricityAcquisitionMode.PURCHASED,
            ElectricityAttribute.ORDINARY,
            region="宁夏",
        )
        input_value = CarbonMaterialInput(
            "input.codec-legacy",
            "enterprise.uat03",
            None,
            PERIOD,
            electricity_details=(detail,),
            exported_electricity=(ElectricityOutputLine("power.out.codec", "1", region="宁夏"),),
        )
        encoded = json.loads(encode_canonical_input(input_value))

        def remove_region_fields(value: object) -> None:
            if isinstance(value, dict):
                if value.get("$kind") == "dataclass":
                    dataclass_type = value.get("type")
                    fields = value.get("fields")
                    if dataclass_type in {"electricity_consumption_detail", "electricity_output_line"} and isinstance(fields, dict):
                        fields.pop("region", None)
                        if dataclass_type == "electricity_consumption_detail":
                            fields.pop("selected_factor_id", None)
                            fields.pop("factor_selection_reason", None)
                            fields.pop("factor_override", None)
                for child in value.values():
                    remove_region_fields(child)
            elif isinstance(value, list):
                for child in value:
                    remove_region_fields(child)

        remove_region_fields(encoded)
        decoded = decode_canonical_input(json.dumps(encoded, ensure_ascii=False))
        self.assertIsNone(decoded.electricity_details[0].region)
        self.assertIsNone(decoded.electricity_details[0].selected_factor_id)
        self.assertIsNone(decoded.electricity_details[0].factor_override)
        self.assertIsNone(decoded.exported_electricity[0].region)
