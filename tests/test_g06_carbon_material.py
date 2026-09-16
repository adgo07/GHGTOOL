from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal
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
    FumeIncinerationInput,
    GraphitizationInput,
    HeatInput,
    InMemoryRecordRepository,
    InputValue,
    ParameterValue,
    MaterialComponentKind,
    SteamKind,
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
    return CarbonMaterialInput(
        input_id=kwargs.pop("input_id", "input.g06"),
        enterprise_id=ENTERPRISE_ID,
        enterprise_name="G06 测试企业",
        period=PERIOD,
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
        enthalpy, interpolated, endpoints = saturated_steam_enthalpy("1.75")
        self.assertEqual(enthalpy, Decimal("2794.45"))
        self.assertTrue(interpolated)
        self.assertEqual(endpoints, (Decimal("1.70"), Decimal("1.80")))
        superheated, superheated_interpolated, superheated_endpoints = superheated_steam_enthalpy("1.5", "325")
        self.assertTrue(superheated_interpolated)
        self.assertEqual(superheated_endpoints, (Decimal("1"), Decimal("3")))
        self.assertGreater(superheated, Decimal("3000"))
        with self.assertRaises(ValueError):
            superheated_steam_enthalpy("31", "300")


class G06CalculatorTests(unittest.TestCase):
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
                self.assertTrue(
                    any(problem.code == "CAR-VAL-PERCENT-RANGE" for problem in outcome.problems),
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
        default_k1 = CarbonMaterialCalculator().calculate(
            _input(calcination=CalcinationInput(
                gc="1", wfc="0", cc="0", ucc="0", du="0", wfc_c="0", wvar="0", wvar_c="0",
            )),
            calculated_at=SNAPSHOT_AT,
        )
        self.assertTrue(default_k1.successful)
        self.assertTrue(any(problem.code == "CAR-VAL-K1-DEFAULT" for problem in default_k1.problems))
        self.assertIn("CAR-PAR-K1", {snapshot.parameter_id for snapshot in default_k1.parameter_snapshots})

        default_fgd = CarbonMaterialCalculator().calculate(
            _input(fgd=FGDInput(cal="10")), calculated_at=SNAPSHOT_AT
        )
        self.assertTrue(default_fgd.successful, default_fgd.problems)
        self.assertTrue(any(problem.code == "CAR-VAL-I-DEFAULT" for problem in default_fgd.problems))
        self.assertTrue(any(problem.code == "CAR-VAL-TR-DEFAULT" for problem in default_fgd.problems))
        self.assertTrue({"CAR-PAR-P04B-I", "CAR-PAR-P04B-TR"}.issubset(
            {snapshot.parameter_id for snapshot in default_fgd.parameter_snapshots}
        ))

        default_heat = CarbonMaterialCalculator().calculate(
            _input(purchased_heat=(HeatInput("default.heat", "1000", "2800"),)),
            calculated_at=SNAPSHOT_AT,
        )
        self.assertTrue(default_heat.successful, default_heat.problems)
        self.assertTrue(any(problem.code == "CAR-VAL-HEAT-FACTOR-DEFAULT" for problem in default_heat.problems))

    def test_superheated_without_enthalpy_does_not_use_saturated_table(self) -> None:
        outcome = CarbonMaterialCalculator().calculate(
            _input(purchased_heat=(
                HeatInput(
                    "superheated.heat",
                    "1000",
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
        self.assertFalse(any(line.emission_source_id == SOURCE_PURCHASED_ELECTRICITY for line in blocked.result.lines))

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
        self.assertTrue(any(problem.code == "GEN-VAL-REQUIRED-MISSING" and problem.field_id == SOURCE_FGD for problem in fgd_missing.problems))

    def test_fixed_and_volatile_component_kinds_are_validated_independently(self) -> None:
        wrong_fixed = CalcinationInput(
            gc="10", fixed_carbon_component_kind=MaterialComponentKind.VOLATILE_MATTER,
            volatile_matter_component_kind=MaterialComponentKind.VOLATILE_MATTER,
        )
        outcome = CarbonMaterialCalculator().calculate(
            _input(calcination=wrong_fixed), calculated_at=SNAPSHOT_AT
        )
        self.assertTrue(any(
            problem.code == "CAR-VAL-MATERIAL-COMPONENT-KIND"
            and problem.field_id == "CAR-SRC-CALCINATION-001.fixed-carbon"
            for problem in outcome.problems
        ))

        wrong_volatile = CalcinationInput(
            gc="10", fixed_carbon_component_kind=MaterialComponentKind.FIXED_CARBON,
            volatile_matter_component_kind=MaterialComponentKind.FIXED_CARBON,
        )
        outcome = CarbonMaterialCalculator().calculate(
            _input(calcination=wrong_volatile), calculated_at=SNAPSHOT_AT
        )
        self.assertTrue(any(
            problem.code == "CAR-VAL-MATERIAL-COMPONENT-KIND"
            and problem.field_id == "CAR-SRC-CALCINATION-001.volatile-matter"
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
