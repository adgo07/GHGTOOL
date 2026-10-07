from __future__ import annotations

from dataclasses import replace
from datetime import date, datetime, timezone
from decimal import Decimal, localcontext
import unittest

from packages.core import AccountingPeriod, PeriodType
from packages.core.decimal_policy import DecimalPolicy
from packages.application.carbon_accounting import CarbonAccountingUseCase
from packages.persistence.in_memory_records import InMemoryRecordRepository
from packages.standards.carbon_material import (
    BakingInput,
    ALGORITHM_VERSION,
    CalcinationInput,
    CarbonMaterialCalculator,
    CarbonMaterialInput,
    GraphitizationInput,
    HeatFactorMode,
    HeatInput,
    InputValue,
    ParameterSourceKind,
    ParameterValue,
    SteamKind,
    saturated_steam_enthalpy,
    superheated_steam_enthalpy,
)
from packages.standards.carbon_material_normalization import (
    MaterialDataSource,
    MaterialInputLine,
    MaterialRole,
    normalize_material_inputs,
)


PERIOD = AccountingPeriod(PeriodType.ANNUAL, date(2025, 1, 1), date(2025, 12, 31))
CALCULATED_AT = datetime(2026, 10, 5, 8, 0, tzinfo=timezone.utc)


def _line(
    line_id: str,
    role: MaterialRole,
    name: str,
    mass: str,
    fixed_carbon: str | None,
    volatile: str | None,
) -> MaterialInputLine:
    return MaterialInputLine(
        line_id,
        role,
        name,
        mass,
        fixed_carbon,
        MaterialDataSource.MEASURED,
        volatile,
        MaterialDataSource.MEASURED,
    )


def _input(**kwargs: object) -> CarbonMaterialInput:
    return CarbonMaterialInput(
        input_id=kwargs.pop("input_id", "uat01b.test"),
        enterprise_id="enterprise.uat01b",
        enterprise_name=None,
        period=PERIOD,
        boundary_confirmed=True,
        **kwargs,
    )


def _factor(value: str = "0.11") -> ParameterValue:
    return ParameterValue(
        "heat_emission_factor_measured",
        value,
        "tCO2/GJ",
        ParameterSourceKind.MEASURED,
        source_id="UAT-LAB",
        source_version="2026-10",
        source_location="UAT 实测资料",
        selection_reason="UAT 测试实测值",
    )


