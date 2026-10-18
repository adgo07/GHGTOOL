"""B-HEAT正式领域链：真实目录、边界和不可变记录保护。"""
from dataclasses import replace
from decimal import Decimal
from datetime import date
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from packages.application.carbon_accounting import CarbonAccountingUseCase, create_g06_parameter_resolver
from packages.application.carbon_material_input_codec import encode_canonical_input, decode_canonical_input
from packages.persistence import InMemoryRecordRepository, SQLiteCatalogRepository, build_catalog_database
from packages.reference_data import DEFAULT_SOURCE_PATH
from packages.standards.carbon_material import (
    CarbonMaterialCalculator, HeatInput, HeatFactorMode, InputValue, ParameterSourceKind,
    SOURCE_PURCHASED_HEAT, EmissionSourceState, EmissionSourceStatus,
)
from scripts.project_heat_rules import verify_heat_projection
from tests.test_b1_fuel_lifecycle import fuel_input, parameter


def heat(**changes):
    defaults = dict(line_id="heat.test", amount="1000", enthalpy="2800",
                    manual_enthalpy=True, source_boundary="OUTSIDE_ENTERPRISE")
    defaults.update(changes)
    return HeatInput(**defaults)


def input_with(line):
    value = fuel_input()
    value = replace(value, period=replace(value.period, start=date(2026,1,1), end=date(2026,12,31)))
    return replace(value, purchased_heat=(line,), source_states=(*value.source_states,
        EmissionSourceState(SOURCE_PURCHASED_HEAT, EmissionSourceStatus.INVOLVED)))


class HeatRuntimeTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.root = Path(self.directory.name)
        catalog = build_catalog_database(DEFAULT_SOURCE_PATH, self.root / "catalog.sqlite")
        self.resolver = create_g06_parameter_resolver(SQLiteCatalogRepository(catalog))
        self.calc = CarbonMaterialCalculator(parameter_resolver=self.resolver)
        self.records = InMemoryRecordRepository()
        self.formal = CarbonAccountingUseCase(self.calc, self.records)
        self.original_fuel = self.calc.calculate(fuel_input()).result.total_amount

    def tearDown(self):
        self.directory.cleanup()

    def test_same_resolver_selection_qualification_value_and_snapshot(self):
        verify_heat_projection()
        original = self.resolver.resolve
        contexts = []
        def resolve(context):
            contexts.append(context)
            return original(context)
        with patch.object(self.resolver, "resolve", side_effect=resolve), patch.object(self.calc, "_steam_reference", side_effect=AssertionError("known must not query auto")):
            outcome = self.formal.calculate(input_with(heat(pressure_mpa="999")))
        self.assertTrue(outcome.successful, outcome.problems)
        # Independent arithmetic: 1t * 2800kJ/kg = 2.8GJ; 2.8*.11=.308.
        heat_lines = [x for x in outcome.result.lines if x.emission_source_id == SOURCE_PURCHASED_HEAT]
        self.assertEqual([x.amount for x in heat_lines], [Decimal("0.308")])
        self.assertEqual(outcome.result.total_amount, self.calc.policy.add(self.original_fuel, Decimal("0.308")))
        heat_contexts = [x for x in contexts if x.parameter_id == "heat_emission_factor_default"]
        self.assertEqual(len(heat_contexts), 1)
        snapshots = [x for x in outcome.parameter_snapshots if x.parameter_id == "heat_emission_factor_default"]
        self.assertEqual(len(snapshots), 1)
        self.assertEqual(snapshots[0].value_used, Decimal("0.11"))
        trace = json.loads(outcome.evidence.trace_snapshot_json)
        self.assertIn("CAR-HEAT-KNOWN-017.1", json.dumps(trace))
        self.assertNotIn("STANDARD_TABLE", json.dumps(trace))

    def test_internal_already_counted_preserves_actual_fuel_without_heat_values(self):
        line = heat(amount=None, enthalpy=None, manual_enthalpy=False,
                    source_boundary="INSIDE_ENTERPRISE", fuel_emissions_accounted=True,
                    factor_mode=HeatFactorMode.MEASURED)
        with patch.object(self.calc, "_enthalpy", side_effect=AssertionError("not applicable")), patch.object(self.calc, "_heat_factor", side_effect=AssertionError("not applicable")):
            outcome = self.formal.calculate(input_with(line))
        self.assertTrue(outcome.successful, outcome.problems)
        self.assertEqual(outcome.result.total_amount, self.original_fuel)
        self.assertFalse(any(x.emission_source_id == SOURCE_PURCHASED_HEAT for x in outcome.result.lines))
        self.assertTrue(any(p.code == "CAR-VAL-HEAT-INTERNAL-ACCOUNTED" for p in outcome.problems))

    def test_unknown_or_conflicting_boundary_produces_no_record(self):
        for boundary, accounted in (("UNCONFIRMED", None), ("INSIDE_ENTERPRISE", False),
                                    ("INSIDE_ENTERPRISE", None), ("OUTSIDE_ENTERPRISE", True)):
            with self.subTest(boundary=boundary, accounted=accounted):
                result = self.formal.calculate(input_with(heat(source_boundary=boundary, fuel_emissions_accounted=accounted)))
                self.assertFalse(result.successful)
                self.assertTrue(any(p.code == "CAR-VAL-HEAT-BOUNDARY" for p in result.problems))
        self.assertEqual(len(self.records.list_all()), 0)

    def test_measured_blank_invalid_and_zero_never_fall_back(self):
        for value in (None, "-1"):
            line = heat(factor_mode=HeatFactorMode.MEASURED,
                        factor=None if value is None else parameter("heat_measured", value, "tCO2/GJ"))
            with patch.object(self.resolver, "resolve", side_effect=AssertionError("no default fallback")):
                result = self.formal.calculate(input_with(line))
            self.assertFalse(result.successful, result.problems)
        line = heat(factor_mode=HeatFactorMode.MEASURED, factor=parameter("heat_measured", "0", "tCO2/GJ"))
        with patch.object(self.resolver, "resolve", side_effect=AssertionError("no default fallback")):
            result = self.formal.calculate(input_with(line))
        self.assertTrue(result.successful, result.problems)
        self.assertEqual(result.result.total_amount, self.original_fuel)
        self.assertTrue(any(p.code == "CAR-VAL-FACTOR-SOURCE" for p in result.problems))

    def test_unverified_catalog_does_not_consume_same_numeric_value(self):
        from packages.core.parameter_resolution import ParameterResolver
        self.calc.parameter_resolver = ParameterResolver.with_default_g05_rules(self.resolver.repository)
        outcome = self.formal.calculate(input_with(heat()))
        self.assertFalse(outcome.successful)
        self.assertTrue(any(p.code == "CAR-VAL-HEAT-SOURCE-POLICY" for p in outcome.problems))
        self.assertEqual(len(self.records.list_all()), 0)

    def test_auto_no_old_table_and_known_missing_no_fallback(self):
        for line in (heat(enthalpy=None, manual_enthalpy=False, pressure_mpa="1"),
                     heat(enthalpy=None, manual_enthalpy=True, pressure_mpa="1")):
            with patch.object(self.calc, "_steam_reference", side_effect=AssertionError("no old fallback")):
                result = self.formal.calculate(input_with(line))
            self.assertFalse(result.successful)
        self.assertEqual(len(self.records.list_all()), 0)

    def test_legacy_codec_read_preserves_unknown_boundary_and_known_value(self):
        value = input_with(heat())
        document = json.loads(encode_canonical_input(value))
        def strip(value):
            if isinstance(value, dict):
                if value.get("type") == "heat_input":
                    value["fields"].pop("source_boundary")
                    value["fields"].pop("fuel_emissions_accounted")
                for child in value.values(): strip(child)
            elif isinstance(value, list):
                for child in value: strip(child)
        strip(document)
        for version in (1,2,3,4):
            document["version"] = version
            old = decode_canonical_input(json.dumps(document))
            self.assertEqual(old.purchased_heat[0].source_boundary, "UNCONFIRMED")
            self.assertEqual(old.purchased_heat[0].enthalpy.value, Decimal("2800"))
            self.assertEqual(decode_canonical_input(encode_canonical_input(old)), old)
            self.assertFalse(self.formal.calculate(old).successful)
