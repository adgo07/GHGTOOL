from __future__ import annotations

from datetime import date, datetime, timezone
import tempfile
from pathlib import Path
from decimal import Decimal, localcontext
import unittest

from packages.core import (
    AccountingPeriod,
    ElectricityAcquisitionMode,
    ElectricityAttribute,
    ElectricityConsumptionDetail,
    ElectricityProofStatus,
    ElectricityProofType,
    Factor,
    IssueLevel,
    Parameter,
    ParameterResolver,
    ParameterType,
    PeriodType,
    ReviewStatus,
    ValueType,
)
from packages.standards.carbon_material import (
    ALGORITHM_VERSION,
    MAPPING_VERSION,
    SOURCE_BAKING,
    SOURCE_CALCINATION,
    SOURCE_FGD,
    SOURCE_FUME,
    SOURCE_FUEL,
    SOURCE_GRAPHITIZATION,
    SOURCE_EXPORTED_ELECTRICITY,
    SOURCE_EXPORTED_HEAT,
    SOURCE_PURCHASED_ELECTRICITY,
    SOURCE_PURCHASED_HEAT,
    BakingInput,
    CalcinationInput,
    CarbonMaterialCalculator,
    CarbonMaterialInput,
    CarbonateComponent,
    ElectricityOutputLine,
    EmissionSourceState,
    EmissionSourceStatus,
    FGDInput,
    FuelInput,
    FuelPath,
    FuelType,
    FumeIncinerationInput,
    GraphitizationInput,
    HeatFactorMode,
    HeatInput,
    InMemoryRecordRepository,
    InputValue,
    ParameterValue,
    MaterialComponentKind,
    SteamKind,
    ParameterSourceKind,
    calcination_emission,
    fgd_emission,
    fuel_energy_from_mass,
    fuel_energy_from_volume,
    fuel_heat_emission,
    fuel_mass_emission,
    fuel_volume_emission,
    fume_incineration_emission,
    graphitization_emission,
    purchased_electricity_emission,
    purchased_heat_emission,
    saturated_steam_enthalpy,
    superheated_steam_enthalpy,
)


STANDARD_ID = "gbt_32151_34_2024"
ENTERPRISE_ID = "enterprise.g06"
PERIOD = AccountingPeriod(PeriodType.ANNUAL, date(2025, 1, 1), date(2025, 12, 31))
SNAPSHOT_AT = datetime(2026, 9, 13, 12, 0, tzinfo=timezone.utc)


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


def _factors(*, include_zero: bool = True) -> tuple[Factor, ...]:
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
        valid_from=date(2025, 1, 1),
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
        valid_from=date(2025, 1, 1),
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
        electricity_amount=amount,
        electricity_unit="MWh",
        acquisition_mode=acquisition_mode,
        attribute=attribute,
        proof_type=proof_type,
        proof_status=proof_status,
    )


def _input(**kwargs: object) -> CarbonMaterialInput:
    period = kwargs.pop("period", PERIOD)
    return CarbonMaterialInput(
        input_id=kwargs.pop("input_id", "input.g06"),
        enterprise_id=ENTERPRISE_ID,
        enterprise_name="G06 测试企业",
        period=period,
        boundary_confirmed=kwargs.pop("boundary_confirmed", True),
        **kwargs,
    )


def _explicit_factor(parameter_id: str, value: str, unit: str) -> ParameterValue:
    return ParameterValue(parameter_id, value, unit, source_location="G06 regression fixture")


def _full_input() -> CarbonMaterialInput:
    return _input(
        fuel_inputs=(FuelInput.volume("fuel.full", "2", "0.015", "0.98"),),
        calcination=CalcinationInput(
            gc="100", wfc="0.008", cc="70", ucc="5", du="1",
            wfc_c="0.002", wvar="0.10", wvar_c="0.02", k1="0.35",
        ),
        baking=BakingInput(
            bpm="10", bpmfc="0.005", bg="100", bgfc="0.007", bwt="0.05",
            bp="95", bpfc="0.006", bpmvar="0.10", bgvar="0.02", k2="0.35",
        ),
        graphitization=GraphitizationInput(
            gpm="10", gpmfc="0.005", gta="100", gtafc="0.007", gwt="0.05",
            gp="95", gpfc="0.006", gpmvar="0.10", k3="0.35",
        ),
        fume_incineration=FumeIncinerationInput(
            q="1000", qvar="10", hm="30", fch="0.02", fox="0.98", duration="1",
        ),
        fgd=FGDInput(components=(CarbonateComponent("10", "0.90", "0.44", "1"),)),
        electricity_details=(
            _detail("power.full", "100", ElectricityAcquisitionMode.PURCHASED, ElectricityAttribute.ORDINARY),
        ),
        exported_electricity=(
            ElectricityOutputLine(
                "exported.power",
                "2",
                _explicit_factor("electricity_emission_factor_national", "0.5", "tCO2/MWh"),
            ),
        ),
        purchased_heat=(
            HeatInput(
                "purchased.heat",
                "1000",
                "2800",
                _explicit_factor("heat_emission_factor_default", "0.11", "tCO2/GJ"),
            ),
        ),
        exported_heat=(
            HeatInput(
                "exported.heat",
                "100",
                "2800",
                _explicit_factor("heat_emission_factor_default", "0.11", "tCO2/GJ"),
            ),
        ),
    )


