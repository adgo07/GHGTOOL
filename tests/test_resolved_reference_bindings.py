"""Actual Resolver selection and independent negative binding associations."""
from dataclasses import replace
from datetime import date
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock

from packages.application.carbon_accounting import create_g06_parameter_resolver
from packages.core.models import AccountingPeriod, ParameterType, PeriodType
from packages.core.parameter_resolution import ParameterResolutionContext, ParameterResolver
from packages.persistence import SQLiteCatalogRepository, build_catalog_database

PERIOD = AccountingPeriod(PeriodType.ANNUAL, date(2026, 1, 1), date(2026, 12, 31))


class ResolvedReferenceBindingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.directory = tempfile.TemporaryDirectory()
        cls.catalog = SQLiteCatalogRepository(build_catalog_database(output_path=Path(cls.directory.name) / "catalog.sqlite"))

    @classmethod
    def tearDownClass(cls):
        cls.directory.cleanup()

    def context(self, **changes):
        return replace(ParameterResolutionContext(
            "natural_gas_lhv", standard_id="gbt_32151_34_2024", accounting_period=PERIOD,
            subject_id="natural_gas", parameter_type=ParameterType.LOWER_HEATING_VALUE,
        ), **changes)

    def test_fuel_context_is_produced_from_actual_resolver_not_claimed_ids(self):
        from packages.standards.carbon_material_business_policy import fuel_source_context, evaluate_fuel_power_field
        resolver = create_g06_parameter_resolver(self.catalog)
        context = fuel_source_context("fuel.fch", resolver=resolver, origin="CATALOG", subject_id="natural_gas", accounting_period=PERIOD)
        self.assertEqual(context["binding_status"], "VERIFIED")
        self.assertEqual(context["parameter_id"], "natural_gas_carbon_content")
        self.assertEqual(evaluate_fuel_power_field("fuel.fch", {**context, "business_source": "STANDARD_DEFAULT"})["status"], "READY")
        expired = Mock(wraps=self.catalog)
        expired.list_reference_data_bindings.return_value = tuple(
            replace(item, valid_to=date(2025,12,31)) if item.binding_id == "binding-natural_gas_carbon_content_gbt32151_34_c1" else item
            for item in self.catalog.list_reference_data_bindings())
        unavailable = fuel_source_context("fuel.fch", resolver=create_g06_parameter_resolver(expired), origin="CATALOG", subject_id="natural_gas", accounting_period=PERIOD)
        self.assertEqual(unavailable["binding_status"], "ABSENT")
        wrong = fuel_source_context("fuel.fch", resolver=resolver, origin="CATALOG", subject_id="unknown", accounting_period=PERIOD)
        self.assertEqual(wrong["binding_status"], "PENDING")
        custom = fuel_source_context("fuel.fch", resolver=resolver, origin="CUSTOM", subject_id=None, accounting_period=PERIOD)
        self.assertEqual(custom, {"origin": "CUSTOM", "binding_status": "ABSENT"})

    def test_actual_fuel_resolver_selection_has_exact_binding(self):
        resolver = create_g06_parameter_resolver(self.catalog)
        resolution = resolver.resolve(self.context())
        result = resolver.reference_binding_for(resolution)
        self.assertEqual(result.status, "VERIFIED")
        self.assertEqual(result.binding.binding_id, "binding-natural_gas_lhv_gbt32151_34_c1")
        self.assertEqual(result.binding.table_number, "C.1")
        self.assertEqual(result.binding.factor_id, resolution.recommended.factor_id)

    def test_wrong_object_parameter_or_source_cannot_verify(self):
        for changes in ({"subject_id": "raw_coal"}, {"source_id": "unrelated"}, {"parameter_id": "anthracite_lhv"}):
            with self.subTest(changes=changes):
                overlay = Mock(wraps=self.catalog)
                original = self.catalog.list_factors()
                overlay.list_factors.return_value = tuple(replace(item, **changes) if item.factor_id == "natural_gas_lhv_gbt32151_34_c1" else item for item in original)
                resolver = create_g06_parameter_resolver(overlay)
                result = resolver.reference_binding_for(resolver.resolve(self.context()))
                self.assertNotEqual(result.status, "VERIFIED")

    def test_expired_binding_is_checked_with_existing_period_semantics(self):
        overlay = Mock(wraps=self.catalog)
        overlay.list_reference_data_bindings.return_value = tuple(
            replace(item, valid_to=date(2025, 12, 31)) if item.binding_id == "binding-natural_gas_lhv_gbt32151_34_c1" else item
            for item in self.catalog.list_reference_data_bindings())
        resolver = create_g06_parameter_resolver(overlay)
        resolution = resolver.resolve(self.context())
        self.assertIsNotNone(resolution.recommended)
        self.assertEqual(resolver.reference_binding_for(resolution).status, "ABSENT")

    def test_multiple_associations_are_not_first_or_last_wins(self):
        original = create_g06_parameter_resolver(self.catalog)
        resolution = original.resolve(self.context())
        evidence = original.reference_binding_for(resolution).binding
        resolver = ParameterResolver(
            original.repository, common_rules=original._common_rules, industry_rules=original._industry_rules,
            reference_bindings=(evidence, replace(evidence, binding_id="another-approved-binding")),
        )
        result = resolver.reference_binding_for(resolver.resolve(self.context()))
        self.assertEqual(result.status, "AMBIGUOUS")
        self.assertEqual(len(result.bindings), 2)
        self.assertIsNone(result.binding)

    def test_old_constructor_is_explicitly_unverified_without_changing_resolve(self):
        original = create_g06_parameter_resolver(self.catalog)
        resolver = ParameterResolver(original.repository, common_rules=original._common_rules, industry_rules=original._industry_rules)
        resolution = resolver.resolve(self.context())
        self.assertIsNotNone(resolution.recommended)
        self.assertEqual(resolver.reference_binding_for(resolution).status, "PENDING")

    def test_invalid_asset_is_pending_not_fake_absent_or_measured(self):
        overlay = Mock(wraps=self.catalog)
        target = next(binding for binding in self.catalog.list_reference_data_bindings()
                      if binding.binding_id == "binding-natural_gas_lhv_gbt32151_34_c1")
        overlay.list_reference_data_assets.return_value = tuple(
            replace(item, subject_id="wrong") if item.asset_id == target.asset_id else item
            for item in self.catalog.list_reference_data_assets())
        resolver = create_g06_parameter_resolver(overlay)
        result = resolver.reference_binding_for(resolver.resolve(self.context()))
        self.assertEqual(result.status, "PENDING")

    def test_confirmed_nonrecommended_legal_factor_keeps_its_own_binding(self):
        original = create_g06_parameter_resolver(self.catalog)
        original_resolution = original.resolve(self.context())
        factor = original_resolution.recommended.factor
        alternate = replace(factor, factor_id="natural-gas-alternate", value=factor.value + 1)
        repository = Mock(wraps=original.repository)
        repository.get_factor.side_effect = lambda factor_id: alternate if factor_id == alternate.factor_id else original.repository.get_factor(factor_id)
        repository.list_factors.side_effect = lambda parameter_id: (*original.repository.list_factors(parameter_id), alternate) if parameter_id == factor.parameter_id else original.repository.list_factors(parameter_id)
        evidence = original.reference_binding_for(original_resolution).binding
        resolver = ParameterResolver(repository, common_rules=original._common_rules, industry_rules=original._industry_rules,
            reference_bindings=(evidence, replace(evidence, factor_id=alternate.factor_id, binding_id="alternate-binding")))
        context = self.context(confirmed_factor_id=alternate.factor_id, confirmation_reason="明确选择适用的其他版本")
        resolution = resolver.resolve(context)
        self.assertFalse(resolution.blocked, resolution.warnings)
        self.assertEqual(resolution.recommended.factor_id, alternate.factor_id)
        association = resolver.reference_binding_for(resolution)
        self.assertEqual(association.status, "VERIFIED")
        self.assertEqual(association.binding.binding_id, "alternate-binding")

    def test_confirmed_legal_selection_is_not_replaced_by_another_recommendation(self):
        resolver = create_g06_parameter_resolver(self.catalog)
        context = self.context(
            confirmed_factor_id="natural_gas_lhv_gbt32151_34_c1", confirmation_reason="用户显式切回缺省",
        )
        resolution = resolver.resolve(context)
        result = resolver.reference_binding_for(resolution)
        self.assertEqual(result.status, "VERIFIED")
        self.assertEqual(result.binding.factor_id, context.confirmed_factor_id)
        inconsistent = replace(resolution, context=replace(context, confirmed_factor_id="wrong"))
        self.assertEqual(resolver.reference_binding_for(inconsistent).status, "PENDING")
