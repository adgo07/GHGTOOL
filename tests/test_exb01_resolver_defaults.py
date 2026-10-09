"""Verified process-clause defaults remain selected by the formal Resolver."""
from dataclasses import replace
from datetime import date
from decimal import Decimal
from pathlib import Path
import tempfile
import unittest

from packages.application.carbon_accounting import create_g06_parameter_resolver, _catalog_parameter_rules
from packages.core.models import AccountingPeriod, PeriodType
from packages.core.parameter_resolution import ParameterResolutionContext
from packages.persistence import build_catalog_database
from packages.persistence.catalog_repository import SQLiteCatalogRepository
from packages.reference_data import DEFAULT_SOURCE_PATH
from packages.standards.carbon_material import STANDARD_ID


class AppendixBResolverDefaultsTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        path = build_catalog_database(DEFAULT_SOURCE_PATH, Path(self.directory.name) / "catalog.sqlite")
        self.repository = SQLiteCatalogRepository(path)

    def test_each_verified_process_clause_has_unique_formal_default(self):
        resolver = create_g06_parameter_resolver(self.repository)
        parameters = {p.parameter_id: p for p in self.repository.list_parameters()}
        for parameter_id, expected in {
            "car-par-k1": "0.35", "car-par-k2": "0.35", "car-par-k3": "0.35",
            "car-par-p04b-i": "0.90", "car-par-p04b-tr": "1",
        }.items():
            with self.subTest(parameter=parameter_id):
                parameter = parameters[parameter_id]
                result = resolver.resolve(ParameterResolutionContext(
                    parameter_id=parameter_id, standard_id=STANDARD_ID,
                    accounting_period=AccountingPeriod(PeriodType.ANNUAL, date(2025, 1, 1), date(2025, 12, 31)),
                    subject_id=parameter.subject_id, parameter_type=parameter.parameter_type,
                ))
                self.assertFalse(result.blocked, result.warnings)
                self.assertIsNotNone(result.recommended, result.warnings)
                self.assertEqual(result.recommended.factor.value, Decimal(expected))
                self.assertEqual(result.recommended.factor.source_id, "SRC-32151-34-2024")

    def test_unverified_process_bindings_cannot_create_default_rules(self):
        from packages.core.models import ReviewStatus
        repository = self.repository
        bindings = tuple(repository.list_reference_data_bindings())
        class UnverifiedBindings:
            def __getattr__(self, name):
                return getattr(repository, name)
            def list_reference_data_bindings(self):
                return tuple(replace(binding, review_status=ReviewStatus.PENDING_SOURCE)
                    if "methane_conversion_factor" in binding.binding_id else binding
                    for binding in bindings)
        rules = _catalog_parameter_rules(UnverifiedBindings())
        self.assertFalse(any(rule.parameter_id in {"car-par-k1", "car-par-k2", "car-par-k3"} for rule in rules))