class G06FormulaTests(unittest.TestCase):
    def test_fuel_paths_and_energy_mapping_vectors(self) -> None:
        self.assertLess(abs(fuel_volume_emission("2", "0.015", "0.98") - Decimal("0.1078")), Decimal("1e-24"))
        self.assertLess(abs(fuel_mass_emission("10", "0.02", "1") - (Decimal("10") * Decimal("0.02") * Decimal(44) / Decimal(12))), Decimal("1e-24"))
        self.assertLess(abs(fuel_heat_emission("100", "0.0001", "1") - (Decimal("100") * Decimal("0.0001") * Decimal(44) / Decimal(12))), Decimal("1e-24"))
        self.assertEqual(fuel_energy_from_volume("2", "35"), Decimal("70"))
        self.assertEqual(fuel_energy_from_mass("10", "28"), Decimal("280"))

    def test_process_and_gas_control_vectors(self) -> None:
        calcination = CalcinationInput(
            gc="100", wfc="0.008", cc="70", ucc="5", du="1",
            wfc_c="0.002", wvar="0.10", wvar_c="0.02", k1="0.35",
        )
        baking = BakingInput(
            bpm="10", bpmfc="0.005", bg="100", bgfc="0.007", bwt="0.05",
            bp="95", bpfc="0.006", bpmvar="0.10", bgvar="0.02", k2="0.35",
        )
        graphitization = GraphitizationInput(
            gpm="10", gpmfc="0.005", gta="100", gtafc="0.007", gwt="0.05",
            gp="95", gpfc="0.006", gpmvar="0.10", k3="0.35",
        )
        component = CarbonateComponent("10", "0.90", "0.44", "1")
        self.assertEqual(
            calcination_emission := __import__(
                "packages.standards.carbon_material", fromlist=["calcination_emission"]
            ).calcination_emission(
                gc="100", wfc="0.008", cc="70", ucc="5", du="1", wfc_c="0.002",
                wvar="0.10", wvar_c="0.02", k1="0.35",
            ),
            Decimal("10.6535"),
        )
        self.assertLess(
            abs(
                __import__(
                    "packages.standards.carbon_material", fromlist=["baking_emission"]
                ).baking_emission(
                    bpm="10", bpmfc="0.005", bg="100", bgfc="0.007", bwt="0.05", bp="95",
                    bpfc="0.006", bpmvar="0.10", bgvar="0.02", k2="0.35",
                )
                - Decimal("3.364166666666666666666666666667")
            ),
            Decimal("1e-24"),
        )
        self.assertLess(
            abs(
                graphitization_emission(
                    gpm="10", gpmfc="0.005", gta="100", gtafc="0.007", gwt="0.05", gp="95",
                    gpfc="0.006", gpmvar="0.10", k3="0.35",
                )
                - Decimal("1.439166666666666666666666666667")
            ),
            Decimal("1e-24"),
        )
        self.assertEqual(MAPPING_VERSION, "SM01-2026-09-13-R6")
        self.assertLess(abs(fume_incineration_emission("1000", "10", "30", "0.02", "0.98", "1") - Decimal("0.00051744")), Decimal("1e-24"))
        self.assertEqual(fgd_emission((component,)), Decimal("3.96"))
        self.assertEqual(calcination.gc.value, Decimal("100"))
        self.assertEqual(baking.bpm.value, Decimal("10"))
        self.assertEqual(graphitization.gpm.value, Decimal("10"))

    def test_r6_vector_correction_keeps_standard_formula_without_extra_gta_term(self) -> None:
        old_mapping_expectation = Decimal("3.364166666666666666666666666667")
        approved_r6_expectation = Decimal("1.439166666666666666666666667")
        actual = graphitization_emission(
            gpm="10", gpmfc="0.005", gta="100", gtafc="0.007", gwt="0.05",
            gp="95", gpfc="0.006", gpmvar="0.10", k3="0.35",
        )
        self.assertEqual(actual, approved_r6_expectation)
        self.assertNotEqual(actual, old_mapping_expectation)

    def test_electricity_heat_and_steam_mapping_vectors(self) -> None:
        self.assertEqual(purchased_electricity_emission("100", "0.5306"), Decimal("53.06"))
        self.assertEqual(purchased_heat_emission("1000", "2800", "0.11"), Decimal("0.308"))
        c4_170 = saturated_steam_enthalpy("1.70")
        c4_180 = saturated_steam_enthalpy("1.80")
        self.assertEqual(c4_170[0], Decimal("2793.8"))
        self.assertEqual(c4_170[1:], (False, (Decimal("1.70"), Decimal("1.70"))))
        self.assertEqual(c4_180[0], Decimal("2795.1"))
        self.assertEqual(c4_180[1:], (False, (Decimal("1.80"), Decimal("1.80"))))
        enthalpy, interpolated, endpoints = saturated_steam_enthalpy("1.75")
        self.assertEqual(enthalpy, Decimal("2794.45"))
        self.assertTrue(interpolated)
        self.assertEqual(endpoints, (Decimal("1.70"), Decimal("1.80")))
        superheated, superheated_interpolated, superheated_endpoints = superheated_steam_enthalpy("1.5", "325")
        self.assertTrue(superheated_interpolated)
        self.assertEqual(superheated_endpoints, (Decimal("1"), Decimal("3")))
        self.assertGreater(superheated, Decimal("3000"))
        self.assertEqual(superheated_steam_enthalpy("1", "300")[0], Decimal("3051.3"))
        self.assertEqual(superheated_steam_enthalpy("3", "350")[0], Decimal("3115.7"))
        with self.assertRaises(ValueError):
            superheated_steam_enthalpy("31", "300")


