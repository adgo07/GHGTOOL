"""Material-only independent expectations for SM01-006 / Issues016 and018.

Dry conversion uses the Owner-approved water/received-mass denominator and
mass conservation, not a claimed formula quoted from the standard. Equation
expectations below are from Mapping TV-CAR-POL-014/016, not the Calculator.
"""
from dataclasses import replace
from datetime import date
from pathlib import Path
import tempfile
from decimal import Decimal, ROUND_DOWN, ROUND_HALF_UP, localcontext
import unittest
from unittest.mock import patch

from packages.core.decimal_policy import DecimalPolicy
from packages.standards.carbon_material_normalization import (
    MaterialDataSource as Source, MaterialInputLine as Line, MaterialRole as Role,
    normalize_material_inputs,
)


def line(identity, role, mass, carbon=None, volatile=None, **kwargs):
    return Line(identity, role, "同名物料", mass, carbon,
                kwargs.pop("fixed_carbon_source", Source.MEASURED), volatile,
                kwargs.pop("volatile_matter_source", Source.MEASURED), **kwargs)


def rows(*, cc="20", ucc="30", du="10", carbon=("80", "40", "25")):
    return (
        line("feed", Role.CALCINATION_FEED, "100", "90", "10"),
        line("cc", Role.CALCINED_PRODUCT, cc, carbon[0], "5"),
        line("ucc", Role.UNDERBURN_RECOVERED, ucc, carbon[1]),
        line("du", Role.CARBON_DUST, du, carbon[2]),
    )


class MaterialRoleNormalizationTests(unittest.TestCase):
    def normalize(self, inputs, process="calcination", policy=None):
        return normalize_material_inputs(process, inputs, policy=policy or DecimalPolicy())

    def test_different_output_roles_keep_actual_carbon_masses(self):
        result = self.normalize(rows())
        self.assertFalse(result.problems)
        values = dict(result.values)
        self.assertEqual([values[f"output_carbon_{role}"] for role in ("cc", "ucc", "du")],
                         list(map(Decimal, ("16", "12", "2.5"))))
        self.assertEqual(values["output_carbon_total"], Decimal("30.5"))
        self.assertEqual([values[f"wfc_c_{role}"] for role in ("cc", "ucc", "du")],
                         list(map(Decimal, (".8", ".4", ".25"))))
        with localcontext() as context:
            context.prec = 40
            context.rounding = ROUND_HALF_UP
            # Independent original equation expansion using the adopted term.
            emission = (Decimal("90") - values["output_carbon_total"]) * 44 / 12
            emission += (Decimal("10") - Decimal("1")) * Decimal(".35") * 44 / 16
        self.assertEqual(emission, Decimal("226.8291666666666666666666666666666666667"))

    def test_equal_contents_reduce_to_grouped_original(self):
        values = dict(self.normalize(rows(carbon=("80", "80", "80"))).values)
        self.assertEqual(values["output_carbon_total"], Decimal("48"))
        self.assertEqual(values["output_carbon_total"], Decimal("60") * Decimal(".8"))
        with localcontext() as context:
            context.prec = 40
            emission = (Decimal("90") - values["output_carbon_total"]) * 44 / 12
            emission += Decimal("9") * Decimal(".35") * 44 / 16
        self.assertEqual(emission, Decimal("162.6625"))

    def test_zero_cc_does_not_borrow_or_drop_ucc_content(self):
        inputs = (line("feed", Role.CALCINATION_FEED, "10", "90", "0"),
                  line("cc", Role.CALCINED_PRODUCT, "0"),
                  line("ucc", Role.UNDERBURN_RECOVERED, "5", "80"))
        result = self.normalize(inputs)
        self.assertFalse(result.problems)
        self.assertEqual(result.value("output_carbon_total"), Decimal("4"))
        self.assertEqual(result.value("wfc_c_cc"), Decimal("0"))
        with localcontext() as context:
            context.prec = 40
            self.assertEqual((Decimal("9") - result.value("output_carbon_total")) * 44 / 12,
                             Decimal("18.33333333333333333333333333333333333333"))

    def test_nonzero_role_missing_content_blocks_even_other_role_has_value(self):
        inputs = rows(carbon=("80", None, "25"))
        result = self.normalize(inputs)
        self.assertIn("ucc.fixed_carbon", {p.field_id for p in result.problems})
        self.assertIn("CAR-VAL-MATERIAL-COMPONENT-MISSING", {p.code for p in result.problems})

    def test_same_role_rows_weight_by_mass_and_do_not_leak_across_roles(self):
        inputs = rows() + (line("ucc-second", Role.UNDERBURN_RECOVERED, "10", "80"),)
        result = self.normalize(inputs)
        self.assertFalse(result.problems)
        self.assertEqual(result.value("wfc_c_ucc"), Decimal(".5"))
        self.assertEqual(result.value("output_carbon_ucc"), Decimal("20"))
        self.assertEqual(result.value("output_carbon_cc"), Decimal("16"))

    def test_same_names_and_line_ids_in_separate_instances_do_not_share_state(self):
        first = self.normalize(rows())
        second = self.normalize(rows(carbon=("10", "20", "30")))
        again = self.normalize(rows())
        self.assertEqual(first, again)
        self.assertEqual(second.value("output_carbon_total"), Decimal("11"))
        self.assertEqual(first.value("output_carbon_total"), Decimal("30.5"))

    def test_absent_blank_and_explicit_zero_are_distinct(self):
        zero = (line("feed", Role.CALCINATION_FEED, "0"), line("cc", Role.CALCINED_PRODUCT, "0"))
        self.assertFalse(self.normalize(zero).problems)
        self.assertEqual(self.normalize(zero).value("output_carbon_total"), Decimal("0"))
        missing = self.normalize((replace(zero[0], mass_t=""), zero[1]))
        self.assertTrue(missing.problems)
        self.assertFalse(self.normalize(zero + (Line("blank", Role.CARBON_DUST, "", None),)).problems)


