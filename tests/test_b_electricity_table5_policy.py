"""Issue010：普通购电显式表5保持真实属性，不扩大来源或自动补位。"""
from dataclasses import replace
from datetime import date
from decimal import Decimal
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock

from packages.application.carbon_accounting import CarbonAccountingUseCase, create_g06_parameter_resolver
from packages.application.catalog_queries import CatalogQueryService
from packages.application.uat03_parameter_queries import UAT03ParameterQueries
from packages.core.models import DomainValidationError, ElectricityAcquisitionMode, ElectricityAttribute
from packages.core.parameter_resolution import ElectricityConsumptionDetail
from packages.persistence import SQLiteCatalogRepository, SQLiteRecordRepository, build_catalog_database
from packages.standards.carbon_material import CarbonMaterialCalculator, CarbonMaterialInput
from packages.standards.carbon_material_business_policy import electricity_source_context, evaluate_fuel_power_field
from tests.test_pr46_baseline_integration import NOW, PERIOD

TABLE5 = "electricity_national_fossil_2023_01"


class ElectricityTable5PolicyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.directory = tempfile.TemporaryDirectory()
        cls.root = Path(cls.directory.name)
        cls.catalog = SQLiteCatalogRepository(build_catalog_database(output_path=cls.root / "catalog.sqlite"))

    @classmethod
    def tearDownClass(cls):
        cls.directory.cleanup()

    def detail(self, **changes):
        return replace(ElectricityConsumptionDetail(
            "power.explicit-table5", "enterprise.power", "gbt_32151_34_2024", PERIOD, "100", "MWh",
            ElectricityAcquisitionMode.PURCHASED, ElectricityAttribute.ORDINARY,
            selected_factor_id=TABLE5, factor_selection_reason="用户显式选择全国化石能源电力口径（表5）。",
        ), **changes)

    def adopted(self, resolver, detail):
        result = resolver.resolve_electricity_details((detail,), snapshot_at=NOW)[0]
        self.assertIsNotNone(result.result)
        context = electricity_source_context(resolver, result.result, direction="PURCHASED", attribute="CONVENTIONAL")
        return result, context, evaluate_fuel_power_field("electricity.factor", {**context, "business_source": "STANDARD_DEFAULT"})

    def test_explicit_table5_is_ready_and_100_mwh_is_82_73_without_relabeling_ordinary(self):
        resolver = create_g06_parameter_resolver(self.catalog)
        detail = self.detail()
        resolved, context, policy = self.adopted(resolver, detail)
        self.assertEqual(policy["status"], "READY", policy["problems"])
        self.assertEqual(context["attribute"], "CONVENTIONAL")
        self.assertIs(detail.attribute, ElectricityAttribute.ORDINARY)
        self.assertIs(resolved.result.context.electricity_attribute, ElectricityAttribute.ORDINARY)
        self.assertEqual(resolved.snapshot.factor_id, TABLE5)
        self.assertEqual(resolved.snapshot.value_used, Decimal("0.8273"))
        records = SQLiteRecordRepository(self.root / "table5-records.sqlite")
        formal = CarbonAccountingUseCase(CarbonMaterialCalculator(parameter_resolver=resolver), records)
        outcome = formal.calculate(CarbonMaterialInput("table5", "enterprise.power", None, PERIOD, boundary_confirmed=True, electricity_details=(detail,)), calculated_at=NOW)
        self.assertTrue(outcome.successful, outcome.problems)
        self.assertEqual(outcome.record.calculation_result.total_amount, Decimal("82.73"))

    def test_table5_missing_wrong_parameter_and_expired_binding_cannot_grant_field_qualification(self):
        for defect in ("missing", "wrong-parameter", "expired"):
            with self.subTest(defect=defect):
                overlay = Mock(wraps=self.catalog)
                if defect == "wrong-parameter":
                    overlay.list_factors.return_value = tuple(replace(factor, parameter_id="electricity_emission_factor_national") if factor.factor_id == TABLE5 else factor for factor in self.catalog.list_factors())
                else:
                    overlay.list_reference_data_bindings.return_value = tuple(
                        replace(binding, valid_to=date(2025, 12, 31)) if defect == "expired" and binding.factor_id == TABLE5 else binding
                        for binding in self.catalog.list_reference_data_bindings()
                        if defect != "missing" or binding.factor_id != TABLE5
                    )
                resolver = create_g06_parameter_resolver(overlay)
                resolved, context, policy = self.adopted(resolver, self.detail())
                self.assertEqual(policy["status"], "BLOCKED")
                self.assertNotEqual(context.get("binding_status"), "VERIFIED")
                if resolved.result.recommended is not None:
                    self.assertEqual(resolved.result.recommended.factor_id, TABLE5)
                queries = UAT03ParameterQueries(CatalogQueryService(overlay), resolver)
                self.assertNotIn(TABLE5, {option.factor.factor_id for option in queries.electricity_catalog_options("全国", None, PERIOD)})
                records = SQLiteRecordRepository(self.root / ("invalid-table5-" + defect + ".sqlite"))
                formal = CarbonAccountingUseCase(CarbonMaterialCalculator(parameter_resolver=resolver), records)
                invalid = CarbonMaterialInput("invalid-table5-" + defect, "enterprise.power", None, PERIOD,
                                              boundary_confirmed=True, electricity_details=(self.detail(),))
                outcome = formal.calculate(invalid, calculated_at=NOW)
                self.assertFalse(outcome.successful, outcome.problems)
                self.assertIsNone(outcome.record)
                self.assertEqual(records.list_all(), ())

    def test_nonfossil_and_other_cannot_borrow_table5_and_no_selection_does_not_use_it(self):
        resolver = create_g06_parameter_resolver(self.catalog)
        resolved, _, _ = self.adopted(resolver, self.detail())
        nonfossil = electricity_source_context(resolver, resolved.result, direction="PURCHASED", attribute="NONFOSSIL")
        self.assertEqual(nonfossil["attribute"], "NONFOSSIL")
        self.assertEqual(evaluate_fuel_power_field("electricity.factor", {**nonfossil, "business_source": "STANDARD_DEFAULT"})["status"], "BLOCKED")
        other = electricity_source_context(resolver, resolved.result, direction="PURCHASED", attribute="CONVENTIONAL")
        self.assertEqual(evaluate_fuel_power_field("electricity.factor", {**other, "business_source": "OTHER"})["status"], "BLOCKED")
        with self.assertRaises(DomainValidationError):
            self.detail(attribute=ElectricityAttribute.NONFOSSIL)
        overlay = Mock(wraps=self.catalog)
        overlay.list_factors.return_value = tuple(factor for factor in self.catalog.list_factors() if factor.factor_id != "electricity_national_average_2023")
        unavailable = create_g06_parameter_resolver(overlay)
        default = unavailable.resolve_electricity_details((self.detail(selected_factor_id=None, factor_selection_reason=None),), snapshot_at=NOW)[0]
        self.assertTrue(default.blocked)
        self.assertIsNone(default.snapshot)
        queries = UAT03ParameterQueries(CatalogQueryService(overlay), unavailable)
        self.assertEqual(queries.electricity_options(None, PERIOD), ())