class G06CalculatorTests(unittest.TestCase):
    def test_multi_entry_processes_calculate_each_instance_then_sum_without_merging(self) -> None:
        calcination_a = CalcinationInput(
            gc="100", wfc="0.06", cc="45", ucc="4", du="1", wfc_c="0.06",
            wvar="0.10", wvar_c="0.02", k1="0.35", instance_id="calc-a",
        )
        calcination_b = CalcinationInput(
            gc="200", wfc="0.06", cc="90", ucc="10", du="0", wfc_c="0.06",
            wvar="0.10", wvar_c="0.02", k1="0.20", instance_id="calc-b",
        )
        bakings = (
            BakingInput("10", "0.005", "100", "0.007", "0.05", "95", "0.006", "0.10", "0.02", "0.35", instance_id="bake-a"),
            BakingInput("25", "0.012", "150", "0.01", "0.02", "110", "0.009", "0.08", "0.03", "0.35", instance_id="bake-b"),
        )
        graphitizations = (
            GraphitizationInput("10", "0.005", "100", "0.007", "0.05", "95", "0.006", "0.10", "0.35", instance_id="graph-a"),
            GraphitizationInput("20", "0.012", "140", "0.01", "0.02", "115", "0.008", "0.08", "0.35", instance_id="graph-b"),
        )
        fumes = (
            FumeIncinerationInput("1000", "10", "30", "0.02", "0.98", "1", instance_id="fume-a"),
            FumeIncinerationInput("500", "15", "25", "0.03", "0.95", "2", instance_id="fume-b"),
        )
        fgd_units = (
            FGDInput(components=(CarbonateComponent("10", "0.45", "0.44", "1"), CarbonateComponent("2", "0.45", "0.522", "1")), instance_id="fgd-a"),
            FGDInput(components=(CarbonateComponent("5", "0.90", "0.415", "1"),), instance_id="fgd-b"),
        )
        exported_power = (
            ElectricityOutputLine("power-out-a", "10", _explicit_factor("electricity_emission_factor_national", "0.50", "tCO2/MWh")),
            ElectricityOutputLine("power-out-b", "4", _explicit_factor("electricity_emission_factor_national", "0.25", "tCO2/MWh")),
        )
        purchased_heat = (
            HeatInput("heat-in-a", "1000", "2800", _explicit_factor("heat_emission_factor_default", "0.11", "tCO2/GJ")),
            HeatInput("heat-in-b", "500", "3000", _explicit_factor("heat_emission_factor_default", "0.20", "tCO2/GJ")),
        )
        exported_heat = (
            HeatInput("heat-out-a", "250", "2700", _explicit_factor("heat_emission_factor_default", "0.11", "tCO2/GJ")),
            HeatInput("heat-out-b", "750", "2900", _explicit_factor("heat_emission_factor_default", "0.16", "tCO2/GJ")),
        )
        outcome = CarbonMaterialCalculator(parameter_resolver=_resolver()).calculate(
            _input(
                calcinations=(calcination_a, calcination_b), bakings=bakings,
                graphitizations=graphitizations, fume_incinerations=fumes, fgd_units=fgd_units,
                exported_electricity=exported_power, purchased_heat=purchased_heat, exported_heat=exported_heat,
            ),
            calculated_at=SNAPSHOT_AT,
        )
        self.assertTrue(outcome.successful, outcome.problems)
        lines = {line.line_id: line for line in outcome.result.lines}
        for line_id in (
            "CAR-FLD-P01-RESULT.calc-a", "CAR-FLD-P01-RESULT.calc-b",
            "CAR-FLD-P02-RESULT.bake-a", "CAR-FLD-P02-RESULT.bake-b",
            "CAR-FLD-P03-RESULT.graph-a", "CAR-FLD-P03-RESULT.graph-b",
            "CAR-FLD-P04A-RESULT.fume-a", "CAR-FLD-P04A-RESULT.fume-b",
            "CAR-FLD-P04B-RESULT.fgd-a", "CAR-FLD-P04B-RESULT.fgd-b",
            "CAR-FLD-POWER-EXPORTED-RESULT.power-out-a", "CAR-FLD-POWER-EXPORTED-RESULT.power-out-b",
            "CAR-FLD-HEAT-PURCHASED-RESULT.heat-in-a", "CAR-FLD-HEAT-PURCHASED-RESULT.heat-in-b",
            "CAR-FLD-HEAT-EXPORTED-RESULT.heat-out-a", "CAR-FLD-HEAT-EXPORTED-RESULT.heat-out-b",
        ):
            self.assertIn(line_id, lines)
        with localcontext() as context:
            context.prec = 60
            calc_sum = lines["CAR-FLD-P01-RESULT.calc-a"].amount + lines["CAR-FLD-P01-RESULT.calc-b"].amount
            self.assertEqual(lines["CAR-FLD-P01-RESULT.calc-a"].amount, Decimal("19.75875"))
            self.assertEqual(lines["CAR-FLD-P01-RESULT.calc-b"].amount, Decimal("32.01"))
            self.assertEqual(calc_sum, Decimal("51.76875"))
            direct = lines["CAR-FLD-DIRECT-RESULT"].amount
            expected_direct = calc_sum + sum(
                (lines[line_id].amount for line_id in (
                    "CAR-FLD-P02-RESULT.bake-a", "CAR-FLD-P02-RESULT.bake-b",
                    "CAR-FLD-P03-RESULT.graph-a", "CAR-FLD-P03-RESULT.graph-b",
                    "CAR-FLD-P04A-RESULT.fume-a", "CAR-FLD-P04A-RESULT.fume-b",
                    "CAR-FLD-P04B-RESULT.fgd-a", "CAR-FLD-P04B-RESULT.fgd-b",
                )),
                Decimal("0"),
            )
            self.assertLess(abs(direct - expected_direct), Decimal("1e-35"))
        # Independent Eq. (1) reference values: each process is evaluated with
        # its own K1, while the intentionally wrong merged case reuses K1=0.35.
        merged_wrong_expected = calcination_emission(
            gc=Decimal("300"), wfc=Decimal("0.06"), cc=Decimal("135"), ucc=Decimal("14"),
            du=Decimal("1"), wfc_c=Decimal("0.06"), wvar=Decimal("0.10"), wvar_c=Decimal("0.02"), k1=Decimal("0.35"),
        )
        self.assertEqual(merged_wrong_expected, Decimal("59.27625"))
        self.assertNotEqual(calc_sum, merged_wrong_expected)
        trace_ids = [trace.trace_id for trace in outcome.traces]
        self.assertEqual(len(trace_ids), len(set(trace_ids)))
        heat_snapshots = {snapshot.snapshot_id for snapshot in outcome.parameter_snapshots if snapshot.parameter_id == "heat_emission_factor_default"}
        self.assertTrue(all(
            any(line_id in snapshot_id for snapshot_id in heat_snapshots)
            for line_id in ("heat-in-a", "heat-in-b", "heat-out-a", "heat-out-b")
        ))

    def test_incomplete_process_instance_blocks_aggregate_record(self) -> None:
        complete = CalcinationInput(
            gc="100", wfc="0.008", cc="70", ucc="5", du="1", wfc_c="0.002",
            wvar="0.10", wvar_c="0.02", k1="0.35", instance_id="valid-line",
        )
        incomplete = CalcinationInput(gc="50", instance_id="missing-line")
        repository = InMemoryRecordRepository()
        outcome = CarbonMaterialCalculator(record_repository=repository).calculate(
            _input(calcinations=(complete, incomplete)), calculated_at=SNAPSHOT_AT,
        )
        self.assertTrue(outcome.blocked)
        self.assertIsNone(outcome.result)
        self.assertIsNone(outcome.record)
        self.assertEqual(repository.list_all(), ())
        self.assertTrue(any("missing-line" in (problem.field_id or "") for problem in outcome.problems))

    def test_three_electricity_details_have_independent_results_and_snapshots(self) -> None:
        details = (
            _detail("power.ordinary", "100", ElectricityAcquisitionMode.PURCHASED, ElectricityAttribute.ORDINARY),
            _detail(
                "power.market.nonfossil", "20", ElectricityAcquisitionMode.PURCHASED,
                ElectricityAttribute.NONFOSSIL, proof_type=ElectricityProofType.CONTRACT_AND_SETTLEMENT,
                proof_status=ElectricityProofStatus.VALID,
            ),
            _detail(
                "power.self.nonfossil", "30", ElectricityAcquisitionMode.SELF_CONSUMED,
                ElectricityAttribute.NONFOSSIL, proof_type=ElectricityProofType.MONTHLY_ORIGINAL_RECORD,
                proof_status=ElectricityProofStatus.VALID,
            ),
        )
        repository = InMemoryRecordRepository()
        outcome = CarbonMaterialCalculator(
            parameter_resolver=_resolver(), record_repository=repository
        ).calculate(_input(electricity_details=details), calculated_at=SNAPSHOT_AT)

        self.assertTrue(outcome.successful)
        self.assertEqual(outcome.algorithm_version, ALGORITHM_VERSION)
        self.assertEqual(outcome.result.total_amount, Decimal("53.06"))
        power_lines = [line for line in outcome.result.lines if line.emission_source_id == SOURCE_PURCHASED_ELECTRICITY]
        self.assertEqual({line.line_id for line in power_lines}, {
            "CAR-FLD-PWR-PURCHASED-RESULT.power.ordinary",
            "CAR-FLD-PWR-PURCHASED-RESULT.power.market.nonfossil",
            "CAR-FLD-PWR-PURCHASED-RESULT.power.self.nonfossil",
        })
        self.assertEqual({snapshot.detail_id for snapshot in outcome.parameter_snapshots}, {
            detail.detail_id for detail in details
        })
        self.assertEqual(len(repository.list_all()), 1)
        self.assertEqual(repository.list_all()[0].calculation_result.total_amount, Decimal("53.06"))

    def test_all_sources_have_normal_and_zero_paths(self) -> None:
        normal = CarbonMaterialCalculator(parameter_resolver=_resolver()).calculate(
            _full_input(), calculated_at=SNAPSHOT_AT
        )
        self.assertTrue(normal.successful, normal.problems)
        self.assertFalse(
            [problem for problem in normal.problems if problem.level is IssueLevel.ERROR],
            normal.problems,
        )

        zero_cases = (
            (SOURCE_FUEL, _input(fuel_inputs=(FuelInput.volume("zero.fuel", "0", "0.015", "0.98"),))),
            (
                SOURCE_CALCINATION,
                _input(calcination=CalcinationInput(
                    gc="0", wfc="0", cc="0", ucc="0", du="0", wfc_c="0",
                    wvar="0", wvar_c="0", k1="0",
                )),
            ),
            (
                SOURCE_BAKING,
                _input(baking=BakingInput(
                    bpm="0", bpmfc="0", bg="0", bgfc="0", bwt="0", bp="0",
                    bpfc="0", bpmvar="0", bgvar="0", k2="0",
                )),
            ),
            (
                SOURCE_GRAPHITIZATION,
                _input(graphitization=GraphitizationInput(
                    gpm="0", gpmfc="0", gta="0", gtafc="0", gwt="0", gp="0",
                    gpfc="0", gpmvar="0", k3="0",
                )),
            ),
            (
                SOURCE_FUME,
                _input(fume_incineration=FumeIncinerationInput(
                    q="0", qvar="0", hm="0", fch="0", fox="0", duration="0",
                )),
            ),
            (
                SOURCE_FGD,
                _input(fgd=FGDInput(components=(CarbonateComponent("0", "0", "0", "0"),))),
            ),
            (
                SOURCE_PURCHASED_ELECTRICITY,
                _input(electricity_details=(
                    _detail("zero.power", "0", ElectricityAcquisitionMode.PURCHASED, ElectricityAttribute.ORDINARY),
                )),
            ),
            (
                SOURCE_PURCHASED_HEAT,
                _input(purchased_heat=(
                    HeatInput("zero.heat", "0", "2800", _explicit_factor("heat", "0.11", "tCO2/GJ")),
                )),
            ),
            (
                SOURCE_EXPORTED_ELECTRICITY,
                _input(exported_electricity=(
                    ElectricityOutputLine("zero.export.power", "0", _explicit_factor("power", "0.5", "tCO2/MWh")),
                )),
            ),
            (
                SOURCE_EXPORTED_HEAT,
                _input(exported_heat=(
                    HeatInput("zero.export.heat", "0", "2800", _explicit_factor("heat", "0.11", "tCO2/GJ")),
                )),
            ),
        )
        for source_id, input_value in zero_cases:
            with self.subTest(source_id=source_id):
                calculator = CarbonMaterialCalculator(parameter_resolver=_resolver())
                outcome = calculator.calculate(input_value, calculated_at=SNAPSHOT_AT)
                errors = [problem for problem in outcome.problems if problem.level is IssueLevel.ERROR]
                self.assertFalse(errors, (source_id, errors))

    def test_missing_and_not_involved_paths_are_explicit_for_each_source(self) -> None:
        source_ids = (
            SOURCE_FUEL,
            SOURCE_CALCINATION,
            SOURCE_BAKING,
            SOURCE_GRAPHITIZATION,
            SOURCE_FUME,
            SOURCE_FGD,
            SOURCE_PURCHASED_ELECTRICITY,
            SOURCE_PURCHASED_HEAT,
            SOURCE_EXPORTED_ELECTRICITY,
            SOURCE_EXPORTED_HEAT,
        )
        calculator = CarbonMaterialCalculator(parameter_resolver=_resolver())
        for source_id in source_ids:
            with self.subTest(path="missing", source_id=source_id):
                outcome = calculator.calculate(
                    _input(source_states=(EmissionSourceState(source_id, EmissionSourceStatus.INVOLVED),)),
                    calculated_at=SNAPSHOT_AT,
                )
                self.assertTrue(
                    any(
                        problem.code == "GEN-VAL-REQUIRED-MISSING"
                        and problem.field_id == source_id
                        for problem in outcome.problems
                    ),
                    (source_id, outcome.problems),
                )

        not_involved_payloads = (
            (SOURCE_FUEL, {"fuel_inputs": (FuelInput.volume("ni.fuel", "1", "0.015", "0.98"),)}),
            (SOURCE_CALCINATION, {"calcination": CalcinationInput(
                gc="1", wfc="0", cc="0", ucc="0", du="0", wfc_c="0", wvar="0", wvar_c="0", k1="0",
            )}),
            (SOURCE_BAKING, {"baking": BakingInput(
                bpm="1", bpmfc="0", bg="0", bgfc="0", bwt="0", bp="0", bpfc="0", bpmvar="0", bgvar="0", k2="0",
            )}),
            (SOURCE_GRAPHITIZATION, {"graphitization": GraphitizationInput(
                gpm="1", gpmfc="0", gta="0", gtafc="0", gwt="0", gp="0", gpfc="0", gpmvar="0", k3="0",
            )}),
            (SOURCE_FUME, {"fume_incineration": FumeIncinerationInput(
                q="1", qvar="0", hm="0", fch="0", fox="0", duration="0",
            )}),
            (SOURCE_FGD, {"fgd": FGDInput(components=(CarbonateComponent("1", "0", "0", "0"),))}),
            (SOURCE_PURCHASED_ELECTRICITY, {"electricity_details": (
                _detail("ni.power", "1", ElectricityAcquisitionMode.PURCHASED, ElectricityAttribute.ORDINARY),
            )}),
            (SOURCE_PURCHASED_HEAT, {"purchased_heat": (
                HeatInput("ni.heat", "1", "2800", _explicit_factor("heat", "0.11", "tCO2/GJ")),
            )}),
            (SOURCE_EXPORTED_ELECTRICITY, {"exported_electricity": (
                ElectricityOutputLine("ni.export.power", "1", _explicit_factor("power", "0.5", "tCO2/MWh")),
            )}),
            (SOURCE_EXPORTED_HEAT, {"exported_heat": (
                HeatInput("ni.export.heat", "1", "2800", _explicit_factor("heat", "0.11", "tCO2/GJ")),
            )}),
        )
        for source_id, payload in not_involved_payloads:
            with self.subTest(path="not_involved", source_id=source_id):
                outcome = calculator.calculate(
                    _input(
                        source_states=(EmissionSourceState(source_id, EmissionSourceStatus.NOT_INVOLVED),),
                        **payload,
                    ),
                    calculated_at=SNAPSHOT_AT,
                )
                self.assertTrue(
                    any(
                        problem.code == "CAR-VAL-SOURCE-CONFLICT"
                        and problem.field_id == source_id
                        for problem in outcome.problems
                    ),
                    (source_id, outcome.problems),
                )

    def test_applicable_percentage_and_unit_errors_are_not_silent(self) -> None:
        percentage_cases = (
            (SOURCE_FUEL, _input(fuel_inputs=(
                FuelInput.volume("bad.fuel", "1", "0.015", InputValue("101", "percent")),
            ))),
            (SOURCE_CALCINATION, _input(calcination=CalcinationInput(
                gc="1", wfc=InputValue("101", "percent"), cc="0", ucc="0", du="0",
                wfc_c="0", wvar="0", wvar_c="0", k1="0",
            ))),
            (SOURCE_BAKING, _input(baking=BakingInput(
                bpm="1", bpmfc="0", bg="0", bgfc="0", bwt="0", bp="0", bpfc="0",
                bpmvar=InputValue("101", "percent"), bgvar="0", k2="0",
            ))),
            (SOURCE_GRAPHITIZATION, _input(graphitization=GraphitizationInput(
                gpm="1", gpmfc="0", gta="0", gtafc="0", gwt="0", gp="0", gpfc="0",
                gpmvar=InputValue("101", "percent"), k3="0",
            ))),
            (SOURCE_FUME, _input(fume_incineration=FumeIncinerationInput(
                q="1", qvar="0", hm="0", fch="0", fox=InputValue("101", "percent"), duration="0",
            ))),
            (SOURCE_FGD, _input(fgd=FGDInput(components=(
                CarbonateComponent("1", InputValue("101", "percent"), "0", "0"),
            )))),
        )
        calculator = CarbonMaterialCalculator(parameter_resolver=_resolver())
        for source_id, input_value in percentage_cases:
            with self.subTest(error="percentage", source_id=source_id):
                outcome = calculator.calculate(input_value, calculated_at=SNAPSHOT_AT)
                expected_code = "CAR-VAL-PARAMETER-RATIO-RANGE" if source_id == SOURCE_FUEL else "CAR-VAL-PERCENT-RANGE"
                self.assertTrue(
                    any(problem.code == expected_code for problem in outcome.problems),
                    (source_id, outcome.problems),
                )

        unit_cases = (
            (SOURCE_FUEL, _input(fuel_inputs=(FuelInput.volume(
                "unit.fuel", InputValue("1", "MWh"), "0.015", "0.98",
            ),))),
            (SOURCE_CALCINATION, _input(calcination=CalcinationInput(
                gc=InputValue("1", "MWh"), wfc="0", cc="0", ucc="0", du="0",
                wfc_c="0", wvar="0", wvar_c="0", k1="0",
            ))),
            (SOURCE_BAKING, _input(baking=BakingInput(
                bpm=InputValue("1", "MWh"), bpmfc="0", bg="0", bgfc="0", bwt="0",
                bp="0", bpfc="0", bpmvar="0", bgvar="0", k2="0",
            ))),
            (SOURCE_GRAPHITIZATION, _input(graphitization=GraphitizationInput(
                gpm=InputValue("1", "MWh"), gpmfc="0", gta="0", gtafc="0", gwt="0",
                gp="0", gpfc="0", gpmvar="0", k3="0",
            ))),
            (SOURCE_FUME, _input(fume_incineration=FumeIncinerationInput(
                q=InputValue("1", "MWh"), qvar="0", hm="0", fch="0", fox="0", duration="0",
            ))),
            (SOURCE_FGD, _input(fgd=FGDInput(components=(
                CarbonateComponent(InputValue("1", "MWh"), "0", "0", "0"),
            )))),
            (SOURCE_PURCHASED_ELECTRICITY, _input(electricity_details=(
                _detail("unit.power", "1", ElectricityAcquisitionMode.PURCHASED, ElectricityAttribute.ORDINARY),
            ))),
            (SOURCE_PURCHASED_HEAT, _input(purchased_heat=(
                HeatInput("unit.heat", "1", "2800", _explicit_factor("heat", "0.11", "tCO2/GJ"), unit="MWh"),
            ))),
            (SOURCE_EXPORTED_ELECTRICITY, _input(exported_electricity=(
                ElectricityOutputLine("unit.export.power", "1", _explicit_factor("power", "0.5", "tCO2/MWh"), unit="kg"),
            ))),
            (SOURCE_EXPORTED_HEAT, _input(exported_heat=(
                HeatInput("unit.export.heat", "1", "2800", _explicit_factor("heat", "0.11", "tCO2/GJ"), unit="MWh"),
            ))),
        )
        unit_cases = list(unit_cases)
        unit_cases[6] = (
            SOURCE_PURCHASED_ELECTRICITY,
            _input(electricity_details=(ElectricityConsumptionDetail(
                detail_id="unit.power",
                enterprise_id=ENTERPRISE_ID,
                standard_id=STANDARD_ID,
                accounting_period=PERIOD,
                electricity_amount="1",
                electricity_unit="kg",
                acquisition_mode=ElectricityAcquisitionMode.PURCHASED,
                attribute=ElectricityAttribute.ORDINARY,
            ),)),
        )
        for source_id, input_value in unit_cases:
            with self.subTest(error="unit", source_id=source_id):
                outcome = calculator.calculate(input_value, calculated_at=SNAPSHOT_AT)
                self.assertTrue(
                    any(problem.code == "GEN-VAL-UNIT-INCOMPATIBLE" for problem in outcome.problems),
                    (source_id, outcome.problems),
                )

    def test_defaults_emit_warnings_and_parameter_snapshots(self) -> None:
        k1_default = ParameterValue(
            "car-par-k1", "0.35", "ratio", ParameterSourceKind.STANDARD_DEFAULT,
            "SRC-32151-34-2024", "2024", "第5.2.2条；PDF第12页；印刷页4",
            "来自本地Canonical标准一般取值因子。", "methane_conversion_factor_calcination_gbt32151_34_2024", 2024,
        )
        default_k1 = CarbonMaterialCalculator().calculate(
            _input(calcination=CalcinationInput(
                gc="1", wfc="0", cc="0", ucc="0", du="0", wfc_c="0", wvar="0", wvar_c="0",
                k1=k1_default,
            )),
            calculated_at=SNAPSHOT_AT,
        )
        self.assertTrue(default_k1.successful)
        self.assertIn("car-par-k1", {snapshot.parameter_id for snapshot in default_k1.parameter_snapshots})

        record_store = InMemoryRecordRepository()
        unknown_fgd = CarbonMaterialCalculator(record_repository=record_store).calculate(
            _input(fgd=FGDInput(cal="10")), calculated_at=SNAPSHOT_AT
        )
        self.assertFalse(unknown_fgd.successful)
        self.assertTrue(unknown_fgd.blocked)
        self.assertIsNone(unknown_fgd.record)
        self.assertEqual(record_store.list_all(), ())
        self.assertTrue(any(
            problem.code == "CAR-VAL-CARBONATE-FACTOR-MISSING"
            and "请选择脱硫剂中的碳酸盐种类" in problem.message
            for problem in unknown_fgd.problems
        ))

        default_heat_store = InMemoryRecordRepository()
        default_heat = CarbonMaterialCalculator(record_repository=default_heat_store).calculate(
            _input(purchased_heat=(HeatInput("default.heat", "1000", "2800"),)),
            calculated_at=SNAPSHOT_AT,
        )
        self.assertTrue(default_heat.blocked)
        self.assertTrue(any(
            problem.code == "CAR-VAL-HEAT-FACTOR-DEFAULT"
            and problem.level is IssueLevel.ERROR
            and "标准参数目录" in problem.message
            for problem in default_heat.problems
        ))
        self.assertIsNone(default_heat.record)
        self.assertEqual(default_heat_store.list_all(), ())

    def test_domain_parameter_gate_blocks_invalid_values_from_every_source_without_records(self) -> None:
        for source_kind in ParameterSourceKind:
            with self.subTest(source_kind=source_kind):
                record_store = InMemoryRecordRepository()
                carbon = ParameterValue(
                    "fuel_carbon", "-0.01", "tC/10^4Nm3", source_kind,
                    "test-source", "test-version", "test location", "validation fixture",
                )
                oxidation = ParameterValue(
                    "fuel_oxidation", "0.98", "ratio", source_kind,
                    "test-source", "test-version", "test location", "validation fixture",
                )
                outcome = CarbonMaterialCalculator(record_repository=record_store).calculate(
                    _input(fuel_inputs=(FuelInput("negative-carbon", FuelPath.VOLUME, "1", carbon, oxidation),)),
                    calculated_at=SNAPSHOT_AT,
                )
                self.assertTrue(outcome.blocked)
                self.assertTrue(any(problem.code == "CAR-VAL-PARAMETER-NONNEGATIVE" for problem in outcome.problems))
                self.assertIsNone(outcome.record)
                self.assertEqual(record_store.list_all(), ())

        record_store = InMemoryRecordRepository()
        negative_heat = CarbonMaterialCalculator(record_repository=record_store).calculate(
            _input(purchased_heat=(HeatInput(
                "negative-heat", "1", "2800",
                ParameterValue("measured_heat_factor", "-0.11", "tCO2/GJ", ParameterSourceKind.MEASURED,
                               "test-report", "2026", "report page 2", "measured fixture"),
            ),)),
            calculated_at=SNAPSHOT_AT,
        )
        self.assertTrue(negative_heat.blocked)
        self.assertTrue(any(problem.code == "CAR-VAL-PARAMETER-NONNEGATIVE" for problem in negative_heat.problems))
        self.assertIsNone(negative_heat.record)
        self.assertEqual(record_store.list_all(), ())

    def test_ratio_parameter_range_and_legal_zero(self) -> None:
        for value in ("-0.01", "1.01", "101"):
            unit = "percent" if value == "101" else "ratio"
            outcome = CarbonMaterialCalculator().calculate(
                _input(fuel_inputs=(FuelInput(
                    "bad-ratio", FuelPath.VOLUME, "1",
                    ParameterValue("fuel_carbon", "0.015", "tC/10^4Nm3", source_location="test"),
                    ParameterValue("fuel_oxidation", value, unit, source_location="test"),
                ),)),
                calculated_at=SNAPSHOT_AT,
            )
            self.assertTrue(outcome.blocked, (value, outcome.problems))
            self.assertTrue(any(problem.code == "CAR-VAL-PARAMETER-RATIO-RANGE" for problem in outcome.problems))
            self.assertIsNone(outcome.record)

        zero = CarbonMaterialCalculator().calculate(
            _input(fuel_inputs=(FuelInput(
                "zero-ratio", FuelPath.VOLUME, "1",
                ParameterValue("fuel_carbon", "0.015", "tC/10^4Nm3", source_location="test"),
                ParameterValue("fuel_oxidation", "0", "ratio", source_location="test"),
            ),)),
            calculated_at=SNAPSHOT_AT,
        )
        self.assertTrue(zero.successful, zero.problems)
        self.assertEqual(zero.result.total_amount, Decimal("0"))

    def test_canonical_heat_default_resolves_for_purchased_and_exported_heat(self) -> None:
        heat_parameter = Parameter(
            "heat_emission_factor_default",
            "purchased_heat",
            ParameterType.HEAT_EMISSION_FACTOR,
            "热力缺省排放因子",
            "tCO₂/GJ",
            "2025",
        )
        heat_factor = Factor(
            factor_id="heat_default_2025",
            parameter_id="heat_emission_factor_default",
            subject_id="purchased_heat",
            parameter_type=ParameterType.HEAT_EMISSION_FACTOR,
            value="0.11",
            unit="tCO₂/GJ",
            version="2025",
            value_type=ValueType.STANDARD_DEFAULT,
            review_status=ReviewStatus.VERIFIED,
            source_id="SRC-32150-2025",
            source_location="GB/T 32150—2025 第7.5.6～7.5.7条",
            applicable_standard_ids=("gbt_32150_2025", STANDARD_ID),
            factor_year=2025,
            valid_from=date(2025, 1, 1),
        )
        resolver = ParameterResolver.with_default_g05_rules(
            MemoryParameterRepository((*_parameters(), heat_parameter), (*_factors(), heat_factor))
        )
        outcome = CarbonMaterialCalculator(parameter_resolver=resolver).calculate(
            _input(
                purchased_heat=(HeatInput("purchased-1", "1", unit="t", manual_enthalpy=False, pressure_mpa="0.1", factor_mode=HeatFactorMode.STANDARD_DEFAULT),),
                exported_heat=(HeatInput("exported-1", "0.5", unit="t", manual_enthalpy=False, pressure_mpa="0.1", factor_mode=HeatFactorMode.STANDARD_DEFAULT),),
            ),
            calculated_at=SNAPSHOT_AT,
        )
        self.assertTrue(outcome.successful, outcome.problems)
        self.assertEqual(
            {snapshot.detail_id for snapshot in outcome.parameter_snapshots if snapshot.parameter_id == "heat_emission_factor_default"},
            {"purchased-1", "exported-1"},
        )
        for formula_id in ("CAR-FML-PURCHASED-HEAT-001", "CAR-FML-EXPORTED-HEAT-001"):
            trace = next(item for item in outcome.traces if item.formula_id == formula_id)
            self.assertEqual(dict(trace.provenance)["heat_factor_source"], "标准缺省值")
            variables = {name: value for name, value, _unit in trace.variables}
            self.assertEqual(variables["EF3"], Decimal("0.11"))

    def test_c3_heat_default_resolves_for_standard_effective_dates_and_custom_periods(self) -> None:
        from packages.application.catalog_queries import CatalogQueryService
        from packages.application.carbon_accounting import create_g06_parameter_resolver
        from packages.persistence import SQLiteCatalogRepository, build_catalog_database

        temporary_root = Path("build/pf01-test-tmp")
        temporary_root.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=temporary_root) as directory:
            catalog_path = Path(directory) / "catalog.sqlite"
            build_catalog_database(output_path=catalog_path)
            repository = SQLiteCatalogRepository(catalog_path)
            catalog = CatalogQueryService(repository)
            resolver = create_g06_parameter_resolver(repository)
            implementation_date = catalog.standard_implementation_date(STANDARD_ID)
            self.assertEqual(implementation_date, date(2025, 3, 1))
            cases = (
                (
                    "entirely_before",
                    AccountingPeriod(PeriodType.ANNUAL, date(2024, 1, 1), date(2024, 12, 31)),
                    "heat_default_gbt32151_34_c3",
                    "BEFORE",
                ),
                (
                    "crosses",
                    AccountingPeriod(PeriodType.CUSTOM, date(2025, 2, 1), date(2025, 3, 31)),
                    "heat_default_gbt32151_34_c3",
                    "CROSSES",
                ),
                (
                    "after",
                    AccountingPeriod(PeriodType.ANNUAL, date(2026, 1, 1), date(2026, 12, 31)),
                    "heat_default_2025",
                    "AFTER",
                ),
            )
            for case_name, period, expected_factor_id, expected_relation in cases:
                with self.subTest(case=case_name, period=period, expected=expected_factor_id):
                    outcome = CarbonMaterialCalculator(
                        parameter_resolver=resolver,
                        standard_implementation_date=implementation_date,
                    ).calculate(
                        _input(
                            period=period,
                            purchased_heat=(HeatInput(
                                "purchased-heat", "1", unit="t", manual_enthalpy=False,
                                pressure_mpa="0.1", factor_mode=HeatFactorMode.STANDARD_DEFAULT,
                            ),),
                            exported_heat=(HeatInput(
                                "exported-heat", "0.5", unit="t", manual_enthalpy=False,
                                pressure_mpa="0.1", factor_mode=HeatFactorMode.STANDARD_DEFAULT,
                            ),),
                        ),
                        calculated_at=SNAPSHOT_AT,
                    )
                    self.assertTrue(outcome.successful, outcome.problems)
                    heat_snapshots = {
                        snapshot.detail_id: snapshot.factor_id
                        for snapshot in outcome.parameter_snapshots
                        if snapshot.parameter_id == "heat_emission_factor_default"
                    }
                    self.assertEqual(
                        heat_snapshots,
                        {"purchased-heat": expected_factor_id, "exported-heat": expected_factor_id},
                    )
                    warnings = [
                        problem
                        for problem in outcome.problems
                        if problem.code == "CAR-VAL-STANDARD-IMPLEMENTATION-PERIOD"
                    ]
                    self.assertEqual(len(warnings), 1)
                    self.assertEqual(warnings[0].level, IssueLevel.WARNING)
                    self.assertEqual(dict(warnings[0].details)["period_relation"], expected_relation)
                    self.assertIsNotNone(outcome.record)
                    self.assertIsNotNone(outcome.result)
                    assert outcome.record is not None
                    assert outcome.result is not None
                    self.assertIn(warnings[0], outcome.result.problems)
                    self.assertIn(warnings[0], outcome.record.problems)
                    self.assertEqual(outcome.record.status.value, "COMPLETED_WITH_WARNINGS")
                    self.assertIsNotNone(outcome.record)
                    assert outcome.record is not None

    def test_c1_heat_conversion_uses_standard_parameter_snapshots(self) -> None:
        fuels = (
            FuelInput(
                "diesel-default", FuelPath.MASS, "1",
                ParameterValue("diesel_carbon_content", "0.0202", "tC/GJ", source_location="C.1"),
                ParameterValue("diesel_oxidation_rate", "0.98", "ratio", source_location="C.1"),
                ParameterValue("diesel_lhv", "42.652", "GJ/t", source_location="C.1"),
                fuel_type=FuelType.DIESEL,
            ),
            FuelInput(
                "gas-default", FuelPath.VOLUME, "1",
                ParameterValue("natural_gas_carbon_content", "0.0153", "tC/GJ", source_location="C.1"),
                ParameterValue("natural_gas_oxidation_rate", "0.99", "ratio", source_location="C.1"),
                ParameterValue("natural_gas_lhv", "389.31", "GJ/10⁴Nm³", source_location="C.1"),
                fuel_type=FuelType.NATURAL_GAS,
            ),
            FuelInput(
                "heat-path", FuelPath.HEAT, "2",
                ParameterValue("heat_path_carbon", "0.0153", "tC/GJ", source_location="measured"),
                ParameterValue("heat_path_oxidation", "0.99", "ratio", source_location="C.1"),
                fuel_type=FuelType.NATURAL_GAS,
            ),
        )
        outcome = CarbonMaterialCalculator().calculate(_input(fuel_inputs=fuels), calculated_at=SNAPSHOT_AT)
        self.assertTrue(outcome.successful, outcome.problems)
        by_id = {line.line_id: line.amount for line in outcome.result.lines}
        expected_diesel = fuel_heat_emission(fuel_energy_from_mass("1", "42.652"), "0.0202", "0.98")
        expected_gas = fuel_heat_emission(fuel_energy_from_volume("1", "389.31"), "0.0153", "0.99")
        expected_heat = fuel_heat_emission("2", "0.0153", "0.99")
        self.assertLess(abs(by_id["CAR-SRC-FUEL-001.diesel-default"] - expected_diesel), Decimal("1e-24"))
        self.assertLess(abs(by_id["CAR-SRC-FUEL-001.gas-default"] - expected_gas), Decimal("1e-24"))
        self.assertLess(abs(by_id["CAR-SRC-FUEL-001.heat-path"] - expected_heat), Decimal("1e-24"))
        snapshots = {snapshot.parameter_id for snapshot in outcome.parameter_snapshots}
        self.assertTrue({"diesel_lhv", "diesel_carbon_content", "diesel_oxidation_rate", "natural_gas_lhv"}.issubset(snapshots))

    def test_heat_activity_path_cannot_apply_a_second_heating_value(self) -> None:
        records = InMemoryRecordRepository()
        outcome = CarbonMaterialCalculator(record_repository=records).calculate(
            _input(fuel_inputs=(FuelInput(
                "heat-with-lhv", FuelPath.HEAT, "1",
                ParameterValue("heat_carbon", "0.0153", "tC/GJ", source_location="test"),
                ParameterValue("heat_oxidation", "0.99", "ratio", source_location="test"),
                ParameterValue("inapplicable_lhv", "1", "GJ/GJ", source_location="test"),
            ),)),
            calculated_at=SNAPSHOT_AT,
        )
        self.assertTrue(outcome.blocked)
        self.assertTrue(any(problem.code == "CAR-VAL-FUEL-LHV-NOT-APPLICABLE" for problem in outcome.problems))
        self.assertIsNone(outcome.record)
        self.assertEqual(records.list_all(), ())

    def test_explicit_measured_carbonate_factor_keeps_source_and_is_accepted(self) -> None:
        measured = ParameterValue(
            "measured_carbonate_factor", "0.50", "tCO2/t", ParameterSourceKind.MEASURED,
            "TEST-LAB-2026-01", "2026", "report page 3", "measured factor test",
        )
        outcome = CarbonMaterialCalculator().calculate(
            _input(fgd=FGDInput(components=(CarbonateComponent("10", "0.90", measured, "1"),))),
            calculated_at=SNAPSHOT_AT,
        )
        self.assertTrue(outcome.successful, outcome.problems)
        factor_snapshot = next(s for s in outcome.parameter_snapshots if s.parameter_id == "measured_carbonate_factor")
        self.assertEqual(factor_snapshot.source_id, "TEST-LAB-2026-01")
        self.assertEqual(factor_snapshot.value_used, Decimal("0.50"))
        fgd_line = next(line for line in outcome.result.lines if line.line_id == "CAR-FLD-P04B-RESULT")
        self.assertEqual(fgd_line.amount, Decimal("4.500"))

    def test_superheated_without_enthalpy_does_not_use_saturated_table(self) -> None:
        outcome = CarbonMaterialCalculator().calculate(
            _input(purchased_heat=(
                HeatInput(
                    "superheated.heat",
                    "1000",
                    factor=_explicit_factor("heat_emission_factor_default", "0.11", "tCO2/GJ"),
                    steam_kind=SteamKind.SUPERHEATED,
                    pressure_mpa="1.0",
                    temperature_c="300",
                ),
            )),
            calculated_at=SNAPSHOT_AT,
        )
        self.assertTrue(outcome.successful, outcome.problems)
        heat_line = next(line for line in outcome.result.lines if line.line_id.endswith("superheated.heat"))
        self.assertEqual(heat_line.amount, Decimal("0.335643"))

        missing_temperature = CarbonMaterialCalculator().calculate(
            _input(purchased_heat=(
                HeatInput(
                    "superheated.missing-temperature",
                    "1000",
                    steam_kind=SteamKind.SUPERHEATED,
                    pressure_mpa="1.0",
                ),
            )),
            calculated_at=SNAPSHOT_AT,
        )
        self.assertTrue(missing_temperature.blocked)
        self.assertTrue(any(problem.code == "CAR-VAL-STEAM-STATE" for problem in missing_temperature.problems))

    def test_exported_electricity_and_heat_are_subtracted_independently(self) -> None:
        outcome = CarbonMaterialCalculator(parameter_resolver=_resolver()).calculate(
            _input(
                electricity_details=(
                    _detail("power.in", "100", ElectricityAcquisitionMode.PURCHASED, ElectricityAttribute.ORDINARY),
                ),
                exported_electricity=(
                    ElectricityOutputLine("power.out", "2", _explicit_factor("power", "0.5", "tCO2/MWh")),
                ),
                purchased_heat=(
                    HeatInput("heat.in", "1000", "2800", _explicit_factor("heat", "0.11", "tCO2/GJ")),
                ),
                exported_heat=(
                    HeatInput("heat.out", "100", "2800", _explicit_factor("heat", "0.11", "tCO2/GJ")),
                ),
            ),
            calculated_at=SNAPSHOT_AT,
        )
        self.assertTrue(outcome.successful, outcome.problems)
        indirect = next(line for line in outcome.result.lines if line.line_id == "CAR-FLD-INDIRECT-RESULT")
        self.assertEqual(indirect.amount, Decimal("52.3372"))
        self.assertTrue(any(line.line_id == "CAR-FLD-POWER-EXPORTED-RESULT.power.out" for line in outcome.result.lines))
        self.assertTrue(any(line.line_id == "CAR-FLD-HEAT-EXPORTED-RESULT.heat.out" for line in outcome.result.lines))

    def test_missing_proof_blocks_without_zero_or_national_fallback(self) -> None:
        detail = _detail(
            "power.missing.proof", "20", ElectricityAcquisitionMode.PURCHASED,
            ElectricityAttribute.NONFOSSIL, proof_type=ElectricityProofType.GEC,
        )
        repository = InMemoryRecordRepository()
        outcome = CarbonMaterialCalculator(
            parameter_resolver=_resolver(), record_repository=repository
        ).calculate(_input(electricity_details=(detail,)), calculated_at=SNAPSHOT_AT)

        self.assertTrue(outcome.blocked)
        self.assertIsNone(outcome.record)
        self.assertEqual(repository.list_all(), ())
        self.assertTrue(any(problem.code == "CAR-VAL-GREEN-ELECTRICITY-EVIDENCE" for problem in outcome.problems))
        self.assertEqual(outcome.parameter_snapshots, ())

    def test_missing_canonical_zero_blocks_without_average_fallback(self) -> None:
        detail = _detail(
            "power.missing.zero", "20", ElectricityAcquisitionMode.PURCHASED,
            ElectricityAttribute.NONFOSSIL, proof_type=ElectricityProofType.CONTRACT_AND_SETTLEMENT,
            proof_status=ElectricityProofStatus.VALID,
        )
        outcome = CarbonMaterialCalculator(parameter_resolver=_resolver(include_zero=False)).calculate(
            _input(electricity_details=(detail,)), calculated_at=SNAPSHOT_AT
        )

        self.assertTrue(outcome.blocked)
        self.assertTrue(any(problem.code == "GEN-VAL-NONFOSSIL-ZERO-FACTOR-MISSING" for problem in outcome.problems))
        self.assertEqual(outcome.parameter_snapshots, ())
        self.assertNotIn("electricity_national_average_2024", {snapshot.factor_id for snapshot in outcome.parameter_snapshots})

    def test_self_consumed_fossil_is_blocked_or_explicitly_transferred(self) -> None:
        fossil_detail = _detail(
            "power.self.fossil", "15", ElectricityAcquisitionMode.SELF_CONSUMED,
            ElectricityAttribute.FOSSIL,
        )
        blocked = CarbonMaterialCalculator(parameter_resolver=_resolver()).calculate(
            _input(electricity_details=(fossil_detail,)), calculated_at=SNAPSHOT_AT
        )
        self.assertTrue(blocked.blocked)
        self.assertTrue(any(problem.code == "GEN-VAL-SELF-CONSUMED-FOSSIL-ROUTE" for problem in blocked.problems))
        self.assertIsNone(blocked.result)
        self.assertIsNone(blocked.record)

        linked_fuel = FuelInput("fossil-fuel", __import__(
            "packages.standards.carbon_material", fromlist=["FuelPath"]
        ).FuelPath.VOLUME, "1", "0.1", "1", electricity_detail_id="power.self.fossil")
        transferred = CarbonMaterialCalculator(parameter_resolver=_resolver()).calculate(
            _input(input_id="input.linked.fossil", electricity_details=(fossil_detail,), fuel_inputs=(linked_fuel,)),
            calculated_at=SNAPSHOT_AT,
        )
        self.assertTrue(transferred.successful)
        self.assertTrue(any(problem.code == "CAR-ROUTE-SELF-CONSUMED-FOSSIL" for problem in transferred.problems))
        self.assertFalse(any(line.emission_source_id == SOURCE_PURCHASED_ELECTRICITY for line in transferred.result.lines))

    def test_boundary_other_standard_and_fgd_required_validation(self) -> None:
        no_boundary = CarbonMaterialCalculator().calculate(
            _input(boundary_confirmed=False), calculated_at=SNAPSHOT_AT
        )
        self.assertTrue(any(problem.code == "CAR-VAL-BOUNDARY-UNCONFIRMED" for problem in no_boundary.problems))

        other_activity = CarbonMaterialCalculator().calculate(
            _input(other_activity_present=True), calculated_at=SNAPSHOT_AT
        )
        self.assertTrue(any(problem.code == "CAR-VAL-OTHER-STANDARD" for problem in other_activity.problems))

        fgd_missing = CarbonMaterialCalculator().calculate(
            _input(
                source_states=(EmissionSourceState(SOURCE_FGD, EmissionSourceStatus.INVOLVED),),
                fgd=FGDInput(),
            ),
            calculated_at=SNAPSHOT_AT,
        )
        self.assertTrue(any(
            problem.code == "GEN-VAL-REQUIRED-MISSING"
            and problem.field_id.startswith(f"{SOURCE_FGD}.")
            for problem in fgd_missing.problems
        ))

    def test_fixed_and_volatile_component_kinds_are_validated_independently(self) -> None:
        cases = (
            (CalcinationInput, {"gc": "10"}, "CAR-SRC-CALCINATION-001"),
            (BakingInput, {"bpm": "10"}, "CAR-SRC-BAKING-001"),
            (GraphitizationInput, {"gpm": "10"}, "CAR-SRC-GRAPHITIZATION-001"),
        )
        for input_type, values, source_id in cases:
            wrong_fixed = input_type(
                **values,
                fixed_carbon_component_kind=MaterialComponentKind.VOLATILE_MATTER,
                volatile_matter_component_kind=MaterialComponentKind.VOLATILE_MATTER,
            )
            outcome = CarbonMaterialCalculator().calculate(
                _input(source_states=(EmissionSourceState(source_id, EmissionSourceStatus.INVOLVED),), **{
                    {"CAR-SRC-CALCINATION-001": "calcination", "CAR-SRC-BAKING-001": "baking", "CAR-SRC-GRAPHITIZATION-001": "graphitization"}[source_id]: wrong_fixed,
                }),
                calculated_at=SNAPSHOT_AT,
            )
            self.assertTrue(any(
                problem.code == "CAR-VAL-MATERIAL-COMPONENT-KIND"
                and problem.field_id.startswith(f"{source_id}.")
                and problem.field_id.endswith(".fixed-carbon")
                for problem in outcome.problems
            ))

            wrong_volatile = input_type(
                **values,
                fixed_carbon_component_kind=MaterialComponentKind.FIXED_CARBON,
                volatile_matter_component_kind=MaterialComponentKind.FIXED_CARBON,
            )
            outcome = CarbonMaterialCalculator().calculate(
                _input(source_states=(EmissionSourceState(source_id, EmissionSourceStatus.INVOLVED),), **{
                    {"CAR-SRC-CALCINATION-001": "calcination", "CAR-SRC-BAKING-001": "baking", "CAR-SRC-GRAPHITIZATION-001": "graphitization"}[source_id]: wrong_volatile,
                }),
                calculated_at=SNAPSHOT_AT,
            )
            self.assertTrue(any(
                problem.code == "CAR-VAL-MATERIAL-COMPONENT-KIND"
                and problem.field_id.startswith(f"{source_id}.")
                and problem.field_id.endswith(".volatile-matter")
                for problem in outcome.problems
            ))

    def test_material_basis_and_duplicate_output_validation(self) -> None:
        negative = CalcinationInput(
            gc="1", wfc="0.01", cc="2", ucc="0", du="0", wfc_c="0.01",
            wvar="0", wvar_c="0", k1="0.35",
        )
        negative_outcome = CarbonMaterialCalculator().calculate(
            _input(calcination=negative), calculated_at=SNAPSHOT_AT
        )
        self.assertTrue(any(problem.code == "CAR-VAL-MATERIAL-BALANCE-NEGATIVE" for problem in negative_outcome.problems))

        duplicate = CalcinationInput(
            gc="100", wfc="0.008", cc="70", ucc="5", du="1", wfc_c="0.002",
            wvar="0.10", wvar_c="0.02", k1="0.35", carbon_output_included_in_input=True,
        )
        duplicate_outcome = CarbonMaterialCalculator().calculate(
            _input(input_id="input.duplicate", calcination=duplicate), calculated_at=SNAPSHOT_AT
        )
        self.assertTrue(any(problem.code == "CAR-VAL-CARBON-OUTPUT-DUPLICATE" for problem in duplicate_outcome.problems))


if __name__ == "__main__":
    unittest.main()