class ReceivedBasisConversionTests(unittest.TestCase):
    def normalize(self, inputs, process="calcination", policy=None):
        return normalize_material_inputs(process, inputs, policy=policy or DecimalPolicy())

    def dry_feed(self, **kwargs):
        defaults = dict(mass_basis="DRY", composition_basis="DRY", moisture_received_percent="20",
                        conversion_method="DRY_TO_RECEIVED_MOISTURE",
                        fixed_carbon_source=Source.CHEMICAL_CALCULATION,
                        volatile_matter_source=Source.CHEMICAL_CALCULATION)
        defaults.update(kwargs)
        return line("feed", Role.CALCINATION_FEED, "80", "90", "10", **defaults)

    def inputs(self, feed):
        return (feed, line("cc", Role.CALCINED_PRODUCT, "0"))

    def test_dry_mass_and_composition_use_received_water_denominator_once(self):
        feed = self.dry_feed()
        result = self.normalize(self.inputs(feed))
        self.assertFalse(result.problems)
        self.assertEqual(result.value("gc"), Decimal("100"))
        self.assertEqual(result.value("wfc"), Decimal(".72"))
        self.assertEqual(result.value("wvar"), Decimal(".08"))
        self.assertEqual(result.included_lines[0], feed)
        adopted = result.normalized_lines[0]
        self.assertEqual((adopted.line_id, adopted.role, adopted.name), (feed.line_id, feed.role, feed.name))
        self.assertEqual((adopted.mass_t, adopted.fixed_carbon_percent, adopted.volatile_matter_percent),
                         tuple(map(Decimal, ("100", "72", "8"))))
        self.assertEqual((adopted.mass_basis, adopted.composition_basis), ("RECEIVED", "RECEIVED"))
        self.assertIs(adopted.fixed_carbon_source, Source.CHEMICAL_CALCULATION)
        self.assertEqual(self.normalize(self.inputs(feed)), result)

    def test_received_mass_with_dry_composition_only_converts_composition(self):
        result = self.normalize(self.inputs(replace(self.dry_feed(), mass_t="100", mass_basis="RECEIVED")))
        self.assertFalse(result.problems)
        self.assertEqual((result.value("gc"), result.value("wfc")), (Decimal("100"), Decimal(".72")))

    def test_dry_mass_with_received_measured_composition_only_converts_mass(self):
        feed = self.dry_feed(composition_basis="RECEIVED", fixed_carbon_source=Source.MEASURED,
                             volatile_matter_source=Source.MEASURED)
        result = self.normalize(self.inputs(feed))
        self.assertFalse(result.problems)
        self.assertEqual((result.value("gc"), result.value("wfc")), (Decimal("100"), Decimal(".9")))

    def test_calculated_received_value_cannot_pass_with_mass_only_conversion(self):
        result = self.normalize(self.inputs(self.dry_feed(composition_basis="RECEIVED")))
        self.assertIn("CAR-VAL-MATERIAL-SOURCE-INAPPLICABLE", {p.code for p in result.problems})

    def test_measured_received_value_needs_no_method_or_attachment(self):
        result = self.normalize(self.inputs(line("feed", Role.CALCINATION_FEED, "100", "72", "8")))
        self.assertFalse(result.problems)

    def test_selected_calculation_without_definition_is_not_measured(self):
        feed = line("feed", Role.CALCINATION_FEED, "100", "72", "8", fixed_carbon_source=Source.CHEMICAL_CALCULATION)
        self.assertIn("CAR-VAL-MATERIAL-SOURCE-INAPPLICABLE", {p.code for p in self.normalize(self.inputs(feed)).problems})

    def test_missing_or_unknown_conversion_method_blocks(self):
        for method in (None, "", "ANY", "AIR_DRY_TO_RECEIVED"):
            with self.subTest(method=method):
                result = self.normalize(self.inputs(self.dry_feed(conversion_method=method)))
                self.assertIn("CAR-VAL-MATERIAL-BASIS-CONVERSION", {p.code for p in result.problems})

    def test_invalid_or_missing_moisture_blocks_but_zero_is_real(self):
        for moisture in (None, "", "-1", "100", "101", "NaN", True, .2):
            with self.subTest(moisture=moisture):
                self.assertTrue(self.normalize(self.inputs(self.dry_feed(moisture_received_percent=moisture))).problems)
        result = self.normalize(self.inputs(self.dry_feed(moisture_received_percent="0")))
        self.assertFalse(result.problems)
        self.assertEqual((result.value("gc"), result.value("wfc")), (Decimal("80"), Decimal(".9")))

    def test_moisture_below_100_does_not_round_to_zero_dry_fraction(self):
        result = self.normalize(self.inputs(self.dry_feed(moisture_received_percent="99." + "9" * 50)))
        self.assertFalse(result.problems)
        self.assertGreater(result.value("gc"), Decimal("80"))
        self.assertGreater(result.value("wfc"), Decimal("0"))

    def test_other_or_unknown_bases_are_not_guessed(self):
        for basis in ("UNKNOWN", "OTHER_DOCUMENTED", "AIR_DRY", "DRY_ASH_FREE"):
            with self.subTest(basis=basis):
                result = self.normalize(self.inputs(self.dry_feed(composition_basis=basis)))
                self.assertIn("CAR-VAL-MATERIAL-BASIS-CONSISTENCY", {p.code for p in result.problems})

    def test_percent_and_ratio_inputs_have_identical_adopted_values(self):
        percent = self.normalize(self.inputs(self.dry_feed()))
        ratio_feed = replace(self.dry_feed(), fixed_carbon_percent=".9", volatile_matter_percent=".1",
                             fixed_carbon_unit="ratio", volatile_matter_unit="ratio")
        ratio = self.normalize(self.inputs(ratio_feed))
        self.assertEqual(percent.values, ratio.values)
        self.assertEqual(percent.normalized_lines, ratio.normalized_lines)

    def test_float_bool_nonfinite_and_incompatible_units_are_rejected(self):
        for value in (.9, True, "NaN", "Infinity", "-1", "101"):
            with self.subTest(value=value):
                feed = line("feed", Role.CALCINATION_FEED, "100", value, "0")
                self.assertTrue(self.normalize(self.inputs(feed)).problems)
        for mass in (1.0, True, "NaN"):
            self.assertTrue(self.normalize(self.inputs(replace(self.dry_feed(), mass_t=mass))).problems)
        for unit in ("kg", "fraction", "", None):
            self.assertTrue(self.normalize(self.inputs(self.dry_feed(fixed_carbon_unit=unit))).problems)

    def test_no_catalogue_default_is_invented(self):
        feed = line("feed", Role.CALCINATION_FEED, "100", "72", "8", fixed_carbon_source=Source.STANDARD_DEFAULT)
        self.assertIn("CAR-VAL-MATERIAL-SOURCE-INAPPLICABLE", {p.code for p in self.normalize(self.inputs(feed)).problems})

    def test_dry_measured_original_cannot_be_labelled_received_measured(self):
        feed = self.dry_feed(fixed_carbon_source=Source.MEASURED)
        result = self.normalize(self.inputs(feed))
        self.assertIn("CAR-VAL-MATERIAL-SOURCE-INAPPLICABLE", {p.code for p in result.problems})

    def test_shared_qualification_failure_is_not_bypassed_by_local_source(self):
        with patch("packages.standards.carbon_material_normalization.evaluate_material_field",
                   return_value={"status": "BLOCKED", "source_qualification": {"value": {"state": "NO_LEGAL_SOURCES"}}}):
            result = self.normalize(self.inputs(line("feed", Role.CALCINATION_FEED, "100", "72", "8")))
        self.assertIn("CAR-VAL-MATERIAL-SOURCE-INAPPLICABLE", {p.code for p in result.problems})

    def test_missing_shared_resource_blocks_without_falling_back(self):
        from packages.standards.carbon_material_business_policy import BusinessPolicyConfigurationError
        with patch("packages.standards.carbon_material_normalization.evaluate_material_field",
                   side_effect=BusinessPolicyConfigurationError("missing material resource")):
            result = self.normalize(self.inputs(line("feed", Role.CALCINATION_FEED, "100", "72", "8")))
        self.assertIn("CAR-VAL-MATERIAL-POLICY-CONFIGURATION", {p.code for p in result.problems})

    def test_actual_sqlite_reopen_preserves_raw_inputs_and_draft_without_normalizing_on_open(self):
        from packages.application.canonical_input_codec import decode_canonical_input, encode_canonical_input
        from packages.application.project_workspaces import AccountingUnitType, AccountingUnitWorkspace, ProjectWorkspace
        from packages.core import AccountingPeriod, PeriodType
        from packages.persistence.projects_repository import SQLiteProjectWorkspaceRepository
        from packages.standards.carbon_material import CarbonMaterialInput, CalcinationInput
        raw_rows = self.inputs(self.dry_feed())
        domain = CarbonMaterialInput(
            input_id="material-reopen", enterprise_id="material-test", enterprise_name="材料测试",
            period=AccountingPeriod(PeriodType.ANNUAL, date(2025, 1, 1), date(2025, 12, 31)),
            boundary_confirmed=True, calcination=CalcinationInput(k1=".35", material_rows=raw_rows),
        )
        draft = replace(domain, input_id="material-draft", calcinations=(), calcination=replace(
            domain.calcination, material_rows=self.inputs(self.dry_feed(conversion_method=None))))
        units = tuple(AccountingUnitWorkspace(
            value.input_id, "同名单元", AccountingUnitType.PROCESS, index, {}, canonical_input=value,
        ) for index, value in enumerate((domain, draft)))
        workspace = ProjectWorkspace("material-project", "材料", domain.input_id, units)
        with tempfile.TemporaryDirectory(prefix="ghg-material-M-") as temporary:
            path = Path(temporary) / "projects.sqlite"
            repository = SQLiteProjectWorkspaceRepository(path)
            repository.save(workspace)
            reopened = SQLiteProjectWorkspaceRepository(path).get(workspace.project_id)
            self.assertEqual(reopened, workspace)
            for unit in reopened.units:
                restored = decode_canonical_input(encode_canonical_input(unit.canonical_input))
                self.assertEqual(restored, unit.canonical_input)
            adopted = self.normalize(reopened.units[0].canonical_input.calcination.material_rows)
            self.assertEqual(adopted.value("gc"), Decimal("100"))
            self.assertEqual(adopted.included_lines[0].mass_t, "80")
            incomplete = self.normalize(reopened.units[1].canonical_input.calcination.material_rows)
            self.assertTrue(incomplete.problems)
            self.assertIsNone(reopened.units[1].canonical_input.calcination.material_rows[0].conversion_method)

    def test_received_values_cannot_be_converted_again(self):
        feed = line("feed", Role.CALCINATION_FEED, "100", "72", "8", conversion_method="DRY_TO_RECEIVED_MOISTURE")
        self.assertIn("CAR-VAL-MATERIAL-BASIS-CONVERSION", {p.code for p in self.normalize(self.inputs(feed)).problems})

    def test_policy_is_propagated_and_ambient_context_is_irrelevant(self):
        feed = replace(self.dry_feed(), moisture_received_percent="17.12345678901234567890123456789")
        inputs = self.inputs(feed)
        with localcontext() as context:
            context.prec = 6
            context.rounding = ROUND_DOWN
            low_ambient = self.normalize(inputs, policy=DecimalPolicy(precision=50))
        with localcontext() as context:
            context.prec = 70
            high_ambient = self.normalize(inputs, policy=DecimalPolicy(precision=50))
        self.assertEqual(low_ambient, high_ambient)
        self.assertNotEqual(low_ambient.value("gc"), self.normalize(inputs).value("gc"))

    def test_baking_and_graphitization_share_conversion_without_formula_changes(self):
        for process, role, product, mass_key, carbon_key in (
            ("baking", Role.GREEN_BAKING_PRODUCT, Role.BAKED_PRODUCT, "bg", "bgfc"),
            ("graphitization", Role.GREEN_GRAPHITIZATION_PRODUCT, Role.GRAPHITIZED_PRODUCT, "gta", "gtafc"),
        ):
            with self.subTest(process=process):
                feed = replace(self.dry_feed(), role=role)
                result = self.normalize((feed, line("product", product, "0")), process)
                self.assertFalse(result.problems)
                self.assertEqual((result.value(mass_key), result.value(carbon_key)), (Decimal("100"), Decimal(".72")))


if __name__ == "__main__":
    unittest.main()