class UAT01BMaterialNormalizationTests(unittest.TestCase):
    def test_all_three_process_equations_use_multi_material_aggregates(self) -> None:
        calcination_rows = (
            _line("feed-a", MaterialRole.CALCINATION_FEED, "原料甲", "100", "95", "10"),
            _line("feed-b", MaterialRole.CALCINATION_FEED, "原料乙", "200", "75", "5"),
            _line("product-a", MaterialRole.CALCINED_PRODUCT, "煅后料甲", "250", "80", "2"),
            _line("underburn-a", MaterialRole.UNDERBURN_RECOVERED, "欠烧煅料", "20", "50", None),
            _line("dust-a", MaterialRole.CARBON_DUST, "碳粉尘", "10", "25", None),
        )
        baking_rows = (
            _line("filler-a", MaterialRole.BAKING_FILLER, "填充料甲", "20", "90", "1"),
            _line("green-a", MaterialRole.GREEN_BAKING_PRODUCT, "待焙烧品甲", "100", "80", "2"),
            _line("green-b", MaterialRole.GREEN_BAKING_PRODUCT, "待焙烧品乙", "50", "60", "4"),
            _line("baked-a", MaterialRole.BAKED_PRODUCT, "焙烧产品", "100", "98", None),
            _line("byproduct-a", MaterialRole.BAKING_BYPRODUCT, "粉尘", "4", "50", None),
            _line("byproduct-b", MaterialRole.BAKING_BYPRODUCT, "碎屑", "1", "30", None),
        )
        graphitization_rows = (
            _line("packing-a", MaterialRole.GRAPHITIZATION_PACKING, "保温料", "15", "75", "1"),
            _line("green-a", MaterialRole.GREEN_GRAPHITIZATION_PRODUCT, "待石墨化品甲", "80", "80", None),
            _line("green-b", MaterialRole.GREEN_GRAPHITIZATION_PRODUCT, "待石墨化品乙", "40", "60", None),
            _line("graphitized-a", MaterialRole.GRAPHITIZED_PRODUCT, "石墨化产品", "90", "90", None),
            _line("dust-a", MaterialRole.GRAPHITIZATION_BYPRODUCT, "粉尘", "3", "50", None),
            _line("residue-a", MaterialRole.GRAPHITIZATION_BYPRODUCT, "残块", "2", "25", None),
        )
        calc = normalize_material_inputs("calcination", calcination_rows, policy=DecimalPolicy())
        bake = normalize_material_inputs("baking", baking_rows, policy=DecimalPolicy())
        graph = normalize_material_inputs("graphitization", graphitization_rows, policy=DecimalPolicy())
        self.assertFalse(calc.problems, calc.problems)
        self.assertFalse(bake.problems, bake.problems)
        self.assertFalse(graph.problems, graph.problems)
        cv, bv, gv = dict(calc.values), dict(bake.values), dict(graph.values)
        self.assertEqual((cv["gc"], cv["cc"], cv["ucc"], cv["du"]), tuple(map(Decimal, ("300", "250", "20", "10"))))
        self.assertEqual(cv["wfc"], Decimal("0.8166666666666666666666666666666666666667"))
        self.assertEqual(cv["wfc_c"], Decimal("0.7589285714285714285714285714285714285714"))
        self.assertEqual(cv["wvar"], Decimal("0.06666666666666666666666666666666666666667"))
        self.assertEqual(cv["wvar_c"], Decimal("0.02"))
        self.assertEqual(bv["bwt"], Decimal("2.3"))
        self.assertEqual(bv["bgfc"], Decimal("0.7333333333333333333333333333333333333333"))
        self.assertEqual(gv["gwt"], Decimal("2.00"))
        self.assertEqual(gv["gtafc"], Decimal("0.7333333333333333333333333333333333333333"))

        calculator = CarbonMaterialCalculator()
        outcome = calculator.calculate(
            _input(
                calcination=CalcinationInput(k1="0.35", material_rows=calcination_rows),
                baking=BakingInput(k2="0.35", material_rows=baking_rows),
                graphitization=GraphitizationInput(k3="0.35", material_rows=graphitization_rows),
            ),
            calculated_at=CALCULATED_AT,
        )
        self.assertTrue(outcome.successful, outcome.problems)
        calcination_trace = next(item for item in outcome.traces if item.formula_id == "CAR-FML-CALCINATION-001")
        self.assertIn(("material.normalization_version", "CAR-MATERIAL-NORMALIZATION-V1"), calcination_trace.provenance)
        result_by_source = {
            line.emission_source_id: line.amount
            for line in outcome.result.lines
            if line.line_id.startswith(("CAR-FLD-P01-RESULT", "CAR-FLD-P02-RESULT", "CAR-FLD-P03-RESULT"))
        }
        with localcontext() as context:
            context.prec = 40
            expected_calc = (cv["gc"] * cv["wfc"] - (cv["cc"] + cv["ucc"] + cv["du"]) * cv["wfc_c"]) * Decimal(44) / Decimal(12)
            expected_calc += (cv["gc"] * cv["wvar"] - cv["cc"] * cv["wvar_c"]) * Decimal("0.35") * Decimal(44) / Decimal(16)
            expected_bake = (bv["bpm"] * bv["bpmfc"] + bv["bg"] * bv["bgfc"] - bv["bwt"] - bv["bp"] * bv["bpfc"]) * Decimal(44) / Decimal(12)
            expected_bake += (bv["bpm"] * bv["bpmvar"] + bv["bg"] * bv["bgvar"]) * Decimal("0.35") * Decimal(44) / Decimal(16)
            expected_graph = (gv["gpm"] * gv["gpmfc"] + gv["gta"] * gv["gtafc"] - gv["gwt"] - gv["gp"] * gv["gpfc"]) * Decimal(44) / Decimal(12)
            expected_graph += gv["gpm"] * gv["gpmvar"] * Decimal("0.35") * Decimal(44) / Decimal(16)
        self.assertEqual(result_by_source["CAR-SRC-CALCINATION-001"], expected_calc)
        self.assertEqual(result_by_source["CAR-SRC-BAKING-001"], expected_bake)
        self.assertEqual(result_by_source["CAR-SRC-GRAPHITIZATION-001"], expected_graph)

    def test_absent_optional_rows_and_explicit_zero_are_distinct(self) -> None:
        rows = (
            _line("feed", MaterialRole.CALCINATION_FEED, "原料", "0", None, None),
            _line("product", MaterialRole.CALCINED_PRODUCT, "煅后料", "0", None, None),
        )
        normalized = normalize_material_inputs("calcination", rows, policy=DecimalPolicy())
        self.assertFalse(normalized.problems, normalized.problems)
        values = dict(normalized.values)
        self.assertEqual(values["gc"], Decimal("0"))
        self.assertEqual(values["cc"], Decimal("0"))
        self.assertEqual(values["ucc"], Decimal("0"))
        self.assertEqual(values["du"], Decimal("0"))

        incomplete = normalize_material_inputs(
            "calcination",
            (
                _line("feed", MaterialRole.CALCINATION_FEED, "原料", "10", None, "2"),
                _line("product", MaterialRole.CALCINED_PRODUCT, "煅后料", "5", "90", None),
            ),
            policy=DecimalPolicy(),
        )
        self.assertTrue(any(problem.code == "CAR-VAL-MATERIAL-COMPONENT-MISSING" for problem in incomplete.problems))

        repository = InMemoryRecordRepository()
        missing_product = CarbonAccountingUseCase(CarbonMaterialCalculator(), repository).calculate(
            _input(calcination=CalcinationInput(k1="0.35", material_rows=(rows[0],))),
            calculated_at=CALCULATED_AT,
        )
        self.assertTrue(missing_product.blocked)
        self.assertIsNone(missing_product.result)
        self.assertIsNone(missing_product.record)
        self.assertEqual(repository.list_all(), ())


