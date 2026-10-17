from __future__ import annotations

from dataclasses import replace
from datetime import date
import tempfile
from pathlib import Path
import unittest

from packages.application.carbon_accounting import create_g06_parameter_resolver
from packages.core.decimal_policy import DecimalPolicy
from packages.core.models import AccountingPeriod, ParameterType, PeriodType
from packages.persistence import SQLiteCatalogRepository, build_catalog_database
from packages.standards.carbon_material import (
    CarbonMaterialCalculator,
    CarbonMaterialInput,
    CarbonateComponent,
    FGDInput,
    InputOrigin,
    ParameterSourceKind,
    ParameterValue,
    STANDARD_ID,
)
from packages.standards.carbon_material_input_policy import (
    CARBONATE_C2_IDENTITIES,
    carbonate_c2_identity,
    parameter_source_policy,
    validate_parameter_source_policy,
)
from packages.standards.carbon_material_normalization import (
    MaterialDataSource,
    MaterialInputLine,
    MaterialRole,
    normalize_material_inputs,
)


class ParameterSourcePolicyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.directory = tempfile.TemporaryDirectory()
        cls.catalog = SQLiteCatalogRepository(build_catalog_database(output_path=Path(cls.directory.name) / "catalog.sqlite"))
        cls.resolver = create_g06_parameter_resolver(cls.catalog)

    @classmethod
    def tearDownClass(cls):
        cls.directory.cleanup()

    def fuel_context(self, field_id):
        from packages.standards.carbon_material_business_policy import fuel_source_context
        return fuel_source_context(field_id, resolver=self.resolver, origin=InputOrigin.CATALOG,
            subject_id="natural_gas", accounting_period=AccountingPeriod(PeriodType.ANNUAL, date(2026,1,1), date(2026,12,31)))
    def test_fuel_source_choices_are_field_and_origin_specific(self) -> None:
        catalog_fch = parameter_source_policy(
            "fuel.fch", origin=InputOrigin.CATALOG, has_resolver_binding=True,
            resolved_context=self.fuel_context("fuel.fch"),
        )
        self.assertEqual(catalog_fch.allowed_sources, ("STANDARD_DEFAULT", "MEASURED"))
        self.assertEqual(catalog_fch.default_source, "STANDARD_DEFAULT")
        self.assertTrue(catalog_fch.default_locked)
        self.assertTrue(catalog_fch.binding_required)

        custom_fch = parameter_source_policy("fuel.fch", origin=InputOrigin.CUSTOM)
        self.assertEqual(custom_fch.allowed_sources, ("MEASURED",))
        self.assertEqual(custom_fch.default_source, "MEASURED")
        self.assertFalse(custom_fch.default_locked)

        catalog_oxidation = parameter_source_policy(
            "fuel.oxidation", origin=InputOrigin.CATALOG, has_resolver_binding=True,
            resolved_context=self.fuel_context("fuel.oxidation"),
        )
        self.assertEqual(catalog_oxidation.allowed_sources, ("STANDARD_DEFAULT", "MEASURED"))
        self.assertNotIn("CALCULATED", catalog_oxidation.allowed_sources)
        self.assertEqual(catalog_oxidation.default_source, "STANDARD_DEFAULT")
        self.assertTrue(catalog_oxidation.default_locked)

        custom_oxidation = parameter_source_policy("fuel.oxidation", origin=InputOrigin.CUSTOM)
        self.assertEqual(custom_oxidation.allowed_sources, ("MEASURED",))
        self.assertEqual(custom_oxidation.default_source, "MEASURED")
        self.assertFalse(custom_oxidation.default_locked)

        direct = parameter_source_policy("fuel.direct_carbon", origin=InputOrigin.CUSTOM)
        self.assertEqual(direct.allowed_sources, ("CALCULATED", "MEASURED"))
        self.assertEqual(direct.default_source, "MEASURED")
        self.assertEqual(direct.basis, "DIRECT")

        custom_lhv = parameter_source_policy("fuel.lhv", origin=InputOrigin.CUSTOM)
        self.assertEqual(custom_lhv.allowed_sources, ("MEASURED",))
        self.assertEqual(custom_lhv.default_source, "MEASURED")

    def test_material_fields_and_fgd_fields_follow_independent_mapping(self) -> None:
        for field_id in ("material.fixed_carbon", "material.volatile_matter"):
            policy = parameter_source_policy(field_id, input_basis="RECEIVED")
            self.assertEqual(policy.allowed_sources, ("MEASURED", "CALCULATED"))
            self.assertEqual(policy.default_source, "MEASURED")
            self.assertEqual(policy.basis, "RECEIVED")

        one_component_i = parameter_source_policy(
            "fgd.ratio", origin=InputOrigin.CUSTOM,
            has_resolver_binding=True, carbonate_component_count=1,
        )
        self.assertEqual(one_component_i.allowed_sources, ("STANDARD_DEFAULT", "MEASURED"))
        self.assertEqual(one_component_i.default_source, "STANDARD_DEFAULT")
        self.assertTrue(one_component_i.default_locked)

        multiple_component_i = parameter_source_policy(
            "fgd.ratio", origin=InputOrigin.CATALOG,
            has_resolver_binding=True, carbonate_component_count=2,
        )
        self.assertEqual(multiple_component_i.allowed_sources, ("MEASURED",))
        self.assertEqual(multiple_component_i.default_source, "MEASURED")
        self.assertFalse(multiple_component_i.default_locked)

        matched_ef = parameter_source_policy("fgd.factor", has_resolver_binding=True)
        self.assertEqual(matched_ef.allowed_sources, ("STANDARD_DEFAULT",))
        self.assertTrue(matched_ef.default_locked)
        unmatched_ef = parameter_source_policy("fgd.factor", has_resolver_binding=False)
        self.assertEqual(unmatched_ef.allowed_sources, ("MEASURED",))
        self.assertIsNone(unmatched_ef.default_source)

        conversion = parameter_source_policy("fgd.conversion", has_resolver_binding=True)
        self.assertEqual(conversion.allowed_sources, ("STANDARD_DEFAULT", "MEASURED"))
        self.assertEqual(conversion.default_source, "STANDARD_DEFAULT")
        self.assertEqual(conversion.context, "GENERAL_STANDARD_PARAMETER")

        unbound_conversion = parameter_source_policy("fgd.conversion", has_resolver_binding=False)
        self.assertEqual(unbound_conversion.allowed_sources, ("MEASURED",))
        self.assertEqual(unbound_conversion.default_source, "MEASURED")
        self.assertFalse(unbound_conversion.default_locked)
        self.assertIsNotNone(validate_parameter_source_policy(
            "fgd.conversion", "STANDARD_DEFAULT",
            origin=InputOrigin.CATALOG, has_resolver_binding=False,
        ))

    def test_all_canonical_c2_species_match_explicit_subject_and_parameter_ids(self) -> None:
        expected = (
            ("CaCO3", "carbonate_caco3", "car-par-c2-caco3"),
            ("MgCO3", "carbonate_mgco3", "car-par-c2-mgco3"),
            ("Na2CO3", "carbonate_na2co3", "car-par-c2-na2co3"),
            ("NaHCO3", "carbonate_nahco3", "car-par-c2-nahco3"),
            ("FeCO3", "carbonate_feco3", "car-par-c2-feco3"),
            ("MnCO3", "carbonate_mnco3", "car-par-c2-mnco3"),
            ("BaCO3", "carbonate_baco3", "car-par-c2-baco3"),
            ("Li2CO3", "carbonate_li2co3", "car-par-c2-li2co3"),
            ("K2CO3", "carbonate_k2co3", "car-par-c2-k2co3"),
            ("SrCO3", "carbonate_srco3", "car-par-c2-srco3"),
            ("CaMg(CO3)2", "carbonate_camgco3_2", "car-par-c2-camgco3-2"),
        )
        self.assertEqual(len(CARBONATE_C2_IDENTITIES), 11)
        for label, subject_id, parameter_id in expected:
            with self.subTest(label=label):
                identity = carbonate_c2_identity(label)
                self.assertIsNotNone(identity)
                self.assertEqual((identity.subject_id, identity.parameter_id), (subject_id, parameter_id))
        normalized = carbonate_c2_identity(" CaMg(CO₃)₂ ")
        self.assertEqual(normalized.subject_id, "carbonate_camgco3_2")
        self.assertIsNone(carbonate_c2_identity("CaCO2"))
        self.assertIsNone(carbonate_c2_identity("用户自定义碳酸盐"))

    def test_legacy_carbonate_identity_requires_confirmation_even_for_measured_values(self) -> None:
        issue = validate_parameter_source_policy(
            "fgd.factor", "MEASURED", origin=InputOrigin.LEGACY_UNSPECIFIED,
        )
        self.assertIsNotNone(issue)
        self.assertEqual(issue[1], "CAR-VAL-CARBONATE-IDENTITY-REQUIRED")

    def test_legacy_and_unsupported_sources_are_rejected_by_policy_validator(self) -> None:
        self.assertIsNone(validate_parameter_source_policy(
            "fgd.factor", "STANDARD_SPECIFIED", origin=InputOrigin.CATALOG, has_resolver_binding=True,
        ))
        issue = validate_parameter_source_policy(
            "fgd.factor", "CALCULATED", origin=InputOrigin.CATALOG, has_resolver_binding=True,
        )
        self.assertIsNotNone(issue)
        self.assertEqual(issue[1], "CAR-VAL-CARBONATE-FACTOR-SOURCE")
        multi_default = validate_parameter_source_policy(
            "fgd.ratio", "STANDARD_DEFAULT", origin=InputOrigin.CATALOG,
            has_resolver_binding=True, carbonate_component_count=2,
        )
        self.assertIsNotNone(multi_default)
        self.assertEqual(multi_default[1], "CAR-VAL-PARAMETER-SOURCE-INAPPLICABLE")
        legacy_user = validate_parameter_source_policy(
            "fuel.fch", "USER_DEFINED", origin=InputOrigin.CUSTOM,
        )
        self.assertIsNotNone(legacy_user)
        self.assertEqual(legacy_user[1], "CAR-VAL-PARAMETER-SOURCE-INAPPLICABLE")

    def test_process_material_source_must_be_measured(self) -> None:
        line = MaterialInputLine(
            line_id="source-policy-material",
            role=MaterialRole.CALCINATION_FEED,
            name="原料",
            mass_t=1,
            fixed_carbon_percent=80,
            fixed_carbon_source=MaterialDataSource.CHEMICAL_CALCULATION,
            volatile_matter_percent=2,
            volatile_matter_source=MaterialDataSource.MEASURED,
        )
        normalized = normalize_material_inputs("calcination", (line,), policy=DecimalPolicy())
        self.assertIn("CAR-VAL-MATERIAL-SOURCE-INAPPLICABLE", {item.code for item in normalized.problems})

    def test_only_registered_field_ids_are_accepted(self) -> None:
        for field_id in (
            "fuel.direct_carbon", "fuel.lhv", "fuel.fch", "fuel.oxidation",
            "material.fixed_carbon", "material.volatile_matter",
            "fgd.ratio", "fgd.factor", "fgd.conversion",
        ):
            self.assertEqual(parameter_source_policy(field_id).field_id, field_id)
        with self.assertRaises(ValueError):
            parameter_source_policy("fuel.unregistered")