class UAT01BSteamTests(unittest.TestCase):
    def test_c4_and_c5_automatic_values_use_nodes_and_linear_interpolation(self) -> None:
        self.assertEqual(saturated_steam_enthalpy("1.70")[0], Decimal("2793.8"))
        self.assertEqual(saturated_steam_enthalpy("1.80")[0], Decimal("2795.1"))
        c4_middle, c4_interpolated, _ = saturated_steam_enthalpy("1.75")
        self.assertTrue(c4_interpolated)
        self.assertEqual(c4_middle, Decimal("2794.45"))
        self.assertEqual(superheated_steam_enthalpy("1", "300")[0], Decimal("3051.3"))
        self.assertEqual(superheated_steam_enthalpy("1", "350")[0], Decimal("3157.7"))
        c5_pressure_middle, pressure_interpolated, _ = superheated_steam_enthalpy("2", "300")
        self.assertTrue(pressure_interpolated)
        self.assertEqual(c5_pressure_middle, Decimal("3022.75"))
        c5_temperature_middle, temperature_interpolated, _ = superheated_steam_enthalpy("1", "325")
        self.assertTrue(temperature_interpolated)
        self.assertEqual(c5_temperature_middle, Decimal("3104.5"))
        self.assertEqual(superheated_steam_enthalpy("3", "300")[0], Decimal("2994.2"))
        c5_double, c5_interpolated, bounds = superheated_steam_enthalpy("2", "325")
        self.assertTrue(c5_interpolated)
        self.assertEqual(bounds, (Decimal("1"), Decimal("3")))
        self.assertGreater(c5_double, Decimal("3000"))

        for kind, pressure, temperature, reference in (
            (SteamKind.SATURATED, "1.75", None, c4_middle),
            (SteamKind.SUPERHEATED, "2", "325", c5_double),
        ):
            with self.subTest(kind=kind):
                heat = HeatInput(
                    f"auto-{kind.value}",
                    InputValue("1.25", "t"),
                    factor=_factor(),
                    unit="t",
                    steam_kind=kind,
                    pressure_mpa=pressure,
                    temperature_c=temperature,
                    manual_enthalpy=False,
                    factor_mode=HeatFactorMode.MEASURED,
                    steam_amount_t=InputValue("1.25", "t"),
                )
                outcome = CarbonMaterialCalculator().calculate(
                    _input(purchased_heat=(heat,)), calculated_at=CALCULATED_AT,
                )
                self.assertTrue(outcome.successful, outcome.problems)
                heat_line = next(line for line in outcome.result.lines if line.line_id.endswith(heat.line_id))
                with localcontext() as context:
                    context.prec = 28
                    expected = Decimal("1250") * reference * Decimal("0.11") / Decimal("1000000")
                self.assertEqual(heat_line.amount, expected)
                trace = next(trace for trace in outcome.traces if trace.trace_id == heat.line_id)
                provenance = dict(trace.provenance)
                self.assertEqual(provenance["enthalpy_source"], "标准表自动确定")
                self.assertEqual(provenance["automatic_reference_enthalpy_kj_per_kg"], str(reference))
                self.assertEqual(provenance["input_steam_amount_t"], "1.25")
                if kind is SteamKind.SATURATED:
                    self.assertEqual(provenance["pressure_lower_node_mpa"], "1.70")
                    self.assertEqual(provenance["pressure_upper_node_mpa"], "1.80")
                else:
                    self.assertEqual(provenance["pressure_lower_node_mpa"], "1")
                    self.assertEqual(provenance["pressure_upper_node_mpa"], "3")
                    self.assertEqual(provenance["temperature_lower_node_c"], "300")
                    self.assertEqual(provenance["temperature_upper_node_c"], "350")
                self.assertIn(ALGORITHM_VERSION, provenance["interpolation"])

    def test_manual_enthalpy_is_used_and_difference_is_warning_with_record_trace(self) -> None:
        repository = InMemoryRecordRepository()
        heat = HeatInput(
            "manual-steam",
            InputValue("1", "t"),
            "2810",
            _factor(),
            unit="t",
            steam_kind=SteamKind.SUPERHEATED,
            pressure_mpa="1",
            temperature_c="180",
            manual_enthalpy=True,
            factor_mode=HeatFactorMode.MEASURED,
            factor_source_note="检测报告第3页",
            steam_amount_t=InputValue("1", "t"),
        )
        use_case = CarbonAccountingUseCase(CarbonMaterialCalculator(), repository)
        outcome = use_case.calculate(
            _input(purchased_heat=(heat,)), calculated_at=CALCULATED_AT,
        )
        self.assertTrue(outcome.successful, outcome.problems)
        self.assertIsNotNone(outcome.record)
        deviations = [problem for problem in outcome.problems if problem.code == "CAR-VAL-STEAM-MANUAL-DEVIATION"]
        self.assertEqual(len(deviations), 1)
        self.assertEqual(deviations[0].level.value, "WARNING")
        self.assertIn("本次采用您填写的 2810", deviations[0].message)
        heat_line = next(line for line in outcome.result.lines if line.line_id.endswith("manual-steam"))
        with localcontext() as context:
            context.prec = 28
            expected = Decimal("1000") * Decimal("2810") * Decimal("0.11") / Decimal("1000000")
        self.assertEqual(heat_line.amount, expected)
        trace = next(trace for trace in outcome.traces if trace.trace_id == "manual-steam")
        provenance = dict(trace.provenance)
        self.assertEqual(provenance["enthalpy_source"], "用户手动填写")
        self.assertEqual(provenance["enthalpy_used_kj_per_kg"], "2810")
        self.assertEqual(provenance["automatic_reference_enthalpy_kj_per_kg"], "2777.3")
        self.assertEqual(provenance["heat_factor_source_note"], "检测报告第3页")
        assert outcome.record is not None
        trace_snapshot = repository.get_trace_snapshot(outcome.record.record_id)
        self.assertIsNotNone(trace_snapshot)
        assert trace_snapshot is not None
        before = repository.get_raw_input_snapshot(outcome.record.record_id)
        second = use_case.calculate(
            _input(input_id="uat01b.second", purchased_heat=(replace_heat_id(heat, "second"),)),
            calculated_at=CALCULATED_AT,
        )
        self.assertTrue(second.successful, second.problems)
        self.assertEqual(repository.get(outcome.record.record_id), outcome.record)
        self.assertEqual(repository.get_raw_input_snapshot(outcome.record.record_id), before)

        same_reference = replace(replace_heat_id(heat, "manual-steam-equals-reference"), enthalpy="2777.3")
        same_outcome = CarbonMaterialCalculator().calculate(
            _input(input_id="uat01b.manual-equal", purchased_heat=(same_reference,)),
            calculated_at=CALCULATED_AT,
        )
        self.assertTrue(same_outcome.successful, same_outcome.problems)
        self.assertFalse(any(problem.code == "CAR-VAL-STEAM-MANUAL-DEVIATION" for problem in same_outcome.problems))
        same_trace = next(trace for trace in same_outcome.traces if trace.trace_id == same_reference.line_id)
        self.assertEqual(dict(same_trace.provenance)["enthalpy_used_kj_per_kg"], "2777.3")

    def test_manual_outside_reference_range_warns_but_auto_range_blocks(self) -> None:
        manual = HeatInput(
            "manual-outside",
            InputValue("1", "t"),
            "2810",
            _factor(),
            unit="t",
            steam_kind=SteamKind.SUPERHEATED,
            pressure_mpa="31",
            temperature_c="700",
            manual_enthalpy=True,
            factor_mode=HeatFactorMode.MEASURED,
        )
        manual_outcome = CarbonMaterialCalculator().calculate(
            _input(purchased_heat=(manual,)), calculated_at=CALCULATED_AT,
        )
        self.assertTrue(manual_outcome.successful, manual_outcome.problems)
        self.assertTrue(any(problem.code == "CAR-VAL-STEAM-REFERENCE" for problem in manual_outcome.problems))
        self.assertTrue(any(
            problem.level.value == "WARNING" and "未填写来源说明" in problem.message
            for problem in manual_outcome.problems
        ))

        automatic = HeatInput(
            "auto-outside",
            InputValue("1", "t"),
            factor=_factor(),
            unit="t",
            steam_kind=SteamKind.SUPERHEATED,
            pressure_mpa="31",
            temperature_c="700",
            manual_enthalpy=False,
            factor_mode=HeatFactorMode.MEASURED,
        )
        repository = InMemoryRecordRepository()
        automatic_outcome = CarbonAccountingUseCase(
            CarbonMaterialCalculator(), repository
        ).calculate(
            _input(purchased_heat=(automatic,)), calculated_at=CALCULATED_AT,
        )
        self.assertTrue(automatic_outcome.blocked)
        self.assertIsNone(automatic_outcome.result)
        self.assertIsNone(automatic_outcome.record)
        self.assertEqual(repository.list_all(), ())


def replace_heat_id(line: HeatInput, line_id: str) -> HeatInput:
    return replace(line, line_id=line_id)


if __name__ == "__main__":
    unittest.main()