class CanonicalC2BindingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._temporary_directory = tempfile.TemporaryDirectory()
        catalog_path = Path(cls._temporary_directory.name) / "catalog.sqlite"
        build_catalog_database(output_path=catalog_path)
        cls.repository = SQLiteCatalogRepository(catalog_path)
        cls.resolver = create_g06_parameter_resolver(cls.repository)
        cls.calculator = CarbonMaterialCalculator(parameter_resolver=cls.resolver)
        cls.period = AccountingPeriod(PeriodType.ANNUAL, date(2025, 1, 1), date(2025, 12, 31))

    @classmethod
    def tearDownClass(cls) -> None:
        cls._temporary_directory.cleanup()

    def test_domain_resolves_registered_c2_source_for_all_eleven_identities(self) -> None:
        for identity in CARBONATE_C2_IDENTITIES:
            with self.subTest(subject_id=identity.subject_id):
                component = CarbonateComponent(
                    "1", "0.9", "0.44", "1", identity.label, InputOrigin.CATALOG,
                )
                factor = self.calculator._carbonate_default_binding(component, self.period)
                self.assertIsNotNone(factor)
                self.assertEqual(factor.parameter_id, identity.parameter_id)
                self.assertEqual(factor.subject_id, identity.subject_id)
                self.assertEqual(factor.value_type.value, "STANDARD_SPECIFIED")
                self.assertEqual(factor.source_id, "SRC-32151-34-2024")
                self.assertIn("附录C表C.2", factor.source_location)
                parameter = self.resolver.repository.get_parameter(identity.parameter_id)
                self.assertIsNotNone(parameter)
                self.assertEqual(parameter.subject_id, identity.subject_id)
                self.assertIs(parameter.parameter_type, ParameterType.PROCESS_CO2_FACTOR)

    def test_c2_identity_never_reclassifies_custom_or_unconfirmed_component(self) -> None:
        for origin in (InputOrigin.CUSTOM, None):
            with self.subTest(origin=origin):
                component = CarbonateComponent("1", "0.9", "0.44", "1", "CaCO3", origin)
                self.assertIsNone(self.calculator._carbonate_default_binding(component, self.period))

    def test_fgd_catalog_metadata_must_match_resolver_factor_and_locate_the_component(self) -> None:
        def selected_value(parameter_id: str, subject_id: str, parameter_type: ParameterType,
                           source_kind: ParameterSourceKind) -> ParameterValue:
            factor = self.calculator._resolved_source_factor(
                parameter_id, subject_id, parameter_type, self.period,
            )
            self.assertIsNotNone(factor)
            assert factor is not None
            return ParameterValue(
                factor.parameter_id, factor.value, factor.unit, source_kind,
                factor.source_id, factor.version, factor.source_location,
                "采用当前期间Resolver核验的标准参数。",
                factor.factor_id, factor.factor_year,
            )

        standard_values = {
            "fgd.ratio": selected_value(
                "car-par-p04b-i", "fgd", ParameterType.PROCESS_DEFAULT_PARAMETER,
                ParameterSourceKind.STANDARD_DEFAULT,
            ),
            "fgd.factor": selected_value(
                "car-par-c2-caco3", "carbonate_caco3", ParameterType.PROCESS_CO2_FACTOR,
                ParameterSourceKind.STANDARD_SPECIFIED,
            ),
            "fgd.conversion": selected_value(
                "car-par-p04b-tr", "fgd", ParameterType.PROCESS_DEFAULT_PARAMETER,
                ParameterSourceKind.STANDARD_DEFAULT,
            ),
        }
        mutations = (
            ("source_id", "SRC-FAKE"),
            ("source_version", "fake-edition"),
            ("source_location", "其他来源"),
            ("factor_year", 2099),
            ("source_kind", ParameterSourceKind.MEASURED),
        )
        suffixes = {"fgd.ratio": "I", "fgd.factor": "EF1", "fgd.conversion": "TR"}
        for policy_field, suffix in suffixes.items():
            for metadata_field, fake_value in mutations:
                with self.subTest(field=policy_field, metadata=metadata_field):
                    values = dict(standard_values)
                    values[policy_field] = replace(values[policy_field], **{metadata_field: fake_value})
                    component = CarbonateComponent(
                        "1", values["fgd.ratio"], values["fgd.factor"], values["fgd.conversion"],
                        "CaCO3", InputOrigin.CATALOG,
                    )
                    outcome = self.calculator.calculate(CarbonMaterialInput(
                        f"input.fake-metadata.{policy_field}.{metadata_field}",
                        "enterprise.policy", None, self.period,
                        boundary_confirmed=True,
                        fgd=FGDInput(components=(component,), instance_id="metadata-check"),
                    ))
                    self.assertTrue(outcome.blocked, outcome.problems)
                    self.assertIsNone(outcome.record)
                    expected_code = (
                        "CAR-VAL-CARBONATE-FACTOR-SOURCE"
                        if policy_field == "fgd.factor" and metadata_field == "source_kind"
                        else "CAR-VAL-PARAMETER-BINDING-MISMATCH"
                    )
                    mismatch = next(
                        problem for problem in outcome.problems
                        if problem.code == expected_code
                    )
                    self.assertEqual(
                        mismatch.field_id,
                        f"CAR-FLD-P04B-metadata-check-0-{suffix}",
                    )

    def test_domain_blocks_unsupported_fgd_sources_without_catalog_bindings(self) -> None:
        cases = (
            ("ratio", ParameterSourceKind.CALCULATED, "CAR-VAL-PARAMETER-SOURCE-INAPPLICABLE"),
            ("factor", ParameterSourceKind.USER_DEFINED, "CAR-VAL-CARBONATE-FACTOR-SOURCE"),
            ("conversion", ParameterSourceKind.CALCULATED, "CAR-VAL-PARAMETER-SOURCE-INAPPLICABLE"),
        )
        for field_name, source_kind, expected_code in cases:
            with self.subTest(field=field_name, source_kind=source_kind):
                ratio = ParameterValue(
                    "test.fgd.i", "0.9", "ratio", ParameterSourceKind.MEASURED,
                    source_id=None, source_version=None, source_location="test",
                )
                factor = ParameterValue(
                    "test.fgd.ef", "0.44", "tCO2/t", ParameterSourceKind.MEASURED,
                    source_id=None, source_version=None, source_location="test",
                )
                conversion = ParameterValue(
                    "test.fgd.tr", "1", "ratio", ParameterSourceKind.MEASURED,
                    source_id=None, source_version=None, source_location="test",
                )
                replacement = ParameterValue(
                    f"unsupported.fgd.{field_name}", "0.9" if field_name == "ratio" else "0.44" if field_name == "factor" else "1",
                    "tCO2/t" if field_name == "factor" else "ratio",
                    source_kind, source_id=None, source_version=None, source_location="legacy test source",
                )
                if field_name == "ratio":
                    ratio = replacement
                elif field_name == "factor":
                    factor = replacement
                else:
                    conversion = replacement
                component = CarbonateComponent(
                    "1", ratio, factor, conversion, "CaCO3", InputOrigin.CUSTOM,
                )
                outcome = CarbonMaterialCalculator().calculate(CarbonMaterialInput(
                    f"input.unsupported.{field_name}", "enterprise.policy", None, self.period,
                    boundary_confirmed=True, fgd=FGDInput(components=(component,)),
                ))
                self.assertTrue(outcome.blocked, outcome.problems)
                self.assertIn(expected_code, {problem.code for problem in outcome.problems})
                self.assertIsNone(outcome.record)


if __name__ == "__main__":
    unittest.main()
